<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
const route = useRoute(); const router = useRouter()
const pagesOrder = ['3d','process','footprint','account','optimization','prediction','technology','factors','assistant','game']
const links = computed(() => router.getRoutes().filter(r => r.meta.title).sort((a,b) => pagesOrder.indexOf(String(a.meta.path)) - pagesOrder.indexOf(String(b.meta.path))))
const title = '寻清问碳：基于智能体与数字孪生的污水处理甲烷监测调控与智慧科普系统'
</script>
<template>
  <div class="shell"><aside><h2>数据输入与设置</h2><label>上传运行数据（Excel）<input type="file" accept=".xlsx" /></label><h3>工艺优化模拟</h3><label>曝气时间调整（%）<input type="range" min="-30" max="30" value="0" /></label><label>PAC投加量调整（%）<input type="range" min="-20" max="20" value="0" /></label><label>污泥回流比<input type="range" min="0.3" max="0.8" step="0.05" value="0.5" /></label><h3>动态效果设置</h3><label><input type="checkbox" checked /> 启用动态水流效果</label><label>水流速度<input type="range" min="1000" max="20000" value="10000" /></label><h3>高级功能设置</h3><button>更新电力排放因子</button><button>生成模拟数据</button><button>重置甲烷因子数据库</button></aside><main><h1>{{ title }}</h1><nav><button v-for="link in links" :key="link.path" :class="{active: route.path === link.path}" @click="router.push(link.path)">{{ link.meta.title }}</button></nav><RouterView /></main></div>
</template>
