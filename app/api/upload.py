# app/api/upload.py
from pickle import FALSE
from fastapi import APIRouter, File, UploadFile, HTTPException
import matplotlib.pyplot as plt
import shutil
import os
import pandas as pd
from tempfile import NamedTemporaryFile
from typing import cast

from pandas.core import series

from app.core.fit_parser import *
from app.core.power import *
from app.core.heart_rate import *
from app.core.cadence import *
from app.core.more_data import *
from app.core.utils import format_seconds

fields = [
    "avg_cadence", "avg_cadence_position", "avg_combined_pedal_smoothness", "avg_fractional_cadence",
    "avg_heart_rate", "avg_left_pco", "avg_left_pedal_smoothness", "avg_left_power_phase",
    "avg_left_power_phase_peak", "avg_left_torque_effectiveness", "avg_power", "avg_power_position",
    "avg_right_pco", "avg_right_pedal_smoothness", "avg_right_power_phase", "avg_right_power_phase_peak",
    "avg_right_torque_effectiveness", "avg_speed", "avg_temperature", "avg_vam", "enhanced_avg_speed",
    "enhanced_max_speed", "event", "event_group", "event_type", "first_lap_index", "intensity_factor",
    "left_right_balance", "max_cadence", "max_cadence_position", "max_fractional_cadence", "max_heart_rate",
    "max_power", "max_power_position", "max_speed", "max_temperature", "message_index", "nec_lat", "nec_long",
    "normalized_power", "num_laps", "sport", "sport_index", "stand_count", "start_position_lat",
    "start_position_long", "start_time", "sub_sport", "swc_lat", "swc_long", "threshold_power", "time_standing",
    "timestamp", "total_anaerobic_training_effect", "total_ascent", "total_calories", "total_cycles",
    "total_descent", "total_distance", "total_elapsed_time", "total_fat_calories", "total_fractional_cycles",
    "total_timer_time", "total_training_effect", "total_work", "training_stress_score", "trigger",
]


router = APIRouter()

@router.post("/upload_fit")
async def upload_fit(file: UploadFile = File(...), debug: bool = True, raw_data: bool = False, curves: bool = True, Zone: bool = False):
    if not file.filename or not file.filename.endswith(".fit"): # 检查文件名是否为空或是否为.fit文件
        raise HTTPException(status_code=400, detail="Only .fit files are supported")

    # 保存上传文件到临时文件
    try:
        with NamedTemporaryFile(delete=False, suffix=".fit") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
    finally:
        file.file.close()
    try:
        data      = parse_fit_file(tmp_path)
        time_info = get_fit_date_time_info(tmp_path)
        session   = parse_fit_session(tmp_path)

    finally:
        os.remove(tmp_path)

    # print(device_info_summary)

    cleaned_data = clean_fit_data(data)
    FTP           = user_config["power"]["FTP"]



    results = {}

    for f in fields:
        import math

        def to_builtin_type(val):
            # 如果是numpy的标量，转为python内置类型
            if hasattr(val, 'item'):
                val = val.item()
            # nan转为None
            if isinstance(val, float) and math.isnan(val):
                return None
            return val

        # 将 session 字段转为标准类型，nan转为None
        if f in session.columns:
            value = session[f].iloc[0]
            results[f] = to_builtin_type(value)
        else:
            results[f] = None

    # 打印 session 中的字段名称（不打印具体数据）
    # print("Session包含的字段名称：", list(session.columns))

    # 计算基本指标
    def calc_basic_metrics():
        # ===== 基本骑行指标计算 =====

        import math

        # 1. 移动时间（秒）
        if "total_timer_time" in session.columns:
            moving_time = to_builtin_type(session["total_timer_time"].iloc[0])
            if moving_time is not None:
                try:
                    moving_time = int(moving_time)
                except Exception:
                    pass
        else:
            moving_time = int(len(cleaned_data))  # 兜底用数据长度

        # 2. 总距离（km）
        if "total_distance" in session.columns:
            val = session["total_distance"].iloc[0]
            total_dis = to_builtin_type(round(val / 1000.0, 2)) if val is not None and not (isinstance(val, float) and math.isnan(val)) else None
        else:
            total_dis = to_builtin_type(round(total_distance(cast(pd.Series, cleaned_data['distance'])), 2))

        # 3. 最大速度（km/h）
        if "max_speed" in session.columns:
            val = session["max_speed"].iloc[0]
            max_speed_val = to_builtin_type(round(val * 3.6, 1)) if val is not None and not (isinstance(val, float) and math.isnan(val)) else None
        elif "enhanced_max_speed" in session.columns:
            val = session["enhanced_max_speed"].iloc[0]
            max_speed_val = to_builtin_type(round(val * 3.6, 1)) if val is not None and not (isinstance(val, float) and math.isnan(val)) else None
        else:
            max_speed_val = to_builtin_type(round(max_speed(cast(pd.Series, cleaned_data['enhanced_speed'])), 1))

        # 4. 平均速度（km/h），保留1位小数
        if "avg_speed" in session.columns:
            val = session["avg_speed"].iloc[0]
            avg_speed_val = to_builtin_type(round(val * 3.6, 1)) if val is not None and not (isinstance(val, float) and math.isnan(val)) else None
        elif "enhanced_avg_speed" in session.columns:
            val = session["enhanced_avg_speed"].iloc[0]
            avg_speed_val = to_builtin_type(round(val * 3.6, 1)) if val is not None and not (isinstance(val, float) and math.isnan(val)) else None
        else:
            avg_speed_val = round(total_dis / (moving_time / 3600.0), 1) if moving_time and moving_time > 0 and total_dis is not None else None
            avg_speed_val = to_builtin_type(avg_speed_val)

        # 5. 总爬升（m）
        if "total_ascent" in session.columns:
            val = session["total_ascent"].iloc[0]
            elevation_gain = to_builtin_type(int(val)) if val is not None and not (isinstance(val, float) and math.isnan(val)) else None
        else:
            elevation_gain = to_builtin_type(total_elevation_gain(cast(pd.Series, cleaned_data['enhanced_altitude'])))

        # 6. 总下降（m）
        if "total_descent" in session.columns:
            val = session["total_descent"].iloc[0]
            total_descent = to_builtin_type(int(val)) if val is not None and not (isinstance(val, float) and math.isnan(val)) else None
        else:
            total_descent = to_builtin_type(int(results["total_descent"])) if results.get("total_descent") is not None else None

        # 7. 滑行时间（秒）
        if not cast(pd.Series, cleaned_data['enhanced_speed']).isnull().all():
            coast_time = coasting_time(
                cast(pd.Series, cleaned_data['enhanced_speed']),
                cast(pd.Series, cleaned_data['power'])
            )
        else:
            coast_time = coasting_time(cast(pd.Series, cleaned_data['enhanced_speed']))
        coast_time = to_builtin_type(coast_time)

        # 8. 滑行比例（%）
        coast_ratio = round((coast_time / moving_time) * 100, 1) if moving_time and moving_time > 0 and coast_time is not None else None
        coast_ratio = to_builtin_type(coast_ratio)

        # 赋值到统一变量名，方便后续使用
        Dis   = total_dis
        MaxS  = max_speed_val
        AvgS  = avg_speed_val
        Elev  = elevation_gain
        descent = total_descent

        return {
            "moving_time": to_builtin_type(moving_time),
            "total_dis": total_dis,
            "max_speed_val": max_speed_val,
            "avg_speed_val": avg_speed_val,
            "elevation_gain": elevation_gain,
            "total_descent": total_descent,
            "coast_time": coast_time,
            "coast_ratio": coast_ratio,
            "Dis": Dis,
            "MaxS": MaxS,
            "AvgS": AvgS,
            "Elev": Elev,
            "descent": descent
        }

    basic_metrics  = calc_basic_metrics()
    
    moving_time    = basic_metrics["moving_time"]
    total_dis      = basic_metrics["total_dis"]
    max_speed_val  = basic_metrics["max_speed_val"]
    avg_speed_val  = basic_metrics["avg_speed_val"]
    elevation_gain = basic_metrics["elevation_gain"]
    total_descent  = basic_metrics["total_descent"]
    coast_time     = basic_metrics["coast_time"]
    coast_ratio    = basic_metrics["coast_ratio"]
    Dis            = basic_metrics["Dis"]
    MaxS           = basic_metrics["MaxS"]
    AvgS           = basic_metrics["AvgS"]
    Elev           = basic_metrics["Elev"]
    descent        = basic_metrics["descent"]


    # 计算功率相关指标
    import math

    def to_builtin_type(val):
        # 如果是numpy的标量，转为python内置类型
        if hasattr(val, 'item'):
            val = val.item()
        # nan转为None
        if isinstance(val, float) and math.isnan(val):
            return None
        return val

    # 优先从session中取值，否则计算
    def get_metric_from_session_or_calc(field, calc_func=None):
        if field in session.columns:
            value = session[field].iloc[0]
            return to_builtin_type(value)
        elif calc_func is not None:
            return to_builtin_type(calc_func())
        else:
            return None

    AP          = get_metric_from_session_or_calc("avg_power", lambda: avg_power(cast(pd.Series, cleaned_data['power'])))
    MaxP        = get_metric_from_session_or_calc("max_power", lambda: max_power(cast(pd.Series, cleaned_data['power'])))
    NP          = get_metric_from_session_or_calc("normalized_power", lambda: normalized_power(cast(pd.Series, cleaned_data['power'])))
    TSS         = get_metric_from_session_or_calc("training_stress_score", lambda: training_stress_score(cast(pd.Series, cleaned_data['power']), len(cleaned_data) / 3600.0))
    W           = get_metric_from_session_or_calc("total_work", lambda: calculate_work_kj(cast(pd.Series, cleaned_data['power'])))
    W_ABOVE_FTP = get_metric_from_session_or_calc("work_above_ftp", lambda: calculate_work_kj_above_ftp(cast(pd.Series, cleaned_data['power'])))
    CAL         = get_metric_from_session_or_calc("total_calories", lambda: estimate_calories(cast(pd.Series, cleaned_data['power'])))

    # 兼容session中total_calories优先
    if "total_calories" in session.columns:
        CAL = to_builtin_type(session["total_calories"].iloc[0])

    # 海拔修正功率
    if (
        not cast(pd.Series, cleaned_data['power']).isnull().all() and
        'altitude' in cleaned_data.columns and
        cast(pd.Series, cleaned_data['altitude']).notnull().all()
    ):
        acclim_power     = to_builtin_type(get_altitude_adjusted_power_acclimatized(
            cast(pd.Series, cleaned_data['power']),
            cast(pd.Series, cleaned_data['altitude'])
        ))
        nonacclimpower  = to_builtin_type(get_altitude_adjusted_power_nonacclimatized(
            cast(pd.Series, cleaned_data['power']),
            cast(pd.Series, cleaned_data['altitude'])
        ))
    else:
        acclim_power, nonacclimpower = None, None
        

    # 计算心率相关指标
    if not cast(pd.Series, cleaned_data['heart_rate']).isnull().all():
        AvgHR = avg_heart_rate(cast(pd.Series, cleaned_data['heart_rate']))                             
        MaxHR = max_heart_rate(cast(pd.Series, cleaned_data['heart_rate']))                            
        HRRC  = heart_rate_recovery_capablility(cast(pd.Series, cleaned_data['heart_rate']))            
    else:
        AvgHR, MaxHR, HRRC = None, None, None
    
    # 心率解耦率相关指标
    if not cast(pd.Series, cleaned_data['heart_rate']).isnull().all() and not cast(pd.Series, cleaned_data['power']).isnull().all():
        decoupling, decoupling_curve = decoupling_ratio(cleaned_data)
        hr_lag            = heart_rate_lag(cast(pd.Series, cleaned_data['power']), cast(pd.Series, cleaned_data['heart_rate']))
        simple_decoupling = simple_decoupling_ratio(cleaned_data)
    else: 
        decoupling, decoupling_curve, hr_lag, simple_decoupling = None, None, None, None


    # 计算踏频相关指标
    if 'cadence' in cleaned_data.columns and not cast(pd.Series, cleaned_data['cadence']).isnull().all():
        avgCadence = avg_cadence(cast(pd.Series, cleaned_data['cadence']))
        maxCadence = max_cadence(cast(pd.Series, cleaned_data['cadence']))
    else:
        avgCadence, maxCadence = None, None
    if 'cadence' in cleaned_data.columns and 'power' in cleaned_data.columns and not cast(pd.Series, cleaned_data['cadence']).isnull().all() and not cast(pd.Series, cleaned_data['power']).isnull().all():
        maxTorque = max_torque(cast(pd.Series, cleaned_data['cadence']), cast(pd.Series, cleaned_data['power']))
        avgTorque = avg_torque(cast(pd.Series, cleaned_data['cadence']), cast(pd.Series, cleaned_data['power']))
    else:
        maxTorque, avgTorque = None, None




    if "left_right_balance" in cleaned_data.columns:
        LEFT, RIGHT = left_right_balance(cast(pd.Series, cleaned_data['left_right_balance']))

    else:
        LEFT, RIGHT = None, None



 
    # 计算区间信息
    if Zone:
        P_ZONES  = power_zones(cast(pd.Series, cleaned_data['power']))
        HR_ZONES = heart_rate_zones("threshold", cast(pd.Series, cleaned_data["heart_rate"]))  # 默认使用阈值方法


    # 计算其他指标
    # 计算常用骑行指标：强度因子(IF)、效率因子(EF)、变异系数(VI)
    IF = (
        round(NP / FTP, 2)
        if all(x is not None and x > 0 for x in [NP, FTP])
        else None
    )
    EF = (
        round(AP / AvgHR, 2)
        if all(x is not None and x > 0 for x in [AP, AvgHR])
        else None
    )
    VI = (
        round(NP / AP, 2)
        if all(x is not None and x > 0 for x in [NP, AP])
        else None
    )

    # 温度
    if "temperature" in cleaned_data.columns and not cast(pd.Series, cleaned_data['temperature']).isnull().all():
        MaxT = max_temperature(cast(pd.Series, cleaned_data['temperature']))
        AvgT = avg_temperature(cast(pd.Series, cleaned_data['temperature']))
        MinT = min_temperature(cast(pd.Series, cleaned_data['temperature']))
    else:
        MaxT, AvgT, MinT = None, None, None
    
    
    # 获取绘图信息
    if curves:
        power_series = cast(pd.Series, cleaned_data['power'])
        cadence_series = cast(pd.Series, cleaned_data['cadence'])
        power_curve = get_max_power_duration_curve(power_series) if not power_series.isnull().all() else None
        torque_curve = (
            get_torque_curve(cadence_series, power_series)
            if not cadence_series.isnull().all() and not power_series.isnull().all()
            else None
        )
        wbal_curve = get_wbal_curve(power_series) if not power_series.isnull().all() else None


    # ESTIMATE_FTP(power_curve)

    result_dict = {
        "Basic": {
            "time_info"      : time_info,
            "coast_time"     : format_seconds(coast_time), # Units      : XXhXXmXXs
            "coast_ratio"    : coast_ratio,                # Units      : %
            "avg_speed"      : AvgS,                       # Units      : km/h
            "max_speed"      : MaxS,                       # Units      : km/h
            "total_distance" : Dis,                        # Units      : km
            "elevation"      : Elev,                       # Units      : m
            "descent"        : descent,                    # Total Descent, Units: m
            "max_temperature": MaxT,                       # Units      : °C
            "avg_temperature": AvgT,                       # Units      : °C
            "min_temperature": MinT,                       # Units      : °C
            "avg_vam"        : results["avg_vam"],         # Average VAM, Units: m/h
        },
        "Power": {
            "avg"                  : AP,             # Average Power,          Units: watts
            "max"                  : MaxP,           # Max Power,              Units: watts
            "normalized_power"     : NP,             # Normalized Power,       Units: watts
            "training_stress_score": TSS,            # Training Stress Score,  Units: points
            "work"                 : W,              # Work Done,              Units: kJ
            "work_above_ftp"       : W_ABOVE_FTP,    # Work Done Above FTP,    Units: kJ
            "total_calories"       : CAL,            # Calories Burned,        Units: kcal
            "nonacclimated"        : nonacclimpower, # Non-acclimatized Power, Units: watts
            "acclimated"           : acclim_power,   # Acclimatized Power,     Units: watts
        },
        "HeartRate": {
            "avg_heartrate"              : AvgHR,             # Average Heart Rate,                 Units: bpm
            "max_heartrate"              : MaxHR,             # Max Heart Rate,                     Units: bpm
            "hrrc"             : HRRC,              # Heart Rate Recovery Capability,     Units: bpm
            "decoupling"       : decoupling,        # heart rate decoupling ratio,        Units: None
            "simple_decoupling": simple_decoupling, # simple heart rate decoupling ratio, Units: None
            "hr_lag"           : hr_lag,            # Heart Rate Lag,                     Units: seconds
        },
        "Cadence": {
            "avg_cadence"                           : avgCadence,                                # Average Cadence,                    Units: rpm
            "max_cadence"                           : maxCadence,                                # Max Cadence,                        Units: rpm
            "max_torque"                    : maxTorque,                                 # Max Torque,                         Units: Nm
            "avg_torque"                    : avgTorque,                                 # Average Torque,                     Units: Nm
            "avg_cadence_position"          : results["avg_cadence_position"],           # Average Cadence Position,           Units: degrees
            "avg_combined_pedal_smoothness" : results["avg_combined_pedal_smoothness"],  # Average Combined Pedal Smoothness,  Units: %
            "avg_fractional_cadence"        : results["avg_fractional_cadence"],         # Average Fractional Cadence,         Units: %
            "avg_left_pco"                  : results["avg_left_pco"],                   # Average Left Pedal Center Offset,   Units: mm
            "avg_left_pedal_smoothness"     : results["avg_left_pedal_smoothness"],      # Average Left Pedal Smoothness,      Units: %
            "avg_left_torque_effectiveness" : results["avg_left_torque_effectiveness"],  # Average Left Torque Effectiveness,  Units: %
            "avg_right_pco"                 : results["avg_right_pco"],                  # Average Right Pedal Center Offset,  Units: mm
            "avg_right_pedal_smoothness"    : results["avg_right_pedal_smoothness"],     # Average Right Pedal Smoothness,     Units: %
            "avg_right_power_phase"         : results["avg_right_power_phase"],          # Average Right Power Phase,          Units: degrees
            "avg_right_power_phase_peak"    : results["avg_right_power_phase_peak"],     # Average Right Power Phase Peak,     Units: degrees
            "avg_right_torque_effectiveness": results["avg_right_torque_effectiveness"], # Average Right Torque Effectiveness, Units: %
            "avg_power_position"            : results["avg_power_position"],             # Average Power Position,             Units: degrees
            "max_cadence_position"          : results["max_cadence_position"],           # Max Cadence Position,               Units: degrees
            "max_fractional_cadence"        : results["max_fractional_cadence"],         # Max Fractional Cadence,             Units: %
            "left_balance"                  : LEFT,                                      # Left Balance Percentage,            Units: %
            "right_balance"                 : RIGHT,                                     # Right Balance Percentage,           Units: %
        },

        "Index": {
            "IF"                             : IF,                                         # Intensity Factor,                Units: None
            "EF"                             : EF,                                         # Efficiency Factor,               Units: None
            "VI"                             : VI,                                         # Variance Index,                  Units: None
            "total_anaerobic_training_effect": results["total_anaerobic_training_effect"], # Total Anaerobic Training Effect, Units: None
            "total_training_effect"          : results["total_training_effect"],           # Total Training Effect,           Units: None
        },
    }
    if Zone:
        result_dict["Zones"] = {
            "power_zones"     : P_ZONES,  # Power Zones
            "heart_rate_zones": HR_ZONES, # Heart Rate Zones
        }   

    if curves:
        result_dict["curves"] = {
            "power_curve" : power_curve,  # Max Power Duration Curve
            "torque_curve": torque_curve, # Torque Curve
            "wbal_curve"  : wbal_curve,   # W' Balance Curve
            "decoupling_curve": decoupling_curve, # Decoupling Ratio Curve
        }

    if raw_data:
        result_dict["raw_data"] = {
            "power": cleaned_data['power'].fillna(0).tolist() if 'power' in cleaned_data.columns else None,
            "heart_rate": cleaned_data['heart_rate'].fillna(0).tolist() if 'heart_rate' in cleaned_data.columns else None,
            "cadence": cleaned_data['cadence'].fillna(0).tolist() if 'cadence' in cleaned_data.columns else None,
            "speed": cleaned_data['enhanced_speed'].fillna(0).tolist() if 'enhanced_speed' in cleaned_data.columns else None,
            "altitude": cleaned_data['enhanced_altitude'].fillna(0).tolist() if 'enhanced_altitude' in cleaned_data.columns else None,
            "temperature": cleaned_data['temperature'].fillna(0).tolist() if 'temperature' in cleaned_data.columns else None,
        }

    return result_dict