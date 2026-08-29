# API说明

基础路径：`/api/virtual-plant`

| 方法 | 路径 | Pydantic响应/用途 |
|---|---|---|
| GET | `/config` | `PlantConfig`，完整水厂配置 |
| GET | `/state` | `PlantState`，全厂唯一当前状态 |
| GET | `/history/{unit_id}` | `list[HistoryPoint]` |
| GET | `/units/{unit_id}` | `UnitDetailResponse` |
| GET | `/alarms` | `list[AlarmState]` |
| GET | `/scenarios` | `list[ScenarioDefinition]` |
| GET | `/formulas` | `list[FormulaRecord]` |
| POST | `/start` | 启动墙钟驱动的分钟仿真 |
| POST | `/pause` | 暂停并结算已过工艺步 |
| POST | `/step` | `StepRequest`，暂停状态下推进1–120步 |
| POST | `/reset` | 重置到当前配置初态 |
| POST | `/speed` | `SpeedRequest`，0.25–60倍 |
| POST | `/scenario` | `ScenarioRequest`，加载场景并回到T+0 |
| PATCH | `/units/{unit}/equipment/{equipment}` | `EquipmentUpdateRequest`，验证状态、模式和设定范围 |
| POST | `/snapshots` | 保存命名快照 |
| POST | `/snapshots/restore` | 恢复快照 |

所有动作返回更新后的 `PlantState`，前端不在动作完成后自行推算结果。未知单元/设备/场景返回404，越界设定返回422。
