<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import ProcessTopology from "../components/virtual-plant/ProcessTopology.vue";
import UnitTrendChart from "../components/virtual-plant/UnitTrendChart.vue";
import { useVirtualPlantStore } from "../stores/virtualPlant";
const store = useVirtualPlantStore();
onMounted(async () => {
  await store.initialize();
  store.startPolling();
});
onUnmounted(() => store.stopPolling());
</script>
<template>
  <section class="vp-process-page">
    <header>
      <div>
        <span class="section-kicker">SAME STATE / 2D VIEW</span>
        <h2>工艺流程与状态传播概览</h2>
      </div>
      <div class="process-actions">
        <button :disabled="store.state?.running" @click="store.start">
          启动</button
        ><button :disabled="!store.state?.running" @click="store.pause">
          暂停</button
        ><button :disabled="store.state?.running" @click="store.step(1)">
          单步</button
        ><button @click="store.reset">重置</button>
      </div>
    </header>
    <div v-if="store.config && store.state" class="process-layout">
      <div class="process-canvas"><ProcessTopology /></div>
      <aside>
        <h3>{{ store.selectedUnit?.name }}</h3>
        <p>
          {{ store.selectedConfig?.area }} · {{ store.selectedUnit?.status }}
        </p>
        <dl>
          <dt>仿真分钟</dt>
          <dd>{{ store.state.simulation_minute }}</dd>
          <dt>液位</dt>
          <dd>{{ store.selectedUnit?.level_pct.toFixed(1) }}%</dd>
          <dt>流量</dt>
          <dd>{{ store.selectedUnit?.outflow_m3_d.toFixed(0) }} m³/d</dd>
          <dt>甲烷风险</dt>
          <dd>{{ store.selectedUnit?.methane_risk }}</dd>
          <dt>数据质量</dt>
          <dd>{{ store.selectedUnit?.data_quality_status }}</dd>
        </dl>
        <p class="vp-trust-warning">
          {{ store.selectedConfig?.parameter_source }}
        </p>
      </aside>
      <UnitTrendChart />
    </div>
  </section>
</template>
