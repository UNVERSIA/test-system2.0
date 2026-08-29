from __future__ import annotations

import copy
import json
import threading
import time
import uuid
from pathlib import Path

from .equipment import advance_equipment
from .mass_balance import advance_volume, mix_quality
from .methane import risk_level
from .provenance import FORMULAS
from .scenarios import SCENARIOS
from .schemas import (
    AlarmState,
    DataMode,
    EquipmentMode,
    EquipmentStatus,
    EquipmentUpdateRequest,
    HistoryPoint,
    PlantConfig,
    PlantState,
    QualityStatus,
    SensorState,
    UnitDetailResponse,
)
from .state import MutableSimulationState, initial_units


class SimulationEngine:
    """Minute-step, configuration-driven demonstration plant engine.

    V1 deliberately implements state propagation and explicit illustrative
    relationships only. It is not a calibrated biochemical process model.
    """

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or Path(__file__).parent / "config" / "demo_plant.json"
        self._lock = threading.RLock()
        self.config = self._load_config()
        self._equipment_config = {item.id: item for unit in self.config.units for item in unit.equipment}
        self._unit_config = {unit.id: unit for unit in self.config.units}
        self._water_incoming: dict[str, list[str]] = {unit.id: [] for unit in self.config.units}
        for edge in self.config.connections:
            if edge.medium == "water":
                self._water_incoming[edge.target_unit_id].append(edge.source_unit_id)
        self.state = self._new_state()

    def _load_config(self) -> PlantConfig:
        return PlantConfig.model_validate_json(self.config_path.read_text(encoding="utf-8"))

    def _new_state(self) -> MutableSimulationState:
        state = MutableSimulationState(config=self.config, units=initial_units(self.config))
        state.history = {unit.id: [] for unit in self.config.units}
        self._refresh_derived(state)
        self._record_history(state)
        return state

    def reset(self) -> PlantState:
        with self._lock:
            snapshots = self.state.snapshots
            self.state = self._new_state()
            self.state.snapshots = snapshots
            return self.current_state(advance_clock=False)

    def start(self) -> PlantState:
        with self._lock:
            self.state.running = True
            self.state.last_wall_time = time.monotonic()
            return self.current_state(advance_clock=False)

    def pause(self) -> PlantState:
        with self._lock:
            self._advance_realtime()
            self.state.running = False
            self.state.last_wall_time = None
            return self.current_state(advance_clock=False)

    def set_speed(self, speed: float) -> PlantState:
        with self._lock:
            self._advance_realtime()
            self.state.speed = speed
            self.state.last_wall_time = time.monotonic() if self.state.running else None
            return self.current_state(advance_clock=False)

    def load_scenario(self, scenario_id: str) -> PlantState:
        if scenario_id not in SCENARIOS:
            raise KeyError(scenario_id)
        with self._lock:
            self.state = self._new_state()
            self.state.scenario_id = scenario_id
            return self.current_state(advance_clock=False)

    def step(self, steps: int = 1) -> PlantState:
        with self._lock:
            for _ in range(steps):
                self._step_once()
            self.state.last_wall_time = time.monotonic() if self.state.running else None
            return self.current_state(advance_clock=False)

    def _advance_realtime(self) -> None:
        if not self.state.running:
            return
        now = time.monotonic()
        if self.state.last_wall_time is None:
            self.state.last_wall_time = now
            return
        elapsed = now - self.state.last_wall_time
        steps = min(int(elapsed * self.state.speed), 120)
        if steps:
            for _ in range(steps):
                self._step_once()
            self.state.last_wall_time += steps / self.state.speed

    def _scenario_inputs(self) -> tuple[float, dict[str, float]]:
        params = self.config.simulation_parameters
        flow = float(params["influent_flow_m3_d"])
        quality = dict(params["influent_quality"])
        minute = self.state.simulation_minute
        if self.state.scenario_id == "influent_surge" and 10 <= minute < 50:
            flow *= 1.8
        if self.state.scenario_id == "blower_failure" and minute == 10:
            blower = self._find_equipment("blower_main")
            if blower:
                blower.status = EquipmentStatus.FAULT
        if self.state.scenario_id == "methane_anomaly" and minute >= 10:
            target = self.state.units["anaerobic_tank"]
            target.methane_mg_l = min(target.methane_mg_l + 0.30, 6.0)
        return flow, quality

    def _step_once(self) -> None:
        self.state.simulation_minute += int(self.config.simulation_parameters["time_step_min"])
        dt = float(self.config.simulation_parameters["time_step_min"])
        influent_flow, influent_quality = self._scenario_inputs()
        step_energy = 0.0
        for unit in self.config.units:
            unit_state = self.state.units[unit.id]
            equipment_loads: dict[str, float] = {}
            for item in unit_state.equipment:
                load, energy = advance_equipment(self._equipment_config[item.id], item, dt)
                equipment_loads[item.id] = load
                step_energy += energy
            incoming_ids = self._water_incoming[unit.id]
            is_water_unit = bool(incoming_ids) or unit.id == "coarse_screen"
            if is_water_unit:
                if incoming_ids:
                    incoming_states = [self.state.units[source_id] for source_id in incoming_ids]
                    inflow = sum(item.outflow_m3_d for item in incoming_states)
                    incoming_quality = self._weighted_quality(incoming_states)
                else:
                    inflow, incoming_quality = influent_flow, influent_quality
                unit_state.inflow_m3_d = inflow
                available = unit_state.status == "running"
                capacity_factor = self._flow_capacity_factor(unit.id, equipment_loads)
                requested_outflow = min(inflow, unit.design_flow_m3_d * capacity_factor) if available else 0.0
                max_from_storage = unit_state.volume_m3 * 1440 / dt + inflow
                unit_state.outflow_m3_d = min(requested_outflow, max_from_storage)
                incoming_volume = inflow * dt / 1440
                unit_state.water_quality = mix_quality(unit_state.water_quality, incoming_quality, unit_state.volume_m3, incoming_volume)
                unit_state.volume_m3, unconstrained = advance_volume(unit_state.volume_m3, inflow, unit_state.outflow_m3_d, dt, unit.effective_volume_m3)
                unit_state.level_pct = 100 * unit_state.volume_m3 / unit.effective_volume_m3
                if unconstrained > unit.effective_volume_m3:
                    unit_state.status = "blocked"
            else:
                unit_state.inflow_m3_d = 0
                unit_state.outflow_m3_d = 0
        self.state.total_energy_kwh += step_energy
        self._apply_process_demonstration()
        self._refresh_derived(self.state)
        self._record_history(self.state)

    def _flow_capacity_factor(self, unit_id: str, equipment_loads: dict[str, float]) -> float:
        flow_types = {"pump", "reflux", "mbr_suction"}
        candidates = [load for equipment_id, load in equipment_loads.items() if self._equipment_config[equipment_id].type in flow_types]
        return max(candidates, default=1.0)

    def _weighted_quality(self, states) -> dict[str, float]:
        total = sum(item.outflow_m3_d for item in states)
        if total <= 0:
            return dict(states[0].water_quality) if states else {}
        keys = states[0].water_quality.keys()
        return {key: sum(item.water_quality[key] * item.outflow_m3_d for item in states) / total for key in keys}

    def _apply_process_demonstration(self) -> None:
        blower = self._find_equipment("blower_main")
        blower_config = self._equipment_config.get("blower_main")
        blower_load = 0.0
        if blower and blower_config and blower.status == EquipmentStatus.ON:
            span = max(blower_config.parameter_max - blower_config.parameter_min, 1e-9)
            blower_load = min(max((blower.parameter_value - blower_config.parameter_min) / span, 0), 1)
        for unit_id in ("aerobic_tank", "mbr_tank"):
            unit = self.state.units[unit_id]
            current = unit.water_quality.get("DO", 0)
            unit.water_quality["DO"] = min(max(current + 0.03 * blower_load - 0.015, 0), 10)

    def _refresh_derived(self, state: MutableSimulationState) -> None:
        alarms: list[AlarmState] = []
        for config in self.config.units:
            unit = state.units[config.id]
            unit.methane_risk = risk_level(unit.methane_mg_l)
            unit.alarms = []
            if unit.level_pct >= 90:
                unit.alarms.append("高液位")
                alarms.append(self._alarm("high_level", "critical", unit.unit_id, f"{unit.name}液位达到{unit.level_pct:.1f}%", "检查下游通量并提高可用泵送能力"))
            if unit.status in {"stopped", "blocked"}:
                unit.alarms.append("单元停运或堵塞")
                alarms.append(self._alarm("unit_unavailable", "warning", unit.unit_id, f"{unit.name}当前{unit.status}", "恢复单元运行或执行重置"))
            for equipment in unit.equipment:
                if equipment.status in {EquipmentStatus.FAULT, EquipmentStatus.MAINTENANCE}:
                    unit.alarms.append(f"{equipment.name}{equipment.status.value}")
                    alarms.append(self._alarm("equipment", "critical", unit.unit_id, f"{equipment.name}状态：{equipment.status.value}", "修复后将设备状态切换为开启"))
            if unit.methane_risk in {"high", "critical"}:
                unit.alarms.append("甲烷浓度异常")
                alarms.append(self._alarm("methane", "critical" if unit.methane_risk == "critical" else "warning", unit.unit_id, f"{unit.name}甲烷示范值{unit.methane_mg_l:.2f} mg/L", "现场核查测点；演示系统可重置场景"))
            unit.sensors = self._sensor_states(config.id, state)
        state.alarms = alarms

    def _sensor_states(self, unit_id: str, simulation_state: MutableSimulationState) -> list[SensorState]:
        config = self._unit_config[unit_id]
        state = simulation_state.units[unit_id]
        values = {**state.water_quality, "level": state.level_pct, "flow": state.outflow_m3_d, "methane": state.methane_mg_l}
        return [SensorState(id=sensor.id, name=sensor.name, metric=sensor.metric, value=round(float(values.get(sensor.metric, 0)), 4), unit=sensor.unit, quality_status=sensor.quality_status) for sensor in config.sensors]

    def _alarm(self, kind: str, severity: str, unit_id: str, message: str, action: str) -> AlarmState:
        return AlarmState(id=f"{kind}:{unit_id}", severity=severity, unit_id=unit_id, message=message, simulation_minute=self.state.simulation_minute, recoverable_action=action)

    def _record_history(self, state: MutableSimulationState) -> None:
        for unit_id, unit in state.units.items():
            energy = sum(item.energy_kwh for item in unit.equipment)
            point = HistoryPoint(simulation_minute=state.simulation_minute, unit_id=unit_id, level_pct=unit.level_pct, inflow_m3_d=unit.inflow_m3_d, outflow_m3_d=unit.outflow_m3_d, methane_mg_l=unit.methane_mg_l, cod_mg_l=unit.water_quality.get("COD", 0), do_mg_l=unit.water_quality.get("DO", 0), energy_kwh=energy)
            state.history[unit_id].append(point.model_dump())
            state.history[unit_id] = state.history[unit_id][-1000:]

    def current_state(self, advance_clock: bool = True) -> PlantState:
        with self._lock:
            if advance_clock:
                self._advance_realtime()
            water_sources = [edge.source_unit_id for edge in self.config.connections if edge.medium == "water"]
            water_targets = [edge.target_unit_id for edge in self.config.connections if edge.medium == "water"]
            inlet_ids = [unit.id for unit in self.config.units if unit.id in water_sources and unit.id not in water_targets]
            outlet_ids = [unit.id for unit in self.config.units if unit.id in water_targets and unit.id not in water_sources]
            counts = {name: 0 for name in ("normal", "attention", "high", "critical")}
            for unit in self.state.units.values():
                counts[unit.methane_risk] += 1
            return PlantState(plant_id=self.config.plant_id, data_mode=DataMode.DEMO, simulation_minute=self.state.simulation_minute, running=self.state.running, speed=self.state.speed, scenario_id=self.state.scenario_id, units=list(self.state.units.values()), alarms=self.state.alarms, total_inflow_m3_d=sum(self.state.units[item].inflow_m3_d for item in inlet_ids), total_outflow_m3_d=sum(self.state.units[item].outflow_m3_d for item in outlet_ids), total_energy_kwh=self.state.total_energy_kwh, methane_risk_counts=counts, disclaimer=self.config.disclaimer)

    def history(self, unit_id: str, limit: int = 240) -> list[HistoryPoint]:
        if unit_id not in self.state.history:
            raise KeyError(unit_id)
        return [HistoryPoint.model_validate(item) for item in self.state.history[unit_id][-limit:]]

    def unit_detail(self, unit_id: str) -> UnitDetailResponse:
        if unit_id not in self._unit_config:
            raise KeyError(unit_id)
        return UnitDetailResponse(config=self._unit_config[unit_id], state=self.state.units[unit_id], history=self.history(unit_id, 120), data_mode_notice=self.config.disclaimer)

    def update_equipment(self, unit_id: str, equipment_id: str, update: EquipmentUpdateRequest) -> PlantState:
        if unit_id not in self.state.units:
            raise KeyError(unit_id)
        equipment = next((item for item in self.state.units[unit_id].equipment if item.id == equipment_id), None)
        config = self._equipment_config.get(equipment_id)
        if not equipment or not config:
            raise KeyError(equipment_id)
        if update.parameter_value is not None:
            if not config.parameter_min <= update.parameter_value <= config.parameter_max:
                raise ValueError("parameter outside configured range")
            equipment.parameter_value = update.parameter_value
        if update.status is not None:
            equipment.status = update.status
        if update.mode is not None:
            equipment.mode = update.mode
        self._refresh_derived(self.state)
        return self.current_state(advance_clock=False)

    def save_snapshot(self, name: str) -> str:
        snapshot_id = uuid.uuid4().hex[:12]
        self.state.snapshots[snapshot_id] = {"name": name, "state": copy.deepcopy({"minute": self.state.simulation_minute, "running": False, "speed": self.state.speed, "scenario_id": self.state.scenario_id, "units": self.state.units, "alarms": self.state.alarms, "history": self.state.history, "energy": self.state.total_energy_kwh})}
        return snapshot_id

    def restore_snapshot(self, snapshot_id: str) -> PlantState:
        if snapshot_id not in self.state.snapshots:
            raise KeyError(snapshot_id)
        snapshots = self.state.snapshots
        payload = copy.deepcopy(snapshots[snapshot_id]["state"])
        self.state.simulation_minute = payload["minute"]
        self.state.running = payload["running"]
        self.state.speed = payload["speed"]
        self.state.scenario_id = payload["scenario_id"]
        self.state.units = payload["units"]
        self.state.alarms = payload["alarms"]
        self.state.history = payload["history"]
        self.state.total_energy_kwh = payload["energy"]
        self.state.snapshots = snapshots
        return self.current_state(advance_clock=False)

    def _find_equipment(self, equipment_id: str):
        for unit in self.state.units.values():
            for equipment in unit.equipment:
                if equipment.id == equipment_id:
                    return equipment
        return None

    @property
    def scenarios(self):
        return list(SCENARIOS.values())

    @property
    def formulas(self):
        return FORMULAS
