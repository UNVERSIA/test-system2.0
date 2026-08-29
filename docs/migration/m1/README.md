# M1 验收记录

本目录只记录“全局正式界面与悬浮 3D 烷仔”等价迁移，不代表十个业务页面已经迁移完成。

## 自动验收结果

- Vue 全局布局在 1920×1080、1366×768 下完成浏览器验收。
- 本地 `/assets/models/wanzi_web.glb` 返回 HTTP 200；文件大小为 7,040,336 字节。
- 模型使用 Vue 本地 `/assets/draco/` 解码资源实际完成加载和渲染。
- Playwright 检查了十个路由、光球拖动与位置存储、三级状态、聊天输入、未配置 Coze 提示、跨路由与刷新持久化、收起/恢复，以及浏览器严重错误。
- 原 Streamlit、FastAPI 和 Vue 均已独立启动验证。

## 截图

- `old-wanzi-orb.png`：原基线中的 Streamlit 悬浮光球。
- `new-wanzi-orb.png`
- `new-wanzi-pet.png`：等待 Draco 解码完成后截图，画面中可见真实 GLB 模型。
- `new-wanzi-chat.png`：等待 Draco 解码完成后截图，画面中可见真实 GLB 模型和聊天面板。
- `new-global-layout-1920.png`
- `new-global-layout-1366.png`

## 原版自动截图限制

原组件通过 jsDelivr 动态加载 Three.js 和 Draco。验收浏览器访问该依赖时返回 `net::ERR_BLOCKED_BY_CLIENT`，所以本轮无法生成可信的 `old-wanzi-pet.png` 和 `old-wanzi-chat.png`。这两个文件没有用空白画布、静态图片或重复的光球截图替代。

人工验收步骤：在允许访问 `cdn.jsdelivr.net` 的本机浏览器打开原 Streamlit 页面，点击右下角光球，等待模型出现后分别记录 3D 状态和聊天状态；对照本目录新版截图检查模型、欢迎语、旋转、问候、收起和聊天流程。
