# Simplot Frozen Potato Digital Twin - Technical Walkthrough

## Data Flow

```
Plant Sensors (simulated)
    |
    v
[line_data_generator.py]  -- generates pandas DataFrame
    |
    v
[Bronze Delta Table]  -- ankit_yadav.frozen_potato.potato_sensor_bronze
    |                     Columns: oil_temperature, water_temperature, belt_speed,
    |                     freezer_temperature, moisture_content, product_weight,
    |                     component_yield_output, timestamp, component_id, stage_id,
    |                     damaged_component, abnormal_sensor, line_id
    v
[R2R Mapping Pipeline]  -- Spark Declarative Pipeline (serverless)
    |                       Maps each sensor column to an RDF predicate
    |                       Subject: http://example.com/potato-factory/component-{ID}
    v
[Triples Delta Table]  -- ankit_yadav.frozen_potato.triples
    |                      Columns: s (subject), p (predicate), o (object), timestamp
    v
[Synced Table -> Lakebase]  -- simplot-potato-lakebase instance
    |                          Primary key: (s, p), timeseries key: timestamp
    |                          Snapshot scheduling policy
    v
[Databricks App]  -- simplot-potato-digital-twin
    |
    +-- Flask Backend (telemetry.py)
    |     - /api/telemetry/latest  -- queries bronze table via SQL Warehouse
    |     - /api/telemetry/triples -- queries triples via SQL Warehouse
    |     - /api/telemetry/triples/components -- grouped by component
    |
    +-- React Frontend
          - Graph Editor: vis.js force-directed graph from RDF
          - Telemetry Overlay: real-time sensor cards per component
          - SPARQL Query: semantic queries against the knowledge graph
```

## RDF Ontology Design

The ontology (`example-ttls/improved_factory_model.ttl`) defines:

### Classes
- `ex:Factory` - The plant itself
- `ex:ProductionLine` - French Fries, Hash Browns, Wedges
- `ex:ProcessingStage` - Washing, Peeling, Cutting, Blanching, Frying, IQF Freezing, etc.
- `ex:Component` - The equipment unit at each stage

### Properties
- `dt:partOf` - Containment hierarchy (component -> stage -> line -> factory)
- `dt:dependsOn` - Operational dependency (downstream depends on upstream)
- `dt:propagates` - Fault propagation (faults in upstream affect downstream)
- `ex:upstream` - Serial processing order within a line (subPropertyOf both dependsOn and propagates)
- `ex:inLine` - Stage belongs to a production line (subPropertyOf partOf)
- `ex:componentOf` - Component belongs to a stage (subPropertyOf partOf)

### Component IDs
Components use descriptive prefixes matching their line and stage:
- `FF-WASH`, `FF-PEEL`, `FF-CUT`, `FF-BLANCH`, `FF-FRY`, `FF-IQF` (French Fries)
- `HB-WASH`, `HB-PEEL`, `HB-SHRED`, `HB-FORM`, `HB-IQF` (Hash Browns)
- `WG-WASH`, `WG-CUT`, `WG-SEASON`, `WG-FRY`, `WG-IQF` (Wedges)

## R2R Mapping

The mapping pipeline (`mapping_pipeline/src/dt_mapping.py`) uses `spark-r2r` to convert tabular sensor data into RDF triples:

```python
POTATO_NS = "http://example.com/potato-factory"

# Each row becomes multiple triples:
# Subject: http://example.com/potato-factory/component-FF-WASH
# Predicates:
#   .../pred/oil_temperature -> 178.5
#   .../pred/water_temperature -> 15.2
#   .../pred/belt_speed -> 1.45
#   .../pred/freezer_temperature -> -29.8
#   .../pred/moisture_content -> 62.3
#   .../pred/product_weight -> 485.0
```

## Zerobus Integration

Two integration paths are available:

### Python SDK (Notebook 2)
The Zerobus Python SDK streams records one-by-one into the bronze table:
```python
await stream.ingest_record(PotatoSensor(
    oil_temperature=178.5,
    water_temperature=15.2,
    belt_speed=1.45,
    ...
))
```

### Ignition Module (zerobus_station/)
For production: The Zerobus Station Ignition module connects to OPC-UA servers on the plant floor and forwards tag values to Delta tables via the Zerobus ingest API.

## Lakebase Sync

The triples table is synced to Lakebase for low-latency serving:
- **Instance**: `simplot-potato-lakebase` (autoscaling with `CU_AUTO`)
- **Primary Key**: `(s, p)` - each subject-predicate pair is unique at a point in time
- **Timeseries Key**: `timestamp` - enables efficient latest-value lookups
- **Scheduling**: `SNAPSHOT` - full table sync on each pipeline run

## App Architecture

The Databricks App (`deployment-staging/`) consists of:

### Backend (Flask)
- `server.py` - Entry point, registers blueprints
- `app/blueprints/telemetry.py` - Sensor data queries
- `app/blueprints/rdf_models.py` - RDF model CRUD (stored in Lakebase)
- `app/blueprints/triples.py` - Direct triples access
- `app/db/postgres.py` - Lakebase connection with token refresh

### Frontend (React)
- `pages/Home.jsx` - Main layout with embedded RDF model
- `components/GraphEditor/` - Interactive vis.js graph visualization
- `components/TelemetryPanel/` - Real-time sensor data cards
- `components/Sidebar/` - Navigation ("Frozen Potato / Digital Twin")
- `services/rdfTripleService.js` - Semantic telemetry mapping
- `utils/telemetryFetcher.js` - Sensor definitions, health thresholds

### Sensor-to-Frontend Mapping
| Backend Column | Frontend Key | Label | Unit |
|---------------|-------------|-------|------|
| oil_temperature | sensorAReading | Oil Temperature | C |
| water_temperature | sensorBReading | Water Temperature | C |
| belt_speed | sensorCReading | Belt Speed | m/s |
| freezer_temperature | sensorDReading | Freezer Temperature | C |
| moisture_content | sensorEReading | Moisture Content | % |
| product_weight | sensorFReading | Product Weight | g |

### Health Thresholds
| Sensor | Warning | Critical |
|--------|---------|----------|
| Oil Temperature | >182 C | >190 C |
| Water Temperature | >88 C | >95 C |
| Belt Speed | >2.2 m/s | >2.5 m/s |
| Freezer Temperature | >-25 C | >-20 C |
