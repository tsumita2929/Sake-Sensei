#!/usr/bin/env python3
"""
Sake Sensei - Add Gateway Targets

Adds Lambda functions as MCP tools to the AgentCore Gateway.
"""

import os
import sys
import time
from pathlib import Path

import boto3
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
AGENTCORE_GATEWAY_ID = os.getenv("AGENTCORE_GATEWAY_ID")

# Lambda ARNs
LAMBDA_ARNS = {
    "recommendation": os.getenv("LAMBDA_RECOMMENDATION_ARN"),
    "preference": os.getenv("LAMBDA_PREFERENCE_ARN"),
    "tasting": os.getenv("LAMBDA_TASTING_ARN"),
    "brewery": os.getenv("LAMBDA_BREWERY_ARN"),
    "image_recognition": os.getenv("LAMBDA_IMAGE_RECOGNITION_ARN"),
}

# MCP Tool definitions for each Lambda
# Note: inputSchema only supports: type, properties, required, items, description
TOOL_DEFINITIONS = {
    "recommendation": {
        "name": "get_sake_recommendations",
        "description": "Get personalized sake recommendations based on user preferences and tasting history. limit parameter defaults to 5 if not provided.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User ID to get recommendations for"},
                "preferences": {
                    "type": "object",
                    "description": "User preferences (flavor_profile, sake_type, price_range, etc.)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of recommendations to return (default: 5)",
                },
            },
            "required": ["user_id"],
        },
    },
    "preference": {
        "name": "manage_user_preferences",
        "description": "Get or update user sake preferences. action must be 'get' or 'update'. When action is 'update', provide preferences object.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User ID"},
                "action": {"type": "string", "description": "Action to perform: 'get' or 'update'"},
                "preferences": {
                    "type": "object",
                    "description": "Preferences to update (only when action is 'update')",
                },
            },
            "required": ["user_id", "action"],
        },
    },
    "tasting": {
        "name": "manage_tasting_records",
        "description": "Create, retrieve, or search tasting records. action can be 'create', 'get', 'list', or 'search'. limit defaults to 20 if not provided.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User ID"},
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'create', 'get', 'list', or 'search'",
                },
                "record_id": {
                    "type": "string",
                    "description": "Tasting record ID (required when action is 'get')",
                },
                "tasting_data": {
                    "type": "object",
                    "description": "Tasting record data (required when action is 'create')",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of records to return (default: 20)",
                },
            },
            "required": ["user_id", "action"],
        },
    },
    "brewery": {
        "name": "get_brewery_info",
        "description": "Get information about sake breweries. Provide either brewery_id or search query. limit defaults to 10 if not provided.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "brewery_id": {
                    "type": "string",
                    "description": "Brewery ID to retrieve specific brewery",
                },
                "search": {
                    "type": "string",
                    "description": "Search query for brewery name or location",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 10)",
                },
            },
        },
    },
    "image_recognition": {
        "name": "recognize_sake_label",
        "description": "Recognize sake information from a label image using Claude vision model. Provide either image_s3_key or image_base64 with media_type. media_type can be 'image/jpeg', 'image/png', or 'image/webp' (default: image/jpeg).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_s3_key": {
                    "type": "string",
                    "description": "S3 key of the uploaded sake label image",
                },
                "image_base64": {
                    "type": "string",
                    "description": "Base64-encoded image data (alternative to S3)",
                },
                "media_type": {
                    "type": "string",
                    "description": "Image media type: image/jpeg, image/png, or image/webp (default: image/jpeg)",
                },
            },
        },
    },
}


def add_gateway_targets():
    """Add Lambda functions as MCP tools to the Gateway."""

    if not AGENTCORE_GATEWAY_ID:
        print("Error: AGENTCORE_GATEWAY_ID not set in environment")
        print("Please run create_gateway.py first")
        sys.exit(1)

    # Validate all Lambda ARNs are set
    missing_arns = [name for name, arn in LAMBDA_ARNS.items() if not arn]
    if missing_arns:
        print(f"Error: Missing Lambda ARNs for: {', '.join(missing_arns)}")
        sys.exit(1)

    print(f"Adding Lambda tools to Gateway: {AGENTCORE_GATEWAY_ID}")
    print(f"Region: {AWS_REGION}")

    # Initialize Bedrock AgentCore Control client
    try:
        client = boto3.client(
            "bedrock-agentcore-control",
            region_name=AWS_REGION,
        )
    except Exception as e:
        print(f"Error initializing bedrock-agentcore-control client: {e}")
        sys.exit(1)

    # Credential configuration for Gateway IAM Role
    credential_config = [{"credentialProviderType": "GATEWAY_IAM_ROLE"}]

    # Add each Lambda as a gateway target
    added_tools = []
    for lambda_name, lambda_arn in LAMBDA_ARNS.items():
        tool_def = TOOL_DEFINITIONS[lambda_name]

        print(f"\n  Adding tool: {tool_def['name']} ({lambda_name})...")

        # Construct target configuration in the correct format
        target_config = {
            "mcp": {
                "lambda": {
                    "lambdaArn": lambda_arn,
                    "toolSchema": {
                        "inlinePayload": [
                            {
                                "name": tool_def["name"],
                                "description": tool_def["description"],
                                "inputSchema": tool_def["inputSchema"],
                            }
                        ]
                    },
                }
            }
        }

        try:
            # Replace underscores with hyphens for valid target name
            target_name = f"SakeSensei-{lambda_name.replace('_', '-').title()}"

            response = client.create_gateway_target(
                gatewayIdentifier=AGENTCORE_GATEWAY_ID,
                name=target_name,
                description=f"Target for {tool_def['name']} Lambda function",
                credentialProviderConfigurations=credential_config,
                targetConfiguration=target_config,
            )

            target_id = response.get("targetId")
            print(f"    ✅ Tool added successfully (Target ID: {target_id})")
            added_tools.append(tool_def["name"])

            # Add delay to avoid throttling
            time.sleep(2)

        except Exception as e:
            print(f"    ❌ Error adding tool: {e}")

    print(f"\n{'=' * 60}")
    if added_tools:
        print(f"✅ Successfully added {len(added_tools)} MCP tools:")
        for tool in added_tools:
            print(f"   - {tool}")
    else:
        print("❌ No tools were added")
        sys.exit(1)

    print(f"{'=' * 60}")
    print(f"\nGateway {AGENTCORE_GATEWAY_ID} is now ready to use!")


if __name__ == "__main__":
    add_gateway_targets()
