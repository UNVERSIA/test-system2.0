import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { api } from "../api";

export type DataMode = "DEMO" | "UPLOADED" | "LIVE";
export type EquipmentStatus = "on" | "off" | "fault" | "maintenance";
export type Medium = "water" | "sludge" | "air";
export interface SensorConfig {
  id: string;
  name: string;
  metric: string;
  unit: string;
  quality_status: string;
}
export interface EquipmentConfig {
  id: string;
  name: string;
  type: string;
  rated_power_kw: number;
  capacity: number;
  capacity_unit: string;
  adjustable_parameter: string;
  parameter_min: number;
  parameter_max: number;
  parameter_default: number;
  parameter_unit: string;
  relationship_status: string;
}
export interface UnitConfig {
  id: string;
  name: string;
  process_type: string;
  area: string;
  effective_volume_m3: number;
  design_flow_m3_d: number;
  initial_level_pct: number;
  initial_status: string;
  visual_layout: {
    position: number[];
    size: number[];
    structure: string;
    color: string;
  };
  inlets: { id: string; kind: Medium }[];
  outlets: { id: string; kind: Medium }[];
  sensors: SensorConfig[];
  equipment: EquipmentConfig[];
  parameter_source: string;
  data_quality_status: string;
  initial_quality: Record<string, number>;
  initial_methane_mg_l: number;
}
export interface ConnectionConfig {
  id: string;
  source_unit_id: string;
  target_unit_id: string;
  medium: Medium;
  source_port: string;
  target_port: string;
}
export interface PlantConfig {
  plant_id: string;
  plant_name: string;
  data_mode: DataMode;
  units: UnitConfig[];
  connections: ConnectionConfig[];
  constraints: Record<string, unknown>;
  visual_layout: Record<string, unknown>;
  simulation_parameters: Record<string, unknown>;
  disclaimer: string;
}
export interface EquipmentState {
  id: string;
  name: string;
  type: string;
  status: EquipmentStatus;
  mode: "auto" | "manual";
  parameter_value: number;
  parameter_unit: string;
  power_kw: number;
  energy_kwh: number;
}
export interface SensorState {
  id: string;
  name: string;
  metric: string;
  value: number;
  unit: string;
  quality_status: string;
}
export interface UnitState {
  unit_id: string;
  name: string;
  status: "running" | "stopped" | "blocked";
  level_pct: number;
  volume_m3: number;
  inflow_m3_d: number;
  outflow_m3_d: number;
  water_quality: Record<string, number>;
  methane_mg_l: number;
  methane_risk: "normal" | "attention" | "high" | "critical";
  sensors: SensorState[];
  equipment: EquipmentState[];
  alarms: string[];
  data_quality_status: string;
}
export interface AlarmState {
  id: string;
  severity: "info" | "warning" | "critical";
  unit_id: string | null;
  message: string;
  simulation_minute: number;
  recoverable_action: string;
}
export interface PlantState {
  plant_id: string;
  data_mode: DataMode;
  simulation_minute: number;
  running: boolean;
  speed: number;
  scenario_id: string;
  units: UnitState[];
  alarms: AlarmState[];
  total_inflow_m3_d: number;
  total_outflow_m3_d: number;
  total_energy_kwh: number;
  methane_risk_counts: Record<string, number>;
  disclaimer: string;
}
export interface HistoryPoint {
  simulation_minute: number;
  unit_id: string;
  level_pct: number;
  inflow_m3_d: number;
  outflow_m3_d: number;
  methane_mg_l: number;
  cod_mg_l: number;
  do_mg_l: number;
  energy_kwh: number;
}
export interface Scenario {
  scenario_id: string;
  name: string;
  description: string;
  trigger_minute: number;
  affected_units: string[];
  expected_changes: string[];
  recoverable_action: string;
  end_condition: string;
  status: string;
}
export interface Formula {
  formula_id: string;
  name: string;
  expression: string;
  variables: Record<string, string>;
  units: string;
  scope: string;
  source_type: string;
  full_source: string | null;
  source_locator: string | null;
  trust_status: string;
  requires_plant_calibration: boolean;
  implementation: string;
  tests: string;
}

export const useVirtualPlantStore = defineStore("virtualPlant", () => {
  const config = ref<PlantConfig | null>(null);
  const state = ref<PlantState | null>(null);
  const scenarios = ref<Scenario[]>([]);
  const formulas = ref<Formula[]>([]);
  const history = ref<HistoryPoint[]>([]);
  const selectedUnitId = ref("coarse_screen");
  const selectedEquipmentId = ref("");
  const selectedSensorId = ref("");
  const loading = ref(false);
  const actionPending = ref(false);
  const error = ref("");
  const showLabels = ref(true);
  const showPipelines = ref(true);
  const animationEnabled = ref(true);
  const autoCruise = ref(false);
  let pollTimer: number | undefined;
  let initialization: Promise<void> | null = null;
  const selectedUnit = computed(
    () =>
      state.value?.units.find(
        (unit) => unit.unit_id === selectedUnitId.value,
      ) || null,
  );
  const selectedConfig = computed(
    () =>
      config.value?.units.find((unit) => unit.id === selectedUnitId.value) ||
      null,
  );
  const selectedEquipment = computed(
    () =>
      selectedUnit.value?.equipment.find(
        (item) => item.id === selectedEquipmentId.value,
      ) || null,
  );
  const selectedEquipmentConfig = computed(
    () =>
      selectedConfig.value?.equipment.find(
        (item) => item.id === selectedEquipmentId.value,
      ) || null,
  );
  const selectedSensor = computed(
    () =>
      selectedUnit.value?.sensors.find(
        (item) => item.id === selectedSensorId.value,
      ) || null,
  );
  const scenario = computed(
    () =>
      scenarios.value.find(
        (item) => item.scenario_id === state.value?.scenario_id,
      ) || null,
  );
  async function initialize(force = false) {
    if (initialization && !force) return initialization;
    initialization = (async () => {
      loading.value = true;
      error.value = "";
      try {
        const [cfg, current, scenarioList, formulaList] = await Promise.all([
          api.get("/virtual-plant/config"),
          api.get("/virtual-plant/state"),
          api.get("/virtual-plant/scenarios"),
          api.get("/virtual-plant/formulas"),
        ]);
        const loadedConfig = cfg.data as PlantConfig;
        config.value = loadedConfig;
        state.value = current.data;
        scenarios.value = scenarioList.data;
        formulas.value = formulaList.data;
        if (
          !loadedConfig.units.some((unit) => unit.id === selectedUnitId.value)
        )
          selectedUnitId.value = loadedConfig.units[0]?.id || "";
        await refreshHistory();
      } catch (e) {
        error.value = "虚拟水厂服务连接失败，请确认 FastAPI 已启动";
        throw e;
      } finally {
        loading.value = false;
      }
    })();
    try {
      await initialization;
    } finally {
      initialization = null;
    }
  }
  function applyState(next: PlantState) {
    state.value = next;
  }
  async function refreshState() {
    try {
      applyState((await api.get("/virtual-plant/state")).data);
      if (selectedUnitId.value) await refreshHistory();
    } catch {
      error.value = "状态刷新失败";
    }
  }
  async function refreshHistory() {
    if (!selectedUnitId.value) return;
    history.value = (
      await api.get(`/virtual-plant/history/${selectedUnitId.value}`, {
        params: { limit: 180 },
      })
    ).data;
  }
  async function act(path: string, payload?: unknown) {
    if (actionPending.value) return;
    actionPending.value = true;
    error.value = "";
    try {
      const response = await api.post(`/virtual-plant/${path}`, payload || {});
      applyState(response.data.state);
      await refreshHistory();
    } catch {
      error.value = "仿真操作失败，请检查后端状态";
    } finally {
      actionPending.value = false;
    }
  }
  const start = () => act("start");
  const pause = () => act("pause");
  const step = (steps = 1) => act("step", { steps });
  const reset = () => act("reset");
  const setSpeed = (speed: number) => act("speed", { speed });
  const loadScenario = (scenario_id: string) =>
    act("scenario", { scenario_id });
  async function updateEquipment(update: {
    status?: EquipmentStatus;
    mode?: "auto" | "manual";
    parameter_value?: number;
  }) {
    if (!selectedEquipment.value || !selectedUnit.value) return;
    actionPending.value = true;
    try {
      const response = await api.patch(
        `/virtual-plant/units/${selectedUnit.value.unit_id}/equipment/${selectedEquipment.value.id}`,
        update,
      );
      applyState(response.data.state);
      await refreshHistory();
    } catch {
      error.value = "设备参数更新失败";
    } finally {
      actionPending.value = false;
    }
  }
  async function selectUnit(unitId: string) {
    selectedUnitId.value = unitId;
    selectedEquipmentId.value = "";
    selectedSensorId.value = "";
    await refreshHistory();
  }
  function selectEquipment(unitId: string, equipmentId: string) {
    selectedUnitId.value = unitId;
    selectedEquipmentId.value = equipmentId;
    selectedSensorId.value = "";
    void refreshHistory();
  }
  function selectSensor(unitId: string, sensorId: string) {
    selectedUnitId.value = unitId;
    selectedSensorId.value = sensorId;
    selectedEquipmentId.value = "";
    void refreshHistory();
  }
  function startPolling() {
    if (pollTimer) return;
    pollTimer = window.setInterval(() => {
      if (state.value?.running) void refreshState();
    }, 1000);
  }
  function stopPolling() {
    if (pollTimer) {
      window.clearInterval(pollTimer);
      pollTimer = undefined;
    }
  }
  return {
    config,
    state,
    scenarios,
    formulas,
    history,
    selectedUnitId,
    selectedEquipmentId,
    selectedSensorId,
    selectedUnit,
    selectedConfig,
    selectedEquipment,
    selectedEquipmentConfig,
    selectedSensor,
    scenario,
    loading,
    actionPending,
    error,
    showLabels,
    showPipelines,
    animationEnabled,
    autoCruise,
    initialize,
    refreshState,
    start,
    pause,
    step,
    reset,
    setSpeed,
    loadScenario,
    updateEquipment,
    selectUnit,
    selectEquipment,
    selectSensor,
    startPolling,
    stopPolling,
  };
});
