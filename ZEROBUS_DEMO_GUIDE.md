# Zerobus Integration - Complete Demo Guide

## 🚀 What is Zerobus in This Project?

**Zerobus** is Databricks' managed real-time ingestion service for streaming IoT/OT data into Delta tables without running Kafka infrastructure. In the Frozen Potato Digital Twin, it simulates **real-time sensor data streaming** from a potato processing factory.

### ⚠️ Zerobus Availability Notice

**Status**: Zerobus is in **Public Preview** (as of January 2026) and may not be enabled in all workspaces.

**If you get `StatusCode.UNIMPLEMENTED` error**:
- Zerobus is not enabled in your workspace
- Contact your Databricks account team to enable it
- **Alternative**: Use Notebook 1 instead (generates same data without Zerobus)

**Alternative Demo Path** (if Zerobus unavailable):
- Run **Notebook 1** to generate sensor data directly
- Same outcome: sensor readings in bronze table
- For customer, say: "This simulates the data that would stream through Zerobus in production"

## 🏗️ Architecture Overview

```
Plant Floor Sensors → Zerobus Ingest → Delta Bronze Table → R2R Pipeline → RDF Triples → Lakebase → App
```

**Two Integration Paths:**

1. **Python SDK** (Notebook 2) - For demos/testing
2. **Ignition Gateway Module** (Production) - For real factory deployments

---

## 🎬 Demo Scenario for Customer

### **Story**: Real-time IoT monitoring for frozen potato manufacturing

**Customer problem**: "We have 16 components across 3 production lines (French Fries, Hash Browns, Wedges) generating sensor data every millisecond. We need to:
- Ingest data in real-time (no batch delays)
- Build a knowledge graph for root cause analysis
- Serve low-latency queries to operators
- All without managing Kafka/message queue infrastructure"

**Solution**: Databricks Zerobus + Delta + Lakebase + Digital Twin App

---

## 📋 Demo Steps for Customer Meeting

### **Setup (5 minutes before demo)**

1. **Open the notebook in workspace UI**:
   - Navigate to: `/Users/ankit.yadav@databricks.com/frozen-potato-digital-twin/2-Ingest-Data-Zerobus`
   - Attach to serverless compute

2. **Set sample size** (adjust based on demo time):
   ```python
   # For quick demo (30 seconds): sample_size = 1000 → 16,000 rows
   # For longer demo (2-3 min): sample_size = 10000 → 160,000 rows
   ```

### **Demo Script (15-20 minutes)**

#### **Part 1: Show the Current State (2 min)**

"Let me show you the current app with static data..."

```bash
# In terminal - show current row count
databricks api post /api/2.0/sql/statements/ --profile simplot-v1 --json '{
  "warehouse_id": "55d3a94c50a43f96",
  "statement": "SELECT COUNT(*) as current_rows FROM serverless_simplot_v1_catalog.frozen_potato.potato_sensor_bronze",
  "wait_timeout": "50s"
}'
```

Open app: https://frozen-potato-digital-twin-7474648424393858.aws.databricksapps.com
- Show **Telemetry** section with 16 components
- Point out: "This is currently showing 16 static data points"

#### **Part 2: Explain Zerobus Value Prop (3 min)**

"Traditional approach requires Kafka brokers, connectors, partition management...
**With Zerobus**: Direct gRPC streaming to Delta. Fully managed. No infra."

Show notebook 2:
- **Cell 1-4**: SDK setup (2 lines of code)
- **Cell 13-14**: Permissions (automatic via service principal)
- **Cell 17**: Connection test
  ```python
  stream = await sdk.create_stream(CLIENT_ID, CLIENT_SECRET, table_properties)
  # Connection successful ✅
  ```

#### **Part 3: Live Streaming Demo (5-7 min)**

**Scenario 1: Single Source Ingestion**

Run **Step 4** (cells 28-34):
- Shows progress bar ingesting 16,000 rows (16 components × 1,000 readings each)
- Point out: "This simulates 1 second of factory telemetry at 1ms intervals"
- Time: ~30-60 seconds to ingest

**While it's ingesting**, explain:
- "Each record is a protobuf message with 13 fields"
- "Zerobus buffers, batches, and commits to Delta automatically"
- "Automatic recovery on network failures"

After completion:
```sql
-- Show new row count
SELECT COUNT(*) FROM potato_sensor_bronze; -- Now 16,016 rows!
```

**Scenario 2: Parallel Multi-Line Ingestion** (Optional, if time)

Run **Step 5** (cells 35-44):
- Shows 3 parallel progress bars (one per production line)
- "Simulating multiple edge devices streaming simultaneously"
- All land in same Delta table with ACID guarantees

#### **Part 4: Show Real-time Updates in App (3 min)**

1. **Refresh the app** (F5)
2. Navigate to **Telemetry** section
3. Point out: "Data auto-refreshes every 5 seconds"
4. Show **System Logs** - new events appear
5. Show **Analytics** - temperature distribution updated

**Key message**: "From sensor → Delta → Knowledge Graph → App in seconds"

#### **Part 5: Production Deployment Path (2 min)**

Show `zerobus_station/` folder:

"For production deployment with **real factory sensors**:
- Install Ignition Gateway module (`.modl` file)
- Connect to OPC-UA/MQTT/PLC tags
- Configure in Ignition UI (no code)
- Same Zerobus backend, different data source"

Show architecture diagram:
```
Real Factory Floor:
OPC-UA Servers → Ignition Gateway → Zerobus → Delta → Digital Twin
     ↑
   (PLCs, SCADA, sensors)
```

#### **Part 6: Why This Matters (2 min)**

Benefits callouts:
- ✅ **No Kafka/message queue management**
- ✅ **Sub-second latency** (sensor → app)
- ✅ **Serverless** (no cluster sizing)
- ✅ **ACID guarantees** (Delta Lake)
- ✅ **Schema evolution** (via protobuf)
- ✅ **Exactly-once semantics**

---

## 🎯 Key Demo Talking Points

### **For Manufacturing/IoT Customers**:
1. "16 components, 6 sensors each, 1ms intervals → 96,000 data points/second"
2. "No data loss on network failures (SDK auto-retry)"
3. "OPC-UA, MQTT, Modbus - all supported via Ignition"
4. "From edge to insights in < 5 seconds"

### **For Data Engineering Teams**:
1. "Record-by-record ingestion with batching under the hood"
2. "Async Python SDK or Ignition Gateway (no code)"
3. "Delta Lake ACID from the start"
4. "Protobuf schema registered automatically"

### **For IT/Platform Teams**:
1. "Fully managed - no Kafka brokers to patch"
2. "Serverless compute - no cluster capacity planning"
3. "Service principal auth (OAuth2)"
4. "Built-in observability (metrics, tracing)"

---

## 📱 Quick Demo Checklist

Before customer call:
- [ ] Notebook 2 opened and attached to serverless
- [ ] Service principal credentials verified in 0-Parameters
- [ ] App URL bookmarked and tested
- [ ] Query ready to show row count growth
- [ ] Architecture slide prepared (optional)

During demo:
- [ ] Show current state (static data)
- [ ] Run Zerobus ingestion (live progress bars)
- [ ] Query table to show row count increase
- [ ] Refresh app to show updated data
- [ ] Explain production path (Ignition module)

---

## 🔧 How to Run Zerobus Demo Right Now

1. **Open notebook 2**: `/Users/ankit.yadav@databricks.com/frozen-potato-digital-twin/2-Ingest-Data-Zerobus`
2. **Run cells 1-18** (setup and connection test)
3. **Run cells 28-34** (ingest 16K rows, ~1 minute)
4. **Check results**:
   ```sql
   SELECT component_id, COUNT(*) as readings
   FROM serverless_simplot_v1_catalog.frozen_potato.potato_sensor_bronze
   GROUP BY component_id
   ORDER BY component_id;
   ```
5. **Refresh app** and see updated telemetry!

---

## 🎓 Customer Objection Handlers

**"How is this different from Kafka?"**
→ "Same use case, zero operational overhead. Kafka requires brokers, Zookeeper, partition tuning. Zerobus: just call `stream.ingest_record()` and we handle the rest."

**"What about backpressure?"**
→ "SDK buffers locally, Zerobus batches server-side. If Delta is slow, backpressure signals the client. Configurable batch sizes."

**"Can we replay/reprocess?"**
→ "Yes - it's Delta Lake. Time travel, OPTIMIZE, VACUUM - all standard Delta operations work."

**"What about schema changes?"**
→ "Protobuf for forward/backward compatibility. Add fields without breaking existing readers."

**"What's the cost model?"**
→ "No separate ingestion infrastructure costs. Pay for Delta table storage + serverless compute for queries. Typical customer sees 60-70% TCO reduction vs self-managed Kafka."

**"What about data governance?"**
→ "Full Unity Catalog integration. Row/column-level security, audit logs, lineage tracking - all available from the moment data lands."

---

## 📊 Demo Metrics to Highlight

After running the demo, call out these numbers:

```sql
-- Total sensors streaming
SELECT COUNT(DISTINCT component_id) as active_sensors FROM potato_sensor_bronze;
-- Result: 16 sensors

-- Data points per component
SELECT component_id, COUNT(*) as data_points
FROM potato_sensor_bronze
GROUP BY component_id
ORDER BY component_id;
-- Result: 1,000+ readings per component

-- Throughput demonstration
SELECT
  line_id,
  COUNT(*) as total_readings,
  COUNT(DISTINCT component_id) as components,
  MIN(timestamp) as first_reading,
  MAX(timestamp) as last_reading,
  DATEDIFF(second, MIN(timestamp), MAX(timestamp)) as duration_seconds
FROM potato_sensor_bronze
GROUP BY line_id;
-- Shows data velocity per production line
```

---

## 🎥 Optional: Screen Recording Setup

For async demos or video walkthroughs:

1. **Record notebook execution** (show progress bars)
2. **Record SQL query** showing row count growth
3. **Record app refresh** with updated telemetry
4. **Add voiceover** explaining Zerobus benefits

Tools: Loom, QuickTime, or OBS Studio

---

## 📞 Follow-up Resources for Customer

After demo, share:
1. **This guide** (ZEROBUS_DEMO_GUIDE.md)
2. **Notebook 2** (export as PDF or share workspace link)
3. **Ignition module documentation** (zerobus_station/README.md)
4. **Architecture diagram** (images/zerobus-architecture.png)
5. **Public Zerobus docs**: https://docs.databricks.com/ingestion/zerobus.html

---

## 🚀 Next Steps After Demo

If customer is interested:

1. **POC Planning**:
   - Identify 1-2 production lines for pilot
   - Determine sensor types (OPC-UA, MQTT, etc.)
   - Size expected data volume
   - Define success metrics

2. **Technical Setup**:
   - Provision Databricks workspace
   - Install Ignition Gateway (if using)
   - Configure service principals
   - Set up Unity Catalog structure

3. **Data Pipeline Design**:
   - Bronze → Silver → Gold architecture
   - Real-time alerting requirements
   - Dashboard/reporting needs
   - ML model integration (predictive maintenance, anomaly detection)

4. **Go-Live Checklist**:
   - Security review (service principals, network policies)
   - Monitoring setup (system tables, alerts)
   - Runbook for operations team
   - Training sessions for end users

---

## 💡 Pro Tips for Demo Success

1. **Test the flow 2-3 times** before customer meeting (muscle memory)
2. **Have backup static data** in case Zerobus has network issues
3. **Use 2 browser windows** (notebook + app) for smooth transitions
4. **Prepare 2-3 discussion points** per section (don't just show, explain why)
5. **Time yourself** - aim for 15 min content, leave 5 min for Q&A
6. **Record your practice run** - watch it back to spot awkward pauses

---

## 🎯 Success Metrics

Demo is successful if customer:
- ✅ Understands Zerobus value prop (no Kafka needed)
- ✅ Sees live data flowing (progress bars, row counts)
- ✅ Recognizes production path (Ignition module)
- ✅ Asks follow-up questions about their specific use case
- ✅ Requests POC or next technical discussion

---

---

## 🔧 Troubleshooting

### Error: `StatusCode.UNIMPLEMENTED` when creating stream

**Cause**: Zerobus is not enabled in your workspace (Public Preview feature)

**Solution**:
1. **Short-term**: Use Notebook 1 to generate data instead
2. **Long-term**: Contact Databricks to enable Zerobus on your workspace

**Check if Zerobus is available**:
```bash
# This should return configuration if Zerobus is enabled
databricks workspace-conf get-status --profile YOUR_PROFILE | grep -i zerobus
```

### Error: Authentication failures

**Cause**: Service principal credentials not configured or incorrect

**Solution**:
1. Go to workspace UI: Settings > Identity and Access > Service Principals
2. Create new service principal (or use existing)
3. Generate OAuth credentials
4. Update `0-Parameters.ipynb` with real CLIENT_ID and CLIENT_SECRET

### Error: Table not found

**Cause**: Bronze table not created before running Notebook 2

**Solution**: Run Notebook 1 first to create the bronze table

---

**Last Updated**: 2026-02-18
**App URL**: https://frozen-potato-digital-twin-7474648424393858.aws.databricksapps.com
**Workspace**: simplot-v1 (fe-sandbox-serverless-simplot-v1)
**Maintainer**: Ankit Yadav (ankit.yadav@databricks.com)
