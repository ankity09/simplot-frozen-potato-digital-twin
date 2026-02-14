# Simplot Frozen Potato Digital Twin

A customized IoT Digital Twin demo for **Clarebout/Simplot** (frozen potato manufacturer), built on the Databricks [Digital Twin Solution Accelerator](https://github.com/databricks-industry-solutions/digital-twin).

## Architecture

```
Potato Factory Sensors
        |
        v
  [Zerobus Ingest SDK]  -->  [Delta Bronze Table]
                                     |
                              [R2R Mapping Pipeline (SDP)]
                                     |
                                     v
                              [RDF Triples Table]
                                     |
                              [Synced Table -> Lakebase]
                                     |
                              [Databricks App]
                               Flask + React
                              (Graph + Telemetry UI)
```

## Production Lines

| Line | Product | Stages | Components |
|------|---------|--------|------------|
| 1 | French Fries | Washing -> Peeling -> Cutting -> Blanching -> Frying -> IQF Freezing | 6 |
| 2 | Hash Browns | Washing -> Peeling -> Shredding -> Forming -> IQF Freezing | 5 |
| 3 | Wedges | Washing -> Cutting -> Seasoning -> Frying -> IQF Freezing | 5 |

**Total: 16 components across 3 lines**

## Sensors (per component)

| Sensor | Column | Typical Range | Unit |
|--------|--------|---------------|------|
| Oil Temperature | `oil_temperature` | 170-185 C (fryers), ~20 C (non-fryer) | C |
| Water Temperature | `water_temperature` | 10-20 C (washers), 80-90 C (blanchers) | C |
| Belt Speed | `belt_speed` | 1.0-2.0 | m/s |
| Freezer Temperature | `freezer_temperature` | -35 to -25 C (IQF), ~20 C (non-freezer) | C |
| Moisture Content | `moisture_content` | 50-80 | % |
| Product Weight | `product_weight` | 400-600 | g |

## Tech Stack

- **Data Generation**: Custom Python generator with `mandrova` library
- **Ingestion**: Zerobus Ingest SDK (record-by-record, serverless)
- **Storage**: Delta Lake on Unity Catalog (`ankit_yadav.frozen_potato`)
- **Knowledge Graph**: RDF/Turtle ontology mapped via `spark-r2r`
- **Serving**: Lakebase (autoscaling PostgreSQL) for low-latency queries
- **App**: Databricks App (Flask backend + React frontend)
- **Compute**: 100% serverless (no clusters)

## Quick Start

### 1. Run notebooks in order

All notebooks run on **serverless compute** - no cluster needed.

```
0-Parameters.ipynb                  # Configuration (already set for ankit_yadav.frozen_potato)
1-Create-Sensor-Bronze-Table.ipynb  # Create table + generate data
2-Ingest-Data-Zerobus.ipynb         # (Optional) Stream data via Zerobus
3-Setup-Mapping-Pipeline.ipynb      # Deploy R2R mapping pipeline
4-Sync-To-Lakebase.ipynb            # Create Lakebase instance + synced table
5-Create-App.ipynb                  # Deploy Databricks App
```

### 2. Access the app

The app deploys to: `https://simplot-potato-digital-twin-<workspace>.databricks.app`

### 3. Cleanup

Run `6-Cleanup.ipynb` to tear down all resources.

## Project Structure

```
frozen-potato-digital-twin/
  0-Parameters.ipynb              # All configuration parameters
  1-Create-Sensor-Bronze-Table.ipynb
  2-Ingest-Data-Zerobus.ipynb
  3-Setup-Mapping-Pipeline.ipynb
  4-Sync-To-Lakebase.ipynb
  5-Create-App.ipynb
  6-Cleanup.ipynb
  line_data_generator/            # Frozen potato data generator module
  mapping_pipeline/src/           # R2R mapping (sensor -> RDF triples)
  example-ttls/                   # RDF ontology definitions
  frontend/                       # React frontend source
  serving-app/                    # Flask backend source
  deployment-staging/             # Pre-built app bundle for deployment
  zerobus_station/                # Zerobus Ignition connector (reference)
  zerobus_config/                 # Zerobus SDK configuration
```

## Workspace

- **Workspace**: `fe-sandbox-serverless-lakebase`
- **Catalog**: `ankit_yadav`
- **Schema**: `frozen_potato`
- **Lakebase Instance**: `simplot-potato-lakebase`
- **App Name**: `simplot-potato-digital-twin`

## RDF Namespace

All RDF entities use the namespace `http://example.com/potato-factory/`.

Component IRIs follow the pattern: `http://example.com/potato-factory/component-{ID}` where ID matches the component prefix (e.g., `FF-WASH`, `HB-SHRED`, `WG-FRY`).
