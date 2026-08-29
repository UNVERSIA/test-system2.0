# 水厂配置说明

规范配置位于 `backend/app/simulation/config/demo_plant.json`，由Pydantic `PlantConfig`完整验证。

## 顶层字段

`plant_id`、`plant_name`、`data_mode`、`units`、`connections`、`sensors`、`equipment`、`constraints`、`visual_layout`、`simulation_parameters`、`disclaimer`。

## 工艺单元字段

每个单元具有唯一ID、中文名称、工艺类型、区域、有效容积、设计流量、初始液位、运行状态、3D位置/尺寸/结构、入口、出口、测点、设备、参数来源、数据质量状态、水质初值和甲烷示范初值。

## 连接关系

连接单独存储并明确 `source_unit_id`、`target_unit_id`、介质和两端端口。仿真和2D拓扑不根据3D坐标推断上下游。

当前包含：

- 12条主水线连接；
- 2条污泥/回流连接；
- 2条曝气空气线；
- 2条除臭空气线。

## V1示范设施

粗格栅、提升泵房、细格栅、曝气沉砂池、膜格栅、厌氧池、缺氧池、好氧池、MBR膜池、鼓风机房、污泥处理车间、DF系统、催化氧化、消毒接触池、出水区域、除臭系统。

所有现有尺寸、坐标、容量和初始参数均标记为 `illustrative / 待真实水厂资料校准`。更换水厂时优先替换配置文件；只有出现新的设施结构类型或数据协议时才扩展Vue/Three.js或适配器。
