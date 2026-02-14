# Why Are the Graphs Empty? - Setup Guide

## What This Application Actually Does

### **Purpose: Digital Twin for Frozen Potato Manufacturing**

This is NOT just a dashboard - it's a **semantic knowledge graph** of an entire frozen potato processing plant.

### **The Business Problem**
- **Siloed Monitoring**: When a fryer's oil temperature drifts, operators don't see the downstream impact on IQF freezer performance
- **Reactive Maintenance**: Equipment failures cascade through the production line
- **No Dependency Visibility**: Can't trace which components depend on each other

### **The Solution**
A Digital Twin that models the factory as a **knowledge graph**:
```
Factory
  ├── French Fries Production Line
  │   ├── Washing (FF-WASH) → Peeling (FF-PEEL) → Cutting (FF-CUT) → Blanching (FF-BLANCH) → Frying (FF-FRY) → IQF Freezing (FF-IQF)
  │   └── Each component has 6 sensors: oil temp, water temp, belt speed, freezer temp, moisture, weight
  ├── Hash Browns Production Line
  │   └── Washing → Peeling → Shredding → Forming → IQF Freezing
  └── Wedges Production Line
      └── Washing → Cutting → Seasoning → Frying → IQF Freezing
```

---

## What is RDF (Resource Description Framework)?

RDF is a way to represent relationships as **triples**:
- **Subject** → **Predicate** → **Object**
- Example: `FF-WASH` → `upstream` → `FF-PEEL`

This creates a **semantic graph** where you can query:
- "Which stages depend on FF-WASH?"
- "If FF-CUT fails, what downstream components are affected?"
- "Show me all components in the French Fries line"

---

## Why Are the Graphs Empty?

The graphs are empty because the **RDF triples data hasn't been generated yet**.

### **Current State**
✅ App is deployed and running
✅ Frontend components (Dashboard, Analytics, Logs) are working
✅ Database tables exist
❌ **RDF triples table is EMPTY** - no graph data has been generated
❌ **Mapping pipeline hasn't been run** - sensor data hasn't been converted to RDF triples

### **What Needs to Happen**

The setup process requires running 5 notebooks in order:

```
1. 0-Parameters.ipynb                 ✅ Already configured
2. 1-Create-Sensor-Bronze-Table.ipynb ❓ Need to check if bronze table has data
3. 2-Ingest-Data-Zerobus.ipynb        ❓ Optional - for streaming data
4. 3-Setup-Mapping-Pipeline.ipynb     ❌ NOT RUN - This generates the RDF triples!
5. 4-Sync-To-Lakebase.ipynb           ❓ Lakebase instance exists but may need sync
6. 5-Create-App.ipynb                 ✅ Already done (app is deployed)
```

---

## The Data Flow Pipeline

### **Step 1: Sensor Data → Bronze Table**
```python
# Generate sensor readings for 16 components
component_id | stage_id | oil_temperature | water_temperature | belt_speed | freezer_temperature | moisture_content | product_weight
-------------|----------|-----------------|-------------------|------------|---------------------|------------------|----------------
FF-WASH      | washing  | 20.5           | 15.2              | 1.5        | 22.0                | 75.3             | 520
FF-FRY       | frying   | 178.3          | 18.5              | 1.8        | 21.5                | 42.1             | 485
```

### **Step 2: R2R Mapping Pipeline → RDF Triples**
The mapping pipeline transforms sensor data into semantic triples:

```turtle
# Component definition
<http://example.com/potato-factory/component-FF-WASH> a <http://example.com/potato-factory/Component> .
<http://example.com/potato-factory/component-FF-WASH> rdfs:label "FF-WASH" .

# Relationship to stage
<http://example.com/potato-factory/component-FF-WASH> ex:componentOf <http://example.com/potato-factory/stage-ff-washing> .

# Upstream dependency
<http://example.com/potato-factory/stage-ff-peeling> ex:upstream <http://example.com/potato-factory/stage-ff-washing> .

# Sensor reading
<http://example.com/potato-factory/component-FF-WASH> dt:hasOilTemperature "20.5"^^xsd:float .
<http://example.com/potato-factory/component-FF-WASH> dt:hasWaterTemperature "15.2"^^xsd:float .
```

### **Step 3: Triples Table → Lakebase**
Synced Tables automatically sync the latest triples to Lakebase (PostgreSQL) for low-latency serving.

### **Step 4: App Queries → Graph Visualization**
The React frontend queries the backend, which reads from Lakebase and renders the graph.

---

## Why the Graph Editor and Graph Viewer Are Important

### **Graph Editor**
- **Interactive visualization** of the factory hierarchy
- Click on nodes to see telemetry overlays with sensor readings
- Shows **upstream/downstream dependencies** visually
- Highlights components in warning/critical state

### **Graph Viewer**
- Alternative visualization showing the current state
- Based on the **latest RDF model** from the triples database
- Shows real-time updates as sensor data changes

### **RDF Model Editor**
- Edit the **ontology** that defines the factory structure
- Add new components, stages, or production lines
- Define custom relationships (e.g., `dependsOn`, `propagates`)
- Save and load different factory configurations

### **SPARQL Query Interface**
- **Semantic queries** over the knowledge graph
- Example queries:
  ```sparql
  # Find all stages that depend on FF-WASH
  SELECT ?stage WHERE {
    ?stage ex:upstream <http://example.com/potato-factory/stage-ff-washing> .
  }

  # Find all components in the French Fries line
  SELECT ?component WHERE {
    ?component ex:componentOf ?stage .
    ?stage ex:inLine <http://example.com/potato-factory/line-french-fries> .
  }
  ```

---

## What You Need to Do

### **Option 1: Upload and Run the Setup Notebooks** (Recommended)

1. Upload the notebooks to the workspace:
   ```bash
   databricks workspace import-dir . /Workspace/Users/ankit.yadav@databricks.com/frozen-potato-digital-twin --profile serverless-lakebase
   ```

2. Run notebooks in order:
   - `1-Create-Sensor-Bronze-Table.ipynb` - Generate sensor data
   - `3-Setup-Mapping-Pipeline.ipynb` - Convert sensor data to RDF triples
   - `4-Sync-To-Lakebase.ipynb` - Ensure sync is active

3. Refresh the app - the graphs should now populate!

### **Option 2: Generate Mock Data Locally**

If the notebooks aren't ready, I can:
1. Generate mock RDF triples data
2. Insert it directly into the database
3. The graphs will populate immediately

### **Option 3: Use Static RDF Model**

The app currently has a **static RDF model** built into the frontend (you saw this in the RDF Model Editor with 109 nodes). This model defines:
- 3 production lines
- 16 components
- All upstream/downstream relationships

**Problem**: The static model isn't being visualized in the Graph Editor because the frontend is trying to load from the (empty) database first.

---

## Quick Fix: Make Graphs Work Now

I can modify the frontend to:
1. **Always render the static RDF model** in the Graph Editor
2. Add mock telemetry data to the graph nodes
3. Make the graphs interactive even without database data

This would let you demo the graph visualization immediately while the backend data pipeline is being set up.

---

## The 3D Viewer Issue

The 3D Viewer is showing a placeholder because:
- It's meant to show a **3D model of the factory floor**
- Requires 3D asset files (GLB/GLTF format) or procedural generation
- Was likely a stretch goal for the demo

**Options**:
1. Add a simple 3D scene using Three.js
2. Use a 2.5D isometric view of the production lines
3. Replace it with an enhanced 2D layout diagram

---

## Summary

### **What Works Now**
✅ App is deployed and accessible
✅ Backend API is connected (after fixing app.yaml)
✅ Dashboard, Analytics, and System Logs components
✅ Static RDF model is defined in the frontend
✅ Lakebase and warehouse resources are configured

### **What Needs Work**
❌ RDF triples table is empty (need to run mapping pipeline)
❌ Graph Editor shows no nodes (waiting for triples data)
❌ Graph Viewer shows no nodes (waiting for triples data)
❌ 3D Viewer is a placeholder (needs implementation)
❌ SPARQL queries return empty results (no triples to query)

### **Recommended Next Steps**
1. **Immediate**: Make graphs work with static data (quick frontend fix)
2. **Short-term**: Run notebooks 1, 3, 4 to generate real RDF triples
3. **Medium-term**: Implement or enhance 3D viewer
4. **Long-term**: Connect to real OPC-UA/Ignition data streams

---

Would you like me to:
1. **Fix the graphs now** by making them render the static RDF model?
2. **Upload and run the notebooks** to generate real triples data?
3. **Implement a better 3D viewer**?
4. **All of the above**?
