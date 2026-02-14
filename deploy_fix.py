#!/usr/bin/env python3
"""Deploy the backend URL fix to the Simplot Potato Digital Twin app"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.apps import AppDeployment, AppDeploymentArtifacts, AppDeploymentMode
import uuid

# Configuration
APP_NAME = "simplot-potato-digital-twin"
SOURCE_CODE_PATH = "/Workspace/Users/ankit.yadav@databricks.com/frozen-potato-digital-twin/deployment-staging"

# Initialize client with serverless-lakebase profile
w = WorkspaceClient(profile="serverless-lakebase")

print(f"🚀 Deploying fix for: {APP_NAME}")
print(f"📁 Source path: {SOURCE_CODE_PATH}")

# Get current app details
app = w.apps.get(APP_NAME)
print(f"✅ App found: {app.name}")
print(f"🌐 App URL: {app.url}")
print(f"📊 Current status: {app.compute_status.state}")

# Create new deployment
deployment_id = str(uuid.uuid4())
print(f"\n🔄 Creating new deployment: {deployment_id}")

new_deployment = AppDeployment(
    deployment_id=deployment_id,
    mode=AppDeploymentMode.SNAPSHOT,
    source_code_path=SOURCE_CODE_PATH,
    deployment_artifacts=AppDeploymentArtifacts(source_code_path=SOURCE_CODE_PATH)
)

try:
    w.apps.deploy(APP_NAME, new_deployment)
    print(f"✅ Deployment initiated successfully!")
    print(f"\n⏳ Deployment in progress...")
    print(f"   This will take 1-2 minutes.")
    print(f"\n🌐 App URL: {app.url}")
    print(f"\n💡 The backend URL placeholder has been replaced with:")
    print(f"   {app.url}")
    print(f"\n✅ Once deployment completes, refresh your browser to see the fix!")
except Exception as e:
    print(f"❌ Deployment failed: {e}")
    exit(1)
