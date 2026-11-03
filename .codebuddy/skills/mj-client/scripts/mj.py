#!/usr/bin/env python3
"""Midjourney 客户端 CLI（zhongwenmj.aitoptop.cn / channels/001/007 前端同源 API）。

仅依赖 Python 标准库。所有命令输出 JSON 到 stdout，错误写到 stderr 并以非 0 退出。

用法见 `python scripts/mj.py --help` 或 SKILL.md。
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

BASE_URL = os.environ.get("MJ_BASE_URL", "https://zhongwenmj.aitoptop.cn")
DEFAULT_CACHE_DIR = Path(os.environ.get("MJ_CACHE_DIR", Path.home() / ".mj-client"))
DEFAULT_TIMEOUT = 30

# 前端默认设置兜底（账号里没保存设置时用；实际以 /api/user/auth 返回的 settings 为准）
DEFAULT_SETTINGS_MJ = {
    "model": "--v 8.2",
    "style": "",
    "stylize": 100,
    "remix": False,
    "variation": "high",
    "speed": "fast",
}
DEFAULT_SETTINGS_NIJI = {
    "model": "--niji 7",
    "style": "",
    "stylize": 100,
    "remix": False,
    "variation": "high",
    "speed": "fast",
}

# 站点 settings 下拉里可选的模型：MJ 已到 v8.2，Niji 最高仅 v7（无 --niji 8.x）
MODELS_MJ = ["", "--v 8.2", "--v 7", "--v 6.1", "--v 6.0", "--v 6",
             "--v 5.2", "--v 5.1", "--v 5", "--v 4", "--v 3", "--v 2", "--v 1"]
MODELS_NIJI = ["--niji 7", "--niji 6", "--niji 5", "--niji 4"]
SUPPORTED_MODELS = set(MODELS_MJ) | set(MODELS_NIJI)

TERMINAL_STATUS = {"SUCCESS", "FAILURE", "CANCEL"}


class MJError(Exception):
    def __init__(self, message: str, payload=None):
        super().__init__(message)
        self.payload = payload


def _stdout_utf8() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def jprint(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


class MJClient:
    def __init__(self, base_url: str = BASE_URL, auth_code: str | None = None,
                 cache_dir: Path = DEFAULT_CACHE_DIR, timeout: int = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.cache_dir = Path(cache_dir)
        self.timeout = timeout
        self._auth_code = auth_code
        self._state = self._load_state()

    # ---------- 认证 ----------

    def _state_path(self) -> Path:
        return self.cache_dir / "state.json"

    def _load_state(self) -> dict:
        try:
            return json.loads(self._state_path().read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_state(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._state_path().write_text(
            json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _find_auth_code() -> str | None:
        """按优先级查找 Auth Code：环境变量 -> 工作区/上级目录 AUTH_CODE.txt -> 缓存目录。"""
        env = os.environ.get("MJ_AUTH_CODE")
        if env:
            return env.strip()
        here = Path(__file__).resolve()
        for root in [Path.cwd(), *here.parents, Path.home() / ".mj-client"]:
            for name in ("AUTH_CODE.txt", "auth_code.txt"):
                candidate = root / name
                if candidate.is_file():
                    value = candidate.read_text(encoding="utf-8").strip()
                    if value:
                        return value
        return None

    def auth_code(self) -> str:
        code = self._auth_code or self._state.get("auth_code") or self._find_auth_code()
        if not code:
            raise MJError(
                "未找到 Auth Code。使用 --auth-code <CODE>、设置环境变量 MJ_AUTH_CODE，"
                "或在项目根目录放置 AUTH_CODE.txt。")
        return code

    @property
    def token(self) -> str | None:
        return self._state.get("token")

    def _token_valid(self) -> bool:
        token = self._state.get("token")
        exp = self._state.get("token_exp")
        if not token:
            return False
        if exp and time.time() > float(exp) - 60:
            return False
        return True

    @staticmethod
    def _jwt_exp(token: str) -> float | None:
        try:
            payload = token.split(".")[1]
            payload += "=" * (-len(payload) % 4)
            data = json.loads(base64.urlsafe_b64decode(payload))
            return float(data.get("exp")) if data.get("exp") else None
        except Exception:
            return None

    def login(self, force: bool = False) -> dict:
        if not force and self._token_valid():
            return self._state
        code = self.auth_code()
        res = self.request("POST", "/api/user/auth", {"username": code}, auth=False)
        data = res.get("data") or {}
        self._state = {
            "auth_code": code,
            "token": data.get("token"),
            "token_exp": self._jwt_exp(data.get("token") or "") or time.time() + 86400 * 6,
            "username": data.get("username"),
            "dc_username": (data.get("user_info") or {}).get("dc_username"),
            "settings": (data.get("user_info") or {}).get("settings") or {},
        }
        self._save_state()
        return self._state

    def ensure_token(self) -> str:
        self.login()
        return self._state["token"]

    # ---------- HTTP ----------

    def request(self, method: str, path: str, body=None, auth: bool = True,
                content_type: str = "application/json", require_success: bool = True) -> dict:
        url = path if path.startswith("http") else self.base_url + path
        data = None
        if body is not None:
            data = body if isinstance(body, (bytes, bytearray)) else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, method=method.upper())
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "mj-client/1.0")
        if data is not None:
            req.add_header("Content-Type", content_type)
        if auth:
            req.add_header("Authorization", "Bearer " + self.ensure_token())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(raw)
            except Exception:
                raise MJError("HTTP %s: %s" % (exc.code, raw[:500]))
            if auth and parsed.get("code") in (401, 1100):
                self.login(force=True)
                req.add_header("Authorization", "Bearer " + self.ensure_token())
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8", "replace")
                parsed = json.loads(raw)
            if require_success and not parsed.get("success"):
                raise MJError("API %s: %s" % (parsed.get("code"), parsed.get("msg")), parsed)
            return parsed
        except urllib.error.URLError as exc:
            raise MJError("网络错误: %s" % exc.reason)

        try:
            parsed = json.loads(raw)
        except Exception:
            raise MJError("响应不是 JSON: %s" % raw[:500])
        if auth and parsed.get("code") in (401, 1100):
            self.login(force=True)
            req.add_header("Authorization", "Bearer " + self.ensure_token())
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                parsed = json.loads(resp.read().decode("utf-8", "replace"))
        if require_success and not parsed.get("success"):
            raise MJError("API %s: %s" % (parsed.get("code"), parsed.get("msg")), parsed)
        return parsed

    def get(self, path, auth=True, require_success=True):
        return self.request("GET", path, auth=auth, require_success=require_success)

    def post(self, path, body=None, auth=True):
        return self.request("POST", path, body if body is not None else {}, auth=auth)

    def delete(self, path, auth=True):
        return self.request("DELETE", path, auth=auth)

    # ---------- 业务封装 ----------

    def settings_for(self, bot_type: str, overrides: dict | None = None) -> dict:
        saved = (self._state.get("settings") or {})
        base = dict(DEFAULT_SETTINGS_NIJI if bot_type == "NIJI_JOURNEY" else DEFAULT_SETTINGS_MJ)
        base.update(saved.get(bot_type) or {})
        for key, value in (overrides or {}).items():
            if value is not None:
                base[key] = value
        return base

    def imagine(self, prompt: str, bot_type="MID_JOURNEY", settings=None) -> dict:
        return self.post("/api/msg/interaction", {
            "type": bot_type,
            "action": "IMAGINE",
            "data": {"settings": self.settings_for(bot_type, settings), "prompt": prompt},
        })

    def describe(self, image_url: str, bot_type="MID_JOURNEY", settings=None) -> dict:
        return self.post("/api/msg/interaction", {
            "type": bot_type,
            "action": "DESCRIBE",
            "data": {"settings": self.settings_for(bot_type, settings), "image_url": image_url},
        })

    def blend(self, image_urls: list, bot_type="MID_JOURNEY", settings=None) -> dict:
        return self.post("/api/msg/interaction", {
            "type": bot_type,
            "action": "BLEND",
            "data": {"settings": self.settings_for(bot_type, settings), "img_url_array": list(image_urls)},
        })

    def action(self, bot_type: str, task_id, custom_id: str, settings=None) -> dict:
        return self.post("/api/msg/interaction", {
            "type": bot_type,
            "action": "ACTION",
            "data": {"settings": self.settings_for(bot_type, settings),
                     "task_id": task_id, "custom_id": custom_id},
        })

    def modal(self, bot_type: str, task_id, prompt: str, parent_task_id=None,
              mask_base64: str | None = None, settings=None) -> dict:
        payload = {"settings": self.settings_for(bot_type, settings), "task_id": task_id, "prompt": prompt}
        if parent_task_id is not None:
            payload["parent_task_id"] = parent_task_id
        if mask_base64 is not None:
            payload["mask_base64"] = mask_base64
        return self.post("/api/msg/interaction", {
            "type": bot_type, "action": "MODAL", "data": payload})

    def seed(self, bot_type: str, task_id, settings=None) -> dict:
        return self.post("/api/msg/interaction", {
            "type": bot_type,
            "action": "SEED",
            "data": {"settings": self.settings_for(bot_type, settings), "task_id": task_id},
        })

    def cancel(self, bot_type: str, task_id, settings=None) -> dict:
        return self.post("/api/msg/interaction", {
            "type": bot_type,
            "action": "CANCEL",
            "data": {"settings": self.settings_for(bot_type, settings), "task_id": task_id},
        })

    def send_message(self, content: str) -> dict:
        return self.post("/api/msg/interaction", {
            "type": "MSG", "action": "MSG", "data": {"message_content": content}})

    def message_list(self, page_size=10, before=0) -> dict:
        return self.post("/api/msg/list", {"page_size": page_size, "before": before})

    def message_by_id(self, msg_id) -> dict | None:
        """POST /api/msg/ids，返回单条消息（服务端 data 可能是数组或 {list:[...]}）。"""
        res = self.post("/api/msg/ids", {"msg_ids": [msg_id]})
        data = res.get("data")
        if isinstance(data, list):
            return data[0] if data else None
        data = data or {}
        items = data.get("list") or []
        if items:
            return items[0]
        return data if "id" in data else None

    def delete_message(self, msg_id) -> dict:
        return self.delete("/api/msg/delete/%s" % msg_id)

    def wait_message(self, msg_id, interval=5, timeout=900, quiet=False) -> dict:
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            msg = self.message_by_id(msg_id)
            if msg:
                last = msg
                if not quiet:
                    print("[wait] %s status=%s progress=%s" % (
                        msg_id, msg.get("status"), (msg.get("task") or {}).get("progress")),
                        file=sys.stderr)
                if msg.get("status") in TERMINAL_STATUS:
                    return msg
            time.sleep(interval)
        raise MJError("等待超时（%ss），最后状态: %s" % (timeout, (last or {}).get("status")), last)

    # ---------- 文件上传（阿里云 OSS 直传） ----------

    def upload_file(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.is_file():
            raise MJError("文件不存在: %s" % file_path)
        sig = self.post("/api/file/oss/signature", {})["data"]
        host = sig["host"]
        ext = path.suffix.lstrip(".")
        key = sig["dir"].rstrip("/") + "/" + (uuid.uuid4().hex + ("." + ext if ext else ""))
        fields = {
            "key": key,
            "policy": sig["policy"],
            "OSSAccessKeyId": sig["accessid"],
            "success_action_status": "200",
            "signature": sig["signature"],
            "callback": sig["callback"],
            "x:filename": path.name,
        }
        body, content_type = _multipart(fields, "file", path.name, path.read_bytes())
        raw = self.request("POST", host, body, content_type=content_type)
        data = raw.get("data") or {}
        url = data.get("file_url") or data.get("url") or raw.get("file_url")
        if not url:
            raise MJError("上传成功但未返回文件地址: %s" % json.dumps(raw, ensure_ascii=False)[:500])
        return url

    def upload_file_direct(self, file_path: str) -> str:
        """POST /api/file/upload：直传到站点自身存储（multipart，字段名 file）。

        注意：该接口返回的 file_url 形如 https://zhongwenmj.aitoptop.cn/static/<user>_<name>，
        实测公网路径暂未开放（404），默认仍走 upload_file()（OSS）。
        """
        path = Path(file_path)
        if not path.is_file():
            raise MJError("文件不存在: %s" % file_path)
        ctype = {
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp", ".gif": "image/gif",
        }.get(path.suffix.lower(), "application/octet-stream")
        body, content_type = _multipart({}, "file", path.name, path.read_bytes(), ctype)
        raw = self.request("POST", "/api/file/upload", body, content_type=content_type)
        data = raw.get("data") or {}
        url = data.get("file_url") or raw.get("file_url")
        if not url:
            raise MJError("上传成功但未返回文件地址: %s" % json.dumps(raw, ensure_ascii=False)[:500])
        return url

    def upload(self, file_path: str, method: str = "oss") -> str:
        """按 method 选择上传通道：oss（默认，可用）/ direct（新接口，URL 暂不可达）。"""
        if method == "direct":
            return self.upload_file_direct(file_path)
        return self.upload_file(file_path)

    def resolve_target(self, value: str, method: str = "oss") -> str:
        """本地路径先上传，否则按 URL 原样返回。"""
        if value.startswith(("http://", "https://")):
            return value
        return self.upload(value, method)


def _multipart(fields: dict, file_field: str, filename: str, content: bytes,
               file_content_type: str = "application/octet-stream"):
    boundary = "----mjFormBoundary" + uuid.uuid4().hex
    buf = bytearray()
    for key, value in fields.items():
        buf += ("--%s\r\n" % boundary).encode()
        buf += ('Content-Disposition: form-data; name="%s"\r\n\r\n' % key).encode("utf-8")
        buf += str(value).encode("utf-8") + b"\r\n"
    buf += ("--%s\r\n" % boundary).encode()
    buf += ('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (file_field, filename)).encode("utf-8")
    buf += ("Content-Type: %s\r\n\r\n" % file_content_type).encode("utf-8")
    buf += content + b"\r\n"
    buf += ("--%s--\r\n" % boundary).encode()
    return bytes(buf), "multipart/form-data; boundary=" + boundary


# ------------------------------ CLI ------------------------------

def _settings_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--type", default="MID_JOURNEY", choices=["MID_JOURNEY", "NIJI_JOURNEY"])
    parser.add_argument("--model", help='模型后缀，如 "--v 7"、"--niji 6"')
    parser.add_argument("--style", help="风格值，生成 --style <value>")
    parser.add_argument("--stylize", type=int, help="风格化 0-1000")
    parser.add_argument("--speed", choices=["relax", "fast", "turbo"], help="出图模式")
    parser.add_argument("--variation", choices=["high", "low"])
    parser.add_argument("--remix", dest="remix", action="store_true", default=None)
    parser.add_argument("--no-remix", dest="remix", action="store_false")


def _settings_from_args(args) -> dict:
    return {k: v for k, v in {
        "model": args.model, "style": args.style, "stylize": args.stylize,
        "speed": args.speed, "variation": args.variation, "remix": args.remix,
    }.items() if v is not None}


def _warn_unknown_model(model: str | None) -> None:
    """模型值不在站点下拉列表里时给个提示（不阻断，MJ 仍可能接受）。"""
    if model and model not in SUPPORTED_MODELS:
        print("[warn] 模型 %s 不在已知列表中（MJ: %s / Niji: %s），仍会原样提交。" % (
            model, ", ".join(m or "(默认)" for m in MODELS_MJ[:6]), ", ".join(MODELS_NIJI)),
            file=sys.stderr)


def _maybe_wait(client: MJClient, res: dict, wait: bool, interval: int, timeout: int):
    """提交任务后，若返回 msg_id 且需要等待，则轮询到终态。"""
    info = res.get("data") or {}
    msg_id = info.get("msg_id")
    if not wait or not msg_id:
        return res
    if not msg_id:
        # MODAL/局部重绘等场景直接返回 prompt，无 msg_id
        return res
    final = client.wait_message(msg_id, interval=interval, timeout=timeout)
    return {"submit": res, "message": final}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mj", description="Midjourney API 客户端")
    parser.add_argument("--auth-code", help="Auth Code（默认读取 AUTH_CODE.txt / MJ_AUTH_CODE）")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--cache-dir", default=str(DEFAULT_CACHE_DIR))
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth", help="登录并缓存 token（同时返回配额与默认设置）")
    sub.add_parser("app-info", help="GET /api/app/info 首页信息")
    sub.add_parser("me", help="GET /api/user/info 账户与配额")
    sub.add_parser("models", help="列出可选模型（含 --v 8.2 / --niji 7）及账号默认设置")

    p = sub.add_parser("list", help="POST /api/msg/list 消息列表")
    p.add_argument("--page-size", type=int, default=10)
    p.add_argument("--before", type=int, default=0, help="分页游标：已加载最早消息的 submit_time")
    p.add_argument("--pages", type=int, default=1, help="连续翻页数")

    p = sub.add_parser("get", help="POST /api/msg/ids 按 id 查询消息")
    p.add_argument("msg_id")

    p = sub.add_parser("wait", help="轮询消息直到 SUCCESS/FAILURE/CANCEL")
    p.add_argument("msg_id")
    p.add_argument("--interval", type=int, default=5)
    p.add_argument("--timeout", type=int, default=900)

    p = sub.add_parser("imagine", help="提交绘图任务")
    p.add_argument("prompt")
    _settings_args(p)
    p.add_argument("--ar", help='追加画幅后缀，如 "16:9"')
    p.add_argument("--suffix", help="追加任意 MJ 参数后缀，如 '--no text --raw'（注意写 --raw，不是 --style raw）")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--interval", type=int, default=5)
    p.add_argument("--timeout", type=int, default=900)

    p = sub.add_parser("describe", help="以图生文（图片 URL 或本地路径）")
    p.add_argument("image")
    _settings_args(p)
    p.add_argument("--upload-method", choices=["oss", "direct"], default="oss",
                   help="本地图上传通道（默认 oss；direct 走新的 /api/file/upload）")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--interval", type=int, default=5)
    p.add_argument("--timeout", type=int, default=900)

    p = sub.add_parser("blend", help="图片融合（2~5 张，URL 或本地路径）")
    p.add_argument("images", nargs="+")
    _settings_args(p)
    p.add_argument("--upload-method", choices=["oss", "direct"], default="oss",
                   help="本地图上传通道（默认 oss；direct 走新的 /api/file/upload）")
    p.add_argument("--wait", action="store_true")
    p.add_argument("--interval", type=int, default=5)
    p.add_argument("--timeout", type=int, default=900)

    p = sub.add_parser("action", help="点击消息按钮：U1-U4 / V1-V4 / reroll / 自定义 custom_id")
    p.add_argument("msg_id")
    p.add_argument("button", help="按钮标签（U1、V2、reroll、🔄）或 MJ:: 开头的 custom_id")
    _settings_args(p)
    p.add_argument("--wait", action="store_true")
    p.add_argument("--interval", type=int, default=5)
    p.add_argument("--timeout", type=int, default=900)

    p = sub.add_parser("modal", help="弹出式提交（Remix / 局部重绘 Inpaint）")
    p.add_argument("--msg-id", help="来源消息 id，用于自动取 task_id / parent_task_id / prompt")
    p.add_argument("--task-id")
    p.add_argument("--parent-task-id")
    p.add_argument("--prompt")
    p.add_argument("--mask-file", help="局部重绘遮罩 PNG（自动 base64）")
    _settings_args(p)
    p.add_argument("--wait", action="store_true")
    p.add_argument("--interval", type=int, default=5)
    p.add_argument("--timeout", type=int, default=900)

    p = sub.add_parser("seed", help="查询任务 seed")
    p.add_argument("--msg-id", help="消息 id，自动解析 task_id 与 type")
    p.add_argument("--task-id")
    _settings_args(p)

    p = sub.add_parser("cancel", help="取消任务")
    p.add_argument("--msg-id")
    p.add_argument("--task-id")
    _settings_args(p)

    p = sub.add_parser("msg", help="发送普通聊天消息")
    p.add_argument("content")

    p = sub.add_parser("delete", help="DELETE /api/msg/delete/{id}")
    p.add_argument("msg_id")

    p = sub.add_parser("upload", help="上传本地图片并返回 URL")
    p.add_argument("file")
    p.add_argument("--method", choices=["oss", "direct"], default="oss",
                   help="oss=阿里云直传（默认，返回的 URL 可直接用）；"
                        "direct=新的 /api/file/upload（返回的 /static/ URL 目前公网 404）")

    p = sub.add_parser("raw", help="直接调用任意接口")
    p.add_argument("method", choices=["GET", "POST", "DELETE", "PUT"])
    p.add_argument("path", help='以 / 开头的路径，如 /api/msg/list')
    p.add_argument("--body", help="JSON 请求体字符串，或 @file.json")
    return parser


def _resolve_button(msg: dict, button: str) -> str:
    if button.startswith("MJ::") or "::" in button:
        return button
    buttons = (msg.get("task") or {}).get("buttons") or []
    target = button.strip().lower()
    if target in ("reroll", "🔄", "retry"):
        for b in buttons:
            if "reroll" in (b.get("custom_id") or ""):
                return b["custom_id"]
    for b in buttons:
        label = (b.get("label") or "").strip().lower()
        emoji = (b.get("emoji") or "").strip()
        if target == label or target == emoji:
            return b["custom_id"]
    raise MJError("未找到按钮 %s，可用: %s" % (
        button, ", ".join((b.get("label") or b.get("emoji") or b.get("custom_id")) for b in buttons)))


def _task_id_of(msg: dict):
    return (msg.get("task") or {}).get("id")


def main(argv=None) -> int:
    _stdout_utf8()
    args = build_parser().parse_args(argv)
    client = MJClient(base_url=args.base_url, auth_code=args.auth_code,
                      cache_dir=Path(args.cache_dir))
    try:
        if args.cmd == "auth":
            jprint(client.login(force=True))
            return 0
        if args.cmd == "app-info":
            # 该接口响应没有 success 字段，跳过信封校验
            jprint(client.get("/api/app/info", auth=False, require_success=False))
            return 0

        client.ensure_token()

        if args.cmd == "me":
            jprint(client.get("/api/user/info"))

        elif args.cmd == "models":
            jprint({
                "MID_JOURNEY": MODELS_MJ,
                "NIJI_JOURNEY": MODELS_NIJI,
                "saved_settings": client._state.get("settings") or {},
            })

        elif args.cmd == "list":
            collected, before, pagination = [], args.before, None
            for _ in range(args.pages):
                res = client.message_list(page_size=args.page_size, before=before)
                data = res["data"]
                items = data.get("list") or []
                pagination = data.get("pagination")
                collected.extend(items)
                if not items or len(items) < args.page_size:
                    break
                times = [m.get("submit_time") for m in items if m.get("submit_time")]
                before = min(times) if times else before
            jprint({"list": collected, "pagination": pagination})

        elif args.cmd == "get":
            msg = client.message_by_id(args.msg_id)
            if not msg:
                raise MJError("消息不存在: %s" % args.msg_id)
            jprint(msg)

        elif args.cmd == "wait":
            jprint(client.wait_message(args.msg_id, interval=args.interval, timeout=args.timeout))

        elif args.cmd == "imagine":
            prompt = args.prompt
            if args.ar:
                prompt = "%s --ar %s" % (prompt.strip(), args.ar)
            if args.suffix:
                prompt = "%s %s" % (prompt.strip(), args.suffix.strip())
            _warn_unknown_model(args.model)
            res = client.imagine(prompt, args.type, _settings_from_args(args))
            jprint(_maybe_wait(client, res, args.wait, args.interval, args.timeout))

        elif args.cmd == "describe":
            url = client.resolve_target(args.image, args.upload_method)
            res = client.describe(url, args.type, _settings_from_args(args))
            jprint(_maybe_wait(client, res, args.wait, args.interval, args.timeout))

        elif args.cmd == "blend":
            urls = [client.resolve_target(i, args.upload_method) for i in args.images]
            res = client.blend(urls, args.type, _settings_from_args(args))
            jprint(_maybe_wait(client, res, args.wait, args.interval, args.timeout))

        elif args.cmd == "action":
            msg = client.message_by_id(args.msg_id)
            if not msg:
                raise MJError("消息不存在: %s" % args.msg_id)
            custom_id = _resolve_button(msg, args.button)
            bot_type = msg.get("type") or args.type
            res = client.action(bot_type, _task_id_of(msg), custom_id, _settings_from_args(args))
            jprint(_maybe_wait(client, res, args.wait, args.interval, args.timeout))

        elif args.cmd == "modal":
            task_id, parent_task_id, prompt, bot_type = args.task_id, args.parent_task_id, args.prompt, args.type
            if args.msg_id:
                msg = client.message_by_id(args.msg_id)
                if not msg:
                    raise MJError("消息不存在: %s" % args.msg_id)
                task = msg.get("task") or {}
                task_id = task_id or task.get("id")
                parent_task_id = parent_task_id or task.get("parent_task_id")
                prompt = prompt or task.get("prompt_en") or task.get("prompt")
                bot_type = msg.get("type") or bot_type
            if not task_id:
                raise MJError("缺少 task_id（用 --task-id 或 --msg-id）")
            mask = None
            if args.mask_file:
                mask = base64.b64encode(Path(args.mask_file).read_bytes()).decode("ascii")
            res = client.modal(bot_type, task_id, prompt or "", parent_task_id, mask,
                               _settings_from_args(args))
            jprint(_maybe_wait(client, res, args.wait, args.interval, args.timeout))

        elif args.cmd == "seed":
            bot_type, task_id = args.type, args.task_id
            if args.msg_id:
                msg = client.message_by_id(args.msg_id)
                if not msg:
                    raise MJError("消息不存在: %s" % args.msg_id)
                bot_type, task_id = msg.get("type") or bot_type, _task_id_of(msg)
            if not task_id:
                raise MJError("缺少 task_id")
            jprint(client.seed(bot_type, task_id, _settings_from_args(args)))

        elif args.cmd == "cancel":
            bot_type, task_id = args.type, args.task_id
            if args.msg_id:
                msg = client.message_by_id(args.msg_id)
                if not msg:
                    raise MJError("消息不存在: %s" % args.msg_id)
                bot_type, task_id = msg.get("type") or bot_type, _task_id_of(msg)
            if not task_id:
                raise MJError("缺少 task_id")
            jprint(client.cancel(bot_type, task_id, _settings_from_args(args)))

        elif args.cmd == "msg":
            jprint(client.send_message(args.content))

        elif args.cmd == "delete":
            jprint(client.delete_message(args.msg_id))

        elif args.cmd == "upload":
            jprint({"file_url": client.upload(args.file, args.method), "method": args.method})

        elif args.cmd == "raw":
            body = None
            if args.body:
                if args.body.startswith("@"):
                    body = json.loads(Path(args.body[1:]).read_text(encoding="utf-8"))
                else:
                    body = json.loads(args.body)
            jprint(client.request(args.method, args.path, body))
        return 0
    except MJError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        if exc.payload:
            print(json.dumps(exc.payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
