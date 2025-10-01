#!/usr/bin/env python3
"""
Sake Sensei - Alternative Gateway Setup

Since AgentCore Gateway API is not yet available in boto3, we'll configure
Lambda functions to be directly accessible as MCP tools via HTTP endpoints.
"""

import json
import os
import sys
from pathlib import Path

import boto3
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")

# Lambda function names
LAMBDA_FUNCTIONS = [
    "SakeSensei-Recommendation",
    "SakeSensei-Preference",
    "SakeSensei-Tasting",
    "SakeSensei-Brewery",
    "SakeSensei-ImageRecognition",
]


def create_lambda_function_urls():
    """Create Lambda function URLs for direct HTTP access."""

    print("Creating Lambda Function URLs for MCP tool access...")
    print(f"Region: {AWS_REGION}")

    lambda_client = boto3.client("lambda", region_name=AWS_REGION)

    function_urls = {}

    for function_name in LAMBDA_FUNCTIONS:
        try:
            print(f"\nProcessing {function_name}...")

            # Check if function URL already exists
            try:
                url_config = lambda_client.get_function_url_config(
                    FunctionName=function_name
                )
                function_url = url_config["FunctionUrl"]
                print(f"  ✅ Function URL already exists: {function_url}")
                function_urls[function_name] = function_url
                continue
            except lambda_client.exceptions.ResourceNotFoundException:
                pass  # Function URL doesn't exist, create it

            # Create function URL configuration
            response = lambda_client.create_function_url_config(
                FunctionName=function_name,
                AuthType="AWS_IAM",  # Require IAM auth
                Cors={
                    "AllowOrigins": ["*"],
                    "AllowMethods": ["POST"],
                    "AllowHeaders": ["content-type", "x-amz-date", "authorization"],
                    "MaxAge": 86400,
                },
            )

            function_url = response["FunctionUrl"]
            print(f"  ✅ Created function URL: {function_url}")
            function_urls[function_name] = function_url

            # Add resource-based policy to allow invocation
            try:
                lambda_client.add_permission(
                    FunctionName=function_name,
                    StatementId="AllowFunctionURLInvoke",
                    Action="lambda:InvokeFunctionUrl",
                    Principal="*",
                    FunctionUrlAuthType="AWS_IAM",
                )
                print(f"  ✅ Added invoke permission")
            except lambda_client.exceptions.ResourceConflictException:
                print(f"  ℹ️  Permission already exists")

        except Exception as e:
            print(f"  ❌ Error processing {function_name}: {e}")
            continue

    # Save URLs to .env
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"

    if function_urls:
        print("\n" + "=" * 60)
        print("Lambda Function URLs Created:")
        print("=" * 60)
        for func_name, url in function_urls.items():
            print(f"{func_name}: {url}")

            # Save to .env
            env_key = f"LAMBDA_{func_name.split('-')[1].upper()}_URL"
            if env_file.exists():
                set_key(str(env_file), env_key, url)

        print("\n✅ Updated .env with function URLs")

        # Save as JSON for later use
        urls_file = project_root / "lambda_function_urls.json"
        with open(urls_file, "w") as f:
            json.dump(function_urls, f, indent=2)
        print(f"✅ Saved URLs to {urls_file}")

    return function_urls


if __name__ == "__main__":
    if not AWS_ACCOUNT_ID:
        print("Error: AWS_ACCOUNT_ID not set in environment")
        sys.exit(1)

    urls = create_lambda_function_urls()

    if urls:
        print("\n" + "=" * 60)
        print("Setup Complete!")
        print("=" * 60)
        print(f"Created {len(urls)} Lambda function URLs")
        print("\nNext steps:")
        print("  1. Agent will use these URLs as MCP tools")
        print("  2. Deploy agent: ./scripts/deploy_agent.sh")
        print("  3. Test integration")
    else:
        print("\n❌ No function URLs were created")
        sys.exit(1)
