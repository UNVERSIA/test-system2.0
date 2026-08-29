from __future__ import annotations

from .schemas import EquipmentConfig, EquipmentState


def advance_equipment(config: EquipmentConfig, state: EquipmentState, dt_min: float) -> tuple[float, float]:
    available = state.status.value == "on"
    span = max(config.parameter_max - config.parameter_min, 1e-9)
    load = min(max((state.parameter_value - config.parameter_min) / span, 0.0), 1.0) if available else 0.0
    state.power_kw = config.rated_power_kw * load
    step_energy = state.power_kw * dt_min / 60.0
    state.energy_kwh += step_energy
    return load, step_energy
