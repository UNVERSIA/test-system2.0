from __future__ import annotations

import io
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
GITHUB = ROOT / "GitHub"
load_dotenv(ROOT / "backend" / ".env")
if str(GITHUB) not in sys.path:
    sys.path.insert(0, str(GITHUB))

from carbon_calculator import CarbonCalculator
from data_simulator import DataSimulator
from factor_database import CarbonFactorDatabase
from optimization_engine import OptimizationEngine
from .data_adapter import detect_and_convert_data

CarbonLSTMPredictor = None
TENSORFLOW_AVAILABLE = False


def load_lstm_module():
    """Load the optional TensorFlow module only when a prediction action requests it."""
    global CarbonLSTMPredictor, TENSORFLOW_AVAILABLE
    if CarbonLSTMPredictor is not None:
        return CarbonLSTMPredictor
    try:
        from lstm_predictor import CarbonLSTMPredictor as predictor, TENSORFLOW_AVAILABLE as available
        CarbonLSTMPredictor = predictor
        TENSORFLOW_AVAILABLE = bool(available)
    except Exception:
        CarbonLSTMPredictor = None
        TENSORFLOW_AVAILABLE = False
    return CarbonLSTMPredictor

try:
    from coze_api import CozeAPI
except Exception:
    CozeAPI = None

try:
    from water_treatment_game import GAME_LEVELS
except Exception:
    GAME_LEVELS = []

app = FastAPI(title="污水处理甲烷监测调控与智慧科普系统 API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

calculator = CarbonCalculator()
factor_db = CarbonFactorDatabase(str(ROOT / "data" / "carbon_factors.db"))


class RecordsRequest(BaseModel):
    records: list[dict[str, Any]] = Field(default_factory=list)


class MetricsRequest(RecordsRequest):
    tech_applied: list[str] = Field(default_factory=list)


class OptimizationRequest(RecordsRequest):
    target_reduction: float = 0.1


class ScenarioRequest(RecordsRequest):
    scenario: dict[str, float] = Field(default_factory=dict)


class PredictionRequest(RecordsRequest):
    months: int = Field(default=12, ge=1, le=60)


class TechnologyRequest(RecordsRequest):
    tech_list: list[str] = Field(default_factory=list)
    water_flow: float = 10000


class FactorUpdate(BaseModel):
    factor_type: str
    factor_value: float
    unit: str
    region: str = "中国"
    effective_date: str
    expiry_date: str | None = None
    data_source: str = "用户输入"
    description: str = ""
    change_reason: str = "手动更新"


class UnitUpdate(BaseModel):
    water_flow: float | None = Field(default=None, ge=0)
    energy: float | None = Field(default=None, ge=0)
    enabled: bool | None = None
    TN_in: float | None = Field(default=None, ge=0)
    TN_out: float | None = Field(default=None, ge=0)
    COD_in: float | None = Field(default=None, ge=0)
    COD_out: float | None = Field(default=None, ge=0)
    PAC: float | None = Field(default=None, ge=0)
    PAM: float | None = Field(default=None, ge=0)
    methane_concentration: float | None = Field(default=None, ge=0)
    level: float | None = Field(default=None, ge=0)
    temperature: float | None = None
    pH: float | None = None


UNITS: dict[str, dict[str, Any]] = {
    "粗格栅": {"water_flow": 10000.0, "energy": 1500.0, "emission": 450.0, "enabled": True},
    "提升泵房": {"water_flow": 10000.0, "energy": 3500.0, "emission": 1050.0, "enabled": True},
    "细格栅": {"water_flow": 10000.0, "energy": 800.0, "emission": 240.0, "enabled": True},
    "曝气沉砂池": {"water_flow": 10000.0, "energy": 1200.0, "emission": 360.0, "enabled": True},
    "膜格栅": {"water_flow": 10000.0, "energy": 1000.0, "emission": 300.0, "enabled": True},
    "厌氧池": {"water_flow": 10000.0, "energy": 3000.0, "TN_in": 40.0, "TN_out": 30.0, "COD_in": 200.0, "COD_out": 180.0, "emission": 1200.0, "enabled": True},
    "缺氧池": {"water_flow": 10000.0, "energy": 3500.0, "TN_in": 30.0, "TN_out": 20.0, "COD_in": 180.0, "COD_out": 100.0, "emission": 1500.0, "enabled": True},
    "好氧池": {"water_flow": 10000.0, "energy": 5000.0, "TN_in": 20.0, "TN_out": 15.0, "COD_in": 100.0, "COD_out": 50.0, "emission": 1800.0, "enabled": True},
    "MBR膜池": {"water_flow": 10000.0, "energy": 4000.0, "emission": 1200.0, "enabled": True},
    "污泥处理车间": {"water_flow": 500.0, "energy": 2000.0, "PAM": 100.0, "emission": 800.0, "enabled": True},
    "DF系统": {"water_flow": 10000.0, "energy": 2500.0, "PAC": 300.0, "emission": 1000.0, "enabled": True},
    "催化氧化": {"water_flow": 10000.0, "energy": 1800.0, "emission": 700.0, "enabled": True},
    "鼓风机房": {"water_flow": 0.0, "energy": 2500.0, "emission": 900.0, "enabled": True},
    "消毒接触池": {"water_flow": 10000.0, "energy": 1000.0, "emission": 400.0, "enabled": True},
    "除臭系统": {"water_flow": 0.0, "energy": 1800.0, "emission": 600.0, "enabled": True},
}


def frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


def clean(value: Any) -> Any:
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


def records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return clean(df.to_dict(orient="records"))


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "tensorflow_available": bool(TENSORFLOW_AVAILABLE),
        "coze_configured": bool(os.getenv("COZE_AGENT_TOKEN") and os.getenv("COZE_PROJECT_ID")),
    }


@app.post("/api/data/upload")
async def upload_data(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(400, "仅支持 .xlsx 文件")
    data = await file.read()
    try:
        df, daily, info = detect_and_convert_data(io.BytesIO(data))
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"columns": list(df.columns), "rows": len(df), "is_daily_data": daily, "conversion_info": info, "records": records(df)}


@app.post("/api/data/simulate")
def simulate_data() -> dict[str, Any]:
    simulator = DataSimulator()
    out = simulator.generate_simulated_data(str(ROOT / "data" / "simulated_data.csv"))
    monthly_path = ROOT / "data" / "simulated_data_monthly.csv"
    monthly = pd.read_csv(monthly_path) if monthly_path.exists() else pd.DataFrame()
    return {"records": records(out), "monthly_records": records(monthly), "columns": list(out.columns)}


@app.get("/api/units")
def get_units() -> dict[str, Any]:
    return {"units": clean(UNITS)}


@app.put("/api/units/{name}")
def update_unit(name: str, payload: UnitUpdate):
    if name not in UNITS:
        raise HTTPException(404, "工艺单元不存在")
    UNITS[name].update({k: v for k, v in payload.model_dump().items() if v is not None})
    return {"name": name, "unit": clean(UNITS[name])}


def calc_chain(df: pd.DataFrame) -> pd.DataFrame:
    out = calculator.calculate_direct_emissions(df.copy())
    out = calculator.calculate_indirect_emissions(out)
    return calculator.calculate_unit_emissions(out)


@app.post("/api/carbon/direct")
def carbon_direct(payload: RecordsRequest):
    try:
        return {"records": records(calculator.calculate_direct_emissions(frame(payload.records)))}
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/carbon/indirect")
def carbon_indirect(payload: RecordsRequest):
    try:
        return {"records": records(calculator.calculate_indirect_emissions(frame(payload.records)))}
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/carbon/unit")
def carbon_unit(payload: RecordsRequest):
    try:
        return {"records": records(calc_chain(frame(payload.records)))}
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/carbon/metrics")
def carbon_metrics(payload: MetricsRequest):
    try:
        return clean(calculator.calculate_carbon_reduction_metrics(calc_chain(frame(payload.records)), payload.tech_applied))
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/optimization/run")
def optimization_run(payload: OptimizationRequest):
    try:
        return clean(calculator.optimize_parameters(frame(payload.records), payload.target_reduction))
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/optimization/scenario")
def optimization_scenario(payload: ScenarioRequest):
    try:
        engine = OptimizationEngine(frame(payload.records))
        return clean(engine.simulate_scenario(payload.scenario))
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/prediction/load")
def prediction_load():
    load_lstm_module()
    if CarbonLSTMPredictor is None:
        return {"loaded": False, "tensorflow_available": False, "message": "LSTM模块不可用，将使用备用模式"}
    predictor = CarbonLSTMPredictor()
    loaded = bool(predictor.load_model())
    return {"loaded": loaded, "tensorflow_available": bool(TENSORFLOW_AVAILABLE), "message": "模型加载成功" if loaded else "未找到模型，将使用备用模式"}


@app.post("/api/prediction/train")
def prediction_train(payload: RecordsRequest):
    load_lstm_module()
    if CarbonLSTMPredictor is None or not TENSORFLOW_AVAILABLE:
        return {"trained": False, "tensorflow_available": False, "message": "TensorFlow不可用，预测功能将使用备用模式"}
    try:
        predictor = CarbonLSTMPredictor()
        df = calc_chain(frame(payload.records))
        history = predictor.train(df, "total_CO2eq", epochs=30)
        return {"trained": True, "tensorflow_available": True, "history": clean(history if isinstance(history, dict) else {})}
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/prediction/predict")
def prediction_predict(payload: PredictionRequest):
    df = frame(payload.records)
    if df.empty:
        raise HTTPException(422, "请先上传运行数据")
    try:
        result = calculator._simple_emission_prediction(df, payload.months * 30)
        return {"mode": "tensorflow" if TENSORFLOW_AVAILABLE else "fallback", "records": records(result)}
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/api/technology/compare")
def technology_compare(payload: TechnologyRequest):
    try:
        out = calculator.compare_carbon_techs(payload.tech_list, frame(payload.records) if payload.records else None, payload.water_flow)
        return {"records": records(out)}
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/factors")
def factors(factor_type: str | None = None, region: str = "中国", date_value: str | None = None):
    if factor_type:
        return {"factor_type": factor_type, "region": region, "factor_value": factor_db.get_factor(factor_type, region, date_value)}
    target = ROOT / "work" / "factors.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    out = factor_db.export_factors(str(target), format="csv")
    return {"records": records(out), "fallback_mode": bool(getattr(factor_db, "is_fallback", False))}


@app.get("/api/factors/history")
def factor_history(factor_type: str = "电力", region: str = "中国"):
    return {"records": records(factor_db.get_factor_history(factor_type, region))}


@app.post("/api/factors")
def factor_update(payload: FactorUpdate):
    factor_db.update_factor(**payload.model_dump())
    return {"updated": True, "factor_value": factor_db.get_factor(payload.factor_type, payload.region, payload.effective_date)}


@app.get("/api/factors/export")
def factor_export(format: Literal["csv", "excel"] = "csv"):
    target = ROOT / "work" / ("carbon_factors.xlsx" if format == "excel" else "carbon_factors.csv")
    target.parent.mkdir(parents=True, exist_ok=True)
    df = factor_db.export_factors(str(target), format=format)
    media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "excel" else "text/csv"
    return StreamingResponse(iter([target.read_bytes()]), media_type=media, headers={"Content-Disposition": f'attachment; filename="{target.name}"'})


chat_history: list[dict[str, str]] = []


@app.get("/api/chat/history")
def get_chat_history():
    return {"messages": chat_history}


@app.delete("/api/chat/history")
def clear_chat_history():
    chat_history.clear()
    return {"cleared": True}


@app.post("/api/chat")
def chat(payload: dict[str, str]):
    message = payload.get("message", "")
    if not message.strip():
        return {"success": False, "response": "请输入问题。", "error": "empty_message"}
    if not (os.getenv("COZE_AGENT_TOKEN") and os.getenv("COZE_PROJECT_ID")):
        return {"success": False, "response": "智能体服务尚未配置，请在本地环境变量中配置", "error": "coze_configuration"}
    if CozeAPI is None:
        return {"success": False, "response": "数字人助手暂时不可用，请检查文件配置", "error": "coze_unavailable"}
    try:
        client = CozeAPI()
        result = client.chat(message, conversation_id=payload.get("conversation_id"))
    except Exception as exc:
        return {"success": False, "response": str(exc), "error": "coze_configuration"}
    chat_history.extend([{"role": "user", "content": message}, {"role": "assistant", "content": result.get("response", "")}])
    return result


game_state = {"current_level": 0, "completed_levels": [], "error_counts": {}}


@app.get("/api/game/state")
def game_state_get():
    level = GAME_LEVELS[game_state["current_level"]] if GAME_LEVELS else {}
    return {"current_level": game_state["current_level"], "completed_levels": game_state["completed_levels"], "error_counts": game_state["error_counts"], "level": clean(level)}


@app.post("/api/game/submit")
def game_submit(payload: dict[str, Any]):
    idx = int(payload.get("level", game_state["current_level"]))
    order = payload.get("order", [])
    if idx < 0 or idx >= len(GAME_LEVELS):
        raise HTTPException(400, "关卡不存在")
    correct = [x["name"] for x in GAME_LEVELS[idx]["correct"]]
    ok = order == correct
    if not ok:
        game_state["error_counts"][str(idx)] = game_state["error_counts"].get(str(idx), 0) + 1
    return {"correct": ok, "score": 100 if ok else 0, "correct_order": correct, "state": game_state_get()}


@app.post("/api/game/reset")
def game_reset():
    game_state.update({"current_level": 0, "completed_levels": [], "error_counts": {}})
    return game_state_get()


@app.post("/api/game/next")
def game_next():
    if game_state["current_level"] < len(GAME_LEVELS) - 1:
        game_state["current_level"] += 1
    return game_state_get()


@app.post("/api/game/undo")
def game_undo():
    return {"undone": True, "state": game_state_get()}
