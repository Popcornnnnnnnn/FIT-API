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
    time_threshold_sec: int = 5
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

