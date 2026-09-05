<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { api } from "../api";
import { useAppDataStore } from "../stores/appData";

const route = useRoute();
const data = useAppDataStore();
const path = computed(() => String(route.meta.path));
const title = computed(() => String(route.meta.title).replace(/^🤖|^🎮/, "").trim());
const status = ref("");
const records = computed(() => data.records);
const calculated = computed(() => data.calculated);
const busy = ref(false);
const selectedTechs = ref(["厌氧消化产沼", "光伏发电", "高效曝气"]);
const techOptions = ["厌氧消化产沼", "光伏发电", "高效曝气", "热泵技术", "污泥干化", "沼气发电"];
const techResult = ref<Record<string, any>[]>([]);
const optimization = ref<Record<string, any> | null>(null);
const scenario = ref<Record<string, any> | null>(null);
const prediction = ref<Record<string, any>[]>([]);
const predictionMode = ref("");
const predictionMonths = ref(12);
const modelStatus = ref("模型尚未加载");
const factors = ref<Record<string, any>[]>([]);
const factorHistory = ref<Record<string, any>[]>([]);
const factorType = ref("电力");
const factorValue = ref(0.5366);
const factorYear = ref(2024);
const exportFormat = ref<"csv" | "excel">("csv");
const chatQuestion = ref("");
const chatMessages = ref<{ role: string; content: string }[]>([]);
const level = ref<Record<string, any>>({});
const gameOrder = ref<Record<string, any>[]>([]);
const gameResult = ref("");
const draggingGame = ref<number | null>(null);
const customFormula = ref({ name: "单位水处理甲烷排放", expression: "energy * 0.9419 / water_flow" });
const formulaValue = ref<Record<string, number>>({ water_flow: 10000, energy: 2500, chemicals: 0, pac: 0, pam: 0, naclo: 0, tn_in: 40, tn_out: 20, cod_in: 200, cod_out: 50 });
const formulaResult = ref<number | null>(null);
function n(value: any) { const result = Number(value); return Number.isFinite(result) ? result : 0; }
function sum(key: string, rows = calculated.value) { return rows.reduce((total, row) => total + n(row[key]), 0); }
const zoneTotals = computed(() => { const keys: Record<string, string> = { 预处理区: "pre_CO2eq", 生物处理区: "bio_CO2eq", 深度处理区: "depth_CO2eq", 泥处理区: "sludge_CO2eq", 出水区: "effluent_CO2eq", 除臭系统: "deodorization_CO2eq" }; return Object.entries(keys).map(([name, key]) => ({ name, value: sum(key) })); });
const maxZone = computed(() => Math.max(1, ...zoneTotals.value.map((item) => item.value)));
const ranking = computed(() => [...zoneTotals.value].sort((a, b) => b.value - a.value));
const accountRows = computed(() => {
  const energy = sum("energy_CO2eq");
  const chemicals = sum("chemicals_CO2eq");
  return zoneTotals.value.map((item, index) => {
    const inflow = [energy * .3193, energy * .4453, energy * .1155 + chemicals, energy * .0507, energy * .0672, energy * .0267][index] || 0;
    return { ...item, inflow, net: item.value - inflow };
  });
});
const predictionMax = computed(() => Math.max(1, ...prediction.value.map((row) => n(row.predicted_CO2eq || row.predicted_emission || row.value))));
const techMax = computed(() => Math.max(1, ...techResult.value.map((row) => n(row.减排量_kgCO2eq || row.reduction || row.carbon_reduction))));
async function ensureCalculated() { if (!data.hasData) await data.simulate(); if (!data.calculated.length) await data.calculate(); }
async function calculate() { busy.value = true; try { await ensureCalculated(); status.value = `核算完成，共 ${calculated.value.length} 条记录`; } catch (err: any) { status.value = err?.response?.data?.detail || "核算失败"; } finally { busy.value = false; } }
async function runOptimization() { busy.value = true; try { await ensureCalculated(); const [a, b] = await Promise.all([api.post("/optimization/run", { records: records.value, target_reduction: 0.1 }), api.post("/optimization/scenario", { records: records.value, scenario: { aeration_adjust: -15, pac_adjust: -10, sludge_ratio: 0.6 } })]); optimization.value = a.data; scenario.value = b.data; status.value = "优化分析完成"; } catch (err: any) { status.value = err?.response?.data?.detail || "优化分析失败"; } finally { busy.value = false; } }
async function runPrediction() { busy.value = true; try { await ensureCalculated(); const response = await api.post("/prediction/predict", { records: records.value, months: predictionMonths.value }); prediction.value = response.data.records || []; predictionMode.value = response.data.mode || "fallback"; modelStatus.value = `预测完成，${prediction.value.length} 个时间点`; } catch (err: any) { modelStatus.value = err?.response?.data?.detail || "预测失败"; } finally { busy.value = false; } }
async function loadModel() { const response = await api.post("/prediction/load"); modelStatus.value = response.data.message; }
async function trainModel() { busy.value = true; try { await ensureCalculated(); const response = await api.post("/prediction/train", { records: records.value }); modelStatus.value = response.data.message || (response.data.trained ? "模型训练完成" : "已切换备用模式"); } catch (err: any) { modelStatus.value = err?.response?.data?.detail || "模型训练失败"; } finally { busy.value = false; } }
async function compareTech() { busy.value = true; try { const response = await api.post("/technology/compare", { tech_list: selectedTechs.value, records: records.value, water_flow: 10000 }); techResult.value = response.data.records || []; status.value = "技术对比分析完成"; } catch (err: any) { status.value = err?.response?.data?.detail || "技术对比失败"; } finally { busy.value = false; } }
async function loadFactors() { const response = await api.get("/factors"); factors.value = response.data.records || []; if (!factors.value.length) factors.value = [{ factor_type: "电力", factor_value: 0.5366, unit: "kgCO2/kWh", region: "中国", data_source: "默认示范值" }]; const history = await api.get("/factors/history", { params: { factor_type: "电力", region: "中国" } }); factorHistory.value = history.data.records || []; }
async function updateFactor() { await api.post("/factors", { factor_type: factorType.value, factor_value: factorValue.value, unit: factorType.value === "电力" ? "kgCO2/kWh" : "kgCO2/kg", region: "中国", effective_date: `${factorYear.value}-01-01`, expiry_date: `${factorYear.value}-12-31`, data_source: "用户输入", description: `${factorYear.value}年${factorType.value}排放因子`, change_reason: "手动更新" }); status.value = `已更新 ${factorType.value}`; await loadFactors(); }
function exportFactors() { window.open(`${api.defaults.baseURL}/factors/export?format=${exportFormat.value}`, "_blank"); }
async function sendChat() { const text = chatQuestion.value.trim(); if (!text) return; chatMessages.value.push({ role: "user", content: text }); chatQuestion.value = ""; const response = await api.post("/chat", { message: text }); chatMessages.value.push({ role: "assistant", content: response.data.response || "暂无回答" }); }
function formulaCalculate() { try { const fn = Function(...Object.keys(formulaValue.value), `return (${customFormula.value.expression})`); formulaResult.value = n(fn(...Object.values(formulaValue.value))); status.value = `公式 ${customFormula.value.name} 计算完成`; } catch (err: any) { formulaResult.value = null; status.value = `公式计算错误：${err.message}`; } }
async function loadGame() { const response = await api.get("/game/state"); level.value = response.data.level || {}; gameOrder.value = []; gameResult.value = ""; }
function addGameItem(item: Record<string, any>) { if (!gameOrder.value.some((entry) => entry.name === item.name)) gameOrder.value.push(item); }
function dropGameItem() { if (draggingGame.value === null) return; const item = level.value.correct?.[draggingGame.value]; if (item) addGameItem(item); draggingGame.value = null; }
async function submitGame() { const response = await api.post("/game/submit", { level: level.value.id ? level.value.id - 1 : 0, order: gameOrder.value.map((item) => item.name) }); gameResult.value = response.data.correct ? "🎉 恭喜！完全正确！本关已通过！" : "❌ 顺序还不正确，请根据提示继续调整"; }
async function nextGame() { await api.post("/game/next"); await loadGame(); }
async function resetGame() { await api.post("/game/reset"); await loadGame(); }
watch(path, async (next) => { if (next === "factors") await loadFactors(); if (next === "game") await loadGame(); if (next === "assistant") { const response = await api.get("/chat/history"); chatMessages.value = response.data.messages || []; } }, { immediate: true });
onMounted(() => { if (path.value === "factors") loadFactors(); });
</script>
<template>
  <section class="page parity-page">
    <header class="parity-heading"><div><span class="section-kicker">系统工作台 / {{ title }}</span><h2>{{ title }}</h2></div><span v-if="data.hasData" class="data-badge">{{ data.dataSource }}</span></header>
    <div v-if="path === 'footprint'" class="parity-grid two-col">
      <article class="panel chart-panel"><div class="panel-heading"><h3>工艺全流程甲烷排放热力图</h3><button @click="calculate" :disabled="busy">执行甲烷核算</button></div><p v-if="!data.hasData" class="empty-copy">请从“数据输入与设置”上传运行数据，或点击生成模拟数据。</p><div v-else class="heatmap"><div v-for="item in zoneTotals" :key="item.name" class="heat-cell" :style="{ '--heat': `${20 + 80 * item.value / maxZone}%` }"><strong>{{ item.name }}</strong><b>{{ item.value.toFixed(1) }}</b><small>kgCO2eq</small></div></div></article>
      <article class="panel chart-panel"><h3>甲烷动态追踪图谱</h3><div class="flow-chart"><div v-for="(item,index) in ranking" :key="item.name" class="flow-row"><span>{{ item.name }}</span><i :style="{ width: `${Math.max(5, item.value / maxZone * 100)}%` }"/><b>{{ item.value.toFixed(1) }}</b><em v-if="index < ranking.length - 1">↓</em></div></div></article>
      <article class="panel full-width"><h3>甲烷排放效率排行榜</h3><table class="data-table"><thead><tr><th>排名</th><th>工艺区域</th><th>排放量（kgCO2eq）</th><th>相对占比</th></tr></thead><tbody><tr v-for="(item,index) in ranking" :key="item.name"><td>{{ index + 1 }}</td><td>{{ item.name }}</td><td>{{ item.value.toFixed(2) }}</td><td>{{ (item.value / Math.max(1, sum('total_CO2eq')) * 100).toFixed(1) }}%</td></tr></tbody></table></article>
    </div>
    <div v-else-if="path === 'account'" class="parity-grid"><article class="panel full-width"><div class="panel-heading"><h3>甲烷账户收支明细（当月）</h3><button @click="calculate" :disabled="busy">执行原模块计算</button></div><p v-if="!data.hasData" class="empty-copy">请先加载运行数据。</p><table v-else class="data-table"><thead><tr><th>工艺单元</th><th>甲烷流入</th><th>甲烷流出</th><th>净排放</th></tr></thead><tbody><tr v-for="item in accountRows" :key="item.name"><td>{{ item.name }}</td><td>{{ item.inflow.toFixed(2) }}</td><td>{{ item.value.toFixed(2) }}</td><td :class="item.net >= 0 ? 'positive' : 'negative'">{{ item.net.toFixed(2) }}</td></tr></tbody></table></article><article class="panel"><h3>自定义公式计算器</h3><label>公式名称<input v-model="customFormula.name" /></label><label>公式表达式<input v-model="customFormula.expression" /></label><button @click="formulaCalculate">计算公式</button><p v-if="formulaResult !== null" class="result-copy">计算结果：{{ formulaResult.toFixed(4) }}</p></article><article class="panel"><h3>计算变量</h3><div class="field-grid"><label v-for="(_,key) in formulaValue" :key="key">{{ key }}<input v-model.number="formulaValue[key]" type="number" /></label></div></article></div>
    <div v-else-if="path === 'optimization'" class="parity-grid two-col"><article class="panel full-width"><div class="panel-heading"><h3>优化与决策支持</h3><button @click="runOptimization" :disabled="busy">运行优化分析</button></div><p v-if="!data.hasData" class="empty-copy">请先加载运行数据。</p><div v-else class="optimization-layout"><div class="bar-compare"><div><span>优化前</span><i/><b>{{ n(optimization?.baseline_emission || sum('total_CO2eq')).toFixed(1) }}</b></div><div><span>优化后</span><i class="after"/><b>{{ n(optimization?.optimized_emission || scenario?.scenario_emission || sum('total_CO2eq')).toFixed(1) }}</b></div></div><div class="recommendation"><h4>工艺调整建议</h4><p>优先检查曝气系统效率，优化曝气量与污泥回流比；深度处理区应避免过量加药。</p><p v-if="optimization">优化减排：{{ n(optimization.reduction).toFixed(2) }} kgCO2eq（{{ n(optimization.reduction_percent).toFixed(1) }}%）</p><p v-if="scenario">示范场景减排：{{ n(scenario.reduction).toFixed(2) }} kgCO2eq（{{ n(scenario.reduction_percent).toFixed(1) }}%）</p></div></div></article></div>
    <div v-else-if="path === 'prediction'" class="parity-grid"><article class="panel full-width"><h3>甲烷排放趋势预测</h3><div class="action-row"><button @click="loadModel">加载预训练模型</button><button @click="trainModel" :disabled="busy">训练新模型</button><label>预测时长<select v-model.number="predictionMonths"><option :value="1">1</option><option :value="3">3</option><option :value="6">6</option><option :value="12">12</option></select>个月</label><button @click="runPrediction" :disabled="busy">进行预测</button></div><p class="status-line">模型状态：{{ modelStatus }} <span v-if="predictionMode">（{{ predictionMode }}）</span></p><div v-if="prediction.length" class="line-chart"><div v-for="(row,index) in prediction.slice(0, 36)" :key="index" class="line-point" :style="{ left: `${index / Math.max(1, Math.min(35, prediction.length - 1)) * 96 + 2}%`, bottom: `${n(row.predicted_CO2eq || row.predicted_emission || row.value) / predictionMax * 82 + 8}%` }"/></div><table v-if="prediction.length" class="data-table"><thead><tr><th>日期</th><th>预测甲烷排放</th><th>下限</th><th>上限</th></tr></thead><tbody><tr v-for="row in prediction.slice(0, 12)" :key="String(row.date || row.ds)"><td>{{ row.date || row.ds || "未来时间点" }}</td><td>{{ n(row.predicted_CO2eq || row.predicted_emission || row.value).toFixed(2) }}</td><td>{{ n(row.lower_bound).toFixed(2) }}</td><td>{{ n(row.upper_bound).toFixed(2) }}</td></tr></tbody></table></article></div>
    <div v-else-if="path === 'technology'" class="parity-grid"><article class="panel full-width"><h3>甲烷减排技术对比分析</h3><div class="check-grid"><label v-for="tech in techOptions" :key="tech"><input v-model="selectedTechs" type="checkbox" :value="tech" />{{ tech }}</label></div><button @click="compareTech" :disabled="busy">运行技术对比分析</button><div v-if="techResult.length" class="tech-results"><div v-for="row in techResult" :key="String(row.技术名称 || row.name)" class="tech-card"><strong>{{ row.技术名称 || row.name }}</strong><i/><span>{{ n(row.减排量_kgCO2eq || row.reduction || row.carbon_reduction).toFixed(1) }} kgCO2eq</span></div></div><div class="offset-grid"><label>沼气发电量(kWh)<input v-model.number="formulaValue.energy" type="number" /></label><label>光伏发电量(kWh)<input v-model.number="formulaValue.water_flow" type="number" /></label><label>热泵节能量(kWh)<input v-model.number="formulaValue.chemicals" type="number" /></label><strong>总甲烷抵消量：{{ (formulaValue.energy * 2.5 + formulaValue.water_flow * .85 + formulaValue.chemicals * 1.2).toFixed(2) }} kgCO2eq</strong></div></article></div>
    <div v-else-if="path === 'factors'" class="parity-grid two-col"><article class="panel full-width"><div class="panel-heading"><h3>甲烷排放因子库管理</h3><button @click="loadFactors">刷新因子</button></div><table class="data-table"><thead><tr><th>因子类型</th><th>因子值</th><th>单位</th><th>地区</th><th>来源</th></tr></thead><tbody><tr v-for="factor in factors" :key="`${factor.factor_type}-${factor.effective_date}`"><td>{{ factor.factor_type }}</td><td>{{ factor.factor_value }}</td><td>{{ factor.unit }}</td><td>{{ factor.region || "中国" }}</td><td>{{ factor.data_source || "待核实" }}</td></tr></tbody></table></article><article class="panel"><h3>更新排放因子</h3><label>因子类型<select v-model="factorType"><option>电力</option><option>PAC</option><option>PAM</option><option>N2O</option><option>CH4</option><option>臭氧</option></select></label><label>因子值<input v-model.number="factorValue" type="number" step="0.0001" /></label><label>生效年份<input v-model.number="factorYear" type="number" /></label><button @click="updateFactor">更新因子</button></article><article class="panel"><h3>历史与导出</h3><div class="history-bars"><i v-for="item in factorHistory" :key="String(item.effective_date)" :style="{ height: `${Math.min(100, n(item.factor_value) * 100)}%` }"/></div><div class="action-row"><select v-model="exportFormat"><option value="csv">CSV</option><option value="excel">Excel</option></select><button @click="exportFactors">导出因子数据</button></div></article></div>
    <div v-else-if="path === 'assistant'" class="parity-grid two-col"><article class="panel assistant-page"><h3>🤖 数字人助手</h3><p class="assistant-welcome">你好，我是烷仔，你的污水处理智能助手。</p><div class="quick-questions"><button v-for="question in ['水厂有哪些工艺流程？','如何优化工艺降低排放？','有哪些减排技术？','甲烷排放是如何计算的？','LSTM预测如何使用？']" :key="question" @click="chatQuestion = question; sendChat()">{{ question }}</button></div><div class="chat-history"><p v-for="(message,index) in chatMessages" :key="index" :class="message.role">{{ message.content }}</p></div><form @submit.prevent="sendChat"><input v-model="chatQuestion" placeholder="输入你的问题..." /><button>发送</button></form></article><article class="panel"><h3>快捷状态</h3><p>Coze配置缺失时，页面会显示后端的明确配置提示，不会伪造回答。</p><button @click="chatMessages = []">清空历史</button></article></div>
    <div v-else class="game-page panel"><div class="panel-heading"><h3>🎮 AI实验室·污水处理闯关</h3><span>{{ level.name }}</span></div><div class="game-board"><section class="game-pool"><h4>组件库</h4><button v-for="(item,index) in level.correct" :key="item.name" draggable="true" @dragstart="draggingGame = index" @click="addGameItem(item)">{{ item.label }}</button></section><section class="game-flow" @dragover.prevent @drop="dropGameItem"><h4>流程区</h4><div v-for="(item,index) in gameOrder" :key="`${item.name}-${index}`" class="game-chip">{{ index + 1 }}. {{ item.label }}</div><p v-if="!gameOrder.length">将左侧组件拖入这里，或点击组件添加</p></section></div><div class="action-row"><button @click="submitGame">提交</button><button @click="gameOrder = []">重置</button><button @click="gameOrder.pop()">撤销上一步</button><button @click="nextGame">下一关</button><button @click="resetGame">重新开始</button></div><p class="game-result" :class="{ success: gameResult.includes('🎉') }">{{ gameResult }}</p></div>
    <p class="status">{{ status }}</p>
  </section>
</template>
