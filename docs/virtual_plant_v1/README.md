# 虚拟水厂仿真系统 V1

V1 是配置驱动、分钟级、可解释的示范水厂闭环。当前数据模式为 `DEMO`，页面持续显示：**当前为示范仿真数据，不代表真实水厂运行结果**。

本版本完成的闭环：

`示范配置 → Python仿真引擎 → FastAPI → Pinia → 3D/2D/指标/趋势/告警 → 设备调整 → 状态变化`

文档索引：

- [架构说明](architecture.md)
- [水厂配置说明](plant_configuration.md)
- [仿真边界](simulation_boundaries.md)
- [单位表](units.md)
- [公式来源表](formula_registry.md)
- [场景说明](scenarios.md)
- [API说明](api.md)
- [测试报告](test_report.md)
- [已知限制](known_limitations.md)
- [接入真实水厂数据](real_plant_onboarding.md)

截图位于 [screenshots](screenshots)：包含 1920×1080、1366×768 工作台，以及甲烷异常场景的3D联动验收图。
