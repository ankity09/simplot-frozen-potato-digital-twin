"""
Standalone script to generate the potato_sensor_bronze Delta table.
Runs on Databricks serverless compute via spark_python_task.
"""
import subprocess
import sys

# Install dependencies from UC Volume
subprocess.check_call([
    sys.executable, "-m", "pip", "install",
    "/Volumes/ankit_yadav/frozen_potato/wheels/mandrova-0.1-py3-none-any.whl",
    "/Volumes/ankit_yadav/frozen_potato/wheels/line_data_generator-0.1.0-py3-none-any.whl",
])

# Now import after install
import time
from pyspark.sql import SparkSession
from line_data_generator import generate_all_lines, generate_equipment_mapping, table_size_estimator

# ---------- Parameters ----------
CATALOG = "ankit_yadav"
SCHEMA = "frozen_potato"
BRONZE_TABLE_NAME = "potato_sensor_bronze"
BRONZE_TABLE = f"{CATALOG}.{SCHEMA}.{BRONZE_TABLE_NAME}"

# ---------- Spark session ----------
spark = SparkSession.builder.getOrCreate()

# ---------- Step 1: Create table ----------
spark.sql(f"""
CREATE OR REPLACE TABLE {BRONZE_TABLE} (
    oil_temperature DOUBLE,
    water_temperature DOUBLE,
    belt_speed DOUBLE,
    freezer_temperature DOUBLE,
    moisture_content DOUBLE,
    product_weight DOUBLE,
    component_yield_output DOUBLE,
    timestamp STRING,
    component_id STRING,
    stage_id STRING,
    damaged_component BOOLEAN,
    abnormal_sensor STRING,
    line_id STRING
)
""")
print(f"Created table {BRONZE_TABLE}")

# ---------- Step 2: Generate initial batch (1000 samples) ----------
num_lines = 3
machines_per_line = [6, 5, 5]
num_components = 1
sample_size = 1000

equipment_mapping = generate_equipment_mapping(num_lines, machines_per_line, num_components)
tot_num_rows, est_table_size, _, _ = table_size_estimator(machines_per_line, num_components, sample_size)
print(f"Generating {tot_num_rows} rows (~{est_table_size:.2f} MB)")

batch_df_lines = generate_all_lines(equipment_mapping, sample_size, time.time())
spark.createDataFrame(batch_df_lines).write.mode("append").saveAsTable(BRONZE_TABLE)
print(f"Initial batch written to {BRONZE_TABLE}")

# ---------- Step 3: Generate additional batches (5 x 10000 samples) ----------
sample_size = 10000
batch_count = 5

tot_num_rows, est_table_size, _, _ = table_size_estimator(machines_per_line, num_components, sample_size)
print(f"Generating {batch_count} batches of {tot_num_rows} rows each")

min_batch_wait = sample_size * 0.001

for i in range(batch_count):
    current_time = time.time()
    if i > 0:
        if current_time <= batch_time + min_batch_wait:
            wait = int(batch_time + min_batch_wait - current_time + 10)
            time.sleep(wait)
            print(f"Pausing {wait} seconds to avoid overlapping timestamps")

    print(f"--- Generating batch {i+1} / {batch_count} ---")
    batch_time = time.time()
    batch = generate_all_lines(equipment_mapping, sample_size, batch_time)
    spark.createDataFrame(batch).write.mode("append").saveAsTable(BRONZE_TABLE)

count = spark.table(BRONZE_TABLE).count()
print(f"Done! Total rows in {BRONZE_TABLE}: {count}")
