# Simplot Frozen Potato Digital Twin - Demo Script

## Audience
Clarebout/Simplot engineering and operations leadership.

## Duration
15-20 minutes

---

## 1. Opening (2 min)

**Context**: Clarebout Potatoes (now part of J.R. Simplot) operates frozen potato processing plants across Belgium and France. Each plant runs multiple production lines producing french fries, hash browns, and wedges.

**Problem**: Equipment monitoring is siloed. When a fryer's oil temperature drifts, operators don't see the downstream impact on IQF freezer performance. Maintenance is reactive rather than predictive.

**Solution**: A Digital Twin that models the entire factory as a knowledge graph, connects real-time sensor data, and visualizes dependencies across all production lines.

---

## 2. Data Architecture (3 min)

Open the Databricks workspace and show:

1. **Bronze Table** (`ankit_yadav.frozen_potato.potato_sensor_bronze`)
   - 16 components across 3 production lines
   - 6 sensors per component: oil temperature, water temperature, belt speed, freezer temperature, moisture content, product weight
   - Query: `SELECT component_id, stage_id, oil_temperature, freezer_temperature FROM ankit_yadav.frozen_potato.potato_sensor_bronze LIMIT 10`

2. **Zerobus Ingestion** (show notebook 2)
   - Record-by-record streaming into Delta via Zerobus SDK
   - Supports parallel ingestion from multiple lines simultaneously
   - Serverless - no cluster management

3. **R2R Mapping Pipeline** (show notebook 3)
   - Transforms sensor readings into RDF triples
   - Each sensor value becomes a subject-predicate-object triple
   - Namespace: `http://example.com/potato-factory/`

---

## 3. Knowledge Graph (4 min)

Open the app and navigate to the **Graph Editor**:

1. **Factory Hierarchy**: Show how the graph renders:
   - Factory -> 3 Production Lines -> Processing Stages -> Components
   - Serial dependencies (upstream/downstream) within each line

2. **RDF Model**: Switch to the **RDF Model Editor**:
   - Show the Turtle ontology defining the factory structure
   - Classes: Factory, ProductionLine, ProcessingStage, Component
   - Properties: `partOf`, `dependsOn`, `propagates`, `upstream`

3. **Semantic Queries**: Show the **SPARQL Query** module:
   - "Which stages depend on the French Fries Washing stage?"
   - "What components are in the Hash Browns line?"

---

## 4. Real-Time Monitoring (4 min)

Navigate to the **Telemetry** dashboard:

1. **Component Health**: Show the health summary cards
   - Healthy / Warning / Critical counts
   - Click on a component in the graph to see its telemetry overlay

2. **Sensor Readings**: Highlight domain-specific sensors:
   - **Fryer oil at 178 C** - normal for french fry frying
   - **IQF freezer at -30 C** - nominal for IQF stage
   - **Blancher water at 85 C** - required for starch removal

3. **Fault Propagation**: If a component shows warning:
   - Show how `upstream` dependencies propagate the alert
   - If the FF-CUT (Cutter) has a belt speed anomaly, downstream stages (Blanching, Frying, IQF) are flagged

---

## 5. Lakebase Speed (3 min)

Explain the serving architecture:

1. **Delta Table** (cold storage): Full historical sensor data
2. **Lakebase** (hot serving): Latest triples synced via Synced Tables
   - Autoscaling (`CU_AUTO`) - scales to zero when idle
   - Sub-millisecond point lookups for the app
   - No PostgreSQL management needed

3. **Live demo**: Show the app loading telemetry
   - Backend queries Lakebase for latest triples
   - Frontend renders in real-time

---

## 6. Closing (2 min)

**Key Takeaways**:
- Full factory modeled as a knowledge graph with semantic relationships
- Real-time sensor data flows from plant floor to dashboard in seconds
- Fault propagation visible across entire production line
- 100% serverless on Databricks - no infrastructure to manage
- Extensible: add new lines, stages, or sensors by updating the RDF model

**Next Steps**:
- Connect real OPC-UA/Ignition data via Zerobus Station module
- Add ML-based anomaly detection on sensor streams
- Expand to multi-plant digital twin
