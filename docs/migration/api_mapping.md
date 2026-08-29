# API 映射

FastAPI 路由位于 `backend/app/main.py`，统一通过 Pydantic 请求/响应模型调用原 Python 模块。除上传接口外，JSON 返回结构保持 DataFrame 列名和原函数结果，不在 TypeScript 重写计算。

| 页面/能力 | 原函数 | FastAPI 接口 | 请求 | 响应 |
|---|---|---|---|---|
| 健康检查 | - | `GET /api/health` | - | `status`, `tensorflow_available` |
| Excel 识别 | `app.detect_and_convert_data` | `POST /api/data/upload` | multipart `file` | `columns`, `rows`, `is_daily_data`, `conversion_info`, `records` |
| 模拟数据 | `DataSimulator.generate_simulated_data` | `POST /api/data/simulate` | `save_path?` | `records`, `monthly_records`, `columns` |
| 处理单元 | `initialize_session_state` 默认 `unit_data` | `GET /api/units`, `PUT /api/units/{name}` | `UnitUpdate` | `UnitState` |
| 碳/甲烷直接排放 | `CarbonCalculator.calculate_direct_emissions` | `POST /api/carbon/direct` | `DataRequest.records` | `records` |
| 间接排放 | `calculate_indirect_emissions` | `POST /api/carbon/indirect` | records | records |
| 单元拆分 | `calculate_unit_emissions` | `POST /api/carbon/unit` | records | records |
| 减排指标 | `calculate_carbon_reduction_metrics` | `POST /api/carbon/metrics` | records, `tech_applied` | metrics |
| 优化 | `CarbonCalculator.optimize_parameters` / `OptimizationEngine.optimize_parameters` | `POST /api/optimization/run` | records, `target_reduction` | strategy results |
| 情景模拟 | `OptimizationEngine.simulate_scenario` | `POST /api/optimization/scenario` | records, scenario | records/metrics |
| LSTM 加载/训练/预测 | `CarbonLSTMPredictor.load_model/train/predict` | `POST /api/prediction/load`, `/train`, `/predict` | records, months | status/predictions |
| 技术对比 | `CarbonCalculator.compare_carbon_techs` | `POST /api/technology/compare` | `tech_list`, records | records |
| 因子查询 | `CarbonFactorDatabase.get_factor/get_factor_history` | `GET /api/factors`, `/history` | type/region/date | factor rows |
| 因子更新 | `CarbonFactorDatabase.update_factor` | `POST /api/factors` | `FactorUpdate` | updated factor |
| 因子导出 | `export_factors` | `GET /api/factors/export?format=csv|excel` | format | file download |
| 数字人 | `CozeAPI.chat`, `ChatHistoryManager` | `POST /api/chat`, `GET/DELETE /api/chat/history` | message/session | response/history |
| 游戏 | `water_treatment_game.GAME_LEVELS` / state logic | `GET /api/game/state`, `POST /api/game/submit`, `/reset`, `/undo`, `/next` | level/order | state/result |

接口在无数据、缺列、模型不可用、Coze 未配置时返回 HTTP 4xx/5xx 或旧版等价提示文本，不静默改变原算法。

