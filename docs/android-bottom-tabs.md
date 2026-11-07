# 安卓底栏导航（设计稿）

> 目标：安卓端用**底部导航栏**（笔记 / 输入 / 记账 / 设置）替代现在的悬浮球；
> 同时 Web 端保持现有布局不变，业务代码不分叉。

## 1. 先回答那个关键问题：怎么既像原生、又不把 Web 搞坏

**不要让"安卓端"和"Web 端"变成两套页面。**

现在这套是 Vue SPA：路由、状态、接口调用全在 `frontend/src`。
真正平台相关的只有**外壳（导航形态 + 安全区）**，页面内容本身是同一份。
所以正确做法是加一层 **AppShell（布局壳）**：

```
App.vue
└── AppShell            ← 新增：决定"用哪种导航外壳"
    ├── (mobile) MobileTabBar + <router-view/>
    └── (desktop/web) FabMenu  + <router-view/>
```

- 判断依据：`Capacitor.isNativePlatform() && android` **或** 视口宽度 ≤ 640px；
- 页面组件（HomeView / NotesView / LedgersView ...）一行都不用改；
- Web 端（>640px）继续用悬浮球，行为完全不变；
- 想灰度也容易：先只对 native 生效，观察后再放开窄屏浏览器。

这样"原生逻辑"和"Web 保留"是**同一个业务 + 两套壳**，而不是两份代码。

## 2. 底栏怎么定义

| 位置 | 名称 | 行为 |
| --- | --- | --- |
| 1 | 笔记 | 跳到 `/notes` |
| 2 | 输入 | **不是页面，是动作**：打开快速输入 / 笔记编辑器（可做成中间凸起按钮） |
| 3 | 记账 | 跳到 `/ledgers` |
| 4 | 设置 | 打开现有 Settings 弹层（或改 `/settings` 路由） |

要解决的两个遗留问题：

1. **待办 / 统计现在在悬浮球里**，换成四个 tab 后没地方放。三种处理：
   - a) 放进首页卡片入口（首页本来就是聚合页）；
   - b) 笔记/记账页顶部放二级入口；
   - c) 底栏第 5 项（但 5 项在窄屏会挤）。
   推荐 **a**：首页改成"最近记录 + 四个入口"的移动端形态。
2. **设置现在是全屏弹层**，用 tab 打开也没问题；只要保证返回键能关掉（现在是 `@close`）。

## 3. 实现要点

- 新增 `components/MobileTabBar.vue`（约 80 行）：
  - 4 个按钮 + 中间凸起的主按钮；
  - 底部安全区：`padding-bottom: var(--sab)`（上一轮已经加好了变量）；
  - 当前路由高亮；
  - `position: fixed; bottom: 0`，并给 `#app` 加 `padding-bottom: 64px + var(--sab)` 防止内容被遮。
- `App.vue` 里抽 `AppShell`：
  - 移动壳：`<MobileTabBar />` + `<router-view />`；
  - 桌面壳：现有 `<FabMenu />`；
  - 两者都保留 `<Settings /> <AiAssistant /> <Toast /> <ConfirmDialog />` 等全局层。
- 新增 `composables/usePlatform.ts`：
  ```ts
  export const isNativeAndroid = () => Capacitor.isNativePlatform() && Capacitor.getPlatform() === 'android';
  export const useMobileShell = () => isNativeAndroid() || useMediaQuery('(max-width: 640px)');
  ```
- 键盘弹出时底栏上移：用 `100dvh` + `env(safe-area-inset-bottom)`，或监听 `visualViewport`。

## 4. 迁移步骤（可回退）

1. **阶段一**：只加 `MobileTabBar` + `AppShell`，且仅在 native Android 生效；
   悬浮球在 native 上隐藏。→ 打包给真机试。
2. **阶段二**：窄屏浏览器（≤640px）也走移动壳；桌面不变。
3. **阶段三**：把首页改成移动端形态（最近记录 + 入口卡片），去掉对悬浮球的依赖。

每一步都是独立 commit，出问题整段 revert 就行。

## 5. 风险

- **双导航并存期**：`FabMenu` 和 `TabBar` 同时可点会乱，靠 `v-if` 二选一；
- **首页高度**：`min-h-screen` 已按安全区扣过，加底栏后还要再扣 `64px`；
- **横屏**：底栏在横屏会占掉宝贵高度，可考虑横屏时隐藏；
- **Web 回归**：所有改动都要在桌面宽度下跑一遍现有 118 个测试。

## 6. 需要拍板

1. 底栏第 2 项"输入"：打开**快速输入**（一句话记账/记笔记）还是**新笔记编辑器**？
2. 待办 / 统计入口：按推荐放首页，还是保留第五项？
3. 设置是**弹层**（现状）还是改成独立页面 `/settings`？
4. 窄屏浏览器要不要也跟着变（阶段二）？
