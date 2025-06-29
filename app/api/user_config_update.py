from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any
from app.core import user_config as config_helper
from app.core.power import get_power_zones

router = APIRouter()

# 定义所有字段均可选的子模型，支持部分更新

class PowerConfigUpdate(BaseModel):
    FTP: Optional[float] = None
    FTP_indoor: Optional[float] = None
    peak_power: Optional[float] = None
    WJ: Optional[float] = None
    eFTP_time: Optional[int] = None

class HeartRateConfigUpdate(BaseModel):
    max_bpm: Optional[int] = None
    threshold_bpm: Optional[int] = None
    resting_bpm: Optional[int] = None
    hrrc_bpm: Optional[int] = None
    warmup_time: Optional[int] = None
    cooldown_time: Optional[int] = None

class BikeConfigUpdate(BaseModel):
    crank_radius_mm: Optional[float] = None
    tire_Width_cc: Optional[int] = None
    CDA: Optional[float] = None

class UnitsConfigUpdate(BaseModel):
    temperature: Optional[Literal["C", "F"]] = None
    speed: Optional[Literal["kph", "mph"]] = None
    altitude: Optional[Literal["m", "feet"]] = None
    distance: Optional[Literal["km", "miles"]] = None

class UserConfigUpdate(BaseModel):
    weight: Optional[float] = None
    age: Optional[int] = None
    sex: Optional[Literal["male", "female"]] = None
    power: Optional[PowerConfigUpdate] = None
    heart_rate: Optional[HeartRateConfigUpdate] = None
    bike: Optional[BikeConfigUpdate] = None
    units: Optional[UnitsConfigUpdate] = None

def deep_update(source: dict, overrides: dict):
    for key, value in overrides.items():
        if isinstance(value, dict) and key in source and isinstance(source[key], dict):
            source[key] = deep_update(source[key], value)
        else:
            source[key] = value
    return source

@router.patch("/user_config", response_model=dict)
def patch_user_config(update: UserConfigUpdate):
    try:
        current_config = config_helper.load_user_config()
        updated = deep_update(current_config, update.model_dump(exclude_unset=True))
        config_helper.save_user_config(updated)
        if "FTP" in updated.get("power", {}): # 如果有 power 字段中的 FTP 更新，则重新计算功率区间
            updated["P_ZONES"] = get_power_zones(updated["power"]["FTP"])
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {e}")
