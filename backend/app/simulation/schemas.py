from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class DataMode(str, Enum):
    DEMO = "DEMO"
    UPLOADED = "UPLOADED"
    LIVE = "LIVE"


class QualityStatus(str, Enum):
    ILLUSTRATIVE = "illustrative"
    PROVISIONAL = "provisional"
    VERIFIED = "verified"
    AWAITING_SOURCE = "awaiting_source"
    AWAITING_CALIBRATION = "awaiting_calibration"


class EquipmentStatus(str, Enum):
    ON = "on"
    OFF = "off"
    FAULT = "fault"
    MAINTENANCE = "maintenance"


class EquipmentMode(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"


class SensorConfig(BaseModel):
    id: str
    name: str
    metric: str
    unit: str
    quality_status: QualityStatus = QualityStatus.ILLUSTRATIVE


class EquipmentConfig(BaseModel):
    id: str
    name: str
    type: Literal["pump", "blower", "mixer", "reflux", "dosing", "mbr_suction", "mbr_backwash"]
    rated_power_kw: float = Field(ge=0)
    capacity: float = Field(ge=0)
    capacity_unit: str
    adjustable_parameter: str
    parameter_min: float
    parameter_max: float
    parameter_default: float
    parameter_unit: str
    relationship_status: QualityStatus = QualityStatus.AWAITING_CALIBRATION

    @model_validator(mode="after")
    def validate_range(self):
        if not self.parameter_min <= self.parameter_default <= self.parameter_max:
            raise ValueError("equipment default parameter outside configured range")
        return self


class VisualLayout(BaseModel):
    position: list[float] = Field(min_length=3, max_length=3)
    size: list[float] = Field(min_length=3, max_length=3)
    structure: Literal["channel", "building", "circular_tank", "rectangular_tank", "equipment_hall", "outlet"]
    color: str


class PortConfig(BaseModel):
    id: str
    kind: Literal["water", "sludge", "air"]


class UnitConfig(BaseModel):
    id: str
    name: str
    process_type: str
    area: str
    effective_volume_m3: float = Field(gt=0)
    design_flow_m3_d: float = Field(gt=0)
    initial_level_pct: float = Field(ge=0, le=100)
    initial_status: Literal["running", "stopped"] = "running"
    visual_layout: VisualLayout
    inlets: list[PortConfig]
    outlets: list[PortConfig]
    sensors: list[SensorConfig]
    equipment: list[EquipmentConfig]
    parameter_source: str
    data_quality_status: QualityStatus
    initial_quality: dict[str, float]
    initial_methane_mg_l: float = Field(ge=0)


class ConnectionConfig(BaseModel):
    id: str
    source_unit_id: str
    target_unit_id: str
    medium: Literal["water", "sludge", "air"]
    source_port: str
    target_port: str


class PlantConfig(BaseModel):
    plant_id: str
    plant_name: str
    data_mode: DataMode
    units: list[UnitConfig]
    connections: list[ConnectionConfig]
    sensors: list[SensorConfig] = Field(default_factory=list)
    equipment: list[EquipmentConfig] = Field(default_factory=list)
    constraints: dict[str, Any]
    visual_layout: dict[str, Any]
    simulation_parameters: dict[str, Any]
    disclaimer: str


class EquipmentState(BaseModel):
    id: str
    name: str
    type: str
    status: EquipmentStatus
    mode: EquipmentMode
    parameter_value: float
    parameter_unit: str
    power_kw: float
    energy_kwh: float


class SensorState(BaseModel):
    id: str
    name: str
    metric: str
    value: float
    unit: str
    quality_status: QualityStatus


class UnitState(BaseModel):
    unit_id: str
    name: str
    status: Literal["running", "stopped", "blocked"]
    level_pct: float
    volume_m3: float
    inflow_m3_d: float
    outflow_m3_d: float
    water_quality: dict[str, float]
    methane_mg_l: float
    methane_risk: Literal["normal", "attention", "high", "critical"]
    sensors: list[SensorState]
    equipment: list[EquipmentState]
    alarms: list[str]
    data_quality_status: QualityStatus


class AlarmState(BaseModel):
    id: str
    severity: Literal["info", "warning", "critical"]
    unit_id: str | None = None
    message: str
    simulation_minute: int
    recoverable_action: str


class PlantState(BaseModel):
    plant_id: str
    data_mode: DataMode
    simulation_minute: int
    running: bool
    speed: float
    scenario_id: str
    units: list[UnitState]
    alarms: list[AlarmState]
    total_inflow_m3_d: float
    total_outflow_m3_d: float
    total_energy_kwh: float
    methane_risk_counts: dict[str, int]
    disclaimer: str


class HistoryPoint(BaseModel):
    simulation_minute: int
    unit_id: str
    level_pct: float
    inflow_m3_d: float
    outflow_m3_d: float
    methane_mg_l: float
    cod_mg_l: float
    do_mg_l: float
    energy_kwh: float


class ScenarioDefinition(BaseModel):
    scenario_id: str
    name: str
    description: str
    trigger_minute: int
    affected_units: list[str]
    expected_changes: list[str]
    recoverable_action: str
    end_condition: str
    status: QualityStatus = QualityStatus.PROVISIONAL


class FormulaRecord(BaseModel):
    formula_id: str
    name: str
    expression: str
    variables: dict[str, str]
    units: str
    scope: str
    source_type: str
    full_source: str | None = None
    source_locator: str | None = None
    trust_status: QualityStatus
    requires_plant_calibration: bool
    implementation: str
    tests: str


class SpeedRequest(BaseModel):
    speed: float = Field(ge=0.25, le=60)


class ScenarioRequest(BaseModel):
    scenario_id: str


class StepRequest(BaseModel):
    steps: int = Field(default=1, ge=1, le=120)


class EquipmentUpdateRequest(BaseModel):
    status: EquipmentStatus | None = None
    mode: EquipmentMode | None = None
    parameter_value: float | None = None


class SnapshotRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class SnapshotRestoreRequest(BaseModel):
    snapshot_id: str


class SnapshotResponse(BaseModel):
    success: bool = True
    snapshot_id: str


class ActionResponse(BaseModel):
    success: bool = True
    state: PlantState


class UnitDetailResponse(BaseModel):
    config: UnitConfig
    state: UnitState
    history: list[HistoryPoint]
    data_mode_notice: str
