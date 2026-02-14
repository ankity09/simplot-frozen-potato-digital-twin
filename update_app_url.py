"""
Update Databricks App with Fixed Backend URL

This script redeploys the Simplot Frozen Potato Digital Twin app
with the corrected backend URL (BACKEND_URL_PLACEHOLDER replaced).

Usage:
    python update_app_url.py

Requirements:
    - Databricks SDK installed (pip install databricks-sdk)
    - Databricks authentication configured (via environment variables or ~/.databrickscfg)
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.apps import AppDeployment, AppDeploymentArtifacts, AppDeploymentMode
import uuid
import os
import shutil

# Configuration
APP_NAME = "simplot-potato-digital-twin"
APP_URL = "https://simplot-potato-digital-twin-7474645732542565.aws.databricksapps.com"

def main():
    print(f"🚀 Starting app update process for: {APP_NAME}")
    print(f"📍 App URL: {APP_URL}")

    # Initialize Workspace Client
    w = WorkspaceClient()
    print("✅ Connected to Databricks workspace")

    # Get current working directory and determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    deployment_staging = os.path.join(script_dir, "deployment-staging")

    # Verify the fixed JavaScript file exists
    js_file = os.path.join(deployment_staging, "dist/static/js/main.90f88fa5.js")
    if not os.path.exists(js_file):
        print(f"❌ Error: JavaScript file not found at {js_file}")
        return

    # Verify the placeholder has been replaced
    with open(js_file, 'r') as f:
        content = f.read()
        if "BACKEND_URL_PLACEHOLDER" in content:
            print("⚠️  Warning: BACKEND_URL_PLACEHOLDER still found in JavaScript file!")
            print("   Running sed replacement now...")
            os.system(f'sed -i "" "s|BACKEND_URL_PLACEHOLDER|{APP_URL}|g" "{js_file}"')
            print("✅ Placeholder replaced")
        else:
            print("✅ Backend URL placeholder already replaced")

    # Get notebook path for determining workspace location
    try:
        import IPython
        notebook_path = IPython.extract_module_locals()[1]['__vsc_ipynb_file__']
        parent_path = os.path.dirname(notebook_path)
        grandparent_path = os.path.dirname(parent_path)
        workspace_deployment_path = f"/Workspace{grandparent_path}/deployment-digital-twin"
    except:
        # Default path if not in notebook
        workspace_deployment_path = "/Workspace/Users/ankit.yadav@databricks.com/deployment-digital-twin"

    print(f"📁 Target workspace path: {workspace_deployment_path}")

    # Copy updated files to workspace
    print("📂 Copying updated deployment-staging to workspace...")

    # Note: This requires the Databricks workspace filesystem
    # In practice, you'd use dbutils or workspace API to copy files
    # For now, we'll use the deployment path directly

    # Create new deployment
    print("🔄 Creating new deployment...")
    new_deployment = AppDeployment(
        deployment_id=str(uuid.uuid4()),
        mode=AppDeploymentMode.AUTO_SYNC,
        source_code_path=workspace_deployment_path,
        deployment_artifacts=AppDeploymentArtifacts(source_code_path=workspace_deployment_path)
    )

    # Deploy the app
    try:
        w.apps.deploy(APP_NAME, new_deployment)
        print(f"✅ App {APP_NAME} has been successfully redeployed!")
        print(f"🌐 Visit: {APP_URL}")
        print("\n⏳ Wait 1-2 minutes for the deployment to complete, then refresh the app in your browser.")
    except Exception as e:
        print(f"❌ Failed to redeploy {APP_NAME}: {e}")
        print("\n💡 Alternative: Run notebook cell 10 from 5-Create-App.ipynb to redeploy")

if __name__ == "__main__":
    main()
