# 📍 Cycling FIT Analysis API

A FastAPI-based backend service for parsing `.fit` files from cycling computers (e.g., Garmin, Wahoo, IGPSport), computing detailed ride metrics such as power, heart rate, cadence, and more.

---

## 📊 API Overview

### `POST /upload_fit`

**Description:**
Upload a `.fit` file and receive structured cycling metrics.

**Request:**
- Content-Type: `multipart/form-data`
- Parameters:
  - `file`: FIT file (required)

**Response:**
Returns a JSON object containing the analysis result with these keys:

```json
{
  "basic": { ... },
  "power": { ... },
  "heart_rate": { ... },
  "cadence": { ... },
  "Zones": { ... },
  "Index": { ... }
}
```

### `GET /user_config`

**Description**:Returns the full user configuration.

**Response:** Returns the current `UserConfig` JSON object.

### `POST /user_config`

**Description:** Replace the entire user configuration.

**Request Body:**

```json
{ 
  "weight": 68.0,
  "age": 30,
  "sex": "male",
  "power": {
    "FTP": 272,
    "FTP_indoor": 270,
    "peak_power": 1000,
    "WJ": 20000,
    "eFTP_time": 1200
  },
  "heart_rate": {
    "max_bpm": 190,
    "threshold_bpm": 175,
    "resting_bpm": 50,
    "hrrc_bpm": 20,
    "warmup_time": 10,
    "cooldown_time": 10
  },
  "bike": {
    "crank_radius_mm": 175.0,
    "tire_Width_cc": 25,
    "CDA": 0.3
  },
  "units": {
    "temperature": "C",
    "speed": "kph",
    "altitude": "m",
    "distance": "km"
  }
}
```

### `PATCH /user_config`

**Description:** Partially update any nested key in the user config.

**Request Body:**

- Any subset of fields from the full `UserConfig` schema.

**Logic:**

- If `power.FTP` is updated, server will also recalculate and return `power_zones`.

---

##返回结构（JSON）

### `Basic` 基本信息

| 字段名            | 类型   | 单位  | 描述                           |
| ----------------- | ------ | ----- | ------------------------------ |
| `time_info`       | dict   | N/A   | 各类时间戳与持续时间信息       |
| `coast_time`      | string | h/m/s | 滑行总时间（格式化）           |
| `coast_ratio`     | float  | %     | 滑行占比                       |
| `avg_speed`       | float  | km/h  | 平均速度                       |
| `max_speed`       | float  | km/h  | 最大速度                       |
| `total_distance`  | float  | km    | 骑行总距离                     |
| `elevation`       | float  | m     | 总爬升高度                     |
| `descent`         | int    | m     | 总下降高度                     |
| `max_temperature` | float  | °C    | 最高气温                       |
| `avg_temperature` | float  | °C    | 平均气温                       |
| `min_temperature` | float  | °C    | 最低气温                       |
| `avg_vam`         | float  | m/h   | 平均 VAM（单位小时的爬升高度） |



------

### `Power` 功率分析

| 字段名                  | 类型  | 单位 | 描述                          |
| ----------------------- | ----- | ---- | ----------------------------- |
| `avg`                   | float | W    | 平均功率                      |
| `max`                   | float | W    | 最大功率                      |
| `normalized_power`      | float | W    | 归一化功率（NP）              |
| `training_stress_score` | float | pts  | 训练压力得分（TSS）           |
| `work`                  | float | kJ   | 总功（能量输出）              |
| `work_above_ftp`        | float | kJ   | 超阈功（高于 FTP 输出的能量） |
| `total_calories`        | float | kcal | 消耗总卡路里                  |
| `nonacclimated`         | float | W    | 未适应环境下的功率估计        |
| `acclimated`            | float | W    | 已适应环境下的功率估计        |



------

### `HeartRate` 心率分析

| 字段名              | 类型  | 单位 | 描述                             |
| ------------------- | ----- | ---- | -------------------------------- |
| `avg_heartrate`     | int   | bpm  | 平均心率                         |
| `max_heartrate`     | int   | bpm  | 最大心率                         |
| `hrrc`              | int   | bpm  | 心率恢复能力（恢复速率）         |
| `decoupling`        | float | N/A  | 心率解耦率（高级算法）           |
| `simple_decoupling` | float | N/A  | 心率解耦率（简易版本）           |
| `hr_lag`            | int   | 秒   | 心率延迟（心率滞后于功率的时间） |



------

### `Cadence` 踏频与扭矩分析

| 字段名                           | 类型  | 单位    | 描述                 |
| -------------------------------- | ----- | ------- | -------------------- |
| `avg_cadence`                    | int   | rpm     | 平均踏频             |
| `max_cadence`                    | int   | rpm     | 最大踏频             |
| `avg_torque`                     | float | Nm      | 平均扭矩             |
| `max_torque`                     | float | Nm      | 最大扭矩             |
| `avg_cadence_position`           | float | degrees | 平均踏频位置（角度） |
| `avg_combined_pedal_smoothness`  | float | %       | 联合踏频平滑度       |
| `avg_fractional_cadence`         | float | %       | 小数踏频             |
| `avg_left_pco`                   | float | mm      | 左脚踏板中心偏移     |
| `avg_left_pedal_smoothness`      | float | %       | 左脚平滑度           |
| `avg_left_torque_effectiveness`  | float | %       | 左脚扭矩效率         |
| `avg_right_pco`                  | float | mm      | 右脚踏板中心偏移     |
| `avg_right_pedal_smoothness`     | float | %       | 右脚平滑度           |
| `avg_right_power_phase`          | float | degrees | 右脚功率相位         |
| `avg_right_power_phase_peak`     | float | degrees | 右脚功率峰值相位     |
| `avg_right_torque_effectiveness` | float | %       | 右脚扭矩效率         |
| `avg_power_position`             | float | degrees | 功率中心位置         |
| `max_cadence_position`           | float | degrees | 最大踏频时的位置角度 |
| `max_fractional_cadence`         | float | %       | 最大小数踏频         |
| `left_balance`                   | float | %       | 左右平衡（左）       |
| `right_balance`                  | float | %       | 左右平衡（右）       |



------

### `Zones` 区间分布

| 字段名             | 类型 | 单位 | 描述         |
| ------------------ | ---- | ---- | ------------ |
| `power_zones`      | dict | N/A  | 功率分区分布 |
| `heart_rate_zones` | dict | N/A  | 心率分区分布 |



------

### `Index` 指数指标

| 字段名                            | 类型  | 单位 | 描述                          |
| --------------------------------- | ----- | ---- | ----------------------------- |
| `IF`                              | float | N/A  | 强度因子（Intensity Factor）  |
| `EF`                              | float | N/A  | 效率因子（Efficiency Factor） |
| `VI`                              | float | N/A  | 变异指数（Variability Index） |
| `total_anaerobic_training_effect` | float | N/A  | 无氧训练效果评分              |
| `total_training_effect`           | float | N/A  | 总体训练效果评分              |



------

### `curves` 功率/扭矩/解耦曲线

| 字段名             | 类型 | 描述                |
| ------------------ | ---- | ------------------- |
| `power_curve`      | dict | 功率-持续时间曲线   |
| `torque_curve`     | dict | 扭矩-持续时间曲线   |
| `wbal_curve`       | dict | W' 平衡消耗恢复曲线 |
| `decoupling_curve` | dict | 解耦率变化曲线      |



------

### `raw_data` 原始时间序列数据（简化处理）

| 字段名        | 类型 | 单位 | 描述           |
| ------------- | ---- | ---- | -------------- |
| `power`       | list | W    | 每秒功率值序列 |
| `heart_rate`  | list | bpm  | 每秒心率值序列 |
| `cadence`     | list | rpm  | 每秒踏频值序列 |
| `speed`       | list | km/h | 每秒速度值序列 |
| `altitude`    | list | m    | 每秒海拔值序列 |
| `temperature` | list | °C   | 每秒温度值序列 |

---

## 🛋️ Metrics Computation Modules

All logic is modularized under `app/core/`, including:

- `fit_parser.py` — low-level FIT file parsing and cleaning
- `power.py` — normalized power, TSS, FTP zone work etc.
- `heart_rate.py` — HR averages, recovery, lag, decoupling etc.
- `cadence.py` — torque, cadence metrics etc.
- `more_data.py` — temperature, coasting, etc.

---

## 📆 Example Usage (cURL)

```bash
curl -X POST "http://localhost:8000/api/upload_fit" \
  -H  "accept: application/json" \
  -H  "Content-Type: multipart/form-data" \
  -F "file=@ride.fit" 
```

---

## 📁 Project Structure

```python
Intervals/
├── app/                         
│   ├── README.md                 
│   ├── api/                      
│   │   ├── upload.py             # Handles FIT file upload and analysis
│   │   ├── user_config.py        # Full user config (GET/POST)
│   │   └── user_config_update.py # Partial user config updates (PATCH)
│   ├── config/               
│   │   └── user_config.json      # Current user configuration file (JSON)
│   ├── core/            
│   │   ├── cadence.py            # Cadence and torque calculations
│   │   ├── fit_parser.py         # FIT file parsing and data cleaning
│   │   ├── heart_rate.py         # Heart rate metrics
│   │   ├── more_data.py          # Extra metrics
│   │   ├── power.py              # Power metrics
│   │   ├── user_config.py        # Load/save config file logic
│   │   └── utils.py              # Utility functions (e.g., time formatting)
│   └── main.py                   
└── test/                        
    ├── update_user_config.ps1    # Test PATCH /user_config endpoint
    ├── upload_fit.ps1            # Test FIT file upload endpoint

```

---

## 👤 Author

Jack Wang / `@Popcornnnnnnnn`



