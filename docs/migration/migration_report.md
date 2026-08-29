# Vue 3 + FastAPI 迁移阶段报告

## 已完成

- 已从 `https://github.com/UNVERSIA/test-system2.0.git` 克隆到 `D:\Projects\test-system2.0`，创建独立分支 `migration/vue-fastapi-parity`；原 `GitHub/app.py` 和 Python 模块未删除或覆盖。
- 已运行旧 Streamlit：`http://localhost:8501` 返回 200；保存十页旧版 DOM/截图到 `docs/migration/baseline/old-01..old-10`。
- 已生成 `feature_inventory.md`、`api_mapping.md`、`formula_inventory.md`、`parity_checklist.md`。
- 已建立 FastAPI 适配层：健康检查、Excel 上传/日月转换、模拟数据、工艺单元、碳/甲烷计算、优化、预测（含备用模式）、技术对比、因子库查询/更新/导出、数字人、游戏状态/提交/重置/撤销/下一关接口。
- 已建立 Vue 3 + TypeScript + Vite + Pinia + Vue Router + Axios + Plotly/Three 依赖和十个路由页面；十个路由可进入，3D 页创建 WebGL 画布并保存新版截图 `new-01..new-10`。
- 后端测试 `python -m pytest -q backend/tests/test_api.py`：5 passed（有 requests 依赖警告）。前端 `npm run build`：通过。

## 尚未复现/已知差异

- 当前 Vue 页面是迁移骨架，尚未逐项复刻 Streamlit 的全部图表视觉、2D iframe 编辑器、GLB 设备交互、完整数字人流式对话和闯关拖拽界面；这些页面入口和后端接口已具备，但不能宣称功能等价完成。
- 旧版 TensorFlow 在本机 Python 3.10.14/Windows 环境加载 DLL 失败；原 `GitHub/test_trace.py` 收集阶段会因 `predictor.model is None` 报错。新版默认健康检查报告 `tensorflow_available=false`，预测接口保留原统计备用模式。
- Coze 未配置 `COZE_AGENT_TOKEN`/`COZE_PROJECT_ID` 时，接口返回配置错误；未填充任何密钥。
- 原始页面在无上传数据时足迹、账户、优化页显示“请先上传运行数据”，基线已如实保存。
- 数据库中部分排放因子、B0/MCF、能耗分配和预测假设没有明确出处，详见公式清单“待核实”。

## 启动说明（Windows）

```powershell
cd D:\Projects\test-system2.0
python -m pip install -r GitHub\requirements.txt
python -m pip install -r backend\requirements.txt

# 终端 1：原 Streamlit 基线
python -m streamlit run GitHub\app.py

# 终端 2：FastAPI
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 终端 3：Vue
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

新版地址：`http://127.0.0.1:5173`；API 文档：`http://127.0.0.1:8000/docs`。

## 下一阶段

按 `parity_checklist.md` 的顺序逐页把原 HTML/Three.js/Plotly 数据和交互迁入 Vue 组件，使用同一份 Excel 和示例输入进行数值 diff，补齐 Playwright E2E 后再逐页提交并将清单标为通过。

