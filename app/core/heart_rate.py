import pandas as pd
from typing import Literal, List, Tuple
from app.core.utils import format_seconds
import math
import numpy as np
from sklearn.linear_model import LinearRegression

import json
with open('app/config/user_config.json', 'r', encoding='utf-8') as f:
    user_config = json.load(f)

def avg_heart_rate(hr_data: pd.Series) -> int:
    return int(round(hr_data.mean()))

def max_heart_rate(hr_data: pd.Series) -> int:
    return int(hr_data.max())

def get_heart_rate_zones(method: Literal["threshold", "max", "hrr"] = "threshold") -> dict:
    hr_config = user_config["heart_rate"]
    threshold = hr_config["threshold_bpm"]
    max_bpm = hr_config["max_bpm"]
    resting = hr_config["resting_bpm"]

    zones = {}
    
    if method == "threshold":
        # 基于阈值心率，5区间
        bounds = [
            math.floor(0.67 * threshold),
            math.floor(0.80 * threshold),
            math.floor(0.89 * threshold),
            math.floor(0.97 * threshold),
            math.floor(1.02 * threshold),
            max_bpm
        ]
        labels = ["Z1", "Z2", "Z3", "Z4", "Z5"]

    elif method == "max":
        # 基于最大心率，5区间
        bounds = [
            math.floor(0.50 * max_bpm),
            math.floor(0.60 * max_bpm),
            math.floor(0.70 * max_bpm),
            math.floor(0.80 * max_bpm),
            math.floor(0.90 * max_bpm),
            max_bpm
        ]
        labels = ["Z1", "Z2", "Z3", "Z4", "Z5"]

    elif method == "hrr":
        # 基于心率储备，5区间
        hrr = max_bpm - resting
        points = [0.59, 0.74, 0.84, 0.88, 0.95, 1.0]
        bounds = [math.floor(resting + hrr * p) for p in points]
        labels = ["Z1", "Z2", "Z3", "Z4", "Z5"]
    else:
        raise ValueError("method must be 'threshold', 'max', or 'hrr'")

    for i in range(len(labels)):
        lower = bounds[i]
        upper = bounds[i + 1]
        zones[labels[i]] = f"{lower}~{upper}bpm" if i == 0 else f"{lower + 1}~{upper}bpm"

    return zones

def heart_rate_zones(method: Literal["threshold", "max", "hrr"], hr_series: pd.Series) -> dict:
    hr_config = user_config["heart_rate"]
    threshold = hr_config["threshold_bpm"]
    max_bpm = hr_config["max_bpm"]
    resting = hr_config.get("resting_bpm", 60)

    zone_bounds = []
    zone_labels = ["Z1", "Z2", "Z3", "Z4", "Z5"]

    if method == "threshold":
        zone_bounds = [
            math.floor(0.67 * threshold),
            math.floor(0.80 * threshold),
            math.floor(0.89 * threshold),
            math.floor(0.97 * threshold),
            math.floor(1.02 * threshold),
            max_bpm
        ]
    elif method == "max":
        zone_bounds = [
            math.floor(0.50 * max_bpm),
            math.floor(0.60 * max_bpm),
            math.floor(0.70 * max_bpm),
            math.floor(0.80 * max_bpm),
            math.floor(0.90 * max_bpm),
            max_bpm
        ]
    elif method == "hrr":
        hrr = max_bpm - resting
        points = [0.59, 0.74, 0.84, 0.88, 0.95, 1.0]
        zone_bounds = [math.floor(resting + hrr * p) for p in points]
    else:
        raise ValueError("method must be one of: 'threshold', 'max', 'hrr'")

    total_sec = len(hr_series)
    result = {}

    for i, label in enumerate(zone_labels):
        lower = zone_bounds[i]
        upper = zone_bounds[i + 1]
        if i == 0:
            mask = (hr_series >= lower) & (hr_series <= upper)
        else:
            mask = (hr_series > lower) & (hr_series <= upper)

        zone_sec = mask.sum()
        percent = (zone_sec / total_sec * 100) if total_sec else 0

        result[label] = {
            "time": format_seconds(zone_sec),
            "percent": f"{percent:.1f}%"
        }

    return result

def heart_rate_recovery_capablility(hr_data: pd.Series) -> int:
    # 添加功能，如果最大连续数据点小于 60，则返回0
    threshold_bpm = user_config["heart_rate"]["threshold_bpm"]
    hrrc_values = []
    total_points = len(hr_data)

    for i in range(total_points - 60):
        hr_start = hr_data.iloc[i]
        if hr_start >= threshold_bpm:
            window = hr_data.iloc[i + 1 : i + 61]
            if not window.empty:
                min_hr = window.min()
                drop = hr_start - min_hr
                hrrc_values.append(drop)

    return round(max(hrrc_values)) if hrrc_values else 0

def heart_rate_lag(power_data: pd.Series, heart_rate_data: pd.Series, max_lag_sec: int = 120) -> float:

    assert len(power_data) == len(heart_rate_data), "功率和心率长度不一致"

    # ---------------- Step 1: 去除热身/冷却 ----------------
    warmup = user_config["heart_rate"]["warmup_time"]
    cooldown = user_config["heart_rate"]["cooldown_time"]
    total_len = len(power_data)
    if total_len <= (warmup + cooldown) * 60:
        return 0  # 数据长度不足，无法计算滞后
    
    start = warmup * 60
    end = total_len - cooldown * 60

    p_mid = power_data[start:end].reset_index(drop=True) # type: ignore
    hr_mid = heart_rate_data[start:end].reset_index(drop=True) # type: ignore

    # ---------------- Step 2: 平滑处理 ----------------
    power_smooth = p_mid.rolling(window=30, min_periods=1, center=True).mean()
    hr_smooth = hr_mid.rolling(window=30, min_periods=1, center=True).mean()

    # ---------------- Step 3: 枚举滞后并计算相关 ----------------
    best_lag = 0
    best_corr = -np.inf

    for lag in range(0, max_lag_sec + 1):
        shifted_hr = hr_smooth[lag:].reset_index(drop=True)
        aligned_power = power_smooth[:len(shifted_hr)].reset_index(drop=True)

        if len(aligned_power) < 300:  # 至少5分钟有效数据
            continue

        corr = np.corrcoef(aligned_power, shifted_hr)[0, 1]
        if np.isnan(corr):
            continue

        if corr > best_corr:
            best_corr = corr
            best_lag = lag

    return best_lag

# INSERT_YOUR_CODE
def get_power_hr_ratio(power_series: pd.Series, hr_series: pd.Series) -> list:
    """
    接受功率和心率的Series，返回功率/心率的数组，保留两位小数。
    边界条件：
        - 任一Series为None或长度为0，返回空list
        - 对应心率为0或NaN时，结果为0.00
        - 长度不一致时，按最短长度截断
    """
    if power_series is None or hr_series is None:
        return []
    if len(power_series) == 0 or len(hr_series) == 0:
        return []
    # 填充缺失值为0
    power = power_series.fillna(0).astype(float).tolist()
    hr = hr_series.fillna(0).astype(float).tolist()
    min_len = min(len(power), len(hr))
    ratio = []
    for i in range(min_len):
        if hr[i] == 0:
            ratio.append(0.00)
        else:
            ratio.append(round(power[i] / hr[i], 2))
    return ratio



def decoupling_ratio(df: pd.DataFrame) -> Tuple[float, List]:
    warmup = user_config["heart_rate"]["warmup_time"]
    cooldown = user_config["heart_rate"]["cooldown_time"]
    if len(df) <= (warmup + cooldown) * 60:
        return 0, []

    df = df.copy()
    df["hr_smooth"] = df["heart_rate"].rolling(window=30, min_periods=1, center=True).mean()
    
    minute_groups = df.groupby(df.index // 60)  # 每分钟分组
    ratio_list = []
    
    for _, group in minute_groups:
        if group["power"].mean() < 50 or group["hr_smooth"].mean() < 100:
            continue  # 排除无效值
        ratio = group["power"].mean() / group["hr_smooth"].mean()
        ratio_list.append(ratio)
        

    
    # -------- 解耦率计算部分（去除前后10分钟） --------
    start_idx = warmup  # 去掉前10min
    end_idx = len(ratio_list) - cooldown  # 去掉后10min
    valid_ratios = ratio_list[start_idx:end_idx]

    if len(valid_ratios) < 10:  # 如果有效比率列表长度小于10，不计算解耦率
        return 0, []

    # 用线性回归拟合比值趋势
    X = np.arange(len(ratio_list)).reshape(-1, 1)  # 分钟索引作为X
    y = np.array(ratio_list)
    model = LinearRegression().fit(X, y)
    slope = model.coef_[0]

    # 解耦率估计 = 总体变动百分比
    percent_change = (slope * len(ratio_list)) / y.mean() * 100

    converted_ratio_list = [float(x) for x in ratio_list]
    return -round(percent_change, 2), converted_ratio_list


def simple_decoupling_ratio(df: pd.DataFrame) -> float:
    """
    计算简单的心率解耦率（HR Decoupling Ratio）。
    要求 DataFrame 中包含 'heart_rate' 和 'power' 字段。

    Returns:
        解耦率百分比（正数表示后半段效率下降）
    """
    if 'heart_rate' not in df or 'power' not in df:
        raise ValueError("DataFrame must contain 'heart_rate' and 'power' columns.")

    # 去除心率或功率为 NaN 的数据
    df = df.dropna(subset=['heart_rate', 'power'])

    # 如果数据点不足，返回 NaN
    if len(df) < 10:
        return float('nan')

    # 分为前后两段
    half = len(df) // 2
    df_first = df.iloc[:half]
    df_second = df.iloc[half:]

    # 计算功率/心率的平均比值
    p1 = df_first['power'].mean()
    hr1 = df_first['heart_rate'].mean()
    p2 = df_second['power'].mean()
    hr2 = df_second['heart_rate'].mean()

    # print(p1, hr1, p2, hr2)

    # 防止除以 0
    if hr1 == 0 or hr2 == 0:
        return None

    # 功率/心率比值的相对变化（即解耦率百分比）
    ratio1 = p1 / hr1
    ratio2 = p2 / hr2

    # print(ratio1, ratio2)

    decoupling = ((ratio2 - ratio1) / ratio1) * 100

    return -float(round(decoupling, 1))