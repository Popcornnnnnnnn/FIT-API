# app/api/upload.py
from pickle import FALSE
from fastapi import APIRouter, File, UploadFile, HTTPException
import matplotlib.pyplot as plt
import shutil
import os
import pandas as pd
from tempfile import NamedTemporaryFile

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
async def upload_fit(file: UploadFile = File(...), debug: bool = False):
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


    cleaned_data: pd.DataFrame = clean_fit_data(data)
    FTP           = user_config["power"]["FTP"]


    results = {}

    for f in fields:
        results[f] = session[f].iloc[0] if f in session.columns else None


    # 计算基本指标
    # moving_time   = len(cleaned_data)
    # Dis           = total_distance(cleaned_data['distance'])
    # MaxS          = max_speed(cleaned_data['enhanced_speed'])
    # AvgS          = round(Dis / (len(cleaned_data) / 3600.0), 1) # average speed in km/h
    # Elev          = total_elevation_gain(cleaned_data['enhanced_altitude'])
    # coast_time    = coasting_time(cleaned_data['enhanced_speed'], cleaned_data['power']) \
    # if not cleaned_data['enhanced_speed'].isnull().all() else coasting_time(cleaned_data['enhanced_speed'])
    # coast_ratio   = round((coast_time / moving_time) * 100, 1) if moving_time > 0 else None

    # if "total_ascent" in session.columns:
    #     Elev = int(session["total_ascent"].iloc[0])


    # # 计算功率相关指标
    # if not cleaned_data['power'].isnull().all():
    #     AP          = avg_power(cleaned_data['power'])                                          
    #     MaxP        = max_power(cleaned_data['power'])                                          
    #     NP          = normalized_power(cleaned_data['power'])                                   
    #     TSS         = training_stress_score(cleaned_data['power'], len(cleaned_data) / 3600.0)  
    #     W           = calculate_work_kj(cleaned_data['power'])                                 
    #     W_ABOVE_FTP = calculate_work_kj_above_ftp(cleaned_data['power'])                       
    #     CAL         = estimate_calories(cleaned_data['power'])       
    #     # eFTP        = estimate_eFTP(cleaned_data['power']) 
    # else:
    #     AP, MaxP, NP, TSS, W, W_ABOVE_FTP, CAL, eFTP = None, None, None, None, None, None, None, None
        
    # if "total_calories" in session.columns:
    #     CAL = int(session["total_calories"].iloc[0])

    
    # if not cleaned_data['power'].isnull().all() and cleaned_data['altitude'].notnull().all(): 
    #     acclim_power = get_altitude_adjusted_power_acclimatized(cleaned_data['power'], cleaned_data['altitude'],)
    #     nonacclimpower = get_altitude_adjusted_power_nonacclimatized(cleaned_data['power'], cleaned_data['altitude'],)
    # else:
    #     acclim_power, nonacclimpower = None, None
        

    # # 计算心率相关指标
    # if not cleaned_data['heart_rate'].isnull().all():
    #     AvgHR = avg_heart_rate(cleaned_data['heart_rate'])                             
    #     MaxHR = max_heart_rate(cleaned_data['heart_rate'])                            
    #     HRRC  = heart_rate_recovery_capablility(cleaned_data['heart_rate'])            
    # else:
    #     AvgHR, MaxHR, HRRC = None, None, None
    
    # # 心率解耦率相关指标
    # if not cleaned_data['heart_rate'].isnull().all() and not cleaned_data['power'].isnull().all(): 
    #     decoupling, decoupling_curve = decoupling_ratio(cleaned_data)
    #     hr_lag            = heart_rate_lag(cleaned_data['power'], cleaned_data['heart_rate'])
    #     simple_decoupling = simple_decoupling_ratio(cleaned_data)
    # else: 
    #     decoupling, decoupling_curve, hr_lag, simple_decoupling = None, None, None, None


    # 计算踏频相关指标
    if 'cadence' in cleaned_data.columns and not cleaned_data['cadence'].isnull().all(): # type: ignore
        avgCadence = avg_cadence(cleaned_data['cadence']) # type: ignore
        maxCadence = max_cadence(cleaned_data['cadence']) # type: ignore
    else:
        avgCadence, maxCadence = None, None
    if 'cadence' in cleaned_data.columns and 'power' in cleaned_data.columns and not cleaned_data['cadence'].isnull().all() and not cleaned_data['power'].isnull().all():# type: ignore
        maxTorque = max_torque(cleaned_data['cadence'], cleaned_data['power']) # type: ignore
        avgTorque = avg_torque(cleaned_data['cadence'], cleaned_data['power']) # type: ignore
    else:
        maxTorque, avgTorque = None, None

    # 将left_right_balance列输出到文件，方便查看
    with open("left_right_balance_output.txt", "w", encoding="utf-8") as f:
        f.write(cleaned_data['left_right_balance'].to_string())
          


    if "left_right_balance" in cleaned_data.columns:
        LEFT, RIGHT = left_right_balance(cleaned_data['left_right_balance']) # type: ignore

    else:
        LEFT, RIGHT = None, None



 
    # 计算区间信息
    # P_ZONES  = power_zones(cleaned_data['power'])
    # HR_ZONES = heart_rate_zones("threshold", cleaned_data["heart_rate"])  # 默认使用阈值方法


    # 计算其他指标
    # IF = round(NP / FTP, 2) if NP is not None and NP > 0 else None
    # EF = round(AP / AvgHR, 2) if AvgHR is not None and AvgHR > 0 and AP is not None and  AP > 0 else None
    # VI = round(NP / AP, 2) if AP is not None and AP > 0 and NP > 0 else None

    # # 温度
    # if "temperature" in cleaned_data.columns and not cleaned_data['temperature'].isnull().all():
    #     MaxT = max_temperature(cleaned_data['temperature'])
    #     AvgT = avg_temperature(cleaned_data['temperature'])
    #     MinT = min_temperature(cleaned_data['temperature'])
    # else:
    #     MaxT, AvgT, MinT = None, None, None
    
    
    # 获取绘图信息
    # power_curve = get_max_power_duration_curve(cleaned_data['power']) if not cleaned_data['power'].isnull().all() else None
    # torque_curve = get_torque_curve(cleaned_data['cadence'], cleaned_data['power']) if not cleaned_data['cadence'].isnull().all() and not cleaned_data['power'].isnull().all() else None
    # wbal_curve = get_wbal_curve(cleaned_data['power']) if not cleaned_data['power'].isnull().all() else None

    return {
        # "Basic": {
        #     "time_info"      : time_info,
        #     "coast_time"     : format_seconds(coast_time), # Units      : XXhXXmXXs
        #     "coast_ratio"    : coast_ratio,                # Units      : %
        #     "avg_speed"      : AvgS,                       # Units      : km/h
        #     "max_speed"      : MaxS,                       # Units      : km/h
        #     "total_distance" : Dis,                        # Units      : km
        #     "elevation"      : Elev,                       # Units      : m
        #     "descent"         : int(results["total_descent"]) if results["total_descent"] is not None else None,          # Total Descent, Units: m
        #     "max_temperature": MaxT,                       # Units      : °C
        #     "avg_temperature": AvgT,                       # Units      : °C
        #     "min_temperature": MinT,                       # Units      : °C
        #     "avg_vam"        : results["avg_vam"],         # Average VAM, Units: m/h
        # },
        # "Power": {
        #     "avg"            : AP,             # Average Power,          Units: watts
        #     "max"            : MaxP,           # Max Power,              Units: watts
        #     "normalized_power"     : NP,             # Normalized Power,       Units: watts
        #     "training_stress_score"            : TSS,            # Training Stress Score,  Units: points
        #     "work"              : W,              # Work Done,              Units: kJ
        #     "work_above_ftp"    : W_ABOVE_FTP,    # Work Done Above FTP,    Units: kJ
        #     "total_calories" : CAL,            # Calories Burned,        Units: kcal
        #     "nonacclimated"  : nonacclimpower, # Non-acclimatized Power, Units: watts
        #     "acclimated"     : acclim_power,   # Acclimatized Power,     Units: watts
        # },
        # "HeartRate": {
        #     "avg_heartrate"              : AvgHR,             # Average Heart Rate,                 Units: bpm
        #     "max_heartrate"              : MaxHR,             # Max Heart Rate,                     Units: bpm
        #     "hrrc"             : HRRC,              # Heart Rate Recovery Capability,     Units: bpm
        #     "decoupling"       : decoupling,        # heart rate decoupling ratio,        Units: None
        #     "simple_decoupling": simple_decoupling, # simple heart rate decoupling ratio, Units: None
        #     "hr_lag"           : hr_lag,            # Heart Rate Lag,                     Units: seconds
        # },
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
        # "Zones": {
        #     "power_zones"     : P_ZONES,  # Power Zones
        #     "heart_rate_zones": HR_ZONES, # Heart Rate Zones
        # },
        # "Index": {
        #     "IF"                             : IF,                                         # Intensity Factor,                Units: None
        #     "EF"                             : EF,                                         # Efficiency Factor,               Units: None
        #     "VI"                             : VI,                                         # Variance Index,                  Units: None
        #     "total_anaerobic_training_effect": results["total_anaerobic_training_effect"], # Total Anaerobic Training Effect, Units: None
        #     "total_training_effect"          : results["total_training_effect"],           # Total Training Effect,           Units: None
        # },
        # "curves": {
        #     "power_curve" : power_curve,  # Max Power Duration Curve
        #     "torque_curve": torque_curve, # Torque Curve
        #     "wbal_curve"  : wbal_curve,   # W' Balance Curve
        #     "decoupling_curve": decoupling_curve, # Decoupling Ratio Curve
        # },
        # "raw_data": {
        #     "power": cleaned_data['power'].fillna(0).tolist() if 'power' in cleaned_data.columns else None,
        #     "heart_rate": cleaned_data['heart_rate'].fillna(0).tolist() if 'heart_rate' in cleaned_data.columns else None,
        #     "cadence": cleaned_data['cadence'].fillna(0).tolist() if 'cadence' in cleaned_data.columns else None,
        #     "speed": cleaned_data['enhanced_speed'].fillna(0).tolist() if 'enhanced_speed' in cleaned_data.columns else None,
        #     "altitude": cleaned_data['enhanced_altitude'].fillna(0).tolist() if 'enhanced_altitude' in cleaned_data.columns else None,
        #     "temperature": cleaned_data['temperature'].fillna(0).tolist() if 'temperature' in cleaned_data.columns else None,
        # },

    }
