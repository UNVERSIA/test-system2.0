<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "./api";
import WanziFloatingAssistant from "./components/wanzi/WanziFloatingAssistant.vue";
import { useVirtualPlantStore } from "./stores/virtualPlant";
import { useAppDataStore } from "./stores/appData";
const route = useRoute();
const router = useRouter();
const dataFile = ref<File | null>(null);
const dataSource = ref("尚未加载数据");
const settingsOpen = ref(false);
const uploadStatus = ref("");
const apiOnline = ref(false);
const tensorflowAvailable = ref(false);
const cozeConfigured = ref(false);
const plant = useVirtualPlantStore();
const appData = useAppDataStore();
const isVirtualPlant = computed(
  () => route.path === "/3d" || route.path === "/process",
);
const plantClock = computed(() => {
  const minute = plant.state?.simulation_minute || 0;
  return `${String(Math.floor(minute / 60)).padStart(2, "0")}:${String(minute % 60).padStart(2, "0")}`;
});
const pages = [
  { title: "3D水厂仿真", path: "/3d", glyph: "01" },
  { title: "工艺流程仿真", path: "/process", glyph: "02" },
  { title: "甲烷足迹追踪", path: "/footprint", glyph: "03" },
  { title: "甲烷账户管理", path: "/account", glyph: "04" },
  { title: "优化与决策", path: "/optimization", glyph: "05" },
  { title: "甲烷排放预测", path: "/prediction", glyph: "06" },
  { title: "减排技术分析", path: "/technology", glyph: "07" },
  { title: "因子库管理", path: "/factors", glyph: "08" },
  { title: "数字人助手", path: "/assistant", glyph: "09" },
  { title: "AI实验室·污水处理闯关", path: "/game", glyph: "10" },
];
const currentPage = computed(
  () => pages.find((page) => page.path === route.path)?.title || "3D水厂仿真",
);
const apiLabel = computed(() => (apiOnline.value ? "已连接" : "未连接"));
const tfLabel = computed(() =>
  tensorflowAvailable.value ? "可用" : "备用模式",
);
const cozeLabel = computed(() => (cozeConfigured.value ? "已配置" : "未配置"));
async function checkHealth() {
  try {
    const r = await api.get("/health");
    apiOnline.value = true;
    tensorflowAvailable.value = Boolean(r.data.tensorflow_available);
    cozeConfigured.value = Boolean(r.data.coze_configured);
  } catch {
    apiOnline.value = false;
  }
}
async function upload() {
  if (!dataFile.value) return;
  uploadStatus.value = "正在识别数据格式…";
  try {
    const r = await appData.upload(dataFile.value);
    dataSource.value = appData.dataSource;
    uploadStatus.value = r.conversion_info || "数据加载成功";
  } catch {
    uploadStatus.value = "数据加载错误，请检查 Excel 格式或后端服务";
  }
}
async function simulate() {
  try {
    await appData.simulate();
    dataSource.value = appData.dataSource;
    uploadStatus.value = "模拟数据生成完成";
  } catch {
    uploadStatus.value = "模拟数据生成失败，请检查 FastAPI 服务";
  }
}
onMounted(checkHealth);
</script>
<template>
  <div class="app-shell">
    <aside class="main-sidebar">
      <div class="brand-mark">
        <span class="brand-dot" />
        <div>
          <strong>寻清问碳</strong><small>污水处理智能监控与虚拟仿真</small>
        </div>
      </div>
      <div class="sidebar-section-title">系统导航</div>
      <nav class="main-nav" aria-label="系统导航">
        <button
          v-for="page in pages"
          :key="page.path"
          class="nav-item"
          :class="{ active: route.path === page.path }"
          @click="router.push(page.path)"
        >
          <span class="nav-index">{{ page.glyph }}</span
          ><span>{{ page.title }}</span>
        </button>
      </nav>
      <div class="sidebar-foot"><span class="pulse-dot" />实时监控工作台</div>
    </aside>
    <div class="app-body">
      <header class="topbar" :class="{ 'virtual-plant-topbar': isVirtualPlant }">
        <div>
          <span class="eyebrow">污水处理厂 · 数字孪生监控平台</span>
          <h1>污水处理甲烷监测调控与智慧科普系统</h1>
        </div>
        <div class="topbar-status">
          <div class="status-item current-page">
            当前页面 <b>{{ currentPage }}</b>
          </div>
          <div class="status-item">
            <span class="status-light" :class="{ good: apiOnline }" />FastAPI
            <b>{{ apiLabel }}</b>
          </div>
          <template v-if="isVirtualPlant">
            <div class="status-item">
              仿真时间 <b>{{ plantClock }}</b>
            </div>
            <div class="status-item">
              状态 <b>{{ plant.state?.running ? "运行中" : "已暂停" }}</b>
            </div>
            <div class="status-item">
              告警
              <b :class="{ 'alarm-text': plant.state?.alarms.length }">{{
                plant.state?.alarms.length || 0
              }}</b>
            </div>
          </template>
          <template v-else
            ><div class="status-item">
              TensorFlow <b>{{ tfLabel }}</b>
            </div>
            <div class="status-item">
              Coze <b>{{ cozeLabel }}</b>
            </div>
            <div class="status-item source">
              数据源 <b>{{ dataSource }}</b>
            </div>
          </template>
        </div>
      </header>
      <div
        class="workspace"
        :class="{ 'virtual-plant-workspace': isVirtualPlant }"
      >
        <button v-if="!isVirtualPlant" class="settings-toggle" @click="settingsOpen = true">数据输入与设置</button>
        <div v-if="!isVirtualPlant && settingsOpen" class="settings-backdrop" @click.self="settingsOpen = false"></div>
        <section v-if="!isVirtualPlant && settingsOpen" class="settings-drawer">
          <div class="drawer-heading">
            <div>
              <span class="section-kicker">全局设置</span>
              <h2>数据输入与设置</h2>
            </div>
            <button class="drawer-close" aria-label="关闭设置" @click="settingsOpen = false">×</button>
            <span class="connection-badge" :class="{ online: apiOnline }">{{
              apiLabel
            }}</span>
          </div>
          <label class="file-control"
            >上传运行数据（Excel）<input
              type="file"
              accept=".xlsx"
              @change="
                dataFile =
                  ($event.target as HTMLInputElement).files?.[0] || null;
                upload();
              "
            /><span>{{ dataFile?.name || "选择 .xlsx 文件" }}</span></label
          >
          <p v-if="uploadStatus || appData.conversionInfo" class="drawer-status">{{ uploadStatus || appData.conversionInfo }}</p>
          <div class="setting-group">
            <h3>工艺优化模拟</h3>
            <label
              >曝气时间调整（%）<output>0</output
              ><input type="range" min="-30" max="30" value="0" /></label
            ><label
              >PAC投加量调整（%）<output>0</output
              ><input type="range" min="-20" max="20" value="0" /></label
            ><label
              >污泥回流比<output>0.50</output
              ><input type="range" min="0.3" max="0.8" step="0.05" value="0.5"
            /></label>
          </div>
          <div class="setting-group">
            <h3>动态效果设置</h3>
            <label class="check-row"
              ><input type="checkbox" checked />启用动态水流效果</label
            ><label
              >水流速度<output>10000</output
              ><input type="range" min="1000" max="20000" value="10000"
            /></label>
          </div>
          <div class="setting-group">
            <h3>高级功能设置</h3>
            <button class="secondary-action">更新电力排放因子</button
            ><button class="secondary-action" @click="simulate">
              生成模拟数据</button
            ><button class="secondary-action">重置甲烷因子数据库</button>
          </div>
        </section>
        <main
          class="content-area"
          :class="{ 'virtual-plant-content': isVirtualPlant }"
        >
          <div v-if="!isVirtualPlant" class="breadcrumb">
            <span>系统工作台</span><i>/</i><strong>{{ currentPage }}</strong>
          </div>
          <RouterView />
        </main>
      </div>
    </div>
    <WanziFloatingAssistant />
  </div>
</template>
