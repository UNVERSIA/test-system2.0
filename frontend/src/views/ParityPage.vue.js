import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { api } from '../api';
import * as THREE from 'three';
const { defineProps, defineSlots, defineEmits, defineExpose, defineModel, defineOptions, withDefaults, } = await import('vue');
const route = useRoute();
const path = computed(() => String(route.meta.path));
const title = computed(() => String(route.meta.title));
const status = ref('');
const records = ref([]);
const selectedUnit = ref('粗格栅');
const enabled = ref(true);
const message = ref('');
const question = ref('');
const levels = ref([]);
const units = ref({});
const factors = ref([]);
const techs = ref(['厌氧消化产沼', '光伏发电', '高效曝气']);
const chosenTechs = ref([...techs.value]);
const months = ref(12);
const canvas = ref(null);
let animationFrame = 0;
let renderer;
async function simulate() { const r = await api.post('/data/simulate'); records.value = r.data.records; status.value = `模拟数据生成完成，共 ${records.value.length} 条`; }
async function calc() { const r = await api.post('/carbon/unit', { records: records.value }); records.value = r.data.records; status.value = '已完成原计算模块核算'; }
async function loadUnits() { units.value = (await api.get('/units')).data.units; }
async function loadFactors() { factors.value = (await api.get('/factors')).data.records || []; }
async function send() { const r = await api.post('/chat', { message: question.value }); message.value = r.data.response || ''; question.value = ''; }
async function game() { levels.value = [(await api.get('/game/state')).data.level]; }
onMounted(() => { if (path.value === '3d' || path.value === 'process')
    loadUnits(); if (path.value === 'factors')
    loadFactors(); if (path.value === 'game')
    game(); if (path.value === '3d' && canvas.value) {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x101722);
    const camera = new THREE.PerspectiveCamera(45, canvas.value.clientWidth / canvas.value.clientHeight, .1, 100);
    camera.position.set(0, 3, 8);
    renderer = new THREE.WebGLRenderer({ canvas: canvas.value, antialias: true });
    renderer.setSize(canvas.value.clientWidth, canvas.value.clientHeight, false);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x334455, 2));
    const floor = new THREE.Mesh(new THREE.BoxGeometry(8, .2, 4), new THREE.MeshStandardMaterial({ color: 0x2d5d72 }));
    scene.add(floor);
    for (let i = 0; i < 6; i++) {
        const tank = new THREE.Mesh(new THREE.CylinderGeometry(.55, .55, .8, 32), new THREE.MeshStandardMaterial({ color: [0x3498db, 0x2ecc71, 0xe74c3c][i % 3] }));
        tank.position.set(-3 + i * 1.2, .5, 0);
        scene.add(tank);
    }
    ;
    const tick = () => { scene.rotation.y += .002; renderer?.render(scene, camera); animationFrame = requestAnimationFrame(tick); };
    tick();
} });
onUnmounted(() => { if (animationFrame)
    cancelAnimationFrame(animationFrame); renderer?.dispose(); }); /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_fnComponent = (await import('vue')).defineComponent({});
;
let __VLS_functionalComponentProps;
function __VLS_template() {
    const __VLS_ctx = {};
    const __VLS_localComponents = {
        ...{},
        ...{},
        ...__VLS_ctx,
    };
    let __VLS_components;
    const __VLS_localDirectives = {
        ...{},
        ...__VLS_ctx,
    };
    let __VLS_directives;
    let __VLS_styleScopedClasses;
    let __VLS_resolvedLocalAndGlobalComponents;
    __VLS_elementAsFunction(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({ ...{ class: ("page") }, });
    __VLS_elementAsFunction(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({});
    (__VLS_ctx.title === '🤖数字人助手' ? '🤖 污水处理智能助手' : __VLS_ctx.title === '🎮AI实验室·污水处理闯关' ? '🎮AI实验室·污水处理闯关' : __VLS_ctx.title);
    if (__VLS_ctx.path === '3d') {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("panel") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.canvas, __VLS_intrinsicElements.canvas)({ ref: ("canvas"), ...{ class: ("scene") }, "aria-label": ("3D水厂场景"), });
        // @ts-ignore navigation for `const canvas = ref()`
        __VLS_ctx.canvas;
        __VLS_elementAsFunction(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({ value: ((__VLS_ctx.selectedUnit)), });
        for (const [_, name] of __VLS_getVForSourceType((__VLS_ctx.units))) {
            __VLS_elementAsFunction(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({ key: ((name)), });
            (name);
        }
        __VLS_elementAsFunction(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.input)({ type: ("checkbox"), });
        (__VLS_ctx.enabled);
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (...[$event]) => {
                    if (!((__VLS_ctx.path === '3d')))
                        return;
                    __VLS_ctx.status = '参数已保存';
                } }, });
    }
    else if (__VLS_ctx.path === 'process') {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("panel") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("flow") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({ value: ((__VLS_ctx.selectedUnit)), });
        for (const [_, name] of __VLS_getVForSourceType((__VLS_ctx.units))) {
            __VLS_elementAsFunction(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({ key: ((name)), });
            (name);
        }
        __VLS_elementAsFunction(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.input)({ type: ("checkbox"), });
        (__VLS_ctx.enabled);
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (...[$event]) => {
                    if (!(!((__VLS_ctx.path === '3d'))))
                        return;
                    if (!((__VLS_ctx.path === 'process')))
                        return;
                    __VLS_ctx.status = '参数已保存';
                } }, });
    }
    else if (__VLS_ctx.path === 'footprint' || __VLS_ctx.path === 'account' || __VLS_ctx.path === 'optimization') {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("panel") }, });
        if (!__VLS_ctx.records.length) {
            __VLS_elementAsFunction(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
        }
        else {
            __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (__VLS_ctx.calc) }, });
            __VLS_elementAsFunction(__VLS_intrinsicElements.pre, __VLS_intrinsicElements.pre)({});
            (JSON.stringify(__VLS_ctx.records.slice(0, 2), null, 2));
        }
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (__VLS_ctx.simulate) }, });
    }
    else if (__VLS_ctx.path === 'prediction') {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("panel") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (...[$event]) => {
                    if (!(!((__VLS_ctx.path === '3d'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'process'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'footprint' || __VLS_ctx.path === 'account' || __VLS_ctx.path === 'optimization'))))
                        return;
                    if (!((__VLS_ctx.path === 'prediction')))
                        return;
                    __VLS_ctx.status = '模型加载请求已发送';
                } }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (...[$event]) => {
                    if (!(!((__VLS_ctx.path === '3d'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'process'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'footprint' || __VLS_ctx.path === 'account' || __VLS_ctx.path === 'optimization'))))
                        return;
                    if (!((__VLS_ctx.path === 'prediction')))
                        return;
                    __VLS_ctx.status = '训练请求已发送';
                } }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.select, __VLS_intrinsicElements.select)({ value: ((__VLS_ctx.months)), });
        __VLS_elementAsFunction(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({ value: ((1)), });
        __VLS_elementAsFunction(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({ value: ((3)), });
        __VLS_elementAsFunction(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({ value: ((6)), });
        __VLS_elementAsFunction(__VLS_intrinsicElements.option, __VLS_intrinsicElements.option)({ value: ((12)), });
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (...[$event]) => {
                    if (!(!((__VLS_ctx.path === '3d'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'process'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'footprint' || __VLS_ctx.path === 'account' || __VLS_ctx.path === 'optimization'))))
                        return;
                    if (!((__VLS_ctx.path === 'prediction')))
                        return;
                    __VLS_ctx.status = __VLS_ctx.records.length ? '预测请求已发送' : '请先上传运行数据';
                } }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
        (__VLS_ctx.status || '⚠️ 请先加载或训练模型');
    }
    else if (__VLS_ctx.path === 'technology') {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("panel") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        for (const [tech] of __VLS_getVForSourceType((['厌氧消化产沼', '光伏发电', '高效曝气', '热泵技术', '污泥干化', '沼气发电']))) {
            __VLS_elementAsFunction(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({ key: ((tech)), });
            __VLS_elementAsFunction(__VLS_intrinsicElements.input)({ type: ("checkbox"), value: ((tech)), });
            (__VLS_ctx.chosenTechs);
            (tech);
        }
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (...[$event]) => {
                    if (!(!((__VLS_ctx.path === '3d'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'process'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'footprint' || __VLS_ctx.path === 'account' || __VLS_ctx.path === 'optimization'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'prediction'))))
                        return;
                    if (!((__VLS_ctx.path === 'technology')))
                        return;
                    __VLS_ctx.status = '技术对比请求已发送';
                } }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.input)({ type: ("number"), value: ("1000"), "aria-label": ("沼气发电量(kWh)"), });
        __VLS_elementAsFunction(__VLS_intrinsicElements.input)({ type: ("number"), value: ("500"), "aria-label": ("光伏发电量(kWh)"), });
        __VLS_elementAsFunction(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    }
    else if (__VLS_ctx.path === 'factors') {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("panel") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.table, __VLS_intrinsicElements.table)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.th, __VLS_intrinsicElements.th)({});
        for (const [factor] of __VLS_getVForSourceType((__VLS_ctx.factors))) {
            __VLS_elementAsFunction(__VLS_intrinsicElements.tr, __VLS_intrinsicElements.tr)({ key: ((String(factor.factor_type))), });
            __VLS_elementAsFunction(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            (factor.factor_type);
            __VLS_elementAsFunction(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            (factor.factor_value);
            __VLS_elementAsFunction(__VLS_intrinsicElements.td, __VLS_intrinsicElements.td)({});
            (factor.unit);
        }
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (...[$event]) => {
                    if (!(!((__VLS_ctx.path === '3d'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'process'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'footprint' || __VLS_ctx.path === 'account' || __VLS_ctx.path === 'optimization'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'prediction'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'technology'))))
                        return;
                    if (!((__VLS_ctx.path === 'factors')))
                        return;
                    __VLS_ctx.status = '因子导出请求已发送';
                } }, });
    }
    else if (__VLS_ctx.path === 'assistant') {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("panel") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        for (const [q] of __VLS_getVForSourceType((['水厂有哪些工艺流程？', '如何优化工艺降低排放？', '有哪些减排技术？', '甲烷排放是如何计算的？', 'LSTM预测如何使用？']))) {
            __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (...[$event]) => {
                        if (!(!((__VLS_ctx.path === '3d'))))
                            return;
                        if (!(!((__VLS_ctx.path === 'process'))))
                            return;
                        if (!(!((__VLS_ctx.path === 'footprint' || __VLS_ctx.path === 'account' || __VLS_ctx.path === 'optimization'))))
                            return;
                        if (!(!((__VLS_ctx.path === 'prediction'))))
                            return;
                        if (!(!((__VLS_ctx.path === 'technology'))))
                            return;
                        if (!(!((__VLS_ctx.path === 'factors'))))
                            return;
                        if (!((__VLS_ctx.path === 'assistant')))
                            return;
                        __VLS_ctx.question = q;
                    } }, key: ((q)), });
            (q);
        }
        __VLS_elementAsFunction(__VLS_intrinsicElements.input)({ ...{ onKeyup: (__VLS_ctx.send) }, placeholder: ("输入你的问题..."), });
        (__VLS_ctx.question);
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (__VLS_ctx.send) }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
        (__VLS_ctx.message);
    }
    else {
        __VLS_elementAsFunction(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({ ...{ class: ("panel") }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (...[$event]) => {
                    if (!(!((__VLS_ctx.path === '3d'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'process'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'footprint' || __VLS_ctx.path === 'account' || __VLS_ctx.path === 'optimization'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'prediction'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'technology'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'factors'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'assistant'))))
                        return;
                    __VLS_ctx.status = '已提交';
                } }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (__VLS_ctx.game) }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({ ...{ onClick: (...[$event]) => {
                    if (!(!((__VLS_ctx.path === '3d'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'process'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'footprint' || __VLS_ctx.path === 'account' || __VLS_ctx.path === 'optimization'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'prediction'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'technology'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'factors'))))
                        return;
                    if (!(!((__VLS_ctx.path === 'assistant'))))
                        return;
                    __VLS_ctx.status = '下一关';
                } }, });
        __VLS_elementAsFunction(__VLS_intrinsicElements.pre, __VLS_intrinsicElements.pre)({});
        (JSON.stringify(__VLS_ctx.levels, null, 2));
    }
    __VLS_elementAsFunction(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({ ...{ class: ("status") }, });
    (__VLS_ctx.status);
    __VLS_styleScopedClasses['page'];
    __VLS_styleScopedClasses['panel'];
    __VLS_styleScopedClasses['scene'];
    __VLS_styleScopedClasses['panel'];
    __VLS_styleScopedClasses['flow'];
    __VLS_styleScopedClasses['panel'];
    __VLS_styleScopedClasses['panel'];
    __VLS_styleScopedClasses['panel'];
    __VLS_styleScopedClasses['panel'];
    __VLS_styleScopedClasses['panel'];
    __VLS_styleScopedClasses['panel'];
    __VLS_styleScopedClasses['status'];
    var __VLS_slots;
    var __VLS_inheritedAttrs;
    const __VLS_refs = {
        "canvas": __VLS_nativeElements['canvas'],
    };
    var $refs;
    var $el;
    return {
        attrs: {},
        slots: __VLS_slots,
        refs: $refs,
        rootEl: $el,
    };
}
;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            path: path,
            title: title,
            status: status,
            records: records,
            selectedUnit: selectedUnit,
            enabled: enabled,
            message: message,
            question: question,
            levels: levels,
            units: units,
            factors: factors,
            chosenTechs: chosenTechs,
            months: months,
            canvas: canvas,
            simulate: simulate,
            calc: calc,
            send: send,
            game: game,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
    __typeEl: {},
});
; /* PartiallyEnd: #4569/main.vue */
