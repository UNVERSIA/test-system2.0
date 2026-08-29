from __future__ import annotations


QUALITY_KEYS = ("COD", "NH3N", "TN", "TP", "SS", "DO", "pH", "temperature")


def advance_volume(volume_m3: float, inflow_m3_d: float, outflow_m3_d: float, dt_min: float, capacity_m3: float) -> tuple[float, float]:
    unconstrained = volume_m3 + (inflow_m3_d - outflow_m3_d) * dt_min / 1440.0
    return min(max(unconstrained, 0.0), capacity_m3), unconstrained


def mix_quality(current: dict[str, float], incoming: dict[str, float], volume_m3: float, inflow_m3: float) -> dict[str, float]:
    if inflow_m3 <= 0:
        return dict(current)
    denominator = max(volume_m3 + inflow_m3, 1e-9)
    return {key: (volume_m3 * current.get(key, 0.0) + inflow_m3 * incoming.get(key, current.get(key, 0.0))) / denominator for key in QUALITY_KEYS}
