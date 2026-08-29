<script setup lang="ts">
import { computed } from "vue";
import { useVirtualPlantStore } from "../../stores/virtualPlant";
const store = useVirtualPlantStore();
const width = 760,
  height = 160,
  pad = 24;
function pathFor(values: number[]) {
  if (!values.length) return "";
  const min = Math.min(...values),
    max = Math.max(...values);
  return values
    .map((value, index) => {
      const x =
        pad + (index / Math.max(values.length - 1, 1)) * (width - pad * 2);
      const y =
        height -
        pad -
        ((value - min) / Math.max(max - min, 0.001)) * (height - pad * 2);
      return `${index ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}
const levelPath = computed(() =>
  pathFor(store.history.map((item) => item.level_pct)),
);
const methanePath = computed(() =>
  pathFor(store.history.map((item) => item.methane_mg_l)),
);
const doPath = computed(() =>
  pathFor(store.history.map((item) => item.do_mg_l)),
);
const last = computed(() => store.history[store.history.length - 1]);
</script>
<template>
  <div class="vp-trend" data-testid="state-trend">
    <div class="trend-head">
      <strong>{{ store.selectedUnit?.name || "未选择单元" }} · 状态趋势</strong
      ><span>仿真分钟 {{ last?.simulation_minute ?? 0 }}</span>
    </div>
    <svg :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="none">
      <line
        v-for="n in 4"
        :key="n"
        :x1="pad"
        :x2="width - pad"
        :y1="pad + ((n - 1) * (height - pad * 2)) / 3"
        :y2="pad + ((n - 1) * (height - pad * 2)) / 3"
      />
      <path :d="levelPath" class="trend-level" />
      <path :d="methanePath" class="trend-methane" />
      <path :d="doPath" class="trend-do" />
    </svg>
    <div class="trend-legend">
      <span
        ><i class="level" />液位 {{ last?.level_pct.toFixed(1) || "--" }}%</span
      ><span
        ><i class="methane" />甲烷
        {{ last?.methane_mg_l.toFixed(2) || "--" }} mg/L</span
      ><span
        ><i class="do" />DO {{ last?.do_mg_l.toFixed(2) || "--" }} mg/L</span
      >
    </div>
  </div>
</template>
