


# COMMAND ----------

from mandrova.data_generator import SensorDataGenerator as sdg
import numpy as np
import pandas as pd
import random
import time
from datetime import datetime, timedelta
import uuid

# COMMAND ----------

# ============================================================================
# Frozen Potato Factory - Production Line Configuration
# ============================================================================
# Simplot / Clarebout frozen potato processing plant
#
# 3 Production Lines, each with sequential processing stages:
#   - French Fries: Washing → Peeling → Cutting → Blanching → Frying → IQF Freezing
#   - Hash Browns:  Washing → Peeling → Shredding → Forming → IQF Freezing
#   - Wedges:       Washing → Cutting → Seasoning → Frying → IQF Freezing
#
# Each stage has 1 component (the main equipment unit).
# Each component has 6 sensors:
#   oil_temperature, water_temperature, belt_speed,
#   freezer_temperature, moisture_content, product_weight
# ============================================================================

PRODUCTION_LINES = [
    {
        "line_name": "French Fries",
        "stages": [
            {"stage_name": "Washing",    "component_prefix": "FF-WASH"},
            {"stage_name": "Peeling",    "component_prefix": "FF-PEEL"},
            {"stage_name": "Cutting",    "component_prefix": "FF-CUT"},
            {"stage_name": "Blanching",  "component_prefix": "FF-BLANCH"},
            {"stage_name": "Frying",     "component_prefix": "FF-FRY"},
            {"stage_name": "IQF Freezing", "component_prefix": "FF-IQF"},
        ],
    },
    {
        "line_name": "Hash Browns",
        "stages": [
            {"stage_name": "Washing",    "component_prefix": "HB-WASH"},
            {"stage_name": "Peeling",    "component_prefix": "HB-PEEL"},
            {"stage_name": "Shredding",  "component_prefix": "HB-SHRED"},
            {"stage_name": "Forming",    "component_prefix": "HB-FORM"},
            {"stage_name": "IQF Freezing", "component_prefix": "HB-IQF"},
        ],
    },
    {
        "line_name": "Wedges",
        "stages": [
            {"stage_name": "Washing",    "component_prefix": "WG-WASH"},
            {"stage_name": "Cutting",    "component_prefix": "WG-CUT"},
            {"stage_name": "Seasoning",  "component_prefix": "WG-SEASON"},
            {"stage_name": "Frying",     "component_prefix": "WG-FRY"},
            {"stage_name": "IQF Freezing", "component_prefix": "WG-IQF"},
        ],
    },
]

# Sensor configurations per stage type
# Each sensor has: base value, sigma (noise), and sin_step (cyclic drift)
SENSOR_PROFILES = {
    "Washing": {
        "oil_temperature":    {"base": 20.0,  "sigma": 0.5, "sin_step": 0.0},
        "water_temperature":  {"base": 15.0,  "sigma": 1.0, "sin_step": 0.05},
        "belt_speed":         {"base": 1.5,   "sigma": 0.1, "sin_step": 0.02},
        "freezer_temperature":{"base": 20.0,  "sigma": 0.3, "sin_step": 0.0},
        "moisture_content":   {"base": 80.0,  "sigma": 2.0, "sin_step": 0.01},
        "product_weight":     {"base": 500.0, "sigma": 15.0,"sin_step": 0.0},
    },
    "Peeling": {
        "oil_temperature":    {"base": 20.0,  "sigma": 0.5, "sin_step": 0.0},
        "water_temperature":  {"base": 18.0,  "sigma": 1.0, "sin_step": 0.03},
        "belt_speed":         {"base": 1.2,   "sigma": 0.08,"sin_step": 0.02},
        "freezer_temperature":{"base": 20.0,  "sigma": 0.3, "sin_step": 0.0},
        "moisture_content":   {"base": 75.0,  "sigma": 2.5, "sin_step": 0.01},
        "product_weight":     {"base": 450.0, "sigma": 12.0,"sin_step": 0.0},
    },
    "Cutting": {
        "oil_temperature":    {"base": 20.0,  "sigma": 0.5, "sin_step": 0.0},
        "water_temperature":  {"base": 16.0,  "sigma": 0.8, "sin_step": 0.02},
        "belt_speed":         {"base": 1.8,   "sigma": 0.12,"sin_step": 0.03},
        "freezer_temperature":{"base": 20.0,  "sigma": 0.3, "sin_step": 0.0},
        "moisture_content":   {"base": 68.0,  "sigma": 2.0, "sin_step": 0.01},
        "product_weight":     {"base": 480.0, "sigma": 18.0,"sin_step": 0.0},
    },
    "Blanching": {
        "oil_temperature":    {"base": 22.0,  "sigma": 0.8, "sin_step": 0.0},
        "water_temperature":  {"base": 85.0,  "sigma": 2.0, "sin_step": 0.1},
        "belt_speed":         {"base": 1.0,   "sigma": 0.05,"sin_step": 0.01},
        "freezer_temperature":{"base": 20.0,  "sigma": 0.3, "sin_step": 0.0},
        "moisture_content":   {"base": 72.0,  "sigma": 2.0, "sin_step": 0.02},
        "product_weight":     {"base": 460.0, "sigma": 10.0,"sin_step": 0.0},
    },
    "Frying": {
        "oil_temperature":    {"base": 178.0, "sigma": 3.0, "sin_step": 0.15},
        "water_temperature":  {"base": 20.0,  "sigma": 0.5, "sin_step": 0.0},
        "belt_speed":         {"base": 1.3,   "sigma": 0.08,"sin_step": 0.02},
        "freezer_temperature":{"base": 20.0,  "sigma": 0.3, "sin_step": 0.0},
        "moisture_content":   {"base": 55.0,  "sigma": 3.0, "sin_step": 0.05},
        "product_weight":     {"base": 420.0, "sigma": 15.0,"sin_step": 0.0},
    },
    "IQF Freezing": {
        "oil_temperature":    {"base": 20.0,  "sigma": 0.3, "sin_step": 0.0},
        "water_temperature":  {"base": 12.0,  "sigma": 0.5, "sin_step": 0.0},
        "belt_speed":         {"base": 1.0,   "sigma": 0.05,"sin_step": 0.01},
        "freezer_temperature":{"base": -30.0, "sigma": 2.0, "sin_step": 0.1},
        "moisture_content":   {"base": 58.0,  "sigma": 1.5, "sin_step": 0.01},
        "product_weight":     {"base": 500.0, "sigma": 10.0,"sin_step": 0.0},
    },
    "Shredding": {
        "oil_temperature":    {"base": 20.0,  "sigma": 0.5, "sin_step": 0.0},
        "water_temperature":  {"base": 16.0,  "sigma": 0.8, "sin_step": 0.02},
        "belt_speed":         {"base": 2.0,   "sigma": 0.15,"sin_step": 0.03},
        "freezer_temperature":{"base": 20.0,  "sigma": 0.3, "sin_step": 0.0},
        "moisture_content":   {"base": 70.0,  "sigma": 2.0, "sin_step": 0.01},
        "product_weight":     {"base": 440.0, "sigma": 14.0,"sin_step": 0.0},
    },
    "Forming": {
        "oil_temperature":    {"base": 22.0,  "sigma": 0.8, "sin_step": 0.0},
        "water_temperature":  {"base": 18.0,  "sigma": 0.6, "sin_step": 0.01},
        "belt_speed":         {"base": 1.0,   "sigma": 0.06,"sin_step": 0.02},
        "freezer_temperature":{"base": 20.0,  "sigma": 0.3, "sin_step": 0.0},
        "moisture_content":   {"base": 62.0,  "sigma": 2.5, "sin_step": 0.02},
        "product_weight":     {"base": 460.0, "sigma": 12.0,"sin_step": 0.0},
    },
    "Seasoning": {
        "oil_temperature":    {"base": 22.0,  "sigma": 0.8, "sin_step": 0.0},
        "water_temperature":  {"base": 17.0,  "sigma": 0.6, "sin_step": 0.01},
        "belt_speed":         {"base": 1.4,   "sigma": 0.08,"sin_step": 0.02},
        "freezer_temperature":{"base": 20.0,  "sigma": 0.3, "sin_step": 0.0},
        "moisture_content":   {"base": 60.0,  "sigma": 2.0, "sin_step": 0.02},
        "product_weight":     {"base": 510.0, "sigma": 16.0,"sin_step": 0.0},
    },
}

SENSOR_NAMES = [
    "oil_temperature",
    "water_temperature",
    "belt_speed",
    "freezer_temperature",
    "moisture_content",
    "product_weight",
]

# COMMAND ----------

def generate_equipment_mapping(num_lines=None, machines_per_line=None, num_components=None, num_sensors=6):
    """Generate equipment mapping for the frozen potato factory.

    Parameters are accepted for API compatibility with original code but
    the actual structure is driven by PRODUCTION_LINES config.
    """
    equipment_mapping = {"lines": []}

    for line_idx, line_config in enumerate(PRODUCTION_LINES):
        line_id = str(line_idx + 1)
        line = {
            "line_id": line_id,
            "line_name": line_config["line_name"],
            "stages": [],
            "machines": [],  # kept for compatibility
        }

        for stage_idx, stage_config in enumerate(line_config["stages"]):
            stage_id = f"{line_id}-{stage_idx + 1}"
            component_id = stage_config["component_prefix"]
            stage_name = stage_config["stage_name"]

            stage = {
                "stage_id": stage_id,
                "stage_name": stage_name,
                "component_id": component_id,
                "component_prefix": stage_config["component_prefix"],
            }
            line["stages"].append(stage)

            # Also populate machines list for backward compat
            machine = {
                "machine_id": stage_id,
                "machine_name": stage_name,
                "components": [{"component_id": component_id, "sensors": SENSOR_NAMES}],
            }
            line["machines"].append(machine)

        equipment_mapping["lines"].append(line)

    # Sensor config for backward compat
    sensors_config = [
        {"name": "oil_temperature",    "sin_step": 0,    "sigma": 1},
        {"name": "water_temperature",  "sin_step": 0,    "sigma": 1},
        {"name": "belt_speed",         "sin_step": 0.1,  "sigma": 0.1},
        {"name": "freezer_temperature","sin_step": 0,    "sigma": 1},
        {"name": "moisture_content",   "sin_step": 0.01, "sigma": 2},
        {"name": "product_weight",     "sin_step": 0.2,  "sigma": 10},
    ]
    equipment_mapping["sensors_config"] = sensors_config

    return equipment_mapping

# COMMAND ----------

def table_size_estimator(machines_per_line=None, num_components=None, sample_size=1000):
    """Estimate table size based on frozen potato factory layout."""
    # Count total components across all lines
    total_components = sum(len(line["stages"]) for line in PRODUCTION_LINES)
    tot_num_rows = total_components * sample_size
    est_table_size = float(tot_num_rows * 500 / (1024 ** 2))  # ~500 bytes per row

    line_num_rows = []
    est_line_table_size = []
    for line_config in PRODUCTION_LINES:
        num_stages = len(line_config["stages"])
        rows = num_stages * sample_size
        size = float(rows * 500 / (1024 ** 2))
        line_num_rows.append(rows)
        est_line_table_size.append(size)

    return tot_num_rows, est_table_size, line_num_rows, est_line_table_size

# COMMAND ----------

def generate_sensor_data(component_id, sensor_name, sensor_profile, faulty=False, sample_size=1000):
    """Generate data for a single sensor using realistic potato factory ranges."""
    dg = sdg()
    rd = random.Random()
    # Seed from component_id string hash for reproducibility
    seed_val = hash(component_id + sensor_name) % (2**31)
    rd.seed(seed_val)
    dg.seed(seed_val)

    base = sensor_profile["base"]
    sigma = sensor_profile["sigma"]
    sin_step = sensor_profile["sin_step"]

    # Faulty components have more noise
    if faulty:
        sigma *= rd.uniform(1.5, 3.0)

    # Generate noise around zero
    dg.generation_input.add_option(sensor_names="normal", distribution="normal", mu=0, sigma=sigma)
    # Generate cyclic drift
    dg.generation_input.add_option(sensor_names="sin", eq=f"2*exp(sin(t))", initial={"t": 0}, step={"t": sin_step})
    dg.generate(sample_size)
    dg.sum(sensors=["normal", "sin"], save_to="combined")

    # Shift to base value (subtract the sin mean ~2.27 so oscillation is around base)
    values = dg.data["combined"] + base - 2.27

    if faulty:
        # Inject outliers
        n_outliers = int(sample_size * 0.12)
        if sensor_name == "oil_temperature" and base > 100:
            outlier_values = np.random.uniform(base + 15, base + 30, n_outliers)
        elif sensor_name == "freezer_temperature" and base < 0:
            outlier_values = np.random.uniform(base + 10, base + 20, n_outliers)
        else:
            outlier_values = np.random.uniform(base - 3 * sigma, base + 3 * sigma, n_outliers)
        indices = np.sort(np.random.randint(0, sample_size - 1, n_outliers))
        for idx, val in zip(indices, outlier_values):
            values.iloc[idx] = val

    return values

# COMMAND ----------

def generate_component_data(component_id, stage_name, component_count, stage_idx, sample_size, current_time, frequency_sec=0.001):
    """Generate data for a single component (processing stage equipment)."""
    rd = random.Random()
    seed_val = hash(component_id) % (2**31)
    rd.seed(seed_val)

    # Determine if this component is damaged (~30% chance for non-critical stages)
    damaged = rd.random() < 0.3

    sensor_profile = SENSOR_PROFILES.get(stage_name, SENSOR_PROFILES["Washing"])

    df = pd.DataFrame()
    damaged_sensors = []

    for sensor_name in SENSOR_NAMES:
        profile = sensor_profile[sensor_name]

        # Only first sensor of a damaged component gets faulty readings
        faulty = damaged and len(damaged_sensors) == 0 and rd.random() > 0.5
        if faulty:
            damaged_sensors.append(sensor_name)

        df[sensor_name] = generate_sensor_data(
            component_id, sensor_name, profile, faulty, sample_size
        )

    # Component yield output
    dg = sdg()
    factor = 50 if damaged else 30
    dg.generation_input.add_option(
        sensor_names="energy", eq="x", initial={"x": 0},
        step={"x": np.absolute(np.random.randn(sample_size).cumsum() / factor)}
    )
    dg.generate(sample_size, seed=rd.uniform(0, 10000))
    df["component_yield_output"] = dg.data["energy"]

    # Generate timestamps
    timestamps = [current_time + i * frequency_sec for i in range(sample_size)]
    formatted_timestamps = [
        datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        for ts in timestamps
    ]
    df["timestamp"] = formatted_timestamps

    # Metadata columns
    df["component_id"] = component_id
    df["stage_id"] = stage_name
    df["damaged_component"] = damaged
    df["abnormal_sensor"] = "None" if len(damaged_sensors) == 0 else damaged_sensors[0]

    return df

# COMMAND ----------

def generate_line(line_number, equipment_mapping, sample_size, current_time, frequency_sec=0.001):
    """Generate data for a single production line."""
    df_line = pd.DataFrame()
    line_data = equipment_mapping["lines"][line_number]
    stages = line_data["stages"]
    component_count = len(stages)

    for stage_idx, stage in enumerate(stages):
        component_id = stage["component_id"]
        stage_name = stage["stage_name"]

        df_component = generate_component_data(
            component_id, stage_name, component_count, stage_idx,
            sample_size, current_time, frequency_sec
        )
        df_line = pd.concat([df_line, df_component], ignore_index=True)

    # Add line_id (deterministic UUID from line number)
    line_id = int(line_data["line_id"])
    rd = random.Random()
    rd.seed(line_id)
    df_line["line_id"] = str(uuid.UUID(int=rd.getrandbits(128)))

    return df_line

# COMMAND ----------

def generate_all_lines(equipment_mapping, sample_size, current_time, frequency_sec=0.001):
    """Generate data for all production lines."""
    line_count = len(equipment_mapping["lines"])
    df_lines = pd.DataFrame()

    for line_number in range(line_count):
        df_line = generate_line(line_number, equipment_mapping, sample_size, current_time, frequency_sec)
        df_lines = pd.concat([df_lines, df_line], ignore_index=True)

    return df_lines
