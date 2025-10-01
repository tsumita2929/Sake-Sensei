#!/usr/bin/env python3
"""
Sake Sensei - Create AgentCore Gateway

Creates an AgentCore Gateway for MCP tool integration with Lambda functions.
"""

import os
import sys
from pathlib import Path

import boto3
from dotenv import load_dotenv, set_key

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
GATEWAY_NAME = os.getenv("GATEWAY_NAME", "SakeSensei-Gateway")
GATEWAY_DESCRIPTION = os.getenv("GATEWAY_DESCRIPTION", "Sake Sensei MCP Gateway for Lambda tools")

# IAM Role ARN for Gateway (must have permissions for bedrock-agentcore)
GATEWAY_ROLE_ARN = os.getenv("GATEWAY_ROLE_ARN")


def create_gateway():
    """Create AgentCore Gateway with Cognito authentication."""

    if not COGNITO_USER_POOL_ID:
        print("Error: COGNITO_USER_POOL_ID not set in environment")
        sys.exit(1)

    if not COGNITO_CLIENT_ID:
        print("Error: COGNITO_CLIENT_ID not set in environment")
        sys.exit(1)

    if not GATEWAY_ROLE_ARN:
        print("Error: GATEWAY_ROLE_ARN not set in environment")
        print("Please create an IAM role with bedrock-agentcore permissions")
        sys.exit(1)

    print(f"Creating AgentCore Gateway: {GATEWAY_NAME}")
    print(f"Region: {AWS_REGION}")
    print(f"Cognito User Pool: {COGNITO_USER_POOL_ID}")

    # Initialize Bedrock AgentCore Control client
    try:
        client = boto3.client(
            "bedrock-agentcore-control",
            region_name=AWS_REGION,
        )
    except Exception as e:
        print(f"Error initializing bedrock-agentcore-control client: {e}")
        print("Note: bedrock-agentcore service may not be available in all regions")
        sys.exit(1)

    # Configure Cognito JWT authentication
    auth_config = {
        "customJWTAuthorizer": {
            "allowedClients": [COGNITO_CLIENT_ID],
            "discoveryUrl": (
                f"https://cognito-idp.{AWS_REGION}.amazonaws.com/"
                f"{COGNITO_USER_POOL_ID}/.well-known/openid-configuration"
            ),
        }
    }

    # Create Gateway
    try:
        response = client.create_gateway(
            name=GATEWAY_NAME,
            roleArn=GATEWAY_ROLE_ARN,
            protocolType="MCP",  # Model Context Protocol
            authorizerType="CUSTOM_JWT",
            authorizerConfiguration=auth_config,
            description=GATEWAY_DESCRIPTION,
        )

        gateway_id = response.get("gatewayId")
        gateway_arn = response.get("gatewayArn")
        creation_time = response.get("creationTime")

        print("\n✅ Gateway created successfully!")
        print(f"Gateway ID: {gateway_id}")
        print(f"Gateway ARN: {gateway_arn}")
        print(f"Creation Time: {creation_time}")

        # Update .env file
        env_file = project_root / ".env"
        if env_file.exists():
            try:
                set_key(str(env_file), "AGENTCORE_GATEWAY_ID", gateway_id)
                set_key(str(env_file), "AGENTCORE_GATEWAY_ARN", gateway_arn)
                print(f"\n✅ Updated {env_file} with gateway information")
            except Exception as e:
                print(f"\n⚠️  Warning: Failed to update .env file: {e}")
        else:
            print(f"\n⚠️  Warning: .env file not found at {env_file}")
            print("Please manually add:")
            print(f"  AGENTCORE_GATEWAY_ID={gateway_id}")
            print(f"  AGENTCORE_GATEWAY_ARN={gateway_arn}")

        return gateway_id

    except Exception as e:
        print(f"\n❌ Error creating gateway: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_gateway()
