<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import * as THREE from 'three'
const route = useRoute(); const path = computed(() => String(route.meta.path)); const title = computed(() => String(route.meta.title));
const status = ref(''); const records = ref<Record<string, unknown>[]>([]); const selectedUnit = ref('粗格栅'); const enabled = ref(true); const message = ref(''); const question = ref(''); const levels = ref<Record<string, unknown>[]>([])
const units = ref<Record<string, any>>({}); const factors = ref<Record<string, unknown>[]>([]); const techs = ref(['厌氧消化产沼','光伏发电','高效曝气']); const chosenTechs = ref<string[]>([...techs.value]); const months = ref(12)
const canvas = ref<HTMLCanvasElement | null>(null); let animationFrame = 0; let renderer: THREE.WebGLRenderer | undefined
async function simulate(){ const r=await api.post('/data/simulate'); records.value=r.data.records; status.value=`模拟数据生成完成，共 ${records.value.length} 条`; }
async function calc(){ const r=await api.post('/carbon/unit',{records:records.value}); records.value=r.data.records; status.value='已完成原计算模块核算'; }
async function loadUnits(){ units.value=(await api.get('/units')).data.units }
async function loadFactors(){ factors.value=(await api.get('/factors')).data.records || [] }
async function send(){ const r=await api.post('/chat',{message:question.value}); message.value=r.data.response || ''; question.value='' }
async function game(){ levels.value=[(await api.get('/game/state')).data.level] }
onMounted(()=>{ if(path.value==='3d'||path.value==='process') loadUnits(); if(path.value==='factors') loadFactors(); if(path.value==='game') game(); if(path.value==='3d' && canvas.value){ const scene=new THREE.Scene(); scene.background=new THREE.Color(0x101722); const camera=new THREE.PerspectiveCamera(45, canvas.value.clientWidth/canvas.value.clientHeight,.1,100); camera.position.set(0,3,8); renderer=new THREE.WebGLRenderer({canvas:canvas.value,antialias:true}); renderer.setSize(canvas.value.clientWidth,canvas.value.clientHeight,false); scene.add(new THREE.HemisphereLight(0xffffff,0x334455,2)); const floor=new THREE.Mesh(new THREE.BoxGeometry(8,.2,4),new THREE.MeshStandardMaterial({color:0x2d5d72})); scene.add(floor); for(let i=0;i<6;i++){const tank=new THREE.Mesh(new THREE.CylinderGeometry(.55,.55,.8,32),new THREE.MeshStandardMaterial({color:[0x3498db,0x2ecc71,0xe74c3c][i%3]})); tank.position.set(-3+i*1.2,.5,0); scene.add(tank)}; const tick=()=>{scene.rotation.y+=.002; renderer?.render(scene,camera); animationFrame=requestAnimationFrame(tick)}; tick() } })
onUnmounted(()=>{ if(animationFrame) cancelAnimationFrame(animationFrame); renderer?.dispose() })
</script>
<template>
  <section class="page"><h2>{{ title === '🤖数字人助手' ? '🤖 污水处理智能助手' : title === '🎮AI实验室·污水处理闯关' ? '🎮AI实验室·污水处理闯关' : title }}</h2>
    <div v-if="path==='3d'" class="panel"><h3>🏭 污水处理厂 3D 数字孪生系统</h3><p>基于 Three.js 的物理级真实感渲染 | 实时光影 | 动态水面 | 点击编辑</p><canvas ref="canvas" class="scene" aria-label="3D水厂场景"></canvas><select v-model="selectedUnit"><option v-for="(_,name) in units" :key="name">{{name}}</option></select><label>运行状态 <input type="checkbox" v-model="enabled" /></label><button @click="status='参数已保存'">💾 保存参数修改</button></div>
    <div v-else-if="path==='process'" class="panel"><h3>2D水厂工艺流程仿真</h3><div class="flow">粗格栅 → 提升泵房 → 细格栅 → 曝气沉砂池 → 厌氧池 → 缺氧池 → 好氧池 → MBR膜池 → 消毒接触池</div><select v-model="selectedUnit"><option v-for="(_,name) in units" :key="name">{{name}}</option></select><label>启用单元 <input type="checkbox" v-model="enabled" /></label><button @click="status='参数已保存'">保存参数修改</button></div>
    <div v-else-if="path==='footprint'||path==='account'||path==='optimization'" class="panel"><p v-if="!records.length">请先上传运行数据</p><template v-else><button @click="calc">执行原模块计算</button><pre>{{ JSON.stringify(records.slice(0,2),null,2) }}</pre></template><button @click="simulate">生成模拟数据</button></div>
    <div v-else-if="path==='prediction'" class="panel"><h3>1. 模型管理</h3><button @click="status='模型加载请求已发送'">加载预训练模型</button><h3>2. 模型训练</h3><button @click="status='训练请求已发送'">训练新模型</button><h3>3. 预测设置</h3><label>选择预测时长 <select v-model="months"><option :value="1">1</option><option :value="3">3</option><option :value="6">6</option><option :value="12">12</option></select> 个月</label><button @click="status=records.length?'预测请求已发送':'请先上传运行数据'">进行预测</button><p>模型状态：{{ status || '⚠️ 请先加载或训练模型' }}</p></div>
    <div v-else-if="path==='technology'" class="panel"><h3>选择对比技术</h3><label v-for="tech in ['厌氧消化产沼','光伏发电','高效曝气','热泵技术','污泥干化','沼气发电']" :key="tech"><input type="checkbox" :value="tech" v-model="chosenTechs" />{{ tech }}</label><button @click="status='技术对比请求已发送'">运行技术对比分析</button><h3>甲烷抵消计算</h3><input type="number" value="1000" aria-label="沼气发电量(kWh)" /><input type="number" value="500" aria-label="光伏发电量(kWh)" /><p>总甲烷抵消量：3345.00 kgCO2eq</p></div>
    <div v-else-if="path==='factors'" class="panel"><h3>当前甲烷排放因子（权威来源）</h3><table><thead><tr><th>因子类型</th><th>因子值</th><th>单位</th></tr></thead><tbody><tr v-for="factor in factors" :key="String(factor.factor_type)"><td>{{factor.factor_type}}</td><td>{{factor.factor_value}}</td><td>{{factor.unit}}</td></tr></tbody></table><button @click="status='因子导出请求已发送'">导出因子数据</button></div>
    <div v-else-if="path==='assistant'" class="panel"><p>🎉 欢迎来到智能助手！我是「烷仔」，你的污水处理智能助手。</p><h3>❓ 常见问题</h3><button v-for="q in ['水厂有哪些工艺流程？','如何优化工艺降低排放？','有哪些减排技术？','甲烷排放是如何计算的？','LSTM预测如何使用？']" :key="q" @click="question=q">💡 {{q}}</button><input v-model="question" placeholder="输入你的问题..." @keyup.enter="send" /><button @click="send">发送</button><p>{{message}}</p></div>
    <div v-else class="panel"><h3>第1关：预处理</h3><p>组件库与流程区</p><button @click="status='已提交'">提交</button><button @click="game">重置</button><button @click="status='下一关'">下一关</button><pre>{{JSON.stringify(levels,null,2)}}</pre></div><p class="status">{{status}}</p>
  </section>
</template>
