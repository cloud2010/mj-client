---
name: mj-client
description: 通过 zhongwenmj.aitoptop.cn（中文 Midjourney 网页版 /channels/001/007）的同源私有 API 调用 Midjourney 出图。当用户要求用 Midjourney / MJ 生成图片、放大变体、以图生文、图片融合、局部重绘、查任务状态或管理 MJ 消息，或提到 zhongwenmj、aitoptop、Auth Code 出图时使用本 skill。使用 scripts/mj.py 命令行完成全部接口调用。
---

# Midjourney 客户端（zhongwenmj.aitoptop.cn）

用 `scripts/mj.py`（纯标准库 Python）访问该站点的全部后端接口，覆盖登录、出图、放大/变体、以图生文、融合、Remix/局部重绘、取种子、取消、删消息、图片上传。

## 何时使用

- 用户要用 Midjourney（含 niji）生成/编辑图片
- 用户要查询 MJ 任务状态、图片 URL、seed、剩余额度
- 用户提到 Auth Code / zhongwenmj / aitoptop 出图

## 运行环境

- 只需 Python 3.9+，无第三方依赖。
- 脚本路径：`<skill>/scripts/mj.py`。所有命令用 `python <path>/scripts/mj.py <cmd>` 调用。
- Auth Code 自动发现顺序：`--auth-code` → 环境变量 `MJ_AUTH_CODE` → 当前目录/上级目录 `AUTH_CODE.txt` → `~/.mj-client/`。本项目根目录已有 `AUTH_CODE.txt`，通常无需显式传入。
- Token 缓存在 `~/.mj-client/state.json`（含过期时间与用户设置），过期自动重新登录；可用 `--cache-dir` 改路径。

## 常用命令

```bash
python scripts/mj.py auth                       # 登录，缓存 token，返回套餐与默认设置
python scripts/mj.py me                         # 账户与剩余额度
python scripts/mj.py models                     # 可选模型清单（含 --v 8.2 / --niji 8.2）+ 账号默认设置
python scripts/mj.py list --page-size 10        # 历史消息（--pages N 连续翻页）

python scripts/mj.py imagine "a red panda in a bamboo forest" --ar 16:9 --model "--v 8.2" --speed fast
python scripts/mj.py imagine "<prompt>" --wait  # 提交并轮询到出图完成（推荐）
python scripts/mj.py wait <msg_id>              # 单独轮询某条消息
python scripts/mj.py get <msg_id>               # 查单条消息（含图片 URL 与按钮）

python scripts/mj.py action <msg_id> U1 --wait         # 放大第 1 张（U1~U4 / V1~V4 / reroll）
python scripts/mj.py action <msg_id> "MJ::JOB::upsample::1::<hash>"   # 直接给 custom_id

python scripts/mj.py describe ./local.png --wait            # 本地图自动上传后以图生文
python scripts/mj.py blend a.png b.png --wait               # 图片融合
python scripts/mj.py seed --msg-id <id>                     # 取 seed
python scripts/mj.py cancel --msg-id <id>                   # 取消任务
python scripts/mj.py modal --msg-id <id> --prompt "new prompt" --wait   # Remix
python scripts/mj.py modal --msg-id <id> --prompt "..." --mask-file mask.png --wait  # 局部重绘
python scripts/mj.py msg "hello"                # 发送聊天消息
python scripts/mj.py delete <msg_id>            # 删除消息
python scripts/mj.py upload ./image.png         # 上传到 OSS，返回 URL
python scripts/mj.py upload ./image.png --method direct   # 走新的 /api/file/upload（URL 暂不可达，见下）
python scripts/mj.py raw POST /api/msg/list --body @body.json   # 任意接口直调
```

`describe` / `blend` / `upload` 接受本地路径（自动上传）或 http(s) URL。

### 可选模型（2026-10 起站点已支持 MJ 8.2 / Niji 8.2）

| bot | 可选 `--model` |
|-----|----------------|
| `MID_JOURNEY` | `--v 8.2`（最新旗舰）、`--v 7`、`--v 6.1`、`--v 6.0`、`--v 6`、`--v 5.2`、`--v 5.1`、`--v 5`、`--v 4`、`--v 3`、`--v 2`、`--v 1`、``（空=站点默认 V5.2） |
| `NIJI_JOURNEY` | `--niji 8.2`（最新）、`--niji 7`、`--niji 6`、`--niji 5`、`--niji 4` |

未显式传 `--model` 时沿用账号保存的设置（该账号 MID_JOURNEY 现为 `--v 8.2` + relax，NIJI_JOURNEY 为 `--niji 6`）。
传了列表外的值只会在 stderr 提示，仍会原样提交。

## 上传通道

- `oss`（默认）：阿里云 OSS 直传，返回的 URL 可直接用于 `describe` / `blend` / `modal`，**推荐**。
- `direct`：新发现的 `POST /api/file/upload`（multipart，字段名 `file`）。实测能返回
  `data.file_url = https://zhongwenmj.aitoptop.cn/static/<用户名>_<文件名>`，但公网访问该路径目前是 404
  （后端 `http://43.134.16.95:8000/static/...` 能取到文件，nginx 未代理 `/static/`），故暂不用于正式出图。

## `--type` 用法（`MID_JOURNEY` / `NIJI_JOURNEY`）

`--type` 选择投递给哪个机器人，并决定沿用哪一套账号设置（`settings.MID_JOURNEY` 还是 `settings.NIJI_JOURNEY`）；不传时默认 `MID_JOURNEY`。适用于 `imagine` / `describe` / `blend`，以及 `action` / `modal` / `seed` / `cancel`（后者会优先沿用消息自带的 `type`，`--type` 只在消息缺 `type` 时兜底）。

```bash
# 1) Niji 动漫向：niji 6
python scripts/mj.py imagine "1girl, cherry blossom, cinematic light" --type NIJI_JOURNEY --model "--niji 6" --speed fast --wait

# 2) Niji 7（该账号 MID_JOURNEY 保存的默认模型就是 --niji 7，两种写法等价）
python scripts/mj.py imagine "<prompt>" --type NIJI_JOURNEY --model "--niji 7" --ar 2:3 --wait
python scripts/mj.py imagine "<prompt>" --model "--niji 7" --ar 2:3 --wait

# 3) Midjourney 写实向：显式指定模型（不传则用账号默认，该账号已是 --v 8.2）
python scripts/mj.py imagine "a lighthouse in a storm, photorealistic" --type MID_JOURNEY --model "--v 8.2" --speed fast --wait

# 4) 搭配其它设置参数（stylize / style / 速度）
python scripts/mj.py imagine "<prompt>" --type NIJI_JOURNEY --model "--niji 6" --stylize 250 --speed relax --wait

# 5) 以图生文 / 融合也可指定机器人
python scripts/mj.py describe ./ref.png --type NIJI_JOURNEY --wait
python scripts/mj.py blend a.png b.png --type MID_JOURNEY --model "--v 6.1" --wait

# 6) 操作已有消息时通常不需要 --type：脚本自动取消息里的 type
python scripts/mj.py action <msg_id> U1 --wait
#    先确认消息属于哪个机器人，再按需显式指定（必须与消息 type 一致，否则任务会失败）
python scripts/mj.py get <msg_id>            # 看返回的 "type" 字段
python scripts/mj.py action <msg_id> V2 --type NIJI_JOURNEY --wait
```

判断规则：消息返回里的 `"type": "NIJI_JOURNEY"` 表示走 niji；`"type": "MID_JOURNEY"` 表示走 MJ。用户只说"动漫/二次元"用 `NIJI_JOURNEY`，说"写实/照片/MJ v8"用 `MID_JOURNEY` + `--model "--v 8.2"`；未指定版本时默认用最新的 `--v 8.2`。

## 出图示例（`MID_JOURNEY` / `NIJI_JOURNEY`）

提示词建议用英文；出图后可用 `get <msg_id>` 查看 `task.prompt_en` 核对最终生效的提示词。

### MID_JOURNEY —— 写实、产品、建筑、通用插画

```bash
# 写实人像（--style raw 更接近原生照片质感）
python scripts/mj.py imagine "portrait of an old fisherman, weathered face, cinematic lighting, 85mm lens, shallow depth of field" --type MID_JOURNEY --model "--v 8.2" --ar 3:4 --style raw --speed fast --wait

# 产品图（--no text 避免画面出现乱码文字）
python scripts/mj.py imagine "minimal product photo of a matte black wireless earbuds case on white marble, soft studio light" --type MID_JOURNEY --model "--v 8.2" --ar 1:1 --suffix "--no text" --speed fast --wait

# 建筑 / 场景概念图
python scripts/mj.py imagine "modern glass cabin in a snowy forest at dusk, warm interior glow, volumetric light" --type MID_JOURNEY --model "--v 8.2" --ar 16:9 --stylize 250 --speed fast --wait

# 扁平插画（低 stylize 让画面更贴近提示词）
python scripts/mj.py imagine "flat vector illustration of a city skyline at sunrise, muted palette" --type MID_JOURNEY --model "--v 6.1" --ar 16:9 --stylize 50 --speed relax --wait
```

### NIJI_JOURNEY —— 二次元、动漫角色、立绘、贴纸

```bash
# 动漫角色立绘
python scripts/mj.py imagine "1girl, silver hair, red kimono, cherry blossom petals, upper body, clean lineart, soft shading" --type NIJI_JOURNEY --model "--niji 6" --ar 2:3 --speed fast --wait

# 角色设定稿（niji 8.2，带三视图与配色板）
python scripts/mj.py imagine "character design sheet, knight girl in blue armor, front view with small side and back head shots, white background, name plate" --type NIJI_JOURNEY --model "--niji 8.2" --ar 4:5 --speed relax --wait

# 动漫场景 / 主视觉
python scripts/mj.py imagine "anime key visual, two colossal mecha standing behind two pilots, dramatic sky, theatrical anime film" --type NIJI_JOURNEY --model "--niji 8.2" --ar 16:9 --stylize 300 --speed fast --wait

# Q 版贴纸
python scripts/mj.py imagine "cute chibi cat sticker, thick white outline, pastel colors, simple background" --type NIJI_JOURNEY --model "--niji 6" --ar 1:1 --suffix "--no text" --speed fast --wait
```

### 完整一轮：出图 → 放大 → 取图

```bash
python scripts/mj.py imagine "a red panda in a bamboo forest, morning light" --type MID_JOURNEY --model "--v 8.2" --ar 3:2 --speed fast --wait
# 记下返回的 data.msg_id（例如 3222824）
python scripts/mj.py get 3222824          # 看 image_urls 4 张图与 task.buttons 按钮
python scripts/mj.py action 3222824 U1 --wait   # 放大第 1 张
python scripts/mj.py action 3222824 V2 --wait   # 或对第 2 张做变体
```

## 出图工作流

1. `imagine "<prompt>" --wait`，默认 300s 超时基本够；relax 模式可能更久，可加 `--timeout 900`。
2. 从返回的 message 取 `image_urls[].url`（原图）或 `cdn_image_url`（webp 合并图）。
3. 需要放大/变体：`action <msg_id> U1 --wait`，按钮来自该消息 `task.buttons`。
4. 任务未完成可继续 `wait <msg_id>`；不要用 `list` 判断状态。

## 关键约束

- `--type` 需与被操作消息的 `type` 一致（`MID_JOURNEY` / `NIJI_JOURNEY`），`action`/`modal`/`seed`/`cancel` 会自动沿用消息自带的 type。示例见上文「`--type` 用法」。
- `--speed`：relax（慢、便宜）、fast、turbo；出图消耗额度，`me` 可查剩余。默认沿用账号保存的设置（该账号 MID_JOURNEY 现为 `--v 8.2` + relax，NIJI_JOURNEY 为 `--niji 6`），要其它版本请显式 `--model`（`--v 7` / `--v 6.1` / `--niji 8.2` …）。
- `--ar 16:9`、`--no text`、`--style raw` 等其它参数用 `--suffix` 追加或直接写在 prompt 末尾。
- 输出统一为 JSON（stdout），失败时 stderr 打印 `ERROR: API <code>: <msg>` 并以非 0 退出。

## 参考

- 完整接口清单、字段结构与按钮 custom_id 规律：`references/api.md`
