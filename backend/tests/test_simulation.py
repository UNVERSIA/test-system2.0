from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app, virtual_plant
from app.simulation.engine import SimulationEngine


def fresh_engine() -> SimulationEngine:
    return SimulationEngine(Path(__file__).parents[1] / "app" / "simulation" / "config" / "demo_plant.json")


def test_configuration_parsing_topology_and_units():
    engine = fresh_engine()
    assert engine.config.data_mode.value == "DEMO"
    assert len(engine.config.units) == 16
    ids = {unit.id for unit in engine.config.units}
    assert len(ids) == 16
    for edge in engine.config.connections:
        assert edge.source_unit_id in ids
        assert edge.target_unit_id in ids
        source = next(unit for unit in engine.config.units if unit.id == edge.source_unit_id)
        target = next(unit for unit in engine.config.units if unit.id == edge.target_unit_id)
        assert edge.source_port in {port.id for port in source.outlets}
        assert edge.target_port in {port.id for port in target.inlets}
    assert engine.config.simulation_parameters["time_step_min"] == 1
    assert all(sensor.unit for unit in engine.config.units for sensor in unit.sensors)


def test_water_balance_and_level_bounds():
    engine = fresh_engine()
    before = engine.state.units["lift_station"].volume_m3
    state = engine.step(1)
    lift = next(unit for unit in state.units if unit.unit_id == "lift_station")
    expected = before + (lift.inflow_m3_d - lift.outflow_m3_d) / 1440
    assert lift.volume_m3 == pytest.approx(expected)
    engine.load_scenario("influent_surge")
    engine.state.units["coarse_screen"].status = "stopped"
    state = engine.step(80)
    coarse = next(unit for unit in state.units if unit.unit_id == "coarse_screen")
    assert 0 <= coarse.level_pct <= 100
    assert coarse.status == "blocked"
    assert any(alarm.id == "high_level:coarse_screen" for alarm in state.alarms)


def test_quality_is_provisional_and_propagates():
    engine = fresh_engine()
    state = engine.step(3)
    coarse = next(unit for unit in state.units if unit.unit_id == "coarse_screen")
    lift = next(unit for unit in state.units if unit.unit_id == "lift_station")
    assert coarse.water_quality["COD"] == pytest.approx(220)
    assert lift.water_quality["COD"] == pytest.approx(220)
    formula = next(item for item in engine.formulas if item.formula_id == "VP-QUALITY-001")
    assert formula.trust_status.value == "awaiting_source"
    assert formula.full_source is None


def test_equipment_state_changes_energy():
    engine = fresh_engine()
    state_on = engine.step(2)
    assert state_on.total_energy_kwh > 0


def test_equipment_update_validation_and_effect():
    from app.simulation.schemas import EquipmentUpdateRequest

    engine = fresh_engine()
    engine.update_equipment("lift_station", "lift_pump_1", EquipmentUpdateRequest(status="off"))
    state = engine.step(1)
    lift = next(unit for unit in state.units if unit.unit_id == "lift_station")
    assert lift.outflow_m3_d == 0
    with pytest.raises(ValueError):
        engine.update_equipment("lift_station", "lift_pump_1", EquipmentUpdateRequest(parameter_value=101))


def test_four_scenarios_and_reset():
    engine = fresh_engine()
    assert {item.scenario_id for item in engine.scenarios} == {"normal", "influent_surge", "blower_failure", "methane_anomaly"}
    for scenario_id in ("normal", "influent_surge", "blower_failure", "methane_anomaly"):
        state = engine.load_scenario(scenario_id)
        assert state.simulation_minute == 0
        assert state.scenario_id == scenario_id
        assert engine.step(12).simulation_minute == 12
    reset = engine.reset()
    assert reset.simulation_minute == 0
    assert reset.scenario_id == "normal"


def test_blower_fault_changes_do_and_alarm():
    engine = fresh_engine()
    engine.load_scenario("blower_failure")
    engine.step(10)
    blower = engine._find_equipment("blower_main")
    assert blower.status.value == "fault"
    before = engine.state.units["aerobic_tank"].water_quality["DO"]
    state = engine.step(5)
    after = next(unit for unit in state.units if unit.unit_id == "aerobic_tank").water_quality["DO"]
    assert after < before
    assert any(alarm.unit_id == "blower_house" for alarm in state.alarms)


def test_methane_anomaly_scenario():
    engine = fresh_engine()
    engine.load_scenario("methane_anomaly")
    state = engine.step(20)
    anaerobic = next(unit for unit in state.units if unit.unit_id == "anaerobic_tank")
    assert anaerobic.methane_mg_l > 2
    assert anaerobic.methane_risk in {"high", "critical"}
    assert any(alarm.id == "methane:anaerobic_tank" for alarm in state.alarms)


def test_snapshot_restore():
    engine = fresh_engine()
    engine.step(7)
    snapshot_id = engine.save_snapshot("minute seven")
    engine.step(5)
    restored = engine.restore_snapshot(snapshot_id)
    assert restored.simulation_minute == 7


def test_virtual_plant_api_state_consistency():
    client = TestClient(app)
    client.post("/api/virtual-plant/reset")
    config = client.get("/api/virtual-plant/config").json()
    state = client.get("/api/virtual-plant/state").json()
    assert len(config["units"]) == len(state["units"]) == 16
    stepped = client.post("/api/virtual-plant/step", json={"steps": 3}).json()["state"]
    assert stepped["simulation_minute"] == 3
    detail = client.get("/api/virtual-plant/units/aerobic_tank").json()
    assert detail["state"]["unit_id"] == "aerobic_tank"
    assert detail["history"][-1]["simulation_minute"] == 3
    scenario = client.post("/api/virtual-plant/scenario", json={"scenario_id": "methane_anomaly"})
    assert scenario.status_code == 200
    assert scenario.json()["state"]["scenario_id"] == "methane_anomaly"
    bad = client.patch("/api/virtual-plant/units/lift_station/equipment/lift_pump_1", json={"parameter_value": 1000})
    assert bad.status_code == 422
    client.post("/api/virtual-plant/reset")
