from .schemas import QualityStatus, ScenarioDefinition


SCENARIOS = {
    item.scenario_id: item
    for item in [
        ScenarioDefinition(scenario_id="normal", name="正常运行", description="所有单元按示范设计流量稳定运行。", trigger_minute=0, affected_units=[], expected_changes=["状态按分钟推进", "无主动故障"], recoverable_action="无需操作", end_condition="持续运行或用户重置", status=QualityStatus.ILLUSTRATIVE),
        ScenarioDefinition(scenario_id="influent_surge", name="进水流量冲击", description="第10分钟起进水流量升至示范基准的1.8倍。", trigger_minute=10, affected_units=["coarse_screen", "lift_station", "fine_screen"], expected_changes=["前端单元液位上升", "超过90%触发高液位告警"], recoverable_action="提高提升泵设定或重置场景", end_condition="第50分钟恢复基准进水", status=QualityStatus.PROVISIONAL),
        ScenarioDefinition(scenario_id="blower_failure", name="鼓风机或曝气故障", description="第10分钟鼓风机进入故障状态。", trigger_minute=10, affected_units=["blower_house", "aerobic_tank", "mbr_tank"], expected_changes=["曝气停止", "DO演示值下降", "设备故障告警"], recoverable_action="将鼓风机状态恢复为开启", end_condition="鼓风机恢复开启", status=QualityStatus.PROVISIONAL),
        ScenarioDefinition(scenario_id="methane_anomaly", name="甲烷浓度异常", description="第10分钟厌氧池甲烷示范值开始上升。", trigger_minute=10, affected_units=["anaerobic_tank"], expected_changes=["风险颜色变化", "甲烷异常告警", "趋势同步上升"], recoverable_action="检查厌氧池并重置场景", end_condition="甲烷值低于2 mg/L", status=QualityStatus.AWAITING_SOURCE),
    ]
}
