<script setup lang="ts">
import { computed } from "vue";
import { useVirtualPlantStore } from "../../stores/virtualPlant";
const store = useVirtualPlantStore();
const bounds = computed(() => {
  const units = store.config?.units || [];
  const xs = units.map((unit) => unit.visual_layout.position[0]),
    zs = units.map((unit) => unit.visual_layout.position[2]);
  return {
    minX: Math.min(...xs, -1),
    maxX: Math.max(...xs, 1),
    minZ: Math.min(...zs, -1),
    maxZ: Math.max(...zs, 1),
  };
});
function point(unitId: string) {
  const unit = store.config?.units.find((item) => item.id === unitId);
  if (!unit) return { x: 0, y: 0 };
  const b = bounds.value;
  return {
    x:
      35 +
      ((unit.visual_layout.position[0] - b.minX) / (b.maxX - b.minX)) * 730,
    y:
      28 +
      ((unit.visual_layout.position[2] - b.minZ) / (b.maxZ - b.minZ)) * 210,
  };
}
function state(unitId: string) {
  return store.state?.units.find((item) => item.unit_id === unitId);
}
</script>
<template>
  <div class="vp-topology" data-testid="process-topology">
    <svg viewBox="0 0 800 270" role="img" aria-label="示范水厂工艺拓扑">
      <defs>
        <marker
          id="arrow-water"
          markerWidth="7"
          markerHeight="7"
          refX="6"
          refY="3.5"
          orient="auto"
        >
          <path d="M0,0 L7,3.5 L0,7 z" fill="#45aaca" />
        </marker>
        <marker
          id="arrow-air"
          markerWidth="7"
          markerHeight="7"
          refX="6"
          refY="3.5"
          orient="auto"
        >
          <path d="M0,0 L7,3.5 L0,7 z" fill="#69d6ca" />
        </marker>
        <marker
          id="arrow-sludge"
          markerWidth="7"
          markerHeight="7"
          refX="6"
          refY="3.5"
          orient="auto"
        >
          <path d="M0,0 L7,3.5 L0,7 z" fill="#a67b52" />
        </marker>
      </defs>
      <line
        v-for="edge in store.config?.connections"
        :key="edge.id"
        :x1="point(edge.source_unit_id).x"
        :y1="point(edge.source_unit_id).y"
        :x2="point(edge.target_unit_id).x"
        :y2="point(edge.target_unit_id).y"
        :class="['topology-edge', edge.medium]"
        :marker-end="`url(#arrow-${edge.medium})`"
      />
      <g
        v-for="unit in store.config?.units"
        :key="unit.id"
        class="topology-node"
        :class="[
          `risk-${state(unit.id)?.methane_risk || 'normal'}`,
          {
            selected: store.selectedUnitId === unit.id,
            alarm: state(unit.id)?.alarms.length,
          },
        ]"
        :transform="`translate(${point(unit.id).x},${point(unit.id).y})`"
        @click="store.selectUnit(unit.id)"
      >
        <rect x="-31" y="-15" width="62" height="30" rx="5" />
        <circle cx="-22" cy="-7" r="3" />
        <text text-anchor="middle" y="4">{{ unit.name }}</text>
      </g>
    </svg>
    <div class="topology-legend">
      <span>蓝：水线</span><span>棕：污泥线</span><span>青：空气线</span>
    </div>
  </div>
</template>
