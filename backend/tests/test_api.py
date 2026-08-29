import io
import sys
from pathlib import Path

import pandas as pd
import pytest
from openpyxl import Workbook
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parents[1]))
from app.main import app

client = TestClient(app)

SAMPLE = {
    "records": [{
        "日期": "2025-01-01", "处理水量(m³)": 10000, "电耗(kWh)": 3000,
        "PAC投加量(kg)": 200, "PAM投加量(kg)": 50, "次氯酸钠投加量(kg)": 100,
        "臭氧投加量(kg)": 80, "进水COD(mg/L)": 200, "出水COD(mg/L)": 50,
        "进水TN(mg/L)": 40, "出水TN(mg/L)": 15,
    }]
}


def test_health_and_units(monkeypatch):
    monkeypatch.delenv("COZE_AGENT_TOKEN", raising=False)
    monkeypatch.delenv("COZE_PROJECT_ID", raising=False)
    health = client.get("/api/health").json()
    assert health["status"] == "ok"
    assert health["coze_configured"] is False
    assert len(client.get("/api/units").json()["units"]) == 15


def test_chat_without_coze_configuration(monkeypatch):
    monkeypatch.delenv("COZE_AGENT_TOKEN", raising=False)
    monkeypatch.delenv("COZE_PROJECT_ID", raising=False)
    response = client.post("/api/chat", json={"message": "你好"})
    assert response.status_code == 200
    assert response.json() == {
        "success": False,
        "response": "智能体服务尚未配置，请在本地环境变量中配置",
        "error": "coze_configuration",
    }


def test_carbon_parity_sample():
    response = client.post("/api/carbon/unit", json=SAMPLE)
    assert response.status_code == 200
    assert response.json()["records"][0]["total_CO2eq"] == pytest.approx(3951.94956)


def test_metrics_and_invalid_input():
    payload = {**SAMPLE, "tech_applied": ["光伏发电"]}
    assert client.post("/api/carbon/metrics", json=payload).json()["总甲烷排放量_kgCO2eq"] == pytest.approx(3951.94956)
    bad = client.post("/api/carbon/direct", json={"records": [{}]})
    assert bad.status_code == 422


def test_excel_daily_conversion():
    stream = io.BytesIO()
    workbook = Workbook(); sheet = workbook.active
    sheet.append(["日期", "处理水量", "电耗", "进水COD", "出水COD", "进水TN", "出水TN", "PAC投加量", "次氯酸钠投加量", "PAM投加量"])
    sheet.append(["", "m³/d", "kWh/d", "mg/L", "mg/L", "mg/L", "mg/L", "kg/d", "kg/d", "kg/d"])
    sheet.append(["2025-01-01", 100, 30, 200, 50, 40, 15, 2, 1, 0.5])
    workbook.save(stream)
    stream.seek(0)
    response = client.post("/api/data/upload", files={"file": ("daily.xlsx", stream, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert response.status_code == 200
    data = response.json()
    assert data["is_daily_data"] is True
    assert data["records"][0]["处理水量(m³)"] == 3000


def test_technology_and_game():
    response = client.post("/api/technology/compare", json={"tech_list": ["光伏发电"], "records": []})
    assert response.status_code == 200
    state = client.get("/api/game/state").json()
    assert state["current_level"] == 0
    assert len(state["level"]["correct"]) == 5
