# mj-client

基于 <https://zhongwenmj.aitoptop.cn/channels/001/007>（中文 Midjourney 网页版）同源私有 API 的工具集：一个 CodeBuddy **Skill**（命令行调用全部接口）+ 一个**本地图库页面**（浏览最近生成的图片并下载 PNG 原图）。

## 目录结构

```
.
├── .codebuddy/skills/mj-client/     # CodeBuddy 项目级 Skill
│   ├── SKILL.md                     # 触发条件、命令速查、工作流与约束
│   ├── references/api.md            # 完整接口文档（字段/参数/按钮 custom_id/OSS 上传）
│   └── scripts/mj.py                # 纯标准库 CLI，覆盖全部接口
└── gallery/                         # 本地图库
    ├── index.html                   # 前端页面（深色卡片网格，点击图片即下载 PNG）
    ├── server.py                    # FastAPI 服务（接口代理 + 原图下载转发）
    └── requirements.txt             # fastapi / uvicorn / httpx
```

## 快速开始

### 1. 配置 Auth Code（不要提交到仓库）

在项目根目录创建 `AUTH_CODE.txt`，内容只有一行 Auth Code：

```bash
echo "你的AuthCode" > AUTH_CODE.txt
```

该文件已被 `.gitignore` 排除；也可用环境变量 `MJ_AUTH_CODE` 代替。登录后的 JWT 缓存在 `~/.mj-client/state.json`（仓库外）。

### 2. 使用命令行（Skill）

```bash
python .codebuddy/skills/mj-client/scripts/mj.py auth            # 登录并缓存 token
python .codebuddy/skills/mj-client/scripts/mj.py me              # 账户与剩余额度
python .codebuddy/skills/mj-client/scripts/mj.py models            # 可选模型清单（含 --v 8.2）
python .codebuddy/skills/mj-client/scripts/mj.py list --page-size 10
python .codebuddy/skills/mj-client/scripts/mj.py imagine "a red panda" --ar 16:9 --model "--v 8.2" --speed fast --wait
python .codebuddy/skills/mj-client/scripts/mj.py action <msg_id> U1 --wait
python .codebuddy/skills/mj-client/scripts/mj.py describe ./ref.png --wait
python .codebuddy/skills/mj-client/scripts/mj.py blend a.png b.png --wait
python .codebuddy/skills/mj-client/scripts/mj.py seed --msg-id <id>
python .codebuddy/skills/mj-client/scripts/mj.py upload ./image.png
```

无需安装依赖（Python 3.9+ 标准库即可）。在 CodeBuddy 中直接描述需求（如"用 MJ 生成一张…"）会自动触发该 Skill。

### 3. 出图示例（`MID_JOURNEY` / `NIJI_JOURNEY`）

下面示例省略脚本路径，实际命令为 `python .codebuddy/skills/mj-client/scripts/mj.py <...>`；提示词建议用英文。

**MID_JOURNEY** —— 写实、产品、建筑、通用插画：

```bash
# 写实人像（--style raw 更接近原生照片质感）
mj.py imagine "portrait of an old fisherman, weathered face, cinematic lighting, 85mm lens, shallow depth of field" --type MID_JOURNEY --model "--v 8.2" --ar 3:4 --style raw --speed fast --wait

# 产品图（--no text 避免画面出现乱码文字）
mj.py imagine "minimal product photo of a matte black wireless earbuds case on white marble, soft studio light" --type MID_JOURNEY --model "--v 8.2" --ar 1:1 --suffix "--no text" --speed fast --wait

# 建筑 / 场景概念图
mj.py imagine "modern glass cabin in a snowy forest at dusk, warm interior glow, volumetric light" --type MID_JOURNEY --model "--v 8.2" --ar 16:9 --stylize 250 --speed fast --wait
```

**NIJI_JOURNEY** —— 二次元、动漫角色、立绘、贴纸：

```bash
# 动漫角色立绘
mj.py imagine "1girl, silver hair, red kimono, cherry blossom petals, upper body, clean lineart, soft shading" --type NIJI_JOURNEY --model "--niji 6" --ar 2:3 --speed fast --wait

# 角色设定稿（niji 8.2，带三视图与名称条）
mj.py imagine "character design sheet, knight girl in blue armor, front view with small side and back head shots, white background, name plate" --type NIJI_JOURNEY --model "--niji 8.2" --ar 4:5 --speed relax --wait

# Q 版贴纸
mj.py imagine "cute chibi cat sticker, thick white outline, pastel colors, simple background" --type NIJI_JOURNEY --model "--niji 6" --ar 1:1 --suffix "--no text" --speed fast --wait
```

一轮完整流程：出图 → 查看 → 放大/变体

```bash
mj.py imagine "a red panda in a bamboo forest, morning light" --type MID_JOURNEY --model "--v 8.2" --ar 3:2 --speed fast --wait
mj.py get <msg_id>              # 看 image_urls 四张图与 task.buttons 按钮
mj.py action <msg_id> U1 --wait # 放大第 1 张
mj.py action <msg_id> V2 --wait # 或基于第 2 张做变体
```

更多示例（含 niji 场景主视觉、插画低 stylize 等）见 `.codebuddy/skills/mj-client/SKILL.md`。

### 4. 启动图库页面

```bash
cd gallery
pip install -r requirements.txt
python server.py            # 默认 http://localhost:8321，自动打开浏览器
# 其它参数：--port 8322 / --host 0.0.0.0 / --no-open / --reload
# 等价方式：uvicorn server:app --port 8321
```

页面能力：按时间倒序展示最近生成记录；四宫格消息的四张图**单击即下载对应 PNG**；单图消息（放大结果）整幅可下载；支持"下载全部""复制提示词"、每页条数切换、滚动加载更多。接口文档见 <http://localhost:8321/docs>。

> 为什么需要本地服务：列表接口本身允许跨域，但原图 CDN 未返回 CORS 头，浏览器无法把跨域图片 `fetch` 成 Blob，`<a download>` 也会被忽略，因此下载必须由同域服务端转发并补 `Content-Disposition`。

## API 概览

Base URL `https://zhongwenmj.aitoptop.cn`，`Authorization: Bearer <token>`。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/app/info` | 登录页信息与公告 |
| POST | `/api/user/auth` | Auth Code 换 token |
| GET | `/api/user/info` | 账户套餐与剩余额度 |
| POST | `/api/msg/list` | 消息列表（游标分页） |
| POST | `/api/msg/ids` | 按 id 查消息（轮询任务状态） |
| POST | `/api/msg/interaction` | 主接口：绘图/放大/变体/重掷/融合/以图生文/Remix/局部重绘/取消/取种子/聊天 |
| DELETE | `/api/msg/delete/{id}` | 删除消息 |
| POST | `/api/file/oss/signature` | 阿里云 OSS 直传签名（上传本地图片） |

完整字段、`settings` 参数、按钮 `custom_id` 规律见 `.codebuddy/skills/mj-client/references/api.md`。

## 注意事项

- 出图消耗 FAST / RELAX 额度，`mj.py me` 可查剩余；relax 模式出图较慢（约 15–20 分钟）。
- `--type` 决定走 `MID_JOURNEY` 还是 `NIJI_JOURNEY`，需与被操作消息的 `type` 一致（操作已有消息时脚本会自动沿用）。
- 接口无 WebSocket/SSE，任务状态只能轮询。
- 上传仓库前请确认 `AUTH_CODE.txt` 未被跟踪：`git status --porcelain` 中不应出现该文件。
