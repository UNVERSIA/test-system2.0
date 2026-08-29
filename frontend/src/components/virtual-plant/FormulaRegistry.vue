<script setup lang="ts">
import { useVirtualPlantStore } from "../../stores/virtualPlant";
defineEmits<{ close: [] }>();
const store = useVirtualPlantStore();
</script>
<template>
  <div class="vp-modal-backdrop" @click.self="$emit('close')">
    <section class="vp-modal" role="dialog" aria-label="公式与来源状态">
      <header>
        <div>
          <span class="section-kicker">可信度登记</span>
          <h2>公式与数据来源状态</h2>
        </div>
        <button aria-label="关闭公式注册表" @click="$emit('close')">×</button>
      </header>
      <p class="vp-modal-note">
        未取得完整正式来源或水厂校准数据的关系不会标记为已验证。
      </p>
      <div class="formula-list">
        <article v-for="formula in store.formulas" :key="formula.formula_id">
          <div class="formula-title">
            <code>{{ formula.formula_id }}</code
            ><strong>{{ formula.name }}</strong
            ><span :class="`trust-${formula.trust_status}`">{{
              formula.trust_status
            }}</span>
          </div>
          <pre>{{ formula.expression }}</pre>
          <dl>
            <dt>范围</dt>
            <dd>{{ formula.scope }}</dd>
            <dt>单位</dt>
            <dd>{{ formula.units }}</dd>
            <dt>来源</dt>
            <dd>
              {{ formula.full_source || "待核实：当前没有满足要求的完整来源" }}
            </dd>
            <dt>校准</dt>
            <dd>
              {{
                formula.requires_plant_calibration
                  ? "需要真实水厂数据校准"
                  : "不需要"
              }}
            </dd>
            <dt>实现</dt>
            <dd>{{ formula.implementation }}</dd>
            <dt>测试</dt>
            <dd>{{ formula.tests }}</dd>
          </dl>
        </article>
      </div>
    </section>
  </div>
</template>
