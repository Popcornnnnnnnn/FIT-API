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

## 📈 Response Fields (Grouped by Category)

### `basic`
| Field            | Description                   | Unit   |
|------------------|-------------------------------|--------|
| `time_info`      | Start/end time, total time, ... | -      |
| `coast_time`     | Total coasting time           | h: m: s |
| `coast_ratio`    | % of time spent coasting      | %      |
| `avg_speed`      | Average speed                 | km/h   |
| `max_speed`      | Maximum speed                 | km/h   |
| `total_distance` | Total distance                | km     |
| `elevation`      | Total elevation gain          | m      |
| `max_temperature`| Max ambient temperature       | °C    |
| `avg_temperature`| Avg ambient temperature       | °C    |
| `min_temperature`| Min ambient temperature       | °C    |

### `power`

| Field           | Description                          | Unit  |
|------------------|--------------------------------------|--------|
| `avg`            | Average power                        | watts |
| `max`            | Maximum power                        | watts |
| `NP`             | Normalized power                     | watts |
| `TSS`            | Training Stress Score                | pts   |
| `W`              | Work done                            | kJ    |
| `W_ABOVE_FTP`    | Work above FTP                       | kJ    |
| `CAL`            | Calories burned                      | kcal  |
| `acclimated`     | Adjusted power (acclimatized)        | watts |
| `nonacclimated`  | Adjusted power (non-acclimatized)    | watts |

### `heart_rate`
| Field            | Description                         | Unit |
|------------------|-------------------------------------|------|
| `avg`            | Average heart rate                  | bpm  |
| `max`            | Maximum heart rate                  | bpm  |
| `hrrc`           | Heart rate recovery capability      | bpm  |
| `decoupling`     | HR/power decoupling ratio           | -    |
| `simple_decoupling` | Simplified decoupling ratio      | -    |
| `hr_lag`         | Time delay between power and HR     | sec  |

### `cadence`
| Field       | Description         | Unit |
|-------------|---------------------|------|
| `avg`       | Average cadence     | rpm  |
| `max`       | Maximum cadence     | rpm  |
| `max_torque`| Maximum torque      | Nm   |
| `avg_torque`| Average torque      | Nm   |

### `Zones`
| Field              | Description       |
|--------------------|-------------------|
| `power_zones`      | Power zone data   |
| `heart_rate_zones` | Heart rate zones  |

### `Index`

| Field | Description           | Unit |
|-------|-----------------------|------|
| `IF`  | Intensity Factor      | -    |
| `EF`  | Efficiency Factor     | -    |
| `VI`  | Variability Index     | -    |

### `Curves`

Used for drawing graphs, it returns a list where the index represents the time axis.

| Field              | Desciption                                                   |
| ------------------ | ------------------------------------------------------------ |
| `power_curve`      | Records the best power within xx seconds.                    |
| `torque_curve`     | The calculated torque data.                                  |
| `wbal_curve`       | W' bal curve (The changes of anaerobic reserves over time).  |
| `decoupling_curve` | The variation of power/heart rate over time is used to visually represent the decoupling rate. |



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

## 📖 TODO

- [ ] 

---

## 👤 Author

Jack Wang / `@Popcornnnnn`



