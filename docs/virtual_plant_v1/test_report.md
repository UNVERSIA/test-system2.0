# 测试报告

## 后端

`python -m pytest -q`

结果：`16 passed, 1 warning`。警告来自现有环境中的 Requests 依赖版本组合，不影响本次测试结论。

覆盖配置解析、连接端口、单位、水量守恒、液位边界、停运/堵塞、无反应质量传播、设备能耗与通量、四个场景、曝气故障、甲烷异常、快照、API状态一致性、重置和异常输入。

## 前端与浏览器

`npm run build` 与 `npm run test:e2e`

结果：生产构建通过；Playwright `12 passed`。构建仅保留主包大于 500 kB 的体积提示。

Playwright覆盖：

- 16个配置对象与18条连接；
- 三维Canvas和中文标签；
- 单步、仿真时间、全厂指标与趋势一致；
- 四场景和甲烷异常同步；
- 设备故障、DO变化和告警；
- 2D/3D共享状态；
- 路由切换Canvas为 `1 → 0 → 1`；
- 公式可信度；
- M1悬浮烷仔完整回归；
- 1920×1080与1366×768；
- 浏览器严重控制台错误与横向溢出。

验收截图：

- `screenshots/virtual-plant-1920.png`
- `screenshots/virtual-plant-1366.png`
- `screenshots/virtual-plant-methane-anomaly.png`
