# Midjourney API 参考（zhongwenmj.aitoptop.cn）

前端页面 `https://zhongwenmj.aitoptop.cn/channels/001/007` 是 Vue3 SPA，所有接口同源。本文件是逆向其前端产物（Vite 打包 chunk）并逐接口实测后的完整说明。

## 通用约定

- Base URL：`https://zhongwenmj.aitoptop.cn`（前端常量 `baseURL`）
- 认证：`Authorization: Bearer <token>`（除 `/api/app/info`、`/api/user/auth` 外都需要）
- 请求体：`application/json`；响应统一信封：

```json
{ "code": 200, "msg": "请求成功", "data": { }, "success": true }
```

- 失败时 `success=false`，`code` 非 200。前端把 `401` 和 `1100` 视为 token 失效并登出 → 客户端遇到这两个 code 应重新 `auth` 后重试。
- 时间戳为秒级 Unix 时间。

## 认证流程

1. `POST /api/user/auth`，body `{"username": "<Auth Code>"}`（Auth Code 即"用户名"）。
2. 返回 `data.token`（JWT，约 7 天有效）、`data.username`、`data.user_info.dc_username`、`data.user_info.settings.{MID_JOURNEY,NIJI_JOURNEY}`。
3. 后续请求带 Bearer token。缓存 token 到本地，过期前重新 auth。

## 接口清单（共 9 个端点，2026-10 复核）

| # | 方法 | 路径 | 说明 |
|---|------|------|------|
| 1 | GET | `/api/app/info` | 登录页信息：`home_info`（标题/说明/二维码）、`notice` 公告 |
| 2 | POST | `/api/user/auth` | Auth Code 换 token |
| 3 | GET | `/api/user/info` | 账户套餐与剩余额度（HTML 片段 `content_html`） |
| 4 | POST | `/api/msg/list` | 消息列表（会话历史） |
| 5 | POST | `/api/msg/ids` | 按 id 批量查消息（轮询任务状态用） |
| 6 | POST | `/api/msg/interaction` | **主接口**：绘图/变体/放大/重绘/融合/以图生文/取消/取种子/聊天 |
| 7 | DELETE | `/api/msg/delete/{msg_id}` | 删除消息 |
| 8 | POST | `/api/file/oss/signature` | 获取阿里云 OSS 直传签名（用于上传本地图片） |
| 9 | POST | `/api/file/upload` | **新增**：multipart 直接上传图片到站点自身存储（前端尚未使用） |
| — | POST | `/api/file/oss/callback` | OSS 上传回调，内部接口（未带 OSS 签名头时返回 `missing oss signature headers`） |

### 1. GET /api/app/info

无需鉴权，响应**没有 `success` 字段**（只有 `notice` / `home_info`），客户端不要按统一信封校验。
返回 `{"notice": "...", "home_info": {"home_title","home_content","qr_src","qr_title","qr_tip"}}`。

### 2. POST /api/user/auth

```json
{"username": "2609xxxxxxxxxxxxxxxx"}
```
→ `data: {token, username, user_info: {dc_username, settings: {MID_JOURNEY:{...}, NIJI_JOURNEY:{...}}}, notice}`

### 3. GET /api/user/info

返回 `data.content_html`：账户 ID、私密模式、累计使用、FAST/RELAX 套餐的可用/已用/总量与到期时间（需从 HTML 文本中读取）。

### 4. POST /api/msg/list

```json
{"page_size": 10, "before": 0}
```
- `before`：分页游标，传当前已加载**最早**一条消息的 `submit_time`；首页传 `0`。
- 返回按时间倒序（最新在前）的消息数组。
- `data.pagination`：`{page, page_size, page_count, total}`。
- 终止条件：`list.length < page_size`（前端同逻辑）。

### 5. POST /api/msg/ids

```json
{"msg_ids": [3222574]}
```
→ `data` 为**消息数组**（不是 `{list:[...]}`），取 `data[0]`。用于提交任务后轮询状态。

### 6. POST /api/msg/interaction

统一入口，靠 `action` 区分：

```json
{"type": "<MID_JOURNEY|NIJI_JOURNEY|MSG>", "action": "<ACTION>", "data": {}}
```

| action | data 字段 | 说明 |
|--------|-----------|------|
| `IMAGINE` | `settings`, `prompt` | 文生图 |
| `DESCRIBE` | `settings`, `image_url` | 以图生文（图转提示词） |
| `BLEND` | `settings`, `img_url_array` | 2~5 张图融合 |
| `ACTION` | `settings`, `task_id`, `custom_id` | 点击按钮：放大/变体/重掷/局部重绘/Zoom/Pan 等 |
| `MODAL` | `settings`, `task_id`, `prompt`, `parent_task_id?`, `mask_base64?` | Remix 改提示词、Inpaint 局部重绘 |
| `SEED` | `settings`, `task_id` | 取任务 seed |
| `CANCEL` | `settings`, `task_id` | 取消任务 |
| `MSG` | `message_content`（`type` 传 `MSG`） | 发送普通聊天消息 |

成功返回：`data: {task_id, msg_id}`；用 `msg_id` 轮询 `/api/msg/ids`。
`MODAL` 场景可能只返回 `data: {task_id, prompt}`（无 msg_id）。

#### settings 对象

```json
{"model": "--v 7", "style": "", "stylize": 100, "remix": false, "variation": "high", "speed": "fast"}
```

- `model`：服务端接受的取值见下方「模型清单」（MJ 最高 `--v 8.2`；Niji 最高 `--niji 7`，没有 `--niji 8.x`）
- 传了不存在的值（如 `--v 9`）时接口仍返回 200，任务会在 MJ 侧变成 `FAILURE`。
- `style`：对应 `--style <value>`
- `stylize`：0~1000，对应 `--s <n>`
- `speed`：`relax` / `fast` / `turbo`，对应 `--relax` / `--fast` / `--turbo`
- `variation`：`high` / `low`；`remix`：布尔
- 服务端会保存用户设置（`/api/user/auth` 返回），调用时建议沿用用户设置再覆盖。
- 画幅等其它参数（`--ar 16:9`、`--no xxx`、`--raw`）直接拼在 `prompt` 末尾。写实风格用 `--raw`；写成 `--style raw` 上游会报错。

#### 模型清单（取自前端 `assets/settings-*.js` 的 `A`（MJ）与 `U`（Niji）两个下拉数组）

- MJ（`MID_JOURNEY`）：`""`（站点默认 V5.2）、`--v 8.2`、`--v 7`、`--v 6.1`、`--v 6.0`、`--niji 7`、`--niji 6`、`--v 5.2`、`--v 5.1`、`--niji 5`、`--v 5`、`--niji 4`、`--v 4`、`--v 3`、`--v 2`、`--v 1`
- Niji（`NIJI_JOURNEY`）：`--niji 7`（最高版本）、`--niji 6`、`--niji 5`、`--niji 4`

### 7. DELETE /api/msg/delete/{msg_id}

无请求体。

### 8. POST /api/file/oss/signature

请求体 `{}` → 返回：

```json
{"accessid":"LTAI...","host":"https://mjapi.oss-cn-shanghai.aliyuncs.com","policy":"base64",
 "signature":"...","expire":1790523354,"callback":"base64","dir":"2609100082/upload/"}
```

上传：`multipart/form-data` POST 到 `host`，字段顺序为先表单字段后文件（字段名 `file`）：

| 字段 | 值 |
|------|-----|
| `key` | `dir + <uuid>.<ext>` |
| `policy` | 签名返回的 policy |
| `OSSAccessKeyId` | accessid |
| `success_action_status` | `200` |
| `signature` | 签名 |
| `callback` | 签名返回的 callback |
| `x:filename` | 原始文件名 |
| `file` | 文件二进制 |

回调响应为 JSON，文件地址在 `data.file_url`。支持 `.png/.jpg/.jpeg/.webp`。

### 9. POST /api/file/upload（新增，2026-10 发现）

`multipart/form-data`，字段名 `file`，需 Bearer token：

```bash
curl -X POST https://zhongwenmj.aitoptop.cn/api/file/upload \
  -H "Authorization: Bearer $TOKEN" -F "file=@a.png;type=image/png"
```

→ `{"code":200,"msg":"请求成功","data":{"file_url":"https://zhongwenmj.aitoptop.cn/static/<用户名>_<原文件名>"}}`

- 字段名不是 `file` 时返回 `{"code":1001,"msg":"Field required"}`
- **已知缺陷**：返回的 `/static/...` URL 在公网上是 404（后端 `http://43.134.16.95:8000/static/...` 可以取到文件，
  说明 nginx 尚未代理 `/static/`）。因此正式出图仍走第 8 条的 OSS 直传。

## 消息对象结构

```json
{
  "id": 3222574,
  "status": "SUCCESS",              // NOT_START / SUBMITTED / IN_PROGRESS / SUCCESS / FAILURE / CANCEL
  "type": "NIJI_JOURNEY",           // MID_JOURNEY / NIJI_JOURNEY / MSG
  "action": "IMAGINE",              // IMAGINE / DESCRIBE / BLEND / UPSCALE / VARIATION / ACTION / MODAL / SEED / MSG ...
  "submit_time": 1790519929, "start_time": 1790519929, "finish_time": 1790520008,
  "image_url": "https://...", "thumbnail_image_url": "...", "cdn_image_url": "...",
  "image_urls": [{"url": "...", "thumbnail": "..."}],
  "message_content": "**prompt** ...",
  "task": {
    "id": 1790519928949118, "parent_task_id": null, "parent_task_message_content": null,
    "status": "SUCCESS", "description": "/imagine ...", "bot_type": "MID_JOURNEY",
    "action": "IMAGINE", "speed": "relax", "real_speed_mode": "FAST",
    "prompt": "...", "prompt_en": "...", "progress": "100%", "custom_id": null, "fail_reason": null,
    "buttons": [{"custom_id": "MJ::JOB::upsample::1::<hash>", "emoji": "", "label": "U1", "style": 2, "type": 2}]
  }
}
```

常用按钮 `custom_id` 形态：

- 放大：`MJ::JOB::upsample::{1-4}::{hash}`（label `U1`~`U4`）
- 变体：`MJ::JOB::variation::{1-4}::{hash}`（label `V1`~`V4`）
- 重掷：`MJ::JOB::reroll::0::{hash}::SOLO`（emoji `🔄`）
- 局部重绘：`MJ::Inpaint::{...}` 或含 `::Inpaint::`（前端据此弹局部重绘面板）
- 图片阅读重试：`MJ::Picread::Retry`
- 以图生文后接绘图：`::PicReader::{n}`

## 典型工作流

1. **文生图**：`auth` → `interaction(IMAGINE)` 得 `msg_id` → 每 5s 轮询 `msg/ids` 直到 `status ∈ {SUCCESS, FAILURE, CANCEL}`（前端超时上限约 60 分钟）→ 用 `image_urls[].url` 取原图。
2. **放大/变体**：取消息 `task.buttons` 里的 `custom_id` → `interaction(ACTION, {task_id: task.id, custom_id})` → 轮询新 `msg_id`。
3. **以图生文**：本地图先走 OSS 上传拿 URL → `interaction(DESCRIBE, {image_url})` → 结果在 `message_content`（4 条候选提示词）→ 再 `IMAGINE`。
4. **图片融合**：上传 2~5 张 → `interaction(BLEND, {img_url_array})`。
5. **Remix / 局部重绘**：`interaction(MODAL, {task_id, parent_task_id, prompt, mask_base64})`，`mask_base64` 为 PNG 二进制的 base64（不带 data URL 前缀）。
6. **取 seed**：`interaction(SEED, {task_id})` → `data.seed`。
7. **取消**：`interaction(CANCEL, {task_id})`。

## 已知限制

- 无 WebSocket/SSE，状态只能轮询（前端对未完成任务用 5s 间隔重试循环）。
- 出图消耗 FAST/RELAX 额度，可在 `/api/user/info` 查看剩余。
- `type`（bot 类型）需要与被操作消息的 `type` 一致，否则任务可能失败。
