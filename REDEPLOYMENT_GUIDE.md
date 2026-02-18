# Frozen Potato Digital Twin - Full Redeployment Guide

Use this guide to recreate the Frozen Potato Digital Twin demo from scratch in a new Databricks workspace. Each step includes the exact CLI command or Claude Code prompt to run.

**Workspaces are ephemeral** -- they are destroyed every 14 days. This guide must be followed every time a new workspace is provisioned. The entire process takes ~15-20 minutes.

---

## Prerequisites

- Databricks workspace with Unity Catalog enabled (serverless-only)
- Workspace admin permissions
- This repo cloned locally
- `databricks` CLI v0.217.0+ installed and authenticated

---

## Step 0: Configure Databricks Profile

Add the new workspace profile to `~/.databrickscfg` and authenticate.

```bash
# Add profile
databricks auth login --host https://NEW_WORKSPACE.cloud.databricks.com --profile NEW_PROFILE_NAME

# Verify
databricks current-user me --profile NEW_PROFILE_NAME
databricks workspace list / --profile NEW_PROFILE_NAME
```

**After this step, update all references below:**
- Replace `NEW_PROFILE_NAME` with actual profile name (e.g., `simplot-v1`)
- Replace `YOUR_CATALOG` with your catalog name
- Replace `YOUR_EMAIL` with your Databricks email

---

## Step 1: Create Catalog & Schema

```bash
# Create schema via SQL API
databricks api post /api/2.1/unity-catalog/schemas --profile NEW_PROFILE_NAME --json '{
  "name": "frozen_potato",
  "catalog_name": "YOUR_CATALOG",
  "comment": "Schema for Frozen Potato Digital Twin - UC5"
}'
```

**Created schema:** `YOUR_CATALOG.frozen_potato`

---

## Step 2: Update Parameters Notebook

Edit `0-Parameters.ipynb` (or create a workspace-specific copy):

**Find & replace:**
- `ankit_yadav` → `YOUR_CATALOG`
- `simplot-potato-lakebase` → `YOUR_LAKEBASE_INSTANCE_NAME`
- `simplot-potato-digital-twin` → `YOUR_APP_NAME`
- `aef4a1619f5328da` → `YOUR_WAREHOUSE_ID`

Update Zerobus credentials if using Zerobus ingestion:
- `CLIENT_ID` → your service principal client ID
- `CLIENT_SECRET` → your service principal secret
- `WORKSPACE_URL` → your workspace URL
- `ZEROBUS_URL` → your workspace domain

---

## Step 3: Upload All Project Files

```bash
cd /path/to/frozen-potato-digital-twin

# Upload notebooks (without .ipynb extension for %run compatibility)
for f in 0-Parameters 1-Create-Sensor-Bronze-Table 2-Ingest-Data-Zerobus 3-Setup-Mapping-Pipeline 4-Sync-To-Lakebase 5-Create-App 6-Cleanup; do
  databricks workspace import "/Workspace/Users/YOUR_EMAIL/frozen-potato-digital-twin/$f" \
    --file "${f}.ipynb" --language PYTHON --format SOURCE --overwrite --profile NEW_PROFILE_NAME
done

# Upload supporting directories
databricks workspace import-dir line_data_generator /Workspace/Users/YOUR_EMAIL/frozen-potato-digital-twin/line_data_generator --profile NEW_PROFILE_NAME
databricks workspace import-dir mapping_pipeline /Workspace/Users/YOUR_EMAIL/frozen-potato-digital-twin/mapping_pipeline --profile NEW_PROFILE_NAME
databricks workspace import-dir deployment-staging /Workspace/Users/YOUR_EMAIL/frozen-potato-digital-twin/deployment-staging --profile NEW_PROFILE_NAME
databricks workspace import-dir example-ttls /Workspace/Users/YOUR_EMAIL/frozen-potato-digital-twin/example-ttls --profile NEW_PROFILE_NAME
databricks workspace import-dir zerobus_config /Workspace/Users/YOUR_EMAIL/frozen-potato-digital-twin/zerobus_config --profile NEW_PROFILE_NAME
```

**Key change:** Use `--format SOURCE` instead of `--format JUPYTER` to upload notebooks without the `.ipynb` extension in the workspace path. This makes `%run ./0-Parameters` work correctly.

---

## Step 4: Run Notebooks on Serverless (via Jobs)

Create and run a workflow job that executes all setup notebooks in sequence:

```bash
JOB_ID=$(databricks jobs create --json '{
  "name": "Frozen Potato - Full Setup",
  "tasks": [
    {
      "task_key": "create_bronze_table",
      "notebook_task": {
        "notebook_path": "/Workspace/Users/YOUR_EMAIL/frozen-potato-digital-twin/1-Create-Sensor-Bronze-Table",
        "source": "WORKSPACE"
      },
      "environment_key": "frozen_potato_env"
    },
    {
      "task_key": "setup_mapping_pipeline",
      "depends_on": [{"task_key": "create_bronze_table"}],
      "notebook_task": {
        "notebook_path": "/Workspace/Users/YOUR_EMAIL/frozen-potato-digital-twin/3-Setup-Mapping-Pipeline",
        "source": "WORKSPACE"
      },
      "environment_key": "frozen_potato_env"
    },
    {
      "task_key": "sync_to_lakebase",
      "depends_on": [{"task_key": "setup_mapping_pipeline"}],
      "notebook_task": {
        "notebook_path": "/Workspace/Users/YOUR_EMAIL/frozen-potato-digital-twin/4-Sync-To-Lakebase",
        "source": "WORKSPACE"
      },
      "environment_key": "frozen_potato_env"
    },
    {
      "task_key": "create_app",
      "depends_on": [{"task_key": "sync_to_lakebase"}],
      "notebook_task": {
        "notebook_path": "/Workspace/Users/YOUR_EMAIL/frozen-potato-digital-twin/5-Create-App",
        "source": "WORKSPACE"
      },
      "environment_key": "frozen_potato_env"
    }
  ],
  "environments": [{
    "environment_key": "frozen_potato_env",
    "spec": {
      "client": "1",
      "dependencies": ["pandas", "numpy", "mandrova", "databricks-sdk>=0.68.0", "psycopg", "pyyaml"]
    }
  }],
  "format": "MULTI_TASK"
}' --profile NEW_PROFILE_NAME | jq -r '.job_id')

echo "Created job with ID: $JOB_ID"

# Run and wait for completion
databricks jobs run-now $JOB_ID --profile NEW_PROFILE_NAME --timeout 20m
```

**Note:** Notebook 2 (Zerobus) is skipped - it's optional for initial deployment. The notebooks use `%run ./0-Parameters` which now works because notebooks were uploaded without `.ipynb` in their workspace paths.

**Expected duration:** 10-15 minutes total

---

## Step 5: Deploy the App

**CRITICAL:** The app must deploy from `deployment-staging` folder ONLY, not the project root (which contains notebooks).

```bash
# Upload app code to dedicated workspace directory
databricks workspace import-dir deployment-staging /Workspace/Users/YOUR_EMAIL/frozen-potato-digital-twin-app --profile NEW_PROFILE_NAME

# Deploy app from app-specific directory
databricks apps deploy YOUR_APP_NAME \
  --source-code-path /Workspace/Users/YOUR_EMAIL/frozen-potato-digital-twin-app \
  --profile NEW_PROFILE_NAME
```

**Why separate directory?** The project root contains notebooks (.ipynb files) which can cause deployment errors if included in app source. The `deployment-staging` folder contains only the Flask app code (Python + React bundle).

---

## Step 6: Verify Deployment

```bash
# Check bronze table exists and has data
databricks api post /api/2.0/sql/statements/ --profile NEW_PROFILE_NAME --json '{
  "warehouse_id": "YOUR_WAREHOUSE_ID",
  "statement": "SELECT COUNT(*) as row_count, COUNT(DISTINCT component_id) as components, COUNT(DISTINCT line_id) as lines FROM YOUR_CATALOG.frozen_potato.potato_sensor_bronze",
  "wait_timeout": "50s"
}'

# Check triples table exists
databricks api post /api/2.0/sql/statements/ --profile NEW_PROFILE_NAME --json '{
  "warehouse_id": "YOUR_WAREHOUSE_ID",
  "statement": "SELECT COUNT(*) as triple_count FROM YOUR_CATALOG.frozen_potato.triples",
  "wait_timeout": "50s"
}'

# Check Lakebase instance is running
databricks lakebase instances get YOUR_LAKEBASE_INSTANCE_NAME --profile NEW_PROFILE_NAME

# Check app is deployed
databricks apps get YOUR_APP_NAME --profile NEW_PROFILE_NAME
```

---

## Step 6: Test the App

```bash
# Get app URL
APP_URL=$(databricks apps get YOUR_APP_NAME --profile NEW_PROFILE_NAME | jq -r '.url')
echo "App URL: $APP_URL"

# Test health endpoint
curl "${APP_URL}/health"
```

Expected response:
```json
{"status": "healthy"}
```

---

## Collected IDs Checklist

After deployment, record these for reference:

| Resource | ID/Value |
|---|---|
| Workspace URL | `https://________________.cloud.databricks.com` |
| CLI Profile | `________________` |
| Catalog | `________________` |
| Schema | `________________.frozen_potato` |
| SQL Warehouse ID | `________________` |
| Lakebase Instance | `________________` |
| App Name | `________________` |
| App URL | `https://________________.aws.databricksapps.com` |
| App SP Client ID | `________________` |

---

## Known Gotchas

1. **Notebook `%run` dependencies require SOURCE format:** When uploading notebooks via `databricks workspace import`, use `--format SOURCE` (not `JUPYTER`) to upload without the `.ipynb` extension. This allows `%run ./0-Parameters` to resolve correctly.

2. **Serverless environment dependencies:** All Python packages must be declared in the `environments` section of the job config. The `libraries` field is not supported for serverless tasks.

3. **Lakebase startup time:** A new Lakebase instance takes ~5-6 minutes to become available after creation.

4. **App resource authorization is manual:** After deploying the app, you must go to the Databricks UI (Compute > Apps > [app name] > Settings > Resources) and authorize each resource manually.

5. **Service principal for Zerobus:** If using Zerobus (notebook 2), create a dedicated service principal and generate OAuth credentials via the UI at Settings > Identity and Access > Service Principals.

6. **Serverless-only workspace:** These workspaces have no interactive clusters. All notebook execution must use serverless compute via workflow jobs.

7. **App source path must exclude notebooks:** The app's `source_code_path` must point to `deployment-staging` folder only, not the project root. Including notebooks in app source causes "invalid notebook" deployment errors.

---

## Troubleshooting

### Job fails with "Notebook not found: Users/..."
**Cause:** Notebooks were uploaded with `.ipynb` extension in workspace path.
**Fix:** Re-upload notebooks with `--format SOURCE` (not `--format JUPYTER`).

### Job fails with "Libraries field is not supported"
**Cause:** Used `libraries` field instead of `environments` for serverless task.
**Fix:** Move library dependencies to `environments[].spec.dependencies` array.

### MCP tools fail with auth error
**Cause:** MCP server uses `[DEFAULT]` profile from `~/.databrickscfg`, not the target profile.
**Fix:** Use `databricks` CLI with explicit `--profile` flags instead of MCP tools for deployment automation.

### App can't access Lakebase
**Cause:** App service principal lacks permissions on Lakebase tables.
**Fix:** Grant permissions via `databricks psql` after app creation:
```bash
databricks psql YOUR_LAKEBASE_INSTANCE --profile NEW_PROFILE_NAME -- -d YOUR_DB -c "
GRANT ALL ON ALL TABLES IN SCHEMA public TO \"APP_SP_CLIENT_ID\";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO \"APP_SP_CLIENT_ID\";
"
```

---

## Next Steps

After successful deployment:
1. Update memory file (`~/.claude/projects/.../memory/MEMORY.md`) with new workspace details
2. Test all app features (Dashboard, Analytics, Telemetry, etc.)
3. Generate additional sensor data if needed (run notebook 1 again with larger `sample_size`)
