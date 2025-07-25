# type: ignore
# pyright: reportGeneralTypeIssues=false

from fitparse import FitFile
import pandas as pd


def parse_fit_file(file_path: str) -> pd.DataFrame:

    fitfile = FitFile(file_path)
    records = []
    for record in fitfile.get_messages('record'):
        data = {}   
        for d in record:
            data[d.name] = d.value
        records.append(data)


    return pd.DataFrame(records)

import pandas as pd

def clean_fit_data(
    df: pd.DataFrame,
    use_speed: bool = False,
    speed_limit: float = 0,
    use_time_gap: bool = True,
    time_threshold_sec: int = 2
) -> pd.DataFrame:

    """
    清洗 FIT 数据，去除暂停时段

    参数:
    - df: 解析后的原始 DataFrame
    - use_speed: 是否根据 speed/enhanced_speed 去除速度为0的数据
    - speed_limit: 速度阈值，低于该值的数据点将被删除
    - use_time_gap: 是否根据 timestamp 连续性过滤长时间暂停
    - time_threshold_sec: 如果两点间间隔超过该值，认为中间暂停
    
    返回:
    - 清洗后的 DataFrame
    """

    df_clean = df.copy()

    # 1. 清洗速度为0的数据点
    if use_speed:
        if "enhanced_speed" in df_clean.columns:
            df_clean = df_clean[df_clean["enhanced_speed"] > speed_limit]
        elif "speed" in df_clean.columns:
            df_clean = df_clean[df_clean["speed"] > speed_limit]

    # 2. 清洗时间间隔大的数据点
    if use_time_gap and "timestamp" in df_clean.columns:
        df_clean = df_clean.sort_values("timestamp").reset_index(drop=True)
        df_clean["delta"] = df_clean["timestamp"].diff().dt.total_seconds()
        df_clean = df_clean[(df_clean["delta"].isna()) | (df_clean["delta"] <= time_threshold_sec)]
        df_clean = df_clean.drop(columns="delta")

    # 重置索引
    return df_clean.reset_index(drop=True)


def get_fit_date_time_info(file_path: str) -> dict:
    """
    解析 FIT 文件，提取日期和时间相关信息。
    返回字典，包含常见时间字段和值（如创建时间、开始时间等）
    """
    fitfile = FitFile(file_path)
    date_time_info = {}

    for message in fitfile.get_messages():
        if message.name in ['file_id', 'session', 'activity', 'lap']:
            for field in message:
                if 'time' in field.name or 'date' in field.name:
                    date_time_info[f"{message.name}.{field.name}"] = field.value

    return date_time_info

def parse_fit_session(file_path: str) -> pd.DataFrame:
    fitfile = FitFile(file_path)
    sessions = []
    for session in fitfile.get_messages('session'):
        data = {}
        for d in session:
            data[d.name] = d.value
        sessions.append(data)
    return pd.DataFrame(sessions)

def parse_fit_device_info(file_path: str) -> dict:
    """
    解析 FIT 文件中的设备相关信息
    
    Args:
        file_path (str): FIT 文件路径
        
    Returns:
        dict: 包含设备信息的字典，包括：
            - device_info: 设备基本信息列表
            - file_id: 文件ID信息
            - software: 软件信息
            - source: 数据源信息
    """
    fitfile = FitFile(file_path)
    device_info = {
        "device_info": [],
        "file_id": {},
        "software": {},
        "source": {}
    }
    
    # 解析设备信息
    for message in fitfile.get_messages('device_info'):
        device_data = {}
        for field in message:
            device_data[field.name] = field.value
        device_info["device_info"].append(device_data)
    
    # 解析文件ID信息（通常包含设备信息）
    for message in fitfile.get_messages('file_id'):
        for field in message:
            device_info["file_id"][field.name] = field.value
    
    # 解析软件信息
    for message in fitfile.get_messages('software'):
        for field in message:
            device_info["software"][field.name] = field.value
    
    # 解析数据源信息
    for message in fitfile.get_messages('source'):
        for field in message:
            device_info["source"][field.name] = field.value
    
    return device_info


def get_device_summary(file_path: str) -> dict:
    """
    获取设备信息的摘要
    
    Args:
        file_path (str): FIT 文件路径
        
    Returns:
        dict: 设备摘要信息
    """
    device_info = parse_fit_device_info(file_path)
    summary = {
        "device_count": len(device_info["device_info"]),
        "manufacturer": None,
        "product": None,
        "software_version": None,
        "file_type": device_info["file_id"].get("type", "Unknown")
    }
    
    # 从设备信息中提取制造商和产品信息
    if device_info["device_info"]:
        first_device = device_info["device_info"][0]
        summary["manufacturer"] = first_device.get("manufacturer", "Unknown")
        summary["product"] = first_device.get("product", "Unknown")
    
    # 从软件信息中提取版本
    if device_info["software"]:
        summary["software_version"] = device_info["software"].get("version", "Unknown")
    
    return summary


def get_device_details(file_path: str) -> list:
    """
    获取详细的设备信息列表
    
    Args:
        file_path (str): FIT 文件路径
        
    Returns:
        list: 设备详细信息列表
    """
    device_info = parse_fit_device_info(file_path)
    details = []
    
    for device in device_info["device_info"]:
        detail = {
            "timestamp": device.get("timestamp"),
            "manufacturer": device.get("manufacturer"),
            "product": device.get("product"),
            "serial_number": device.get("serial_number"),
            "device_type": device.get("device_type"),
            "hardware_version": device.get("hardware_version"),
            "software_version": device.get("software_version"),
            "battery_voltage": device.get("battery_voltage"),
            "battery_status": device.get("battery_status"),
            "device_index": device.get("device_index")
        }
        details.append(detail)
    
    return details
