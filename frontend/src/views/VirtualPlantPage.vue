<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import VirtualPlantScene from "../components/virtual-plant/VirtualPlantScene.vue";
import ProcessTopology from "../components/virtual-plant/ProcessTopology.vue";
import UnitTrendChart from "../components/virtual-plant/UnitTrendChart.vue";
import FormulaRegistry from "../components/virtual-plant/FormulaRegistry.vue";
import {
  useVirtualPlantStore,
  type EquipmentStatus,
} from "../stores/virtualPlant";

const store = useVirtualPlantStore();
const scene = ref<InstanceType<typeof VirtualPlantScene> | null>(null);
const showFormula = ref(false);
const activeBottom = ref<"trend" | "topology" | "alarms">("trend");
const equipmentValue = ref(0);
const equipmentStatus = ref<EquipmentStatus>("on");
const equipmentMode = ref<"auto" | "manual">("auto");
const simulationClock = computed(() => {
  const minute = store.state?.simulation_minute || 0;
  return `${String(Math.floor(minute / 60)).padStart(2, "0")}:${String(minute % 60).padStart(2, "0")}`;
});
const alarmCount = computed(() => store.state?.alarms.length || 0);
const waterBalanceDelta = computed(() =>
  Math.abs(
    (store.state?.total_inflow_m3_d || 0) -
      (store.state?.total_outflow_m3_d || 0),
  ),
);
const qualityItems = computed(() => {
  const q = store.selectedUnit?.water_quality || {};
  return [
    ["COD", q.COD, "mg/L"],
    ["氨氮", q.NH3N, "mg/L"],
    ["TN", q.TN, "mg/L"],
    ["TP", q.TP, "mg/L"],
    ["SS", q.SS, "mg/L"],
    ["DO", q.DO, "mg/L"],
    ["pH", q.pH, ""],
    ["温度", q.temperature, "°C"],
  ];
});
watch(
  () => store.selectedEquipment,
  (item) => {
    if (item) {
      equipmentValue.value = item.parameter_value;
      equipmentStatus.value = item.status;
      equipmentMode.value = item.mode;
    }
  },
  { immediate: true },
);
async function applyEquipment() {
  await store.updateEquipment({
    parameter_value: equipmentValue.value,
    status: equipmentStatus.value,
    mode: equipmentMode.value,
  });
}
onMounted(async () => {
  await store.initialize();
  store.startPolling();
  await nextTick();
});
onUnmounted(() => store.stopPolling());
</script>

<template>
  <section class="vp-page" data-testid="virtual-plant-workbench">
    <div v-if="store.loading" class="vp-loading">
      正在装载示范水厂配置与仿真状态…
    </div>
    <template v-else-if="store.config && store.state"
      ><div class="vp-page-tools">
        <button @click="showFormula = true">查看公式可信度</button>
      </div>
      <header class="vp-commandbar">
        <div class="vp-command-title">
          <span class="section-kicker">VIRTUAL PLANT V1</span>
          <h2>{{ store.config.plant_name }}</h2>
        </div>
        <div class="vp-live-status">
          <div>
            <small>仿真时间</small><b>{{ simulationClock }}</b>
          </div>
          <div>
            <small>运行状态</small
            ><b :class="store.state.running ? 'running' : 'paused'">{{
              store.state.running ? "运行中" : "已暂停"
            }}</b>
          </div>
          <div>
            <small>告警</small
            ><b :class="{ danger: alarmCount }">{{ alarmCount }}</b>
          </div>
        </div>
      </header>
      <div class="vp-main-grid">
        <aside class="vp-control-panel">
          <section>
            <div class="vp-panel-title">
              <span>场景控制</span><em>{{ store.scenario?.status }}</em>
            </div>
            <label class="vp-field"
              >示范场景<select
                :value="store.state.scenario_id"
                @change="
                  store.loadScenario(($event.target as HTMLSelectElement).value)
                "
              >
                <option
                  v-for="item in store.scenarios"
                  :key="item.scenario_id"
                  :value="item.scenario_id"
                >
                  {{ item.name }}
                </option>
              </select></label
            >
            <p class="vp-hint">{{ store.scenario?.description }}</p>
            <div class="vp-control-buttons">
              <button
                class="primary"
                :disabled="store.state.running"
                @click="store.start"
              >
                启动</button
              ><button :disabled="!store.state.running" @click="store.pause">
                暂停</button
              ><button :disabled="store.state.running" @click="store.step(1)">
                单步</button
              ><button @click="store.reset">重置</button>
            </div>
          </section>
          <section>
            <div class="vp-panel-title">
              <span>仿真速度</span><em>{{ store.state.speed }}×</em>
            </div>
            <div class="vp-speed-options">
              <button
                v-for="speed in [0.25, 1, 5, 15, 60]"
                :key="speed"
                :class="{ active: store.state.speed === speed }"
                @click="store.setSpeed(speed)"
              >
                {{ speed }}×
              </button>
            </div>
            <div class="vp-timeline">
              <div>
                <span>00:00</span><strong>{{ simulationClock }}</strong>
              </div>
              <div class="timeline-track">
                <i
                  :style="{
                    width: `${Math.min(100, (store.state.simulation_minute % 120) / 1.2)}%`,
                  }"
                />
              </div>
              <small>统一工艺时间步：1分钟；浏览器帧率不参与工艺计算</small>
            </div>
          </section>
          <section>
            <div class="vp-panel-title"><span>图层与动画</span></div>
            <label class="vp-switch"
              ><input
                v-model="store.showLabels"
                type="checkbox"
              /><i />中文标签</label
            ><label class="vp-switch"
              ><input
                v-model="store.showPipelines"
                type="checkbox"
              /><i />水/泥/气管线</label
            ><label class="vp-switch"
              ><input
                v-model="store.animationEnabled"
                type="checkbox"
              /><i />水流与设备动画</label
            ><label class="vp-switch"
              ><input
                v-model="store.autoCruise"
                type="checkbox"
              /><i />自动巡航</label
            >
          </section>
          <section>
            <div class="vp-panel-title"><span>视图</span></div>
            <div class="vp-view-buttons">
              <button @click="scene?.resetView()">重置视角</button
              ><button @click="scene?.topView()">顶视图</button
              ><button @click="scene?.birdView()">鸟瞰图</button>
            </div>
            <p class="vp-hint">左键旋转 · 滚轮缩放 · 右键平移</p>
          </section>
        </aside>
        <main class="vp-stage">
          <div class="vp-kpis">
            <div>
              <small>进水流量</small
              ><strong>{{ store.state.total_inflow_m3_d.toFixed(0) }}</strong
              ><span>m³/d</span>
            </div>
            <div>
              <small>出水流量</small
              ><strong>{{ store.state.total_outflow_m3_d.toFixed(0) }}</strong
              ><span>m³/d</span>
            </div>
            <div>
              <small>储量变化指示</small
              ><strong>{{ waterBalanceDelta.toFixed(0) }}</strong
              ><span>m³/d</span>
            </div>
            <div>
              <small>累计示范能耗</small
              ><strong>{{ store.state.total_energy_kwh.toFixed(1) }}</strong
              ><span>kWh</span>
            </div>
          </div>
          <VirtualPlantScene ref="scene" />
        </main>
        <aside class="vp-detail-panel">
          <div class="vp-panel-title">
            <span>对象详情</span
            ><em>{{ store.selectedUnit?.data_quality_status }}</em>
          </div>
          <template v-if="store.selectedUnit && store.selectedConfig"
            ><div class="vp-object-heading">
              <div>
                <span
                  :class="`risk-dot risk-${store.selectedUnit.methane_risk}`"
                />
                <div>
                  <h3>{{ store.selectedUnit.name }}</h3>
                  <p>
                    {{ store.selectedConfig.area }} ·
                    {{ store.selectedConfig.process_type }}
                  </p>
                </div>
              </div>
              <span :class="`unit-status ${store.selectedUnit.status}`">{{
                store.selectedUnit.status
              }}</span>
            </div>
            <div class="vp-detail-stats">
              <div>
                <small>液位</small
                ><strong>{{ store.selectedUnit.level_pct.toFixed(1) }}%</strong>
              </div>
              <div>
                <small>有效容积</small
                ><strong
                  >{{ store.selectedConfig.effective_volume_m3 }} m³</strong
                >
              </div>
              <div>
                <small>出流</small
                ><strong
                  >{{ store.selectedUnit.outflow_m3_d.toFixed(0) }} m³/d</strong
                >
              </div>
              <div>
                <small>甲烷示范值</small
                ><strong
                  >{{ store.selectedUnit.methane_mg_l.toFixed(2) }} mg/L</strong
                >
              </div>
            </div>
            <section class="vp-detail-section">
              <h4>当前测点</h4>
              <div class="vp-quality-grid">
                <button v-for="item in qualityItems" :key="String(item[0])">
                  <span>{{ item[0] }}</span
                  ><b>{{ Number(item[1] || 0).toFixed(2) }}</b
                  ><small>{{ item[2] }}</small>
                </button>
              </div>
              <button
                v-for="sensor in store.selectedUnit.sensors"
                :key="sensor.id"
                class="vp-sensor-row"
                :class="{ selected: store.selectedSensorId === sensor.id }"
                @click="
                  store.selectSensor(store.selectedUnit!.unit_id, sensor.id)
                "
              >
                <span>{{ sensor.name }}</span
                ><b>{{ sensor.value }} {{ sensor.unit }}</b
                ><em>{{ sensor.quality_status }}</em>
              </button>
            </section>
            <section class="vp-detail-section">
              <h4>可调设备</h4>
              <div v-if="!store.selectedUnit.equipment.length" class="vp-empty">
                该单元未配置可调设备
              </div>
              <button
                v-for="equipment in store.selectedUnit.equipment"
                :key="equipment.id"
                class="vp-equipment-row"
                :class="[
                  { selected: store.selectedEquipmentId === equipment.id },
                  `status-${equipment.status}`,
                ]"
                @click="
                  store.selectEquipment(
                    store.selectedUnit!.unit_id,
                    equipment.id,
                  )
                "
              >
                <span><i />{{ equipment.name }}</span
                ><b
                  >{{ equipment.status }} · {{ equipment.parameter_value
                  }}{{ equipment.parameter_unit }}</b
                >
              </button>
              <div
                v-if="store.selectedEquipment && store.selectedEquipmentConfig"
                class="vp-equipment-editor"
              >
                <div class="editor-row">
                  <label
                    >状态<select v-model="equipmentStatus">
                      <option value="on">开启</option>
                      <option value="off">停止</option>
                      <option value="fault">故障</option>
                      <option value="maintenance">维护</option>
                    </select></label
                  ><label
                    >模式<select v-model="equipmentMode">
                      <option value="auto">自动</option>
                      <option value="manual">手动</option>
                    </select></label
                  >
                </div>
                <label class="vp-field"
                  >{{ store.selectedEquipmentConfig.adjustable_parameter
                  }}<output
                    >{{ equipmentValue
                    }}{{ store.selectedEquipmentConfig.parameter_unit }}</output
                  ><input
                    v-model.number="equipmentValue"
                    type="range"
                    :min="store.selectedEquipmentConfig.parameter_min"
                    :max="store.selectedEquipmentConfig.parameter_max"
                    step="1"
                /></label>
                <p class="vp-trust-warning">
                  示范关系：{{
                    store.selectedEquipmentConfig.relationship_status
                  }}，待具体设备性能曲线校准
                </p>
                <button class="primary full" @click="applyEquipment">
                  应用设备调整
                </button>
              </div>
            </section>
            <section class="vp-source-card">
              <span>参数来源</span>
              <p>{{ store.selectedConfig.parameter_source }}</p>
              <b>{{ store.state.disclaimer }}</b>
            </section></template
          >
        </aside>
      </div>
      <section class="vp-bottom-panel">
        <nav>
          <button
            :class="{ active: activeBottom === 'trend' }"
            @click="activeBottom = 'trend'"
          >
            状态趋势</button
          ><button
            :class="{ active: activeBottom === 'topology' }"
            @click="activeBottom = 'topology'"
          >
            2D工艺拓扑</button
          ><button
            :class="{ active: activeBottom === 'alarms' }"
            @click="activeBottom = 'alarms'"
          >
            告警与事件 <span>{{ alarmCount }}</span>
          </button>
        </nav>
        <UnitTrendChart v-if="activeBottom === 'trend'" /><ProcessTopology
          v-else-if="activeBottom === 'topology'"
        />
        <div v-else class="vp-alarm-log">
          <div v-if="!store.state.alarms.length" class="vp-empty good">
            当前无活动告警
          </div>
          <article
            v-for="alarm in store.state.alarms"
            :key="alarm.id"
            :class="alarm.severity"
          >
            <time>T+{{ alarm.simulation_minute }} min</time
            ><strong>{{ alarm.message }}</strong>
            <p>恢复操作：{{ alarm.recoverable_action }}</p>
          </article>
        </div>
      </section>
      <p v-if="store.error" class="vp-error">{{ store.error }}</p></template
    ><FormulaRegistry v-if="showFormula" @close="showFormula = false" />
  </section>
</template>
