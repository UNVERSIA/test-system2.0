import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import App from './App.vue';
import './style.css';
const pages = [
    ['3D水厂仿真', '3d'], ['工艺流程仿真', 'process'], ['甲烷足迹追踪', 'footprint'], ['甲烷账户管理', 'account'],
    ['优化与决策', 'optimization'], ['甲烷排放预测', 'prediction'], ['减排技术分析', 'technology'], ['因子库管理', 'factors'],
    ['🤖数字人助手', 'assistant'], ['🎮AI实验室·污水处理闯关', 'game']
];
const router = createRouter({ history: createWebHistory(), routes: pages.map(([title, path]) => ({ path: `/${path}`, component: () => import('./views/ParityPage.vue'), meta: { title, path } })) });
router.addRoute({ path: '/', redirect: '/3d' });
createApp(App).use(createPinia()).use(router).mount('#app');
