#!/usr/bin/env python3
"""
Quick script to update Lambda function code.
"""

import sys
from pathlib import Path

import boto3

if len(sys.argv) != 2:
    print("Usage: python update_lambda.py <function_name>")
    sys.exit(1)

function_name = sys.argv[1]
region = "us-west-2"

# Read zip file
zip_path = Path(f"/tmp/{function_name}.zip")
if not zip_path.exists():
    print(f"Error: {zip_path} not found")
    sys.exit(1)

print(f"Updating Lambda function: {function_name}")
print(f"Reading from: {zip_path}")

lambda_client = boto3.client("lambda", region_name=region)

with open(zip_path, "rb") as f:
    zip_content = f.read()

try:
    response = lambda_client.update_function_code(
        FunctionName=function_name, ZipFile=zip_content
    )

    print(f"✅ Function updated successfully!")
    print(f"Function ARN: {response['FunctionArn']}")
    print(f"Last modified: {response['LastModified']}")
    print(f"Code size: {response['CodeSize']} bytes")

except Exception as e:
    print(f"❌ Error updating function: {e}")
    sys.exit(1)
