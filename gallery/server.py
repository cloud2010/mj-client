"""MJ 图库本地服务（FastAPI 版）。

为 gallery/index.html（含外链的 app.css / app.js）提供能力：
1. `GET /api/codes` —— 列出 AUTH_CODE.txt 中的全部 Auth Code（多账号切换）
2. `GET /api/list` —— 代理 zhongwenmj 的消息列表接口（自动用 Auth Code 换 token）
3. `GET /dl`       —— 代理下载原图并加 Content-Disposition（原图 CDN 无 CORS 头，
                      浏览器无法直接 fetch 成 Blob，必须由同域服务端转发）

多账号：AUTH_CODE.txt 支持 `AUTHCODE_N=xxx` 每行一个；前端带 `X-Auth-Code` 头（值为
/api/codes 返回的 key）即可按账号出图库/额度，token 与用户设置均按 code 分桶缓存。

启动：`python server.py [--port 8321] [--no-open]`，浏览器打开 http://localhost:8321
或：`uvicorn server:app --port 8321`
"""

from __future__ import annotations

import argparse
import contextvars
import html as html_mod
import json
import mimetypes
import os
import re
import sys
import threading
import time
import urllib.parse
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, List

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Path as PathParam, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

UPSTREAM = "https://zhongwenmj.aitoptop.cn"
# 仅允许转发这两个图片域名，避免 SSRF
ALLOWED_IMAGE_HOSTS = {"imagine-cdn.youchuan.cn", "cdn.aitoptop.cn"}
STATE_FILE = Path.home() / ".mj-client" / "state.json"
HERE = Path(__file__).resolve().parent
INDEX_FILE = HERE / "index.html"
DEFAULT_PORT = 8321
UPSTREAM_TIMEOUT = 30.0
DOWNLOAD_TIMEOUT = 120.0
# 扫描最近多少条消息来找进行中的任务（站点并发上限 2，取 12 足够）
TASK_SCAN_SIZE = 12

# 消息状态：未开始 / 已提交 / 进行中 都算"进行中"；后三者为终态
ACTIVE_STATUS = {"NOT_START", "SUBMITTED", "IN_PROGRESS"}
TERMINAL_STATUS = {"SUCCESS", "FAILURE", "CANCEL"}

# 每个 Auth Code 一份 token / 用户设置：
#   _token_cache[code] = {"token": str, "exp": float}
#   _settings_cache[code] = {BOT_TYPE: settings}
_token_cache: dict[str, dict[str, Any]] = {}
_settings_cache: dict[str, dict[str, Any]] = {}
# 请求级上下文：当前请求选中的 Auth Code key（由中间件从 X-Auth-Code 头解析）
_current_key: contextvars.ContextVar[str] = contextvars.ContextVar("current_key", default="")
_client: httpx.AsyncClient | None = None

# 前端可选的画图 option（值需与上游 settings 字段一致）
BOT_TYPES = {"MID_JOURNEY", "NIJI_JOURNEY"}
SPEEDS = {"relax", "fast", "turbo"}
# 2026-10 起站点已支持 MJ 8.2 / Niji 8.2（取自前端 settings 下拉）
MODELS = {"", "--v 8.2", "--v 7", "--v 6.1", "--v 6.0", "--v 6", "--niji 8.2", "--niji 7", "--niji 6"}
MODELS_MJ = {"", "--v 8.2", "--v 7", "--v 6.1", "--v 6.0", "--v 6"}
MODELS_NIJI = {"--niji 8.2", "--niji 7", "--niji 6"}
# --q 质量可选值（MJ 官方口径；站点 settings 不含此参数，故拼进提示词）
QUALITY_VALUES = ("0.25", "0.5", "1", "2")
DEFAULT_SETTINGS = {
    "MID_JOURNEY": {"model": "--v 8.2", "style": "", "stylize": 100,
                    "remix": False, "variation": "high", "speed": "fast"},
    "NIJI_JOURNEY": {"model": "--niji 8.2", "style": "", "stylize": 100,
                     "remix": False, "variation": "high", "speed": "fast"},
}


# ------------------------------ 认证 ------------------------------

class UpstreamError(Exception):
    """上游接口返回错误。"""


def _parse_auth_codes(text: str) -> List[tuple[str, str]]:
    """解析 AUTH_CODE.txt：支持 `AUTHCODE_N=xxx` 每行一个（# 开头为注释），兼容整文件只有一个裸 code。"""
    found: List[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and value:
                found.append((key, value))
        else:
            found.append(("", line))
    out, n = [], 0
    for key, value in found:
        if not key:  # 裸 code 自动编号
            n += 1
            key = "AUTHCODE_%d" % n
        out.append((key, value))
    return out


def mask_code(code: str) -> str:
    """脱敏展示：2610190057... -> 2610****wDbr"""
    if len(code) <= 10:
        return code[:2] + "****"
    return "%s****%s" % (code[:4], code[-4:])


# AUTH_CODE.txt 内容缓存，mtime 变了才重新读取
_codes_cache: dict[str, Any] = {"mtime": None, "codes": []}


def load_auth_codes() -> List[tuple[str, str]]:
    """可用的 (key, code) 列表：环境变量 MJ_AUTH_CODE 优先（单 code），其次 AUTH_CODE.txt。"""
    env = os.environ.get("MJ_AUTH_CODE")
    if env:
        return [("MJ_AUTH_CODE", env.strip())]
    for root in [Path.cwd(), *HERE.parents, Path.home() / ".mj-client"]:
        for name in ("AUTH_CODE.txt", "auth_code.txt"):
            candidate = root / name
            if candidate.is_file():
                try:
                    mtime = candidate.stat().st_mtime
                    if _codes_cache["mtime"] == mtime:
                        return _codes_cache["codes"]
                    codes = _parse_auth_codes(candidate.read_text(encoding="utf-8"))
                    _codes_cache.update(mtime=mtime, codes=codes)
                    return codes
                except Exception:  # noqa: BLE001
                    pass
    return []


def _jwt_exp(token: str) -> float:
    import base64

    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return float(json.loads(base64.urlsafe_b64decode(payload)).get("exp") or 0)
    except Exception:
        return 0.0


def selected_code() -> str:
    """当前请求要用的 Auth Code（中间件按 X-Auth-Code 头选择 key，缺省取第一个）。"""
    codes = load_auth_codes()
    if not codes:
        raise HTTPException(
            status_code=500,
            detail="未找到 Auth Code：请设置 MJ_AUTH_CODE 或在项目根目录放置 AUTH_CODE.txt")
    known = dict(codes)
    return known.get(_current_key.get("")) or codes[0][1]


def _load_cached_token(code: str) -> tuple[str, float] | None:
    cached = _token_cache.get(code)
    if cached and cached.get("token") and time.time() < cached["exp"] - 60:
        return cached["token"], cached["exp"]
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    entry = (state.get("tokens") or {}).get(code)
    if not entry and state.get("auth_code") == code:  # 兼容旧版单 code 状态文件
        entry = state
    if entry:
        token, exp = entry.get("token"), float(entry.get("token_exp") or 0)
        if token and time.time() < exp - 60:
            _token_cache[code] = {"token": token, "exp": exp}
            _settings_cache[code] = entry.get("settings") or {}
            return token, exp
    return None


async def get_token(force: bool = False) -> str:
    """返回有效 token：优先复用缓存，否则用 Auth Code 重新登录。"""
    code = selected_code()
    if not force:
        cached = _load_cached_token(code)
        if cached:
            return cached[0]
    if force:
        _token_cache.pop(code, None)

    assert _client is not None
    try:
        resp = await _client.post(UPSTREAM + "/api/user/auth", json={"username": code},
                                  timeout=UPSTREAM_TIMEOUT)
        res = resp.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="登录请求失败: %s" % exc)

    if not res.get("success"):
        raise HTTPException(status_code=502,
                            detail="登录失败 %s: %s" % (res.get("code"), res.get("msg")))

    data = res["data"]
    token = data["token"]
    exp = _jwt_exp(token) or time.time() + 86400 * 6
    user_info = data.get("user_info") or {}
    _token_cache[code] = {"token": token, "exp": exp}
    _settings_cache[code] = user_info.get("settings") or {}
    try:  # 状态文件按 code 分桶；顶层字段保留最近使用的 code（兼容 mj.py 读取）
        state: dict[str, Any] = {}
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
        entry = {"token": token, "token_exp": exp, "username": data.get("username"),
                 "dc_username": user_info.get("dc_username"),
                 "settings": user_info.get("settings") or {}}
        tokens = state.get("tokens") or {}
        tokens[code] = entry
        state.update(entry)
        state["auth_code"] = code
        state["tokens"] = tokens
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    return token


async def upstream(method: str, path: str, payload: dict | None = None,
                   retry: bool = True) -> dict:
    """调用上游 API，token 失效时自动重登一次。"""
    assert _client is not None
    token = await get_token()
    try:
        resp = await _client.request(
            method, UPSTREAM + path, json=payload,
            headers={"Authorization": "Bearer " + token},
            timeout=UPSTREAM_TIMEOUT)
        res = resp.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="上游请求失败: %s" % exc)

    # 1103=账号在别处登录（换 token 即可恢复），1100/401=token 失效
    if res.get("code") in (401, 1100, 1103) and retry:
        await get_token(force=True)
        return await upstream(method, path, payload, retry=False)
    if not res.get("success"):
        raise HTTPException(status_code=502,
                            detail="上游返回 %s: %s" % (res.get("code"), res.get("msg")))
    return res


def settings_for(bot_type: str, overrides: dict | None = None) -> dict:
    """当前账号默认设置 -> 本次 overrides 合并后的 settings（同上游 /api/user/auth 的字段）。"""
    base = dict(DEFAULT_SETTINGS.get(bot_type) or DEFAULT_SETTINGS["MID_JOURNEY"])
    base.update((_settings_cache.get(selected_code()) or {}).get(bot_type) or {})
    for key, value in (overrides or {}).items():
        if value is not None:
            base[key] = value
    return base


# ------------------------------ 响应模型 ------------------------------

class MessageList(BaseModel):
    # 字段名 list 会遮蔽内置 list，故用 typing.List 写注解
    list: List[dict] = Field(default_factory=list)
    pagination: dict = Field(default_factory=dict)


class ImagineRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="提示词（不含参数后缀）")
    bot_type: str = Field("MID_JOURNEY", description="MID_JOURNEY 或 NIJI_JOURNEY")
    model: str | None = Field(None, description="如 --v 7 / --niji 7")
    speed: str | None = Field(None, description="relax / fast / turbo")
    stylize: int | None = Field(None, ge=0, le=1000, description="--s 风格化值")
    variation: str | None = Field(None, description="high / low")
    ar: str | None = Field(None, description="画幅，如 16:9；留空则不加 --ar")
    hd: bool | None = Field(None, description="True 时在提示词末尾追加 --hd（高清）")
    quality: str | None = Field(None, description="--q 质量：0.25 / 0.5 / 1 / 2")
    style_raw: bool | None = Field(None, description="True 时追加 --raw（写实风格）")
    chaos: int | None = Field(None, ge=0, le=100, description="--chaos 变化度 0-100")


# ------------------------------ 应用 ------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    _client = httpx.AsyncClient(headers={"Accept": "application/json",
                                         "User-Agent": "mj-gallery/1.0"})
    try:
        await get_token()
        codes = load_auth_codes()
        print("已登录（加载 %d 个 Auth Code，token 缓存于 %s）" % (max(len(codes), 1), STATE_FILE))
    except Exception as exc:  # noqa: BLE001
        print("警告：登录失败 —— %s" % exc, file=sys.stderr)
    yield
    await _client.aclose()
    _client = None


app = FastAPI(title="MJ Gallery", version="1.0", lifespan=lifespan)


@app.middleware("http")
async def pick_code_middleware(request: Request, call_next):
    """按 X-Auth-Code 头选择本次请求的 Auth Code（值为 /api/codes 返回的 key）。

    未带或带了未知的 key 时回退到第一个 code；整条请求链路（含 upstream 重试）
    都通过 _current_key 上下文取值，无需逐个端点传参。
    """
    key = (request.headers.get("X-Auth-Code") or "").strip()
    codes = load_auth_codes()
    valid = key if key in {k for k, _ in codes} else (codes[0][0] if codes else "")
    ctx_token = _current_key.set(valid)
    try:
        return await call_next(request)
    finally:
        _current_key.reset(ctx_token)


@app.get("/", response_class=FileResponse, include_in_schema=False)
@app.get("/index.html", response_class=FileResponse, include_in_schema=False)
async def index():
    if not INDEX_FILE.is_file():
        raise HTTPException(status_code=404, detail="index.html 不存在")
    return FileResponse(INDEX_FILE, media_type="text/html; charset=utf-8",
                        headers={"Cache-Control": "no-cache"})


def _asset(name: str, media_type: str) -> FileResponse:
    """只暴露页面用到的两个静态文件，避免整个目录被下载。"""
    path = HERE / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="%s 不存在" % name)
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "no-cache"})


@app.get("/app.css", include_in_schema=False)
async def app_css():
    return _asset("app.css", "text/css; charset=utf-8")


@app.get("/app.js", include_in_schema=False)
async def app_js():
    return _asset("app.js", "application/javascript; charset=utf-8")


@app.get("/api/list", response_model=MessageList, summary="最近生成的消息列表")
async def message_list(
    page_size: int = Query(20, ge=1, le=50, description="每页条数"),
    before: int = Query(0, ge=0, description="分页游标：已加载最早消息的 submit_time"),
):
    res = await upstream("POST", "/api/msg/list", {"page_size": page_size, "before": before})
    data = res.get("data") or {}
    return MessageList(list=data.get("list") or [], pagination=data.get("pagination") or {})


def _task_view(msg: dict) -> dict:
    """把上游消息裁剪成前端画进度条需要的字段。"""
    task = msg.get("task") or {}
    prompt = task.get("prompt_en") or task.get("prompt") or msg.get("message_content") or ""
    return {
        "id": msg.get("id"),
        "status": msg.get("status") or task.get("status") or "",
        "type": msg.get("type") or "",
        "action": msg.get("action") or task.get("action") or "",
        "progress": task.get("progress"),
        "speed": task.get("real_speed_mode") or task.get("speed") or "",
        "model": task.get("model") or "",
        "prompt": re.sub(r"\*\*", "", str(prompt)).strip(),
        "submit_time": msg.get("submit_time") or 0,
        "start_time": msg.get("start_time") or 0,
        "finish_time": msg.get("finish_time") or 0,
        "fail_reason": task.get("fail_reason") or "",
    }


@app.get("/api/tasks", summary="进行中的任务及其进度")
async def tasks(ids: str = Query("", description="额外精确轮询的消息 id，逗号分隔（提交后跟踪用）")):
    """合并两路数据：ids 精确查询（含已结束的，供前端提示完成）+ 最近消息里的进行中任务。"""
    wanted = [int(p) for p in (x.strip() for x in ids.split(",")) if p.isdigit()][:20]

    found: dict[Any, dict] = {}
    if wanted:
        res = await upstream("POST", "/api/msg/ids", {"msg_ids": wanted})
        for msg in (res.get("data") or []):
            view = _task_view(msg)
            if view["id"] is not None:
                found[view["id"]] = view

    res = await upstream("POST", "/api/msg/list", {"page_size": TASK_SCAN_SIZE, "before": 0})
    for msg in ((res.get("data") or {}).get("list") or []):
        if msg.get("status") in ACTIVE_STATUS:
            view = _task_view(msg)
            found.setdefault(view["id"], view)

    # 进行中的排前面（按提交时间倒序），已结束的排后面
    out = sorted(found.values(),
                 key=lambda v: (v["status"] in TERMINAL_STATUS, -(v["submit_time"] or 0)))
    return {"tasks": out, "server_time": int(time.time())}


@app.get("/api/codes", summary="可用的 Auth Code 列表（多账号切换）")
async def codes():
    items = load_auth_codes()
    return {
        "default": items[0][0] if items else "",
        "codes": [{"key": key, "masked": mask_code(code)} for key, code in items],
    }


@app.get("/api/user/info", summary="当前账号的账户与剩余额度")
async def user_info():
    res = await upstream("GET", "/api/user/info")
    data = res.get("data") or {}
    # 上游返回的是 HTML 片段（content_html），顺手剥出纯文本给前端直接展示
    html_text = data.get("content_html") or ""
    text = re.sub(r"(?is)<script[^>]*>.*?</script>", "", html_text)
    text = re.sub(r"(?i)<(br|/p|/div|/li|/tr|/h[1-6])[^>]*>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_mod.unescape(text)
    lines = [ln.strip(" \t") for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    data["content_text"] = "\n".join(lines)

    # 结构化额度：当前套餐 FAST/RELAX/TURBO -> 可用 / 已用 / 套餐数量
    quota: dict[str, dict[str, Any]] = {}
    current = ""
    num = r"([\d,]+(?:\.\d+)?)"
    for ln in lines:
        pkg = re.search(r"\b(FAST|RELAX|TURBO)\b", ln, re.I)
        if pkg and "套餐" in ln:
            current = pkg.group(1).lower()
            quota.setdefault(current, {})
            continue
        if not current:
            continue
        if m := re.search(r"可用数量\s*:?\s*" + num, ln):
            quota[current]["available"] = float(m.group(1).replace(",", ""))
        elif m := re.search(r"已用数量\s*:?\s*" + num, ln):
            quota[current]["used"] = float(m.group(1).replace(",", ""))
        elif m := re.search(r"套餐数量\s*:?\s*" + num + r"\s*(\S+)?", ln):
            quota[current]["total"] = float(m.group(1).replace(",", ""))
            quota[current]["unit"] = m.group(2) or ""
    if quota:
        data["quota"] = quota
    return data


@app.get("/api/models", summary="可选的绘图模型与默认设置")
async def models():
    return {
        "bot_types": sorted(BOT_TYPES),
        "models": sorted(MODELS),
        "models_mj": sorted(MODELS_MJ),
        "models_niji": sorted(MODELS_NIJI),
        "speeds": sorted(SPEEDS),
        "settings": {k: settings_for(k) for k in sorted(BOT_TYPES)},
    }


@app.post("/api/imagine", summary="提交文生图任务")
async def imagine(req: ImagineRequest):
    bot_type = req.bot_type if req.bot_type in BOT_TYPES else "MID_JOURNEY"
    if req.model is not None and req.model not in MODELS:
        raise HTTPException(status_code=400, detail="不支持的模型: %s" % req.model)
    if req.speed is not None and req.speed not in SPEEDS:
        raise HTTPException(status_code=400, detail="不支持的出图模式: %s" % req.speed)
    if req.variation is not None and req.variation not in {"high", "low"}:
        raise HTTPException(status_code=400, detail="variation 只能是 high / low")

    prompt = req.prompt.strip()
    if req.ar:
        ar = req.ar.strip()
        if not re.fullmatch(r"\d{1,2}:\d{1,2}", ar):
            raise HTTPException(status_code=400, detail="画幅格式应为 宽:高，如 16:9")
        prompt = "%s --ar %s" % (prompt, ar)
    if req.hd:
        prompt = "%s --hd" % prompt
    if req.quality is not None:
        quality = req.quality.strip()
        if quality not in QUALITY_VALUES:
            raise HTTPException(status_code=400,
                                detail="--q 只能是 %s" % " / ".join(QUALITY_VALUES))
        prompt = "%s --q %s" % (prompt, quality)
    if req.style_raw:
        # 注意：这里必须是 --raw；写成 --style raw 上游会报错
        prompt = "%s --raw" % prompt
    if req.chaos is not None:
        prompt = "%s --chaos %d" % (prompt, req.chaos)

    # niji bot 只能吃 niji 模型；MJ bot 两者都收（与站点 settings 下拉一致）
    model = req.model
    if model and bot_type == "NIJI_JOURNEY" and model not in MODELS_NIJI:
        raise HTTPException(status_code=400,
                            detail="模型 %s 与 bot 类型 %s 不匹配" % (model, bot_type))

    res = await upstream("POST", "/api/msg/interaction", {
        "type": bot_type,
        "action": "IMAGINE",
        "data": {
            "settings": settings_for(bot_type, {
                "model": model, "speed": req.speed, "stylize": req.stylize,
                "variation": req.variation,
            }),
            "prompt": prompt,
        },
    })
    data = res.get("data") or {}
    return {"task_id": data.get("task_id"), "msg_id": data.get("msg_id"), "prompt": prompt}


@app.delete("/api/msg/{msg_id}", summary="删除指定消息（含其图片）")
async def delete_message(msg_id: int = PathParam(..., ge=1, description="要删除的消息 id")):
    await upstream("DELETE", "/api/msg/delete/%d" % msg_id)
    return {"ok": True, "id": msg_id}


@app.get("/dl", summary="下载原图（服务端转发并加附件头）")
async def download(
    url: str = Query(..., description="原图 URL，限 imagine-cdn / cdn.aitoptop.cn"),
    name: str = Query("image.png", description="下载文件名"),
):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_IMAGE_HOSTS:
        raise HTTPException(status_code=400, detail="非法的下载地址: %s" % url)

    assert _client is not None
    try:
        request = _client.build_request("GET", url, timeout=DOWNLOAD_TIMEOUT)
        resp = await _client.send(request, stream=True)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="图片下载失败: %s" % exc)
    if resp.status_code >= 400:
        await resp.aclose()
        raise HTTPException(status_code=502, detail="CDN 返回 %s" % resp.status_code)

    content_type = resp.headers.get("Content-Type") or mimetypes.guess_type(name)[0] \
        or "application/octet-stream"
    safe = "".join(c for c in name if c not in '\\/:*?"<>|\r\n') or "image.png"

    return StreamingResponse(
        resp.aiter_bytes(65536),
        media_type=content_type,
        headers={"Content-Disposition": "attachment; filename=\"%s\"; filename*=UTF-8''%s"
                                        % (safe, urllib.parse.quote(safe))},
        background=BackgroundTask(resp.aclose),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """把 FastAPI 默认 {"detail": ...} 统一成前端使用的 {"error": ...}。"""
    detail = exc.detail if isinstance(exc.detail, str) else json.dumps(exc.detail, ensure_ascii=False)
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(x) for x in first.get("loc", [])) or "参数"
    return JSONResponse(status_code=422, content={"error": "参数 %s 不合法: %s"
                                                  % (field, first.get("msg", ""))})


def main() -> int:
    parser = argparse.ArgumentParser(description="MJ 图库本地服务（FastAPI）")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--reload", action="store_true", help="开发模式，代码变更自动重启")
    parser.add_argument("--no-open", action="store_true", help="启动后不自动打开浏览器")
    args = parser.parse_args()

    url = "http://localhost:%d/" % args.port
    print("MJ 图库服务启动: %s（API 文档: %sdocs）" % (url, url))
    if not args.no_open:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
