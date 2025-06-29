from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
from app.core import user_config

router = APIRouter()

# Power 模块配置
class PowerConfig(BaseModel):
    FTP: float
    FTP_indoor: float
    peak_power: float
    WJ: float
    eFTP_time: int

# 心率配置
class HeartRateConfig(BaseModel):
    max_bpm: int
    threshold_bpm: int
    resting_bpm: int
    hrrc_bpm: int
    warmup_time: int # 热身时间（分钟）
    cooldown_time: int # 冷却时间（分钟）

# 自行车信息
class BikeConfig(BaseModel):
    crank_radius_mm: float
    tire_Width_cc: int
    CDA: float

# 单位设置
class UnitsConfig(BaseModel):
    temperature: Literal["C", "F"]
    speed: Literal["kph", "mph"]
    altitude: Literal["m", "feet"]
    distance: Literal["km", "miles"]

# 用户主配置
class UserConfig(BaseModel):
    weight: float
    age: int
    sex: Literal["male", "female"]
    power: PowerConfig
    heart_rate: HeartRateConfig
    bike: BikeConfig
    units: UnitsConfig

@router.get("/user_config", response_model=UserConfig)
def get_user_config():
    return user_config.load_user_config()

@router.post("/user_config", response_model=UserConfig)
def update_user_config(new_config: UserConfig):
    try:
        user_config.save_user_config(new_config.model_dump())
        return new_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {e}")
