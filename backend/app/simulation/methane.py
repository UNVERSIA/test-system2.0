from __future__ import annotations


def risk_level(value_mg_l: float) -> str:
    if value_mg_l >= 4:
        return "critical"
    if value_mg_l >= 2:
        return "high"
    if value_mg_l >= 1:
        return "attention"
    return "normal"
