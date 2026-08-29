<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  useVirtualPlantStore,
  type ConnectionConfig,
  type UnitConfig,
} from "../../stores/virtualPlant";

const store = useVirtualPlantStore();
const host = ref<HTMLElement | null>(null);
const canvas = ref<HTMLCanvasElement | null>(null);
const labels = ref<
  {
    id: string;
    name: string;
    x: number;
    y: number;
    visible: boolean;
    risk: string;
  }[]
>([]);
let scene: THREE.Scene,
  camera: THREE.PerspectiveCamera,
  renderer: THREE.WebGLRenderer,
  controls: OrbitControls,
  frame = 0,
  resizeObserver: ResizeObserver | undefined;
const unitGroups = new Map<string, THREE.Group>();
const unitBodies = new Map<string, THREE.Mesh>();
const waterSurfaces = new Map<string, THREE.Mesh>();
const equipmentMeshes = new Map<string, THREE.Mesh>();
const sensorMeshes = new Map<string, THREE.Mesh>();
const pipeObjects: THREE.Object3D[] = [];
const mixers: THREE.Mesh[] = [];
const pumps: THREE.Mesh[] = [];
const waterMaterials: THREE.MeshStandardMaterial[] = [];
let bubblePoints: THREE.Points | undefined;
let lastLabelUpdate = 0;
let cruiseAngle = 0.55;
const riskColors = {
  normal: 0x32c6a6,
  attention: 0xe3bd63,
  high: 0xe58542,
  critical: 0xef4f5f,
};

function material(color: string | number, metalness = 0.25) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.58, metalness });
}
function tagged(
  mesh: THREE.Object3D,
  unitId: string,
  objectType = "unit",
  objectId = unitId,
) {
  mesh.userData = { unitId, objectType, objectId };
  return mesh;
}
function addBox(
  group: THREE.Group,
  size: number[],
  position: number[],
  color: string,
  unitId: string,
) {
  const mesh = tagged(
    new THREE.Mesh(
      new THREE.BoxGeometry(size[0], size[1], size[2]),
      material(color),
    ),
    unitId,
  ) as THREE.Mesh;
  mesh.position.set(position[0], position[1], position[2]);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  group.add(mesh);
  return mesh;
}
function createTank(group: THREE.Group, unit: UnitConfig, circular = false) {
  const [sx, sy, sz] = unit.visual_layout.size;
  const wall = material(unit.visual_layout.color);
  const base = tagged(
    new THREE.Mesh(
      circular
        ? new THREE.CylinderGeometry(sx * 0.48, sx * 0.48, sy, 36)
        : new THREE.BoxGeometry(sx, sy, sz),
      wall,
    ),
    unit.id,
  ) as THREE.Mesh;
  base.position.y = sy / 2;
  base.castShadow = true;
  base.receiveShadow = true;
  group.add(base);
  const inner = tagged(
    new THREE.Mesh(
      circular
        ? new THREE.CylinderGeometry(sx * 0.4, sx * 0.4, 0.13, 36)
        : new THREE.BoxGeometry(sx * 0.84, 0.12, sz * 0.78),
      new THREE.MeshStandardMaterial({
        color: 0x2b8ca8,
        transparent: true,
        opacity: 0.72,
        roughness: 0.2,
        metalness: 0.15,
      }),
    ),
    unit.id,
  );
  inner.position.y = sy + 0.05;
  group.add(inner);
  waterSurfaces.set(unit.id, inner as THREE.Mesh);
  waterMaterials.push(
    (inner as THREE.Mesh).material as THREE.MeshStandardMaterial,
  );
  return base;
}
function createChannel(group: THREE.Group, unit: UnitConfig) {
  const [sx, sy, sz] = unit.visual_layout.size;
  const floor = addBox(
    group,
    [sx, 0.25, sz],
    [0, 0.12, 0],
    unit.visual_layout.color,
    unit.id,
  );
  addBox(
    group,
    [sx, 0.8, 0.18],
    [0, 0.52, -sz / 2],
    unit.visual_layout.color,
    unit.id,
  );
  addBox(
    group,
    [sx, 0.8, 0.18],
    [0, 0.52, sz / 2],
    unit.visual_layout.color,
    unit.id,
  );
  for (let x = -sx * 0.35; x < sx * 0.4; x += 0.35) {
    const bar = addBox(
      group,
      [0.06, 1, sz * 0.75],
      [x, 0.68, 0],
      "#90a9b5",
      unit.id,
    );
    bar.rotation.z = -0.16;
  }
  const water = tagged(
    new THREE.Mesh(
      new THREE.BoxGeometry(sx * 0.94, 0.1, sz * 0.72),
      new THREE.MeshStandardMaterial({
        color: 0x2f9fbd,
        transparent: true,
        opacity: 0.72,
      }),
    ),
    unit.id,
  );
  water.position.y = 0.38;
  group.add(water);
  waterSurfaces.set(unit.id, water as THREE.Mesh);
  return floor;
}
function createBuilding(
  group: THREE.Group,
  unit: UnitConfig,
  equipmentHall = false,
) {
  const [sx, sy, sz] = unit.visual_layout.size;
  const body = addBox(
    group,
    [sx, sy, sz],
    [0, sy / 2, 0],
    unit.visual_layout.color,
    unit.id,
  );
  const roof = new THREE.Mesh(
    new THREE.ConeGeometry(Math.max(sx, sz) * 0.72, 1, 4),
    material("#3b4d5e", 0.45),
  );
  roof.position.y = sy + 0.5;
  roof.rotation.y = Math.PI / 4;
  group.add(roof);
  const door = addBox(
    group,
    [sx * 0.22, sy * 0.48, 0.12],
    [0, sy * 0.24, sz / 2 + 0.06],
    "#172631",
    unit.id,
  );
  if (equipmentHall) {
    for (let x = -sx * 0.25; x <= sx * 0.25; x += sx * 0.25) {
      const fan = tagged(
        new THREE.Mesh(
          new THREE.CylinderGeometry(0.38, 0.38, 0.18, 20),
          material("#80a7b2", 0.7),
        ),
        unit.id,
      );
      fan.rotation.x = Math.PI / 2;
      fan.position.set(x, sy * 0.68, sz / 2 + 0.14);
      group.add(fan);
      pumps.push(fan as THREE.Mesh);
    }
  }
  return body;
}
function createOutlet(group: THREE.Group, unit: UnitConfig) {
  const [sx, , sz] = unit.visual_layout.size;
  const body = createChannel(group, unit);
  const gate = addBox(
    group,
    [0.18, 1.6, sz * 0.85],
    [sx / 2 - 0.15, 0.8, 0],
    "#b7c4ca",
    unit.id,
  );
  gate.rotation.z = 0.05;
  return body;
}
function createEquipment(group: THREE.Group, unit: UnitConfig) {
  unit.equipment.forEach((item, index) => {
    const isMixer = item.type === "mixer";
    const mesh = tagged(
      new THREE.Mesh(
        isMixer
          ? new THREE.CylinderGeometry(0.2, 0.2, 0.6, 16)
          : new THREE.BoxGeometry(0.55, 0.45, 0.55),
        material("#d3a14f", 0.65),
      ),
      unit.id,
      "equipment",
      item.id,
    ) as THREE.Mesh;
    mesh.position.set(
      -unit.visual_layout.size[0] * 0.28 + index * 0.8,
      unit.visual_layout.size[1] + 0.5,
      0,
    );
    mesh.castShadow = true;
    group.add(mesh);
    equipmentMeshes.set(item.id, mesh);
    if (isMixer) mixers.push(mesh);
    else pumps.push(mesh);
  });
}
function createSensors(group: THREE.Group, unit: UnitConfig) {
  unit.sensors.forEach((sensor, index) => {
    const beacon = tagged(
      new THREE.Mesh(
        new THREE.SphereGeometry(0.13, 14, 14),
        new THREE.MeshStandardMaterial({
          color: 0x7de4d6,
          emissive: 0x28685f,
          emissiveIntensity: 1.2,
        }),
      ),
      unit.id,
      "sensor",
      sensor.id,
    ) as THREE.Mesh;
    beacon.position.set(
      unit.visual_layout.size[0] * 0.34 - index * 0.28,
      unit.visual_layout.size[1] + 0.35,
      unit.visual_layout.size[2] * 0.34,
    );
    group.add(beacon);
    sensorMeshes.set(sensor.id, beacon);
  });
}
function buildUnit(unit: UnitConfig) {
  const group = new THREE.Group();
  group.position.set(
    unit.visual_layout.position[0],
    0,
    unit.visual_layout.position[2],
  );
  group.name = unit.id;
  scene.add(group);
  unitGroups.set(unit.id, group);
  let body: THREE.Mesh;
  switch (unit.visual_layout.structure) {
    case "channel":
      body = createChannel(group, unit);
      break;
    case "rectangular_tank":
      body = createTank(group, unit);
      break;
    case "circular_tank":
      body = createTank(group, unit, true);
      break;
    case "equipment_hall":
      body = createBuilding(group, unit, true);
      break;
    case "outlet":
      body = createOutlet(group, unit);
      break;
    default:
      body = createBuilding(group, unit);
  }
  unitBodies.set(unit.id, body);
  createEquipment(group, unit);
  createSensors(group, unit);
}
function curveFor(connection: ConnectionConfig) {
  const source = store.config!.units.find(
    (unit) => unit.id === connection.source_unit_id,
  )!;
  const target = store.config!.units.find(
    (unit) => unit.id === connection.target_unit_id,
  )!;
  const a = new THREE.Vector3(
    source.visual_layout.position[0],
    0.55,
    source.visual_layout.position[2],
  );
  const b = new THREE.Vector3(
    target.visual_layout.position[0],
    0.55,
    target.visual_layout.position[2],
  );
  const lift =
    connection.medium === "air"
      ? 3.2
      : connection.medium === "sludge"
        ? 0.2
        : 0.65;
  const mid = a.clone().lerp(b, 0.5);
  mid.y = lift;
  return new THREE.CatmullRomCurve3([a, mid, b]);
}
function buildConnection(connection: ConnectionConfig) {
  const colors = { water: 0x2d9ac0, sludge: 0x8c6845, air: 0x65d5ce };
  const tube = new THREE.Mesh(
    new THREE.TubeGeometry(
      curveFor(connection),
      32,
      connection.medium === "water" ? 0.11 : 0.08,
      8,
      false,
    ),
    new THREE.MeshStandardMaterial({
      color: colors[connection.medium],
      transparent: true,
      opacity: 0.78,
      emissive: colors[connection.medium],
      emissiveIntensity: 0.15,
    }),
  );
  tube.userData = { medium: connection.medium };
  scene.add(tube);
  pipeObjects.push(tube);
  for (let i = 1; i <= 3; i++) {
    const marker = new THREE.Mesh(
      new THREE.SphereGeometry(0.11, 10, 10),
      new THREE.MeshBasicMaterial({ color: colors[connection.medium] }),
    );
    marker.userData = {
      curve: curveFor(connection),
      offset: i / 3,
      medium: connection.medium,
    };
    scene.add(marker);
    pipeObjects.push(marker);
  }
}
function buildBubbles() {
  const positions: number[] = [];
  for (const unitId of ["aerobic_tank", "mbr_tank"]) {
    const unit = store.config!.units.find((item) => item.id === unitId)!;
    for (let i = 0; i < 70; i++) {
      const xRatio = ((i * 37) % 101) / 100 - 0.5,
        yRatio = ((i * 53) % 97) / 96,
        zRatio = ((i * 71) % 103) / 102 - 0.5;
      positions.push(
        unit.visual_layout.position[0] +
          xRatio * unit.visual_layout.size[0] * 0.75,
        0.2 + yRatio * 2.2,
        unit.visual_layout.position[2] +
          zRatio * unit.visual_layout.size[2] * 0.7,
      );
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(positions, 3),
  );
  bubblePoints = new THREE.Points(
    geometry,
    new THREE.PointsMaterial({
      color: 0xb9f7ff,
      size: 0.09,
      transparent: true,
      opacity: 0.75,
    }),
  );
  scene.add(bubblePoints);
}
function buildScene() {
  store.config!.units.forEach(buildUnit);
  store.config!.connections.forEach(buildConnection);
  buildBubbles();
  labels.value = store.config!.units.map((unit) => ({
    id: unit.id,
    name: unit.name,
    x: 0,
    y: 0,
    visible: true,
    risk: "normal",
  }));
}
function updateVisualState() {
  const state = store.state;
  if (!state) return;
  state.units.forEach((unit) => {
    const body = unitBodies.get(unit.unit_id);
    const group = unitGroups.get(unit.unit_id);
    if (body) {
      const mat = body.material as THREE.MeshStandardMaterial;
      const risk = riskColors[unit.methane_risk];
      mat.emissive.setHex(risk);
      mat.emissiveIntensity =
        unit.unit_id === store.selectedUnitId
          ? 0.34
          : unit.methane_risk === "normal"
            ? 0.06
            : 0.22;
    }
    if (group) group.userData.hasAlarm = unit.alarms.length > 0;
    const water = waterSurfaces.get(unit.unit_id);
    const cfg = store.config?.units.find((item) => item.id === unit.unit_id);
    if (water && cfg) {
      const base =
        cfg.visual_layout.structure === "channel"
          ? 0.38
          : cfg.visual_layout.size[1];
      water.position.y = base * Math.max(0.28, unit.level_pct / 100);
    }
  });
  state.units
    .flatMap((unit) => unit.equipment)
    .forEach((item) => {
      const mesh = equipmentMeshes.get(item.id);
      if (mesh) {
        const mat = mesh.material as THREE.MeshStandardMaterial;
        mat.color.set(
          item.status === "on"
            ? 0x56d0a8
            : item.status === "fault"
              ? 0xef5061
              : item.status === "maintenance"
                ? 0xe0b45a
                : 0x60717c,
        );
      }
    });
  const blower = state.units
    .flatMap((unit) => unit.equipment)
    .find((item) => item.id === "blower_main");
  if (bubblePoints) bubblePoints.visible = blower?.status === "on";
  pipeObjects.forEach((item) => (item.visible = store.showPipelines));
}
function updateLabels() {
  if (!host.value || !store.config) return;
  const width = host.value.clientWidth,
    height = host.value.clientHeight;
  const byId = new Map(store.state?.units.map((unit) => [unit.unit_id, unit]));
  labels.value = labels.value.map((label) => {
    const group = unitGroups.get(label.id);
    if (!group) return label;
    const v = group.position.clone();
    v.y =
      store.config!.units.find((unit) => unit.id === label.id)!.visual_layout
        .size[1] + 1;
    v.project(camera);
    return {
      ...label,
      x: (v.x * 0.5 + 0.5) * width,
      y: (-0.5 * v.y + 0.5) * height,
      visible: store.showLabels && v.z < 1,
      risk: byId.get(label.id)?.methane_risk || "normal",
    };
  });
}
function resize() {
  if (!host.value) return;
  const width = Math.max(host.value.clientWidth, 1),
    height = Math.max(host.value.clientHeight, 1);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height, false);
}
function pick(event: PointerEvent) {
  if (!canvas.value) return;
  const rect = canvas.value.getBoundingClientRect();
  const pointer = new THREE.Vector2(
    ((event.clientX - rect.left) / rect.width) * 2 - 1,
    -((event.clientY - rect.top) / rect.height) * 2 + 1,
  );
  const raycaster = new THREE.Raycaster();
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster
    .intersectObjects([...unitGroups.values()], true)
    .find((item) => item.object.userData.unitId);
  if (!hit) return;
  const data = hit.object.userData;
  if (data.objectType === "equipment")
    store.selectEquipment(data.unitId, data.objectId);
  else if (data.objectType === "sensor")
    store.selectSensor(data.unitId, data.objectId);
  else void store.selectUnit(data.unitId);
}
function resetView() {
  camera.position.set(24, 23, 30);
  controls.target.set(0, 0, -2);
  controls.update();
}
function topView() {
  camera.position.set(0, 42, 0.1);
  controls.target.set(0, 0, 0);
  controls.update();
}
function birdView() {
  camera.position.set(26, 24, 30);
  controls.target.set(0, 0, -2);
  controls.update();
}
defineExpose({ resetView, topView, birdView });

onMounted(() => {
  if (!host.value || !canvas.value || !store.config) return;
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x091118);
  scene.fog = new THREE.FogExp2(0x091118, 0.012);
  camera = new THREE.PerspectiveCamera(42, 1, 0.1, 160);
  renderer = new THREE.WebGLRenderer({
    canvas: canvas.value,
    antialias: true,
    powerPreference: "high-performance",
  });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.minDistance = 12;
  controls.maxDistance = 70;
  controls.maxPolarAngle = Math.PI * 0.48;
  resetView();
  scene.add(new THREE.HemisphereLight(0xbfe9ff, 0x25313b, 2.2));
  const sun = new THREE.DirectionalLight(0xffffff, 3);
  sun.position.set(16, 28, 12);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  scene.add(sun);
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(48, 32),
    material("#14252b"),
  );
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);
  const grid = new THREE.GridHelper(48, 48, 0x31505a, 0x1b333b);
  grid.position.y = 0.015;
  scene.add(grid);
  buildScene();
  updateVisualState();
  resizeObserver = new ResizeObserver(resize);
  resizeObserver.observe(host.value);
  resize();
  canvas.value.addEventListener("pointerup", pick);
  const clock = new THREE.Clock();
  const animate = () => {
    frame = requestAnimationFrame(animate);
    const dt = clock.getDelta();
    if (store.animationEnabled) {
      const t = performance.now() * 0.001;
      waterMaterials.forEach(
        (mat, index) => (mat.opacity = 0.64 + Math.sin(t * 1.4 + index) * 0.08),
      );
      mixers.forEach((mesh) => (mesh.rotation.y += dt * 2));
      pumps.forEach((mesh) => (mesh.rotation.z += dt * 0.7));
      pipeObjects.forEach((item) => {
        if (item.userData.curve) {
          item.userData.offset =
            (item.userData.offset + dt * 0.08 * (store.state?.speed || 1)) % 1;
          item.position.copy(
            item.userData.curve.getPoint(item.userData.offset),
          );
        }
      });
      if (bubblePoints) {
        const position = bubblePoints.geometry.attributes
          .position as THREE.BufferAttribute;
        for (let i = 0; i < position.count; i++) {
          let y = position.getY(i) + dt * 0.45;
          if (y > 2.6) y = 0.2;
          position.setY(i, y);
        }
        position.needsUpdate = true;
      }
    }
    if (store.autoCruise) {
      cruiseAngle += dt * 0.08;
      camera.position.x = Math.cos(cruiseAngle) * 35;
      camera.position.z = Math.sin(cruiseAngle) * 35;
      camera.lookAt(controls.target);
    }
    controls.update();
    const now = performance.now();
    if (now - lastLabelUpdate > 80) {
      updateLabels();
      lastLabelUpdate = now;
    }
    unitGroups.forEach((group) => {
      if (group.userData.hasAlarm) {
        const s = 1 + Math.sin(now * 0.008) * 0.018;
        group.scale.setScalar(s);
      } else group.scale.setScalar(1);
    });
    renderer.render(scene, camera);
  };
  animate();
});
watch(() => store.state, updateVisualState, { deep: false });
watch(() => [store.selectedUnitId, store.showPipelines], updateVisualState);
watch(() => store.showLabels, updateLabels);
onUnmounted(() => {
  cancelAnimationFrame(frame);
  resizeObserver?.disconnect();
  canvas.value?.removeEventListener("pointerup", pick);
  controls?.dispose();
  scene?.traverse((object) => {
    const mesh = object as THREE.Mesh;
    if (mesh.geometry) mesh.geometry.dispose();
    const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    mats.filter(Boolean).forEach((item) => (item as THREE.Material).dispose());
  });
  renderer?.dispose();
});
</script>

<template>
  <div ref="host" class="vp-scene-host" data-testid="virtual-plant-scene">
    <canvas ref="canvas" aria-label="虚拟水厂三维场景" />
    <div class="vp-scene-vignette" />
    <button
      v-for="label in labels"
      v-show="label.visible"
      :key="label.id"
      class="vp-unit-label"
      :class="[
        `risk-${label.risk}`,
        { selected: store.selectedUnitId === label.id },
      ]"
      :style="{ left: `${label.x}px`, top: `${label.y}px` }"
      @click.stop="store.selectUnit(label.id)"
    >
      {{ label.name }}
    </button>
    <div class="vp-scene-legend">
      <span><i class="normal" />正常</span
      ><span><i class="attention" />关注</span
      ><span><i class="high" />较高</span
      ><span><i class="critical" />严重</span>
    </div>
  </div>
</template>
