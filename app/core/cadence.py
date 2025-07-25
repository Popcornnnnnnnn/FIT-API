import pandas as pd
import math

def avg_cadence(cadence_series: pd.Series) -> int:
    return round(cadence_series.mean())

def max_cadence(cadence_series: pd.Series) -> int:
    return int(cadence_series.max())

def total_pedal_strokes(cadence_series: pd.Series, duration_seconds: float) -> int:
    """
    根据平均踏频（rpm）和运动时长（秒）计算总踩踏次数。
    :param cadence_series: 踏频数据（pd.Series，单位rpm）
    :param duration_seconds: 运动总时长（秒）
    :return: 总踩踏次数（int）
    """
    if cadence_series.empty or duration_seconds <= 0:
        return 0
    avg_cad = cadence_series.mean()  # 平均踏频（rpm）
    total_strokes = avg_cad * duration_seconds / 60  # rpm * 秒 / 60 = 总圈数
    return int(round(total_strokes))


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

def calculate_spi(power_series: pd.Series, window_size: int = 10) -> list[float]:
    """
    计算踩踏平滑指数（SPI），基于功率波动的标准差。
    返回Python列表（内置数据类型），元素为浮点数。

    参数:
        power_series: 功率数据序列（单位：瓦特）
        window_size: 滑动窗口大小（默认10个数据点）

    返回:
        SPI值列表，长度 = len(power_series) - window_size + 1
        空列表如果输入数据不足或无效
    """
    # 输入校验
    if len(power_series) < window_size or window_size < 1:
        return []

    power_values = power_series.tolist()  # 转换为Python列表
    spi_list = []

    # 滑动窗口计算
    for i in range(len(power_values) - window_size + 1):
        window = power_values[i:i + window_size]
        
        # 计算窗口内均值和标准差
        mean = sum(window) / window_size
        variance = sum((x - mean) ** 2 for x in window) / window_size
        std_dev = math.sqrt(variance) if variance > 0 else 0.0
        
        # 计算SPI（避免除零）
        spi = mean / std_dev if std_dev > 0 else 0.0
        spi_list.append(round(spi, 2))  # 保留两位小数

    return spi_list