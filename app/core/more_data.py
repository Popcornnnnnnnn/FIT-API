import pandas as pd
from scipy.signal import savgol_filter

def total_distance(distance_series: pd.Series) -> float:
    if distance_series.empty:
        return 0.0
    return round(distance_series.max() / 1000, 2)

def max_speed(speed_series: pd.Series) -> float:
    if speed_series.empty:
        return 0.0
    return round(speed_series.max() * 3.6, 1)

def total_elevation_gain(altitude_series: pd.Series, min_gain = 0.9, min_duration = 3) -> float:
    smooth_alt = altitude_series.round(1).rolling(window=5, center=True, min_periods=1).mean()

    total_gain = 0.0
    start_index = None

    for i in range(1, len(smooth_alt)):
        current = smooth_alt.iloc[i]
        previous = smooth_alt.iloc[i - 1]

        # 上升趋势
        if current > previous:
            if start_index is None:
                start_index = i - 1
        else:
            if start_index is not None:
                # 结束了一个上升段
                end_index = i - 1
                segment = smooth_alt.iloc[start_index:end_index + 1]
                gain = segment.iloc[-1] - segment.iloc[0]
                duration = end_index - start_index + 1

                if gain >= min_gain and duration >= min_duration:
                    total_gain += gain

                start_index = None

    # 最后一个可能的段
    if start_index is not None and start_index < len(smooth_alt) - 1:
        segment = smooth_alt.iloc[start_index:]
        gain = segment.iloc[-1] - segment.iloc[0]
        duration = len(segment)
        if gain >= min_gain and duration >= min_duration:
            total_gain += gain

    return round(total_gain)

def coasting_time(speed_series: pd.Series, power_series: pd.Series | None = None) -> int:
    coasting_mask = speed_series < 1
    if power_series is not None:
        coasting_mask |= power_series < 10

    return coasting_mask.sum()

def max_temperature(temperature_series: pd.Series) -> int:
    return round(temperature_series.max())

def avg_temperature(temperature_series: pd.Series) -> int:
    return round(temperature_series.mean())

def min_temperature(temperature_series: pd.Series) -> int:
    return round(temperature_series.min())

