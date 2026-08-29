from __future__ import annotations

from pathlib import Path
from typing import IO, Any

import pandas as pd


def detect_and_convert_data(file_path_or_buffer: str | Path | IO[bytes] | IO[str]):
    """Equivalent of ``GitHub/app.py::detect_and_convert_data`` without Streamlit UI."""
    conversion_info: list[str] = []
    df = None
    header_type = None
    try:
        df = pd.read_excel(file_path_or_buffer, header=[0, 1])
        header_type = "multi"
    except Exception:
        try:
            if hasattr(file_path_or_buffer, "seek"):
                file_path_or_buffer.seek(0)
            df_raw = pd.read_excel(file_path_or_buffer, header=0)
            first_row = df_raw.iloc[0]
            has_indicator = any(str(v) in ["进水", "出水", "进水.1", "出水.1"] for v in first_row.values if pd.notna(v))
            if has_indicator:
                df = df_raw.iloc[1:].reset_index(drop=True)
                header_type = "user_with_header"
            else:
                df = df_raw
                header_type = "single"
        except Exception as exc:
            raise ValueError(f"无法解析Excel文件: {exc}") from exc

    if header_type == "multi":
        columns = []
        for col in df.columns:
            if isinstance(col, tuple):
                main_col = str(col[0]).strip().replace("\n", " ")
                sub_col = str(col[1]).strip().replace("\n", " ") if not pd.isna(col[1]) else ""
                columns.append(f"{main_col}_{sub_col}" if sub_col else main_col)
            else:
                columns.append(str(col).strip().replace("\n", " "))
        df.columns = columns

    column_mapping: dict[Any, str] = {}
    is_daily_data = False
    for col in df.columns:
        col_str = str(col).strip()
        if "日期" in col_str or col_str == "Unnamed: 0":
            column_mapping[col] = "日期"
        elif "处理水量" in col_str or col_str == "Unnamed: 1":
            if "/d" in col_str or "m3/d" in col_str.lower() or "m³/d" in col_str.lower():
                is_daily_data = True
                conversion_info.append(f"检测到日处理水量数据: {col_str}")
            column_mapping[col] = "处理水量_raw"
        elif ("能耗" in col_str or "电耗" in col_str or col_str == "Unnamed: 2") and "kWh" in col_str:
            if "/d" in col_str:
                conversion_info.append(f"检测到日电耗数据: {col_str}")
            column_mapping[col] = "电耗"
        elif "COD" in col_str or col_str == "Unnamed: 4":
            if "进水" in col_str or col_str == "Unnamed: 4":
                column_mapping[col] = "进水COD"
            elif "出水" in col_str or col_str == "Unnamed: 5":
                column_mapping[col] = "出水COD"
        elif "TN" in col_str or col_str == "Unnamed: 10":
            if "进水" in col_str or col_str == "Unnamed: 10":
                column_mapping[col] = "进水TN"
            elif "出水" in col_str or col_str == "Unnamed: 11":
                column_mapping[col] = "出水TN"
        elif ("PAC" in col_str or col_str == "Unnamed: 12") and ("消耗" in col_str or "投加" in col_str or "Unnamed" in col_str):
            if "/d" in col_str or "kg/d" in col_str:
                is_daily_data = True
                conversion_info.append(f"检测到日PAC数据: {col_str}")
            column_mapping[col] = "PAC_raw"
        elif ("次氯酸钠" in col_str or col_str == "Unnamed: 13") and ("消耗" in col_str or "投加" in col_str or "Unnamed" in col_str):
            if "/d" in col_str or "kg/d" in col_str:
                is_daily_data = True
            column_mapping[col] = "次氯酸钠_raw"
        elif (("PAM" in col_str or "污泥脱水" in col_str) or col_str == "Unnamed: 14") and ("消耗" in col_str or "投加" in col_str or "药剂" in col_str or "Unnamed" in col_str):
            if "/d" in col_str or "kg/d" in col_str:
                is_daily_data = True
            column_mapping[col] = "PAM_raw"

    df = df.rename(columns=column_mapping)
    if "日期" in df.columns:
        if str(df["日期"].dtype) in ("int64", "float64"):
            df["日期"] = pd.to_datetime(df["日期"], unit="D", origin="1899-12-30")
        else:
            df["日期"] = pd.to_datetime(df["日期"], errors="coerce")

    numeric_cols = ["处理水量_raw", "电耗", "进水COD", "出水COD", "进水TN", "出水TN", "PAC_raw", "次氯酸钠_raw", "PAM_raw"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if is_daily_data:
        conversion_info.append("\n📊 正在进行日数据到月数据的转换：")
        if "处理水量_raw" in df.columns:
            df["处理水量(m³)"] = df["处理水量_raw"] * 30
            conversion_info.append("处理水量: 日数据 × 30 = 月数据")
        if "电耗" in df.columns:
            df["电耗(kWh)"] = df["电耗"] * 30
            conversion_info.append("电耗: 日数据 × 30 = 月数据")
        if "PAC_raw" in df.columns:
            df["PAC投加量(kg)"] = df["PAC_raw"] * 30
            conversion_info.append("PAC: 日数据 × 30 = 月数据")
        if "次氯酸钠_raw" in df.columns:
            df["次氯酸钠投加量(kg)"] = df["次氯酸钠_raw"] * 30
            conversion_info.append("次氯酸钠: 日数据 × 30 = 月数据")
        if "PAM_raw" in df.columns:
            df["PAM投加量(kg)"] = df["PAM_raw"] * 30
            conversion_info.append("PAM: 日数据 × 30 = 月数据")
    else:
        for source, target in {
            "处理水量_raw": "处理水量(m³)", "电耗": "电耗(kWh)", "PAC_raw": "PAC投加量(kg)",
            "次氯酸钠_raw": "次氯酸钠投加量(kg)", "PAM_raw": "PAM投加量(kg)"
        }.items():
            if source in df.columns:
                df[target] = df[source]
        conversion_info.append("✓ 检测到标准月数据格式，无需单位转换")

    df = df.rename(columns={"进水COD": "进水COD(mg/L)", "出水COD": "出水COD(mg/L)", "进水TN": "进水TN(mg/L)", "出水TN": "出水TN(mg/L)"})
    df = df.dropna(subset=["日期", "处理水量(m³)"], how="any")
    for col in ["处理水量_raw", "电耗", "PAC_raw", "次氯酸钠_raw", "PAM_raw"]:
        if col in df.columns:
            df = df.drop(columns=[col])
    return df, is_daily_data, "\n".join(conversion_info)
