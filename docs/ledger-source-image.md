# 记账保留原图（设计稿）

> 目标：截图/照片上传后**原图永久保留**，记账详情里可以直接看到当初提交的那张图；
> OCR 出来的文本只作为 AI 的输入，不再充当"证据"。

## 1. 现状（代码事实）

- `POST /ledger` 收到 multipart 的 `image` 后调用 `save_uploaded_img()` 落到
  `uploads/images/<uuid>.png`，路径只存在局部变量 `image_path` 里；
- 该路径被塞进 Celery 任务链做 OCR，OCR 文本合并后写进 `LedgerEntry.raw_text`；
- **`ledger_entries` 没有存图片路径**，请求结束后这个路径就丢了；
- 更糟的是：`files` 表只登记笔记引用的文件，而 `cleanup_orphan_files` 每小时会删掉
  "没被 files 表引用"的文件 —— 也就是说**现在截图记账的图片会被定时任务当垃圾删掉**。

结论：不是"图片没显示"，是**压根没存**，而且还会被清理任务回收。

## 2. 数据模型

`ledger_entries` 新增两列（都允许 NULL，兼容历史数据）：

| 列 | 类型 | 说明 |
| --- | --- | --- |
| `image_path` | String(512) | 相对路径，如 `uploads/images/<uuid>.png` |
| `image_thumb_path` | String(512) | 缩略图（列表页用），可先不做 |

同时约定 `raw_text` 的语义：**保留现有的"合并文本"**（用户输入 + OCR），AI 用的就是它；
原始 OCR 文本单独存 `meta["ocr_text"]`，便于以后重跑/对比，不再覆盖任何东西。

## 3. 接口

- `LedgerOut` 增加：
  - `image_url: str | None` —— 形如 `/ledger/files/<filename>`，前端直接拼 API base；
  - `has_image: bool`（可选，方便列表页少判空）。
- 新增 `GET /ledger/files/{filename}`：
  - 需要登录（沿用 `get_current_user`）；
  - 只能下载"属于当前用户"的图（查 `LedgerEntry.image_path` 反查，防越权）；
  - 返回 `FileResponse`，带 `Cache-Control: private, max-age=…`。

> 不复用 `/notes/files/{type}/{name}`：那是笔记的资源域，且现有实现按 markdown 引用匹配，
> 混进来会把两种业务绑死。

## 4. 后端改动清单

1. `models.py`：`LedgerEntry` 加 `image_path` / `image_thumb_path`；
2. `alembic/versions/`：新增迁移（两列可空，无回填）；
3. `routers/ledger.py::create_ledger`：`save_uploaded_img()` 之后立刻把路径写进 entry，
   再把 entry 交给 Celery（任务里只更新业务字段，不要覆盖 `image_path`）；
4. `schemas.py`：`LedgerOut` 加字段；列表/详情/统计的构造处补齐；
5. `tasks/ledger_tasks.update_ledger_entry()`：显式跳过 `image_path`；
6. `tasks/file_tasks.cleanup_orphan_files()`：把 `ledger_entries.image_path` 里的文件
   也加入"受保护集合"，否则新存的原图照样被删；
7. `DELETE /ledger/{id}`：顺带删掉对应图片文件（可选，见待定项）。

## 5. 前端改动清单

- `LedgerCardContent.vue`：有图时显示小缩略图（加载失败就退回图标）；
- `LedgerView.vue`（单笔详情）：顶部展示原图，点击看大图（复用笔记的 secure 图片加载方式，
  需要带 token 的 blob URL，不能直接 `<img src>`）；
- `LedgerEditor.vue`：编辑时能替换图片（可选，二期）；
- 上传流程不变（仍是 multipart `image`）。

## 6. 兼容与清理

- 历史记账 `image_path` 为 NULL：前端不显示图片区，无回归；
- 新增的图会被 cleanup 任务保护；删除记账时按策略删文件；
- 迁移可回滚（drop column）。

## 7. 需要拍板

1. **一条记账几张图？** 先做单图（现状），还是直接上多图（`ledger_images` 子表）？
2. **删除记账时删图还是留档？** 删（省空间）／留（可恢复，但要另建清理策略）？
3. **列表页要不要缩略图？** 要的话得加 `image_thumb_path` + 生成缩略图的步骤（Pillow 已在依赖里）。
4. **老数据**：已有的记账没有原图，是否需要"从 OCR 文本反推"？一般不需要，直接留空。
