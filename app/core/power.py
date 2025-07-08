import pandas as pd
import numpy as np
from app.core.utils import format_seconds
import math
import json
from typing import Optional, List, Tuple

with open('app/config/user_config.json', 'r', encoding='utf-8') as f:
    user_config = json.load(f)



def avg_power(power_data: pd.Series) -> int:
    return int(round(power_data.mean()))

def max_power(power_data: pd.Series) -> int:
    return int(power_data.max())

def normalized_power(power_data: pd.Series) -> int:
    rolling = power_data.rolling(window=30, min_periods=30).mean().dropna() # type:ignore
    return int((rolling.pow(4).mean()) ** 0.25)

def training_stress_score(power_data: pd.Series, total_time_hr: float) -> int:
    FTP = user_config["power"]["FTP"]
    NP = normalized_power(power_data)
    return int((total_time_hr * NP * NP) / (FTP * FTP) * 100)

def power_zones(power_data: pd.Series) -> dict:

    FTP = user_config["power"]["FTP"]
    # print(FTP)
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
        if pd.isna(max_power): # type: ignore
            max_power = 0
        else:
            max_power = round(max_power)
        max_avg_power.append(max_power) # type: ignore

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

def left_right_balance(balance_data: pd.Series) -> Tuple[int, int]:
    def parse_left_right(value: Optional[float]) -> Optional[Tuple[int, int]]:
        try:
            raw = int(value) #type:ignore
        except (ValueError, TypeError):
            return None
        
        side_flag = raw & 0x01
        percent = raw >> 1
        if side_flag == 1:
            right = percent
            left = 100 - percent
        else:
            left = percent
            right = 100 - percent
        return (left, right)

    parsed = balance_data.map(parse_left_right).dropna()
    if parsed.empty:
        return (50, 50)

    left_values = [lr[0] for lr in parsed]
    right_values = [lr[1] for lr in parsed]

    avg_left = int(round(np.mean(left_values)))
    avg_right = int(round(np.mean(right_values)))

    return (avg_left, avg_right)
    
def ESTIMATE_FTP(power_curve: pd.Series):
    W_prime = user_config["power"]["WJ"]
    CUR_FTP = user_config["power"]["FTP"]

    #---------------------------------------------------------------
    max_w = 0
    max_time = 0
    for idx, power in enumerate(power_curve):
        w = (power - CUR_FTP) * (idx + 1)
        if w > max_w:
            max_w = w
            max_time = idx + 1
    if max_w > W_prime:
        W_prime = max_w
        # 同时应该更新user_config["power"]["WJ"]中的内容
    # print(f"最大超阈值功 (W') = {max_w}，对应区间时长 = {max_time} 秒")

    #---------------------------------------------------------------

    k = -220
    max_cp = None
    max_cp_time = None
    max_cp_power = None

    for idx, power in enumerate(power_curve):
        time = idx + 1  # 持续时间，单位：秒
        if time < 300 :
            continue  # 只考虑300秒及以上的数据点
        cp = power - W_prime / (time - k)
        if (max_cp is None) or (cp > max_cp):
            max_cp = cp
            max_cp_time = time
            max_cp_power = power

    # 打印或返回结果，便于调试和后续使用
    print(f"估算CP最大值: {max_cp:.2f}, 对应time: {max_cp_time}秒, power: {max_cp_power}W")
    # return max_cp, max_cp_time, max_cp_power



    





