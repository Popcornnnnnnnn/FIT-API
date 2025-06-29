import pandas as pd
import math

def avg_cadence(cadence_series: pd.Series) -> int:
    return round(cadence_series.mean())

def max_cadence(cadence_series: pd.Series) -> int:
    return int(cadence_series.max())

def max_torque(cadence_series: pd.Series, power_series: pd.Series) -> int:
    if len(cadence_series) != len(power_series):
        return 0
    max_torque = 0
    for cadence, power in zip(cadence_series, power_series):
        if cadence is None or cadence == 0 or pd.isna(cadence):
            continue
        torque = (power * 60) / (2 * math.pi * cadence)
        if torque > max_torque:
            max_torque = torque
    return round(max_torque)  # 保留两位小数

def avg_torque(cadence_series: pd.Series, power_series: pd.Series) -> int:
    if len(cadence_series) != len(power_series):
        return 0
    total_torque = 0
    count = 0
    for cadence, power in zip(cadence_series, power_series):
        if cadence is None or cadence == 0 or pd.isna(cadence):
            continue
        torque = (power * 60) / (2 * math.pi * cadence)
        if not math.isnan(torque) and math.isfinite(torque):
            total_torque += torque
            count += 1
    return round(total_torque / count) if count > 0 else 0

def get_torque_curve(cadence_series: pd.Series, power_series: pd.Series) -> list[int]:
    if len(cadence_series) != len(power_series):
        return []

    torque_curve = []

    for cadence, power in zip(cadence_series, power_series):
        if cadence is None or cadence == 0 or pd.isna(cadence) or power is None or pd.isna(power):
            torque_curve.append(0.0)
        else:
            torque = (power * 60) / (2 * math.pi * cadence)
            torque_curve.append(round(torque, 1))  # 保留两位小数

    return torque_curve
