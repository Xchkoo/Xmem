# 安卓截屏记账（快捷开关 + 分享入口）

> 一句话：在系统快捷设置面板点「自动记账」，截取当前屏幕并上传到 `/ledger`，
> 走服务端既有的 OCR + LLM 链路自动生成一笔记账。

## 1. 交互流程

```
┌─ 快捷设置面板 ─┐
│  自动记账 ●    │   ← 用户手动添加的磁贴（系统限制，App 不能自己加）
└───────┬────────┘
        │ 点击
        ▼
  CaptureActivity（透明）
        │ ① 未登录 → 提示并打开 App
        │ ② Android 13+ → 申请通知权限
        │ ③ 系统截屏授权弹窗（每次都必须确认）
        ▼
  CaptureService（前台服务，type=mediaProjection）
        │ 抓一帧（延迟 350ms，避开弹窗残影）
        │ 存 PNG 到 cacheDir
        ├── 预览关闭（默认）→ 立即上传
        └── 预览开启 → 通知栏展示缩略图 + ［上传］［取消］，5 分钟超时自动取消
        ▼
  POST {baseUrl}/ledger   （multipart: image，Bearer token）
        │ 失败重试 2 次（共 3 次），401/403 不重试
        ▼
  结果通知：成功显示「¥金额 分类」，点击打开 App 并跳转到该笔记账
```

## 2. 绕不过去的系统限制

**MediaProjection 每次会话都必须由系统弹窗确认**，任何 App 都无法绕过（Android 8 起如此，
14/15/16 越来越严格）。所以"一键"实际是**两次点击**：磁贴 → 「立即开始」。

要想完全静默只有无障碍服务（`AccessibilityService.takeScreenshot()`）一条路，
但需要用户开启无障碍权限，商店合规风险也更高，本项目没有采用。

## 3. 代码结构

| 文件 | 职责 |
| --- | --- |
| `AutoCaptureTileService.kt` | 快捷设置磁贴；未登录时置灰；Android 14+ 用 `PendingIntent` 重载 |
| `CaptureActivity.kt` | 登录检查 → 通知权限 → 截屏授权 → 交给 Service |
| `CaptureService.kt` | 前台服务：注册投影回调 → 抓帧 → 存图 →（预览）→ 上传 → 发通知 |
| `XmemLedgerUploader.kt` | multipart 上传 + 重试 2 次 + 结果解析 |
| `XmemCaptureStore.kt` | 原生侧凭证/开关/pending ledger 存储 |
| `XmemCapturePlugin.kt` | Capacitor 插件，JS ↔ 原生桥 |
| `ShareCaptureActivity.kt` | 路线 C：系统分享菜单收图，直接上传（无需截屏授权） |

## 4. 鉴权：为什么自建插件

早期版本直接读 `@capacitor/preferences` 的 SharedPreferences，但那个插件用的文件名是
`CapacitorStorage`（不是 `CapacitorPreferences`），且属于第三方内部格式，升级即可能失效。

现在改为：登录成功后由 JS 通过 `XmemCapturePlugin.setSession()` 把 `token` 和 `baseUrl`
下发给原生，存在自己的 `xmem_capture` 偏好文件里；退出登录时清空。

## 5. 关键实现细节

- **Android 14+ 必须先注册 `MediaProjection.Callback` 再 `createVirtualDisplay`**，否则抛异常；
- 抓帧前延迟 350ms，避免拍到授权弹窗的残影或纯黑帧；
- 前台服务先 `startForeground` 再取投影，满足 Android 14 的 FGS 类型要求；
- 预览模式用 BigPictureStyle 通知 + 两个 action，服务保持前台直到用户操作或超时；
- 上传在后台线程执行，成功后删除缓存图片；
- 通知点击 → 打开 MainActivity，并把记账 id 存进原生偏好，App 回到前台时由 JS 读取并导航。

## 6. 首次使用

1. 打开 App 并登录（登录态会同步给原生）；
2. 下拉快捷设置面板 → 编辑 → 把「自动记账」拖进面板；
3. 点磁贴 → 系统弹授权 → 「立即开始」；
4. 通知栏出现结果，点击可查看该笔记账。

## 7. 已知限制

- 每次截屏都需要一次系统授权（见第 2 节）；
- 部分银行/支付类应用设置了 `FLAG_SECURE`，截图会是黑屏；
- 预览模式下若 5 分钟不操作会自动取消；
- 分享入口只处理单张图片（`ACTION_SEND` + `image/*`）。

## 8. 验证方式

- `cd frontend && node .\node_modules\typescript\bin\tsc -p tsconfig.json --noEmit`
- `cd frontend && node .\node_modules\vitest\vitest.mjs run`（Node 25 需加 `NODE_OPTIONS=--no-experimental-webstorage`）
- `cd android && gradlew.bat :app:assembleDebug`（需要 Android SDK 与 JDK 21）
- 真机：磁贴 → 授权 → 观察通知与记账列表
