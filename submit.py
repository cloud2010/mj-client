#!/usr/bin/env python3
"""批量提交 MJ 任务的最小封装。

用法：
  python submit.py prompts/tiangong-ue5.json --dry-run          # 只预览，不花钱
  python submit.py prompts/tiangong-ue5.json                    # 提交全部，立即返回 msg_id
  python submit.py prompts/tiangong-ue5.json --only tg01,tg04   # 只提交指定场景
  python submit.py prompts/tiangong-ue5.json --wait             # 提交并轮询到出图完成
  python submit.py prompts/tiangong-ue5.json --speed relax --stylize 400
  python submit.py --status runs/tiangong-ue5_20260930-120000.json   # 补轮询上次结果
  python submit.py prompts/tiangong-ue5.json --balance          # 只看额度

结果写入 runs/<name>_<timestamp>.json，并在每次更新时同步生成同名 .md 报告。
"""

import argparse
import datetime as dt
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_MJ = ROOT / ".codebuddy" / "skills" / "mj-client" / "scripts" / "mj.py"
RUNS = ROOT / "runs"


# ---------------------------------------------------------------- MJ 模块

def load_mj(mj_path: Path):
    if not mj_path.is_file():
        sys.exit("找不到 MJ 脚本: %s" % mj_path)
    spec = importlib.util.spec_from_file_location("mjmod", str(mj_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pick_image(msg: dict) -> str:
    if not msg:
        return ""
    for key in ("image_url", "cdn_image_url", "thumbnail_image_url"):
        if msg.get(key):
            return msg[key]
    urls = msg.get("image_urls") or []
    return urls[0].get("url", "") if urls else ""


# ---------------------------------------------------------------- 配置

def load_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for key in ("defaults", "items"):
        if key not in cfg:
            sys.exit("配置缺少字段: %s" % key)
    return cfg


def build_prompt(item: dict, defaults: dict) -> str:
    params = item.get("params", defaults.get("params", "")).strip()
    prompt = item["prompt"].strip()
    return ("%s %s" % (prompt, params)).strip() if params else prompt


def resolve_settings(item: dict, defaults: dict, overrides: dict) -> dict:
    settings = dict(defaults.get("settings") or {})
    settings.update(item.get("settings") or {})
    settings.update({k: v for k, v in overrides.items() if v is not None})
    return settings


# ---------------------------------------------------------------- 日志

class Run:
    def __init__(self, path: Path, name: str, config_path: Path):
        self.path = path
        self.data = {
            "name": name,
            "config": str(config_path),
            "created": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": [],
        }

    def upsert(self, rec: dict):
        for i, old in enumerate(self.data["items"]):
            if old["id"] == rec["id"]:
                self.data["items"][i] = rec
                break
        else:
            self.data["items"].append(rec)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.write_md()

    def write_md(self):
        md = self.path.with_suffix(".md")
        lines = ["# %s" % self.data["name"], "",
                 "- 配置：`%s`" % self.data["config"],
                 "- 提交时间：%s" % self.data["created"],
                 "- 日志文件：`%s`" % self.path.name, ""]
        lines += ["| id | 场景 | msg_id | 状态 | 预览 |",
                  "|----|------|--------|------|------|"]
        for r in self.data["items"]:
            preview = "[图](%s)" % r["image_url"] if r.get("image_url") else "-"
            lines.append("| %s | %s | %s | %s | %s |" % (
                r["id"], r.get("title", ""), r.get("msg_id") or "-",
                r.get("status") or "-", preview))
        lines += ["", "## 提示词", ""]
        for r in self.data["items"]:
            lines += ["### %s %s" % (r["id"], r.get("title", "")),
                      "```", r.get("prompt", ""), "```", ""]
        md.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------- 命令

def show_balance(mj, client):
    info = client.get("/api/user/info")
    data = info.get("data") or {}
    user = data.get("user_info") or data
    print(json.dumps({
        "nickname": user.get("nickname") or user.get("name"),
        "credits": user.get("credits") or user.get("remaining") or user.get("balance"),
        "raw_keys": list(user.keys()),
    }, ensure_ascii=False, indent=2))


def submit_once(mj, client, prompt, bot_type, settings, retries, delay):
    last = None
    for attempt in range(retries + 1):
        try:
            res = client.imagine(prompt, bot_type, settings)
            return (res.get("data") or {}).get("msg_id"), None
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < retries:
                print("  [retry %s] %s" % (attempt + 1, exc), file=sys.stderr)
                time.sleep(delay)
    return None, last


def poll(mj, client, rec, args):
    msg = client.wait_message(rec["msg_id"], interval=args.interval, timeout=args.timeout)
    rec["status"] = msg.get("status")
    rec["image_url"] = pick_image(msg)
    rec["prompt_en"] = (msg.get("task") or {}).get("prompt_en")
    rec["finished"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return rec


def cmd_submit(args):
    mj = load_mj(Path(args.mj))
    client = mj.MJClient()
    client.ensure_token()

    if args.balance:
        show_balance(mj, client)

    cfg = load_config(Path(args.config))
    defaults = cfg["defaults"]
    items = cfg["items"]
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        items = [i for i in items if i["id"] in wanted]
    if args.limit:
        items = items[: args.limit]

    if args.resume:
        resume_path = Path(args.resume)
        run = Run(resume_path, cfg.get("name", Path(args.config).stem), Path(args.config))
        run.data = json.loads(resume_path.read_text(encoding="utf-8"))
        done = {r["id"] for r in run.data["items"] if r.get("status") == "SUCCESS"}
        items = [i for i in items if i["id"] not in done]
        print("续跑 %s，已完成 %s 条，剩余 %s 条" % (
            resume_path.name, len(done), len(items)), file=sys.stderr)
    else:
        run = Run(RUNS / ("%s_%s.json" % (Path(args.config).stem,
                                          dt.datetime.now().strftime("%Y%m%d-%H%M%S"))),
                  cfg.get("name", Path(args.config).stem), Path(args.config))

    overrides = {"speed": args.speed, "stylize": args.stylize,
                 "model": args.model, "style": args.style}
    bot_type = args.type or defaults.get("type", "MID_JOURNEY")

    for idx, item in enumerate(items):
        prompt = build_prompt(item, defaults)
        settings = resolve_settings(item, defaults, overrides)
        print("[%s/%s] %s %s" % (idx + 1, len(items), item["id"], item.get("title", "")))
        print("  %s" % prompt)

        rec = {"id": item["id"], "title": item.get("title", ""),
               "prompt": prompt, "type": bot_type, "status": None,
               "msg_id": None, "image_url": None}

        # 续跑时，若该条之前已成功提交过，只补轮询，不重复扣额度
        prev = next((r for r in run.data["items"]
                     if r["id"] == item["id"] and r.get("msg_id")
                     and r.get("status") != "SUBMIT_FAILED"), None)
        if prev:
            print("  已有 msg_id=%s，跳过重复提交" % prev["msg_id"])
            rec = dict(prev)
            if args.wait and rec.get("status") != "SUCCESS":
                rec = poll(mj, client, rec, args)
                print("  %s -> %s" % (rec["status"], rec["image_url"]))
            run.upsert(rec)
            run.save()
            continue

        if args.dry_run:
            rec["status"] = "DRY_RUN"
            run.upsert(rec)
            continue

        msg_id, err = submit_once(mj, client, prompt, bot_type, settings,
                                  args.retries, args.retry_delay)
        if not msg_id:
            rec["status"] = "SUBMIT_FAILED"
            rec["error"] = str(err)
            print("  ERROR: %s" % err, file=sys.stderr)
            run.upsert(rec)
            run.save()
            continue

        rec["msg_id"] = msg_id
        rec["status"] = "SUBMITTED"
        print("  msg_id=%s" % msg_id)
        run.upsert(rec)
        run.save()

        if args.wait:
            rec = poll(mj, client, rec, args)
            print("  %s -> %s" % (rec["status"], rec["image_url"]))
            run.upsert(rec)
            run.save()

        if idx < len(items) - 1:
            time.sleep(args.gap)

    run.save()
    print("\n完成：%s" % run.path)
    print("报告：%s" % run.path.with_suffix(".md"))
    if not args.wait:
        print("轮询结果：python submit.py --status %s" % run.path)


def cmd_status(args):
    mj = load_mj(Path(args.mj))
    client = mj.MJClient()
    client.ensure_token()

    path = Path(args.status)
    data = json.loads(path.read_text(encoding="utf-8"))
    run = Run(path, data.get("name", path.stem), Path(data.get("config", "")))
    run.data = data

    pending = [r for r in run.data["items"] if r.get("msg_id") and r.get("status") != "SUCCESS"]
    for rec in pending:
        try:
            poll(mj, client, rec, args)
            print("%s %s -> %s" % (rec["id"], rec["status"], rec["image_url"]))
        except Exception as exc:  # noqa: BLE001
            rec["status"] = rec.get("status") or "UNKNOWN"
            rec["error"] = str(exc)
            print("%s 轮询失败: %s" % (rec["id"], exc), file=sys.stderr)
    run.save()
    print("报告：%s" % path.with_suffix(".md"))


def build_parser():
    p = argparse.ArgumentParser(description="批量提交 Midjourney 任务")
    p.add_argument("config", nargs="?", help="提示词配置文件（JSON）")
    p.add_argument("--mj", default=str(DEFAULT_MJ), help="mj.py 路径")
    p.add_argument("--only", help="只提交指定 id，逗号分隔")
    p.add_argument("--limit", type=int, help="只提交前 N 条")
    p.add_argument("--type", choices=["MID_JOURNEY", "NIJI_JOURNEY"], help="覆盖机器人类型")
    p.add_argument("--model", help='模型，如 "--v 8.2" / "--niji 8.2"')
    p.add_argument("--stylize", type=int)
    p.add_argument("--style")
    p.add_argument("--speed", choices=["relax", "fast", "turbo"])
    p.add_argument("--dry-run", action="store_true", help="只打印提示词，不提交")
    p.add_argument("--resume", help="续跑已有 runs/*.json，跳过已成功的条目")
    p.add_argument("--balance", action="store_true", help="提交前打印账户额度")
    p.add_argument("--wait", action="store_true", help="提交后轮询到出图完成")
    p.add_argument("--gap", type=float, default=2.0, help="两次提交之间的间隔秒数")
    p.add_argument("--retries", type=int, default=2)
    p.add_argument("--retry-delay", type=float, default=5.0)
    p.add_argument("--interval", type=int, default=5, help="轮询间隔秒数")
    p.add_argument("--timeout", type=int, default=900, help="单条等待超时秒数")
    p.add_argument("--status", help="轮询已有 runs/*.json 的结果")
    return p


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = build_parser().parse_args()
    if args.status:
        cmd_status(args)
    elif args.config:
        cmd_submit(args)
    else:
        build_parser().print_help()


if __name__ == "__main__":
    main()
