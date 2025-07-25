# type: ignore
# pyright: reportGeneralTypeIssues=false

from traceback import StackSummary
import pandas as pd
from scipy.signal import savgol_filter
from typing import Dict, Any, Tuple
import numpy as np

from app.core.power import user_config

def calculate_vam(altitude_series: pd.Series, time_interval: float = 1.0) -> list[float]:
    """
    计算每个采样点的VAM（垂直爬升速度，单位：米/小时），保留1位小数。
    :param altitude_series: 海拔高度数据（pd.Series，单位：米）
    :param time_interval: 采样间隔（秒），默认为1秒
    :return: VAM数组（list[float]，单位：米/小时），长度与altitude_series一致
    """
    if altitude_series.empty or len(altitude_series) < 2:
        return [0.0] * len(altitude_series)

    # 使用Savitzky-Golay滤波平滑海拔数据，减少噪声影响
    window = min(11, len(altitude_series)) if len(altitude_series) >= 5 else (len(altitude_series) | 1)
    try:
        smooth_alt = savgol_filter(altitude_series.fillna(method="ffill").values, window_length=window, polyorder=2)
    except Exception:
        smooth_alt = altitude_series.fillna(method="ffill").values

    # 计算每个点的海拔变化速度（米/秒）
    delta_alt = np.gradient(smooth_alt, time_interval)
    # 转换为米/小时，并保留1位小数
    vam = [round(float(x) * 3600, 1) for x in delta_alt]

    return vam

# INSERT_YOUR_CODE

def calculate_slope_and_segments(
    altitude_series: pd.Series,
    distance_series: pd.Series,
    min_slope: float = 0.5,
    min_segment: float = 10.0
) -> Dict[str, Any]:
    """
    通过海拔和水平距离计算每个点的坡度（百分比），并统计上坡/下坡的总距离（单位：米）。
    自动排除小幅度噪声和微小波动。

    参数:
        altitude_series: 海拔数据（pd.Series，单位：米）
        distance_series: 水平距离数据（pd.Series，单位：米，需单调递增）
        min_slope: 判定上坡/下坡的最小坡度阈值（百分比，默认0.5%）
        min_segment: 判定为一个有效上坡/下坡段的最小距离（米，默认10米）

    """
    if altitude_series is None or distance_series is None:
        return {"slope_percent": [], "uphill_distance": 0.0, "downhill_distance": 0.0}
    if len(altitude_series) < 2 or len(distance_series) < 2:
        return {"slope_percent": [0.0]*len(altitude_series), "uphill_distance": 0.0, "downhill_distance": 0.0}

    # 数据对齐
    min_len = min(len(altitude_series), len(distance_series))
    alt = altitude_series.iloc[:min_len].fillna(method="ffill").astype(float).values
    dist = distance_series.iloc[:min_len].fillna(method="ffill").astype(float).values

    # 平滑处理，减少噪声
    window = min(11, len(alt)) if len(alt) >= 5 else (len(alt) | 1)
    try:
        from scipy.signal import savgol_filter
        smooth_alt = savgol_filter(alt, window_length=window, polyorder=2)
    except Exception:
        smooth_alt = alt

    # 计算每个点的坡度百分比
    slope_percent = []
    for i in range(1, len(smooth_alt)):
        delta_h = smooth_alt[i] - smooth_alt[i-1]
        delta_d = dist[i] - dist[i-1]
        if delta_d < 0.1:  # 距离太小，视为0坡度
            slope = 0.0
        else:
            slope = (delta_h / delta_d) * 100
        slope_percent.append(round(slope, 2))
    # 第一个点补0
    slope_percent = [0.0] + slope_percent

    # 统计上坡/下坡距离
    uphill_distance = 0.0
    downhill_distance = 0.0
    segment_start = 0
    segment_type = None  # "up" or "down" or None

    for i in range(1, len(slope_percent)):
        s = slope_percent[i]
        # 判断当前点属于上坡/下坡/平路
        if s >= min_slope:
            current_type = "up"
        elif s <= -min_slope:
            current_type = "down"
        else:
            current_type = "flat"

        # 段落切换
        if segment_type is None:
            if current_type in ("up", "down"):
                segment_type = current_type
                segment_start = i - 1
        elif current_type != segment_type:
            # 结束一个段落
            seg_dist = dist[i-1] - dist[segment_start]
            if seg_dist >= min_segment:
                if segment_type == "up":
                    uphill_distance += seg_dist
                elif segment_type == "down":
                    downhill_distance += seg_dist
            # 新段落
            if current_type in ("up", "down"):
                segment_type = current_type
                segment_start = i - 1
            else:
                segment_type = None
                segment_start = i

    # 处理最后一个段落
    if segment_type in ("up", "down"):
        seg_dist = dist[-1] - dist[segment_start]
        if seg_dist >= min_segment:
            if segment_type == "up":
                uphill_distance += seg_dist
            elif segment_type == "down":
                downhill_distance += seg_dist

    
    return {
        "slope_percent": round(max(slope_percent), 1),
        "uphill_distance": round(uphill_distance, 1),
        "downhill_distance": round(downhill_distance, 1)
    }




def total_distance(distance_series: pd.Series) -> float:
    if distance_series.empty:
        return 0.0
    return round(distance_series.max() / 1000, 2)

def max_speed(speed_series: pd.Series) -> float:
    if speed_series.empty:
        return 0.0
    return round(speed_series.max() * 3.6, 1)

def max_altitude(altitude_series: pd.Series) -> float:
    """
    计算最高海拔
    :param altitude_series: 海拔数据的pd.Series
    :return: 最高海拔（float, 单位与原始数据一致，通常为米）
    """
    if altitude_series.empty:
        return 0.0
    return round(altitude_series.max(), 1)

def min_altitude(altitude_series: pd.Series) -> float:
    """
    计算最低海拔
    :param altitude_series: 海拔数据的pd.Series
    :return: 最低海拔（float, 单位与原始数据一致，通常为米）
    """
    if altitude_series.empty:
        return 0.0
    return round(altitude_series.min(), 1)

def total_elevation_gain(altitude_series: pd.Series, min_gain = 0.9, min_duration = 3) -> float:
    smooth_alt = altitude_series.round(1).rolling(window=5, center=True, min_periods=1).mean()

    total_gain = 0.0
    start_index = None

    for i in range(1, len(smooth_alt)):
        current = smooth_alt.iloc[i]
        previous = smooth_alt.iloc[i - 1]

        # 上升趋势
        if current > previous:
            if start_index is None:
                start_index = i - 1
        else:
            if start_index is not None:
                # 结束了一个上升段
                end_index = i - 1
                segment = smooth_alt.iloc[start_index:end_index + 1]
                gain = segment.iloc[-1] - segment.iloc[0]
                duration = end_index - start_index + 1

                if gain >= min_gain and duration >= min_duration:
                    total_gain += gain

                start_index = None

    # 最后一个可能的段
    if start_index is not None and start_index < len(smooth_alt) - 1:
        segment = smooth_alt.iloc[start_index:]
        gain = segment.iloc[-1] - segment.iloc[0]
        duration = len(segment)
        if gain >= min_gain and duration >= min_duration:
            total_gain += gain

    return round(total_gain)

def coasting_time(speed_series: pd.Series, power_series: pd.Series | None = None) -> int:
    coasting_mask = speed_series < 1
    if power_series is not None:
        coasting_mask |= power_series < 10

    return coasting_mask.sum()

def max_temperature(temperature_series: pd.Series) -> int:
    return round(temperature_series.max())

def avg_temperature(temperature_series: pd.Series) -> int:
    return round(temperature_series.mean())

def min_temperature(temperature_series: pd.Series) -> int:
    return round(temperature_series.min())

def estimate_carbohydrate_consumption_v2(power_series: pd.Series) -> int:
    """
    估算骑行过程中碳水化合物的消耗量（单位：克），修正版本。
    1. 直接根据每秒采样的功率数据，无需duration_seconds参数。
    2. 体重用于调整基础代谢率和能量消耗，估算更贴合个人实际。
    3. 修正能量换算系数，避免低估（原来低了约5倍）。

    参数:
        power_series: 功率数据（pd.Series，单位：瓦特，1Hz采样）
        ftp: 功能阈值功率（Functional Threshold Power, 单位：瓦特）
        weight_kg: 体重（千克），默认70kg

    返回:
        碳水化合物消耗量（克，int）
    """
    ftp = user_config["power"]["FTP"]
    weight_kg = user_config["weight"]
    if power_series.empty or ftp <= 0 or weight_kg <= 0:
        return 0

    # 区间定义（以FTP百分比为界，参考intervals.icu）
    # 区间: (下限, 上限, 碳水比例)
    zones = [
        (0.0, 0.6, 0.4),   # <60% FTP，约40%能量来自碳水
        (0.6, 0.75, 0.6),  # 60-75% FTP，约60%
        (0.75, 0.9, 0.7),  # 75-90% FTP，约70%
        (0.9, 1.05, 0.8),  # 90-105% FTP，约80%
        (1.05, 1.2, 0.85), # 105-120% FTP，约85%
        (1.2, 99, 0.9),    # >120% FTP，约90%
    ]

    # 体重修正因子（假设70kg为标准，线性修正）
    weight_factor = weight_kg / 70.0

    total_carb_kj = 0.0
    power_values = power_series.fillna(0).astype(float).tolist()

    # 之前的算法只统计了碳水消耗的能量，没有考虑到人体能量利用效率
    # 实际上，骑行时的机械效率大约为20-25%，也就是说，消耗1千焦机械能，实际需要消耗4-5千焦的食物能量
    # 另外，1克碳水=4千卡=16.7千焦，这个没错
    # 所以应该先算出总机械能，再除以效率（比如0.22），再乘以碳水比例，最后除以16.7

    # 机械效率
    mechanical_efficiency = 0.22  # 22%，文献常用值

    for p in power_values:
        rel = p / ftp
        for lower, upper, carb_ratio in zones:
            if lower <= rel < upper:
                # 单点能量（千焦），体重修正
                kj = p * 1 / 1000 * weight_factor
                # 先除以效率，得到实际消耗的总能量，再乘以碳水比例
                total_carb_kj += (kj / mechanical_efficiency) * carb_ratio
                break

    # 1克碳水化合物约16.7千焦
    carb_grams = total_carb_kj / 16.7

    return int(round(carb_grams))

    # INSERT_YOUR_CODE

def classify_training(aerobic_effect: float, anaerobic_effect: float) -> str:
    """根据有氧/无氧效果分类训练类型"""
    if aerobic_effect < 1.5 and anaerobic_effect < 0.5:
        return "恢复骑行/轻松有氧"
    elif 3.0 <= aerobic_effect <= 4.0 and 1.0 <= anaerobic_effect <= 2.0:
        return "最大摄氧量 (VO₂max)"
    elif 3.5 <= aerobic_effect <= 4.5 and 2.0 <= anaerobic_effect <= 3.5:
        return "阈值训练 (Threshold)"
    elif 2.0 <= aerobic_effect <= 3.5 and anaerobic_effect >= 3.0:
        return "高强度间歇 (HIIT)"
    elif aerobic_effect >= 4.0 and anaerobic_effect <= 2.0:
        return "基础耐力 (LSD)"
    else:
        return "混合型训练"

def estimate_training_effect(data_series, data_type="power",):
    """
    评估有氧和无氧训练效果，给出训练效果指数和训练类型总结（参考佳明算法思想，简化实现）。
    
    参数:
        data_series: pd.Series，功率或心率数据
        data_type: "power" 或 "hr"，指定数据类型
        ftp: 功率阈值（仅data_type为power时需要）
        hr_max: 最大心率（仅data_type为hr时需要）
        hr_rest: 静息心率（仅data_type为hr时可选，默认50）

    返回:
        {
            "aerobic_effect": float,   # 有氧训练效果指数（0.0-5.0）
            "anaerobic_effect": float, # 无氧训练效果指数（0.0-5.0）
            "summary": str,            # 训练类型总结
        }
    """
    ftp = user_config["power"]["FTP"]
    hr_max = user_config["heart_rate"]["max_bpm"]
    hr_rest = user_config["heart_rate"]["resting_bpm"]

    if data_series is None or len(data_series) == 0:
        return {
            "aerobic_effect": 0.0,
            "anaerobic_effect": 0.0,
            "summary": "无数据"
        }

    # 数据预处理
    arr = np.array(data_series.fillna(0).astype(float))

    # 训练效果区间（佳明算法思想，简化版）
    # 0.0-0.9: 无训练效果
    # 1.0-1.9: 极低（恢复）
    # 2.0-2.9: 低（LSD/基础耐力）
    # 3.0-3.9: 中（有氧提升/耐力）
    # 4.0-4.9: 高（最大摄氧量/阈值）
    # 5.0: 极高（冲刺/极限）

    # 1. 功率型算法
    if data_type == "power":
        if ftp is None or ftp <= 0:
            ftp = 200  # 默认值
        rel_power = arr / ftp

        # 有氧训练效果：主要看60-90% FTP区间的时间
        aerobic_time = np.sum((rel_power >= 0.6) & (rel_power < 0.9))
        # 无氧训练效果：主要看>120% FTP区间的时间
        anaerobic_time = np.sum(rel_power >= 1.2)
        total_time = len(arr)

        # 简单归一化（假设1小时训练，60min=3600s）
        aerobic_effect = min(5.0, round((aerobic_time / total_time) * 6, 1))
        anaerobic_effect = min(5.0, round((anaerobic_time / total_time) * 10, 1))



    # 2. 心率型算法
    elif data_type == "hr":
        if hr_max is None or hr_max <= 0:
            hr_max = 190  # 默认最大心率
        if hr_rest is None or hr_rest <= 0:
            hr_rest = 50  # 默认静息心率

        # 计算心率储备百分比
        hr_reserve = (arr - hr_rest) / (hr_max - hr_rest)
        # 有氧区间：60-80%心率储备
        aerobic_time = np.sum((hr_reserve >= 0.6) & (hr_reserve < 0.8))
        # 无氧区间：>90%心率储备
        anaerobic_time = np.sum(hr_reserve >= 0.9)
        total_time = len(arr)

        aerobic_effect = min(5.0, round((aerobic_time / total_time) * 6, 1))
        anaerobic_effect = min(5.0, round((anaerobic_time / total_time) * 10, 1))

    summary = classify_training(aerobic_effect, anaerobic_effect)

    return {
        "aerobic_effect": aerobic_effect,
        "anaerobic_effect": anaerobic_effect,
        "summary": summary
    }



