"""MJ 图库本地服务（FastAPI 版）。

为 gallery/index.html 提供两个能力：
1. `GET /api/list` —— 代理 zhongwenmj 的消息列表接口（自动用 Auth Code 换 token）
2. `GET /dl`       —— 代理下载原图并加 Content-Disposition（原图 CDN 无 CORS 头，
                      浏览器无法直接 fetch 成 Blob，必须由同域服务端转发）

启动：`python server.py [--port 8321] [--no-open]`，浏览器打开 http://localhost:8321
或：`uvicorn server:app --port 8321`
"""

from __future__ import annotations

import argparse
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
from fastapi import FastAPI, HTTPException, Path as PathParam, Query
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

_token_cache: dict[str, Any] = {"token": None, "exp": 0.0}
# 服务端保存的用户默认设置（登录时从 user_info.settings 读取），提交任务时作为基底
_settings_cache: dict[str, Any] = {}
_client: httpx.AsyncClient | None = None

# 前端可选的画图 option（值需与上游 settings 字段一致）
BOT_TYPES = {"MID_JOURNEY", "NIJI_JOURNEY"}
SPEEDS = {"relax", "fast", "turbo"}
# 2026-10 起站点已支持 MJ 8.2 / Niji 8.2（取自前端 settings 下拉）
MODELS = {"", "--v 8.2", "--v 7", "--v 6.1", "--v 6.0", "--v 6", "--niji 8.2", "--niji 7", "--niji 6"}
MODELS_MJ = {"", "--v 8.2", "--v 7", "--v 6.1", "--v 6.0", "--v 6"}
MODELS_NIJI = {"--niji 8.2", "--niji 7", "--niji 6"}
DEFAULT_SETTINGS = {
    "MID_JOURNEY": {"model": "--v 8.2", "style": "", "stylize": 100,
                    "remix": False, "variation": "high", "speed": "fast"},
    "NIJI_JOURNEY": {"model": "--niji 8.2", "style": "", "stylize": 100,
                     "remix": False, "variation": "high", "speed": "fast"},
}


# ------------------------------ 认证 ------------------------------

class UpstreamError(Exception):
    """上游接口返回错误。"""


def find_auth_code() -> str | None:
    """按优先级查找 Auth Code：环境变量 -> 项目/上级目录 AUTH_CODE.txt -> 缓存目录。"""
    env = os.environ.get("MJ_AUTH_CODE")
    if env:
        return env.strip()
    for root in [Path.cwd(), *HERE.parents, Path.home() / ".mj-client"]:
        for name in ("AUTH_CODE.txt", "auth_code.txt"):
            candidate = root / name
            if candidate.is_file():
                value = candidate.read_text(encoding="utf-8").strip()
                if value:
                    return value
    return None


def _jwt_exp(token: str) -> float:
    import base64

    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return float(json.loads(base64.urlsafe_b64decode(payload)).get("exp") or 0)
    except Exception:
        return 0.0


def _load_cached_token() -> tuple[str, float] | None:
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        token, exp = state.get("token"), float(state.get("token_exp") or 0)
        if token and time.time() < exp - 60:
            return token, exp
    except Exception:
        pass
    return None


async def get_token(force: bool = False) -> str:
    """返回有效 token：优先复用缓存，否则用 Auth Code 重新登录。"""
    if not force:
        if _token_cache["token"] and time.time() < _token_cache["exp"] - 60:
            return _token_cache["token"]
        cached = _load_cached_token()
        if cached:
            _token_cache.update(token=cached[0], exp=cached[1])
            try:  # 复用缓存 token 时，顺带取回上次保存的用户设置
                state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                _settings_cache.clear()
                _settings_cache.update(state.get("settings") or {})
            except Exception:
                pass
            return cached[0]
    if force:
        _token_cache.update(token=None, exp=0.0)

    code = find_auth_code()
    if not code:
        raise HTTPException(
            status_code=500,
            detail="未找到 Auth Code：请设置 MJ_AUTH_CODE 或在项目根目录放置 AUTH_CODE.txt")

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
    _token_cache.update(token=token, exp=exp)
    _settings_cache.clear()
    _settings_cache.update((data.get("user_info") or {}).get("settings") or {})
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({
            "auth_code": code,
            "token": token,
            "token_exp": exp,
            "username": data.get("username"),
            "dc_username": (data.get("user_info") or {}).get("dc_username"),
            "settings": (data.get("user_info") or {}).get("settings") or {},
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
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
    """用户默认设置 -> 本次 overrides 合并后的 settings（同上游 /api/user/auth 的字段）。"""
    base = dict(DEFAULT_SETTINGS.get(bot_type) or DEFAULT_SETTINGS["MID_JOURNEY"])
    base.update(_settings_cache.get(bot_type) or {})
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


# ------------------------------ 应用 ------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    _client = httpx.AsyncClient(headers={"Accept": "application/json",
                                         "User-Agent": "mj-gallery/1.0"})
    try:
        await get_token()
        print("已登录（token 缓存于 %s）" % STATE_FILE)
    except Exception as exc:  # noqa: BLE001
        print("警告：登录失败 —— %s" % exc, file=sys.stderr)
    yield
    await _client.aclose()
    _client = None


app = FastAPI(title="MJ Gallery", version="1.0", lifespan=lifespan)


@app.get("/", response_class=FileResponse, include_in_schema=False)
@app.get("/index.html", response_class=FileResponse, include_in_schema=False)
async def index():
    if not INDEX_FILE.is_file():
        raise HTTPException(status_code=404, detail="index.html 不存在")
    return FileResponse(INDEX_FILE, media_type="text/html; charset=utf-8")


@app.get("/api/list", response_model=MessageList, summary="最近生成的消息列表")
async def message_list(
    page_size: int = Query(20, ge=1, le=50, description="每页条数"),
    before: int = Query(0, ge=0, description="分页游标：已加载最早消息的 submit_time"),
):
    res = await upstream("POST", "/api/msg/list", {"page_size": page_size, "before": before})
    data = res.get("data") or {}
    return MessageList(list=data.get("list") or [], pagination=data.get("pagination") or {})


@app.get("/api/user/info", summary="账户与剩余额度")
async def user_info():
    res = await upstream("GET", "/api/user/info")
    return res.get("data") or {}


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
