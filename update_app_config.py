#!/usr/bin/env python3
"""Update the app configuration with correct environment variables"""

import subprocess
import json

# Read the local app.yaml to get environment variables
import yaml

with open('/Users/ankit.yadav/Desktop/Databricks/Customers/Simplot/demos/frozen-potato-digital-twin/deployment-staging/app.yaml', 'r') as f:
    app_config = yaml.safe_load(f)

print("📝 App configuration to deploy:")
print(json.dumps(app_config, indent=2))

# Write it to a temp file for uploading
import tempfile
import os

with tempfile.TemporaryDirectory() as tmpdir:
    yaml_path = os.path.join(tmpdir, 'app.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(app_config, f)

    # Upload using workspace import-dir
    print("\n📤 Uploading configuration to workspace...")
    result = subprocess.run([
        'databricks', 'workspace', 'upload',
        tmpdir,
        '/Workspace/Users/ankit.yadav@databricks.com/frozen-potato-digital-twin/deployment-staging-new',
        '--overwrite',
        '--profile', 'serverless-lakebase'
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error uploading: {result.stderr}")
        exit(1)

    print("✅ Configuration uploaded successfully")

    # Now deploy from the new location
    print("\n🚀 Deploying app from updated configuration...")
    result = subprocess.run([
        'databricks', 'apps', 'deploy',
        'simplot-potato-digital-twin',
        '--source-code-path', '/Workspace/Users/ankit.yadav@databricks.com/frozen-potato-digital-twin/deployment-staging-new',
        '--profile', 'serverless-lakebase'
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Deployment failed: {result.stderr}")
        exit(1)

    print("✅ Deployment successful!")
    print(result.stdout)
