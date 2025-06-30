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

## 📈 响应字段（按类别分组）

### `Basic`（基础信息）

| 字段名            | 说明                         | 单位     |
| ----------------- | ---------------------------- | -------- |
| `time_info`       | 开始时间 / 结束时间 / 总时长 | -        |
| `coast_time`      | 溜车总时间                   | 时:分:秒 |
| `coast_ratio`     | 溜车时间占比（百分比）       | %        |
| `avg_speed`       | 平均速度                     | km/h     |
| `max_speed`       | 最大速度                     | km/h     |
| `total_distance`  | 总骑行距离                   | km       |
| `elevation`       | 总爬升海拔                   | m        |
| `max_temperature` | 最高环境温度                 | °C       |
| `avg_temperature` | 平均环境温度                 | °C       |
| `min_temperature` | 最低环境温度                 | °C       |



------

### `Power`（功率相关）

| 字段名          | 说明                                  | 单位 |
| --------------- | ------------------------------------- | ---- |
| `avg`           | 平均功率                              | 瓦特 |
| `max`           | 最大功率                              | 瓦特 |
| `NP`            | 标准化功率（Normalized Power）        | 瓦特 |
| `TSS`           | 训练压力分数（Training Stress Score） | 分   |
| `W`             | 总功                                  | kJ   |
| `W_ABOVE_FTP`   | 高于FTP的做功                         | kJ   |
| `CAL`           | 卡路里消耗                            | kcal |
| `acclimated`    | 高热适应状态下的调整功率              | 瓦特 |
| `nonacclimated` | 非热适应状态下的调整功率              | 瓦特 |



------

### `HeartRate`（心率相关）

| 字段名              | 说明                              | 单位 |
| ------------------- | --------------------------------- | ---- |
| `avg`               | 平均心率                          | bpm  |
| `max`               | 最大心率                          | bpm  |
| `hrrc`              | 心率恢复能力                      | bpm  |
| `decoupling`        | 功率与心率脱耦比（HR decoupling） | -    |
| `simple_decoupling` | 简化版的脱耦比                    | -    |
| `hr_lag`            | 功率与心率的响应延迟              | 秒   |



------

### `Cadence`（踏频相关）

| 字段名       | 说明     | 单位 |
| ------------ | -------- | ---- |
| `avg`        | 平均踏频 | rpm  |
| `max`        | 最大踏频 | rpm  |
| `max_torque` | 最大扭矩 | Nm   |
| `avg_torque` | 平均扭矩 | Nm   |



------

### `Zones`（分区数据）

| 字段名             | 说明         |
| ------------------ | ------------ |
| `power_zones`      | 功率区间统计 |
| `heart_rate_zones` | 心率区间统计 |



------

### `Index`（强度指标）

| 字段名 | 说明                          | 单位 |
| ------ | ----------------------------- | ---- |
| `IF`   | 强度因子（Intensity Factor）  | -    |
| `EF`   | 效率因子（Efficiency Factor） | -    |
| `VI`   | 变异指数（Variability Index） | -    |



------

### `Curves`（用于绘图的曲线数据）

这些字段是用于前端绘图的数组，索引表示时间轴。

| 字段名             | 说明                                        |
| ------------------ | ------------------------------------------- |
| `power_curve`      | 各时间长度（秒）内的最佳功率曲线            |
| `torque_curve`     | 每一时刻的扭矩计算值                        |
| `wbal_curve`       | 无氧储备（W'）的变化曲线                    |
| `decoupling_curve` | 功率/心率比值随时间变化的曲线（表示脱耦率） |

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



