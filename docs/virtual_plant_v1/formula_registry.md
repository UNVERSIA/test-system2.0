# 公式来源与可信度

运行时注册表可通过 `GET /api/virtual-plant/formulas` 和页面“查看公式可信度”打开。

| ID | 公式 | 状态 | 正式来源 | 校准 |
|---|---|---|---|---|
| VP-WATER-001 | `V(t+Δt)=clip(V+(Qin-Qout)Δt/1440,0,Vmax)` | provisional | 待核实 | 需要 |
| VP-QUALITY-001 | `Cmix=(VC+VinCin)/(V+Vin)` | awaiting_source | 待核实 | 需要 |
| VP-ENERGY-001 | `E=Prated×load×Δt/60` | awaiting_calibration | 待具体设备曲线 | 需要 |
| VP-DO-001 | `DO'=clip(DO+0.03×blower_load-0.015,0,10)` | awaiting_calibration | 无；明确为界面反馈关系 | 需要 |
| VP-CH4-001 | 演示风险阈值 | awaiting_source | 待核实 | 需要 |

当前没有任何V1公式标记为 `verified`，因为尚未获得满足要求的完整标准章节、论文公式定位或具体设备性能曲线。旧代码注释没有被用作科学来源，也没有补造IPCC、IWA或国标引用。

每条运行时记录还包含变量定义、单位、适用范围、来源类型、完整来源、章节定位、是否需要校准、实现位置和测试位置。
