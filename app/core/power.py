import pandas as pd
import numpy as np
from app.core.utils import format_seconds
import math
import json

with open('app/config/user_config.json', 'r', encoding='utf-8') as f:
    user_config = json.load(f)



def avg_power(power_data: pd.Series) -> int:
    return round(power_data.mean())

def max_power(power_data: pd.Series) -> int:
    return int(power_data.max())

def normalized_power(power_data: pd.Series) -> int:
    rolling = power_data.rolling(window=30, min_periods=30).mean().dropna()
    return int((rolling.pow(4).mean()) ** 0.25)

def training_stress_score(power_data: pd.Series, total_time_hr: float) -> int:
    FTP = user_config["power"]["FTP"]
    NP = normalized_power(power_data)
    return int((total_time_hr * NP * NP) / (FTP * FTP) * 100)

def power_zones(power_data: pd.Series) -> dict:

    FTP = user_config["power"]["FTP"]
    zone_labels = [f"zone_{i}" for i in range(1, 8)]
    zone_times = {}
    total_time_sec = len(power_data)
    bounds = [
        0,
        math.floor(0.55 * FTP),
        math.floor(0.75 * FTP),
        math.floor(0.9 * FTP),
        math.floor(1.05 * FTP),
        math.floor(1.2 * FTP),
        math.floor(1.5 * FTP),
        float('inf')
    ]
    for i, label in enumerate(zone_labels):
        lower = bounds[i]
        upper = bounds[i + 1]
        if math.isinf(upper):
            mask = power_data > lower
        elif i == 0:
            mask = power_data <= upper
        else:
            mask = (power_data > lower) & (power_data <= upper)

        zone_sec = mask.sum()
        percent = (zone_sec / total_time_sec * 100) if total_time_sec else 0
        zone_times[label] = {
            "time": format_seconds(zone_sec),
            "percent": f"{percent:.1f}%"
        }

    # ===== 新增 SS 区间（84%~97% FTP）=====
    ss_lower = int(0.84 * FTP)
    ss_upper = int(0.97 * FTP)
    ss_mask = (power_data > ss_lower) & (power_data <= ss_upper)
    ss_sec = ss_mask.sum()
    ss_percent = (ss_sec / total_time_sec * 100) if total_time_sec else 0
    zone_times["SS"] = {
        "time": format_seconds(ss_sec),
        "percent": f"{ss_percent:.1f}%"
    }

    return zone_times

def get_power_zones(FTP: int) -> dict:
    zone_names = [f"Z{i}" for i in range(1, 8)]
    zones = {}
    
    # 7 区间的功率边界
    bounds = [
        0,
        math.floor(0.55 * FTP),
        math.floor(0.75 * FTP),
        math.floor(0.9 * FTP),
        math.floor(1.05 * FTP),
        math.floor(1.2 * FTP),
        math.floor(1.5 * FTP),
        float('inf')
    ]

    # 生成 Z1 ~ Z7
    for i, name in enumerate(zone_names):
        lower = bounds[i]
        upper = bounds[i + 1]
        if upper == float('inf'):
            zone_str = f"{lower + 1}w+"
        elif i == 0:
            zone_str = f"{lower}~{upper}w"
        else:
            zone_str = f"{lower + 1}~{upper}w"
        zones[name] = zone_str

    # 添加 Sweet Spot 区间（84% ~ 97% FTP）
    ss_lower = int(FTP * 0.84)
    ss_upper = int(FTP * 0.97)
    zones["SS"] = f"{ss_lower}~{ss_upper}w"

    return zones

def calculate_work_kj(power_data: pd.Series) -> int:
    total_work_joules = power_data.sum()  
    total_work_kj = total_work_joules / 1000
    return round(total_work_kj)

def calculate_work_kj_above_ftp(power_data: pd.Series) -> int:
    FTP = user_config["power"]["FTP"]
    total_work_joules = (power_data[power_data > FTP] - FTP).sum()
    total_work_kj = total_work_joules / 1000
    return round(total_work_kj)

def estimate_calories(power_data: pd.Series, efficiency: float = 0.2955) -> float:
    return round(normalized_power(power_data) * (1 / efficiency) / 4184 * len(power_data))

def get_max_power_duration_curve(power_data: pd.Series) -> list[int]:
    max_avg_power = [0] 

    for duration in range(1, len(power_data) - 2):
        rolling_mean = power_data.rolling(window=duration).mean()
        max_power = rolling_mean.max()
        max_avg_power.append(round(max_power))

    return max_avg_power

import pandas as pd
import numpy as np

def get_wbal_curve(power_data: pd.Series) -> list[float]:
    W_prime = user_config["power"]["WJ"]
    CP = user_config["power"]["FTP"]
    
    dt = 1.0
    tau = W_prime / (CP * 0.5)  # 根据 Skiba 建议公式调整

    wbal = []
    balance = W_prime  # 初始储备

    for p in power_data:
        if p <= CP:
            # 恢复：指数回复（参考 Skiba 模型）
            balance += (W_prime - balance) * (1 - np.exp(-dt / tau))
        else:
            # 消耗：线性损耗
            balance -= (p - CP) * dt

        balance = max(0.0, min(W_prime, balance))  # 限定范围
        wbal.append(balance)

    return wbal

def get_altitude_adjusted_power(
    power_data: pd.Series,
    altitude_data: pd.Series,
    model: str = "peronnet"
) -> dict:
    """
    计算基于海拔修正的平均功率和平均修正因子
    返回标准 Python 内置类型（float 和 dict）
    支持模型: 'peronnet', 'bassett_acclim', 'bassett_nonacclim', 'simmons'
    """
    if power_data.empty or altitude_data.empty:
        return {"alt": 0.0, "alt_acc": 0.0}

    # 截取等长部分
    min_len = min(len(power_data), len(altitude_data))
    power = power_data.iloc[:min_len].fillna(0).astype(float).tolist()
    altitude = altitude_data.iloc[:min_len].ffill().astype(float).tolist()

    # 转换为海拔高度（单位 km）
    x = [alt / 1000.0 for alt in altitude]

    # 计算海拔修正因子
    factor = []
    for xi in x:
        if model == "peronnet":
            f = -0.003 * xi**3 + 0.0081 * xi**2 - 0.0381 * xi + 1
        elif model == "bassett_acclim":
            f = -0.0112 * xi**2 - 0.0190 * xi + 1
        elif model == "bassett_nonacclim":
            f = 0.00178 * xi**3 - 0.0143 * xi**2 - 0.0407 * xi + 1
        elif model == "simmons":
            f = -0.0092 * xi**2 - 0.0323 * xi + 1
        else:
            raise ValueError("未知模型类型")
        factor.append(max(f, 0.01))  # 避免除以 0 或负值

    # 计算修正功率
    adjusted_power = [p / f for p, f in zip(power, factor)]

    # 平均值（标准 Python 类型）
    alt_avg = round(sum(adjusted_power) / len(adjusted_power), 2)
    acc_avg = round(
        sum([adj / p for adj, p in zip(adjusted_power, power) if p > 0]) / len([p for p in power if p > 0]),
        4
    ) if any(p > 0 for p in power) else 0.0

    return {"alt": alt_avg, "alt_acc": acc_avg}

def get_altitude_adjusted_power_acclimatized(power_data: pd.Series, altitude_data: pd.Series) -> float:
    """高原适应运动员的海拔修正功率"""
    return get_altitude_adjusted_power(power_data, altitude_data, model="bassett_acclim")["alt"]

def get_altitude_adjusted_power_nonacclimatized(power_data: pd.Series, altitude_data: pd.Series) -> float:
    """未适应高原运动员的海拔修正功率"""
    return get_altitude_adjusted_power(power_data, altitude_data, model="bassett_nonacclim")["alt"]

def left_right_balance(balance_data: pd.Series):

    balance_series = pd.to_numeric(balance_data, errors='coerce').dropna()

    if balance_series.empty:
        return None  # 没有有效数据

    right_percentages = balance_series.astype(int) & 0b01111111
    left_percentages = 100 - right_percentages

    avg_left = left_percentages.mean()

    return round(avg_left, 1)


from scipy.optimize import curve_fit

def morton_model(t, CP, W_prime):
    # Morton模型公式
    return CP + W_prime / t

def estimate_ftp_morton(power_series, min_duration=3, max_duration=1800):
    length = len(power_series)
    max_duration = min(max_duration, length)

    durations = list(range(min_duration, max_duration + 1))
    max_powers = []

    for d in durations:
        # 计算滑动窗口均值
        rolling_means = []
        window_sum = sum(power_series[:d])
        rolling_means.append(window_sum / d)
        for i in range(d, length):
            window_sum += power_series[i] - power_series[i - d]
            rolling_means.append(window_sum / d)
        max_avg = max(rolling_means) if rolling_means else 0
        max_powers.append(max_avg)

    # 去除NaN（如果有的话，严格处理）
    filtered = [(dur, power) for dur, power in zip(durations, max_powers) if power is not None and not math.isnan(power)]
    if len(filtered) < 3:
        return 0.0, 0, 0.0

    durations, max_powers = zip(*filtered)

    # Morton模型拟合初始值
    CP_init = sorted(max_powers)[len(max_powers)//3]
    W_prime_init = (max_powers[0] - max_powers[-1]) * durations[0]
    p0 = [CP_init, W_prime_init]

    try:
        popt, _ = curve_fit(morton_model, durations, max_powers,
                            bounds=([0, 0], [2000, 20000]),
                            p0=p0,
                            maxfev=10000)
        CP, W_prime = popt
    except Exception:
        return 0.0, 0, 0.0

    # 找最接近CP的时间窗
    diffs = [abs(p - CP) for p in max_powers]
    best_idx = diffs.index(min(diffs))
    best_duration = durations[best_idx]
    max_power_at_best_duration = max_powers[best_idx]

    return round(float(CP), 2), int(best_duration), round(float(max_power_at_best_duration), 2)

