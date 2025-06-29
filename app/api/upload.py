# app/api/upload.py
from fastapi import APIRouter, File, UploadFile, HTTPException
import matplotlib.pyplot as plt
import shutil
import os
import pandas as pd
from tempfile import NamedTemporaryFile

from app.core.fit_parser import *
from app.core.power import *
from app.core.heart_rate import *
from app.core.cadence import *
from app.core.more_data import *
from app.core.utils import format_seconds


router = APIRouter()

@router.post("/upload_fit")
async def upload_fit(file: UploadFile = File(...)):
    if not file.filename.endswith(".fit"):
        raise HTTPException(status_code=400, detail="Only .fit files are supported")

    # 保存上传文件到临时文件
    try:
        with NamedTemporaryFile(delete=False, suffix=".fit") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
    finally:
        file.file.close()
    try:
        data = parse_fit_file(tmp_path)
        time_info = get_fit_date_time_info(tmp_path)
    finally:
        os.remove(tmp_path)


    cleaned_data  = clean_fit_data(data)
    total_seconds = time_info["session.total_timer_time"]
    FTP           = user_config["power"]["FTP"]

    # 计算基本指标
    total_time    = total_seconds  
    moving_time   = len(cleaned_data)
    Dis           = total_distance(cleaned_data['distance'])
    MaxS          = max_speed(cleaned_data['enhanced_speed'])
    AvgS          = round(Dis / (len(cleaned_data) / 3600.0), 1) # average speed in km/h
    Elev          = total_elevation_gain(cleaned_data['enhanced_altitude'])
    coast_time    = coasting_time(cleaned_data['enhanced_speed'], cleaned_data['power']) \
    if not cleaned_data['enhanced_speed'].isnull().all() else coasting_time(cleaned_data['enhanced_speed'])
    coast_ratio   = round((coast_time / moving_time) * 100, 1) if moving_time > 0 else None


    # 计算功率相关指标
    if not cleaned_data['power'].isnull().all():
        AP          = avg_power(cleaned_data['power'])                                          
        MaxP        = max_power(cleaned_data['power'])                                          
        NP          = normalized_power(cleaned_data['power'])                                   
        TSS         = training_stress_score(cleaned_data['power'], len(cleaned_data) / 3600.0)  
        W           = calculate_work_kj(cleaned_data['power'])                                 
        W_ABOVE_FTP = calculate_work_kj_above_ftp(cleaned_data['power'])                       
        CAL         = estimate_calories(cleaned_data['power'])       
    else:
        AP, MaxP, NP, TSS, W, W_ABOVE_FTP, CAL = None, None, None, None, None, None, None

    if not cleaned_data['power'].isnull().all() and cleaned_data['altitude'].notnull().all(): 
        acclim_power = get_altitude_adjusted_power_acclimatized(cleaned_data['power'], cleaned_data['altitude'],)
        nonacclimpower = get_altitude_adjusted_power_nonacclimatized(cleaned_data['power'], cleaned_data['altitude'],)
    else:
        acclim_power, nonacclimpower = None, None
        

    # 计算心率相关指标
    if not cleaned_data['heart_rate'].isnull().all():
        AvgHR = avg_heart_rate(cleaned_data['heart_rate'])                             
        MaxHR = max_heart_rate(cleaned_data['heart_rate'])                            
        HRRC  = heart_rate_recovery_capablility(cleaned_data['heart_rate'])            
    else:
        AvgHR, MaxHR, HRRC = None, None, None
    
    # 心率解耦率相关指标
    if not cleaned_data['heart_rate'].isnull().all() and not cleaned_data['power'].isnull().all(): 
        decoupling, decoupling_curve = decoupling_ratio(cleaned_data)
        hr_lag            = heart_rate_lag(cleaned_data['power'], cleaned_data['heart_rate'])
        simple_decoupling = simple_decoupling_ratio(cleaned_data)
    else: 
        decoupling, decoupling_curve, hr_lag, simple_decoupling = None, None, None, None


    # 计算踏频相关指标
    if not cleaned_data['cadence'].isnull().all():
        avgCadence = avg_cadence(cleaned_data['cadence'])
        maxCadence = max_cadence(cleaned_data['cadence'])
    else:
        avgCadence, maxCadence = None, None
    if not cleaned_data['cadence'].isnull().all() and not cleaned_data['power'].isnull().all():
        maxTorque = max_torque(cleaned_data['cadence'], cleaned_data['power'])
        avgTorque = avg_torque(cleaned_data['cadence'], cleaned_data['power'])
    else:
        maxTorque, avgTorque = None, None

    # 计算区间信息
    P_ZONES  = power_zones(cleaned_data['power'])
    HR_ZONES = heart_rate_zones("threshold", cleaned_data["heart_rate"])  # 默认使用阈值方法


    # 计算其他指标
    IF = round(NP / FTP, 2) if NP > 0 else None
    EF = round(AP / AvgHR, 2) if AvgHR > 0 and AP > 0 else None
    VI = round(NP / AP, 2) if AP > 0 and NP > 0 else None

    # 温度
    if "temperature" in cleaned_data.columns and not cleaned_data['temperature'].isnull().all():
        MaxT = max_temperature(cleaned_data['temperature'])
        AvgT = avg_temperature(cleaned_data['temperature'])
        MinT = min_temperature(cleaned_data['temperature'])
    else:
        MaxT, AvgT, MinT = None, None, None
    
    
    # 获取绘图信息
    power_curve = get_max_power_duration_curve(cleaned_data['power']) if not cleaned_data['power'].isnull().all() else None
    torque_curve = get_torque_curve(cleaned_data['cadence'], cleaned_data['power']) if not cleaned_data['cadence'].isnull().all() and not cleaned_data['power'].isnull().all() else None
    wbal_curve = get_wbal_curve(cleaned_data['power']) if not cleaned_data['power'].isnull().all() else None

    return {
        "basic": {
            "time_info"      : time_info,
            "coast_time"     : format_seconds(coast_time), # Units: XXhXXmXXs
            "coast_ratio"    : coast_ratio,                # Units: %
            "avg_speed"      : AvgS,                       # Units: km/h
            "max_speed"      : MaxS,                       # Units: km/h
            "total_distance" : Dis,                        # Units: km
            "elevation"      : Elev,                       # Units: m
            "max_temperature": MaxT,                       # Units: °C
            "avg_temperature": AvgT,                       # Units: °C
            "min_temperature": MinT,                       # Units: °C
        },
        "power": {
        "avg"            : AP,             # Average Power,          Units: watts
        "max"            : MaxP,           # Max Power,              Units: watts
        "NP"             : NP,             # Normalized Power,       Units: watts
        "TSS"            : TSS,            # Training Stress Score,  Units: points
        "W"              : W,              # Work Done,              Units: kJ
        "W_ABOVE_FTP"    : W_ABOVE_FTP,    # Work Done Above FTP,    Units: kJ
        "CAL"            : CAL,            # Calories Burned,        Units: kcal
        "nonacclimated"  : nonacclimpower, # Non-acclimatized Power, Units: watts
        "acclimated"     : acclim_power,   # Acclimatized Power,     Units: watts
        },
        "heart_rate": {
            "avg" : AvgHR, # Average Heart Rate,             Units: bpm
            "max" : MaxHR, # Max Heart Rate,                 Units: bpm
            "hrrc": HRRC,  # Heart Rate Recovery Capability, Units: bpm
            "decoupling": decoupling, # heart rate decoupling ratio, Units: None
            "simple_decoupling": simple_decoupling, # simple heart rate decoupling ratio, Units: None
            "hr_lag": hr_lag, # Heart Rate Lag, Units: seconds
        },
        "cadence": {
            "avg"       : avgCadence, # Average Cadence, Units: rpm
            "max"       : maxCadence, # Max Cadence,     Units: rpm
            "max_torque": maxTorque,  # Max Torque,      Units: Nm
            "avg_torque": avgTorque,  # Average Torque,  Units: Nm
        },
        "Zones": {
            "power_zones"     : P_ZONES,  # Power Zones
            "heart_rate_zones": HR_ZONES, # Heart Rate Zones
        },
        "Index": {
            "IF": IF, # Intensity Factor,  Units: None
            "EF": EF, # Efficiency Factor, Units: None
            "VI": VI, # Variance Index,    Units: None
        },
        # "curves": {
        #     "power_curve" : power_curve,  # Max Power Duration Curve
        #     "torque_curve": torque_curve, # Torque Curve
        #     "wbal_curve"  : wbal_curve,   # W' Balance Curve
        #     "decoupling_curve": decoupling_curve, # Decoupling Ratio Curve
        # }
    }
