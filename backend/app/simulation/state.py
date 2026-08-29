from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .schemas import AlarmState, EquipmentState, PlantConfig, UnitState


@dataclass
class MutableSimulationState:
    config: PlantConfig
    simulation_minute: int = 0
    running: bool = False
    speed: float = 1.0
    scenario_id: str = "normal"
    units: dict[str, UnitState] = field(default_factory=dict)
    alarms: list[AlarmState] = field(default_factory=list)
    history: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    snapshots: dict[str, dict[str, Any]] = field(default_factory=dict)
    total_energy_kwh: float = 0.0
    last_wall_time: float | None = None


def initial_units(config: PlantConfig) -> dict[str, UnitState]:
    result: dict[str, UnitState] = {}
    for unit in config.units:
        equipment = [
            EquipmentState(
                id=item.id,
                name=item.name,
                type=item.type,
                status="on" if unit.initial_status == "running" else "off",
                mode="auto",
                parameter_value=item.parameter_default,
                parameter_unit=item.parameter_unit,
                power_kw=0,
                energy_kwh=0,
            )
            for item in unit.equipment
        ]
        result[unit.id] = UnitState(
            unit_id=unit.id,
            name=unit.name,
            status=unit.initial_status,
            level_pct=unit.initial_level_pct,
            volume_m3=unit.effective_volume_m3 * unit.initial_level_pct / 100,
            inflow_m3_d=0,
            outflow_m3_d=0,
            water_quality=dict(unit.initial_quality),
            methane_mg_l=unit.initial_methane_mg_l,
            methane_risk="normal",
            sensors=[],
            equipment=equipment,
            alarms=[],
            data_quality_status=unit.data_quality_status,
        )
    return result
