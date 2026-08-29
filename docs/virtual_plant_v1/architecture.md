# 架构说明

## 单一事实来源

```text
backend/app/simulation/config/demo_plant.json
                 ↓
SimulationEngine（统一分钟级时间、状态和历史）
                 ↓
FastAPI /api/virtual-plant/*
                 ↓
Pinia useVirtualPlantStore
        ↓          ↓          ↓          ↓
  Three.js 3D   SVG 2D拓扑   趋势图    告警/详情
```

3D不产生工艺随机数，图表不重新计算状态，参数面板不维护第二份业务状态。Three.js中的气泡位置采用确定性视觉序列，仅代表动画，不进入仿真计算。

## 后端边界

- `schemas.py`：配置、状态、请求和响应模型。
- `engine.py`：生命周期、时间推进、场景、快照、历史和设备更新。
- `state.py`：可变状态初始化。
- `mass_balance.py`：水量和无反应混合传播。
- `equipment.py`：明确标为示范的设备负荷与能耗关系。
- `methane.py`：待来源核实的演示风险分级。
- `scenarios.py`：四个示范场景定义。
- `provenance.py`：公式可信度注册表。

FastAPI路由只负责验证请求、调用引擎和转换HTTP错误，不包含仿真算法。

## 前端边界

- `stores/virtualPlant.ts` 是唯一前端状态源。
- `VirtualPlantScene.vue` 只把配置和状态映射到Three.js对象。
- `ProcessTopology.vue` 使用同一配置连接关系和同一状态。
- `UnitTrendChart.vue` 只显示后端历史接口的数据。
- 离开3D路由时销毁Renderer、Geometry、Material、OrbitControls、ResizeObserver和动画循环。

## 数据模式

| 模式 | V1状态 | 含义 |
|---|---|---|
| `DEMO` | 已实现 | 示例配置和合成初始状态，不能用于真实运行判断 |
| `UPLOADED` | 接口边界预留 | 后续把离线文件适配为统一状态输入 |
| `LIVE` | 接口边界预留 | 后续接入SCADA/PLC，不在V1伪造实时数据 |
