# Backend URL Fix - Simplot Frozen Potato Digital Twin

## Issue Summary

The deployed Databricks App has `BACKEND_URL_PLACEHOLDER` in the JavaScript bundle instead of the actual app URL, causing:
- ❌ Backend API calls to fail
- ❌ Telemetry data not loading from Databricks
- ❌ App running in static/mock data mode only

**Error shown in app**:
```
Backend URL: ✅ BACKEND_URL_PLACEHOLDER
Backend Health: ❌ (Unexpected token '<', "<!doctype "... is not valid JSON)
```

## Root Cause

The deployment notebook (5-Create-App.ipynb, cell 9) attempts to replace the placeholder:

```python
updated_content = content.replace("BACKEND_URL_PLACEHOLDER", app.url)
```

However, this replacement step failed or was overwritten during the deployment process.

## What Was Fixed

### 1. Local File Updated ✅

**File**: `deployment-staging/dist/static/js/main.90f88fa5.js`

**Change**: Replaced `BACKEND_URL_PLACEHOLDER` with the actual app URL:
```
https://simplot-potato-digital-twin-7474645732542565.aws.databricksapps.com
```

**Backup**: Created `main.90f88fa5.js.backup` before modification

**Verification**:
- ✅ Placeholder no longer exists in the JavaScript file
- ✅ Actual app URL is now present in the bundle

## How to Deploy the Fix

### Option 1: Run the Fix Notebook (Recommended) 🚀

1. Upload `99-Fix-Backend-URL.ipynb` to your Databricks workspace (same location as other notebooks)

2. Open and run all cells in the notebook

3. The notebook will:
   - ✅ Get the current app URL
   - ✅ Replace BACKEND_URL_PLACEHOLDER in the JavaScript file
   - ✅ Copy the fixed files to the deployment folder
   - ✅ Redeploy the app with the fix

4. Wait 1-2 minutes for deployment to complete

5. Refresh the app in your browser - backend health check should now show ✅

### Option 2: Re-run Deployment Notebook Cells

1. Open `5-Create-App.ipynb`

2. Run cells in this order:
   - **Cell 6**: Copy deployment-staging to deployment folder
   - **Cell 9**: Replace URL placeholders (this should now work)
   - **Cell 10**: Deploy the app

3. Wait for deployment to complete

### Option 3: Manual Deployment via CLI

If you have the Databricks CLI installed:

```bash
# Navigate to project directory
cd /Users/ankit.yadav/Desktop/Databricks/Customers/Simplot/demos/frozen-potato-digital-twin

# Run the Python update script
python update_app_url.py
```

## Verification After Deployment

Once redeployed, open the app and navigate to **Monitoring > Telemetry**:

**Before Fix**:
```
Backend URL: ✅ BACKEND_URL_PLACEHOLDER
Backend Health: ❌ (Unexpected token '<', "<!doctype "... is not valid JSON)
```

**After Fix** (Expected):
```
Backend URL: ✅ https://simplot-potato-digital-twin-7474645732542565.aws.databricksapps.com
Backend Health: ✅ Available
```

## Files Modified

1. ✅ `deployment-staging/dist/static/js/main.90f88fa5.js` - Placeholder replaced
2. ✅ `99-Fix-Backend-URL.ipynb` - New fix notebook created
3. ✅ `update_app_url.py` - Python script for CLI deployment (optional)
4. ✅ `BACKEND_URL_FIX.md` - This documentation

## Prevention for Future Deployments

To prevent this issue in future deployments, ensure the URL replacement step (cell 9 in 5-Create-App.ipynb) runs **AFTER** copying the deployment-staging folder and **BEFORE** deploying the app.

The correct order should be:
1. Copy deployment-staging → deployment folder
2. **Replace URL placeholders in the copied folder**
3. Deploy the app

---

## Quick Reference

**App Name**: `simplot-potato-digital-twin`
**App URL**: https://simplot-potato-digital-twin-7474645732542565.aws.databricksapps.com/
**Fixed File**: `deployment-staging/dist/static/js/main.90f88fa5.js`
**Fix Notebook**: `99-Fix-Backend-URL.ipynb`

---

**Status**: ✅ Local fix complete, pending deployment
**Next Step**: Run `99-Fix-Backend-URL.ipynb` in Databricks to deploy the fix
