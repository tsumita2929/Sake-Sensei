#!/usr/bin/env python3
"""
Add remaining Gateway targets (brewery and image_recognition).
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
LAMBDA_BREWERY_ARN = os.getenv("LAMBDA_BREWERY_ARN")
LAMBDA_IMAGE_RECOGNITION_ARN = os.getenv("LAMBDA_IMAGE_RECOGNITION_ARN")

client = boto3.client("bedrock-agentcore-control", region_name=AWS_REGION)

credential_config = [{"credentialProviderType": "GATEWAY_IAM_ROLE"}]

# Tool 1: Brewery
print("Adding brewery tool...")
try:
    response = client.create_gateway_target(
        gatewayIdentifier=AGENTCORE_GATEWAY_ID,
        name="SakeSensei-Brewery",
        description="Target for get_brewery_info Lambda function",
        credentialProviderConfigurations=credential_config,
        targetConfiguration={
            "mcp": {
                "lambda": {
                    "lambdaArn": LAMBDA_BREWERY_ARN,
                    "toolSchema": {
                        "inlinePayload": [
                            {
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
                            }
                        ]
                    },
                }
            }
        },
    )
    print(f"✅ Brewery tool added (Target ID: {response['targetId']})")
except Exception as e:
    print(f"❌ Error: {e}")

time.sleep(3)

# Tool 2: Image Recognition
print("\nAdding image recognition tool...")
try:
    response = client.create_gateway_target(
        gatewayIdentifier=AGENTCORE_GATEWAY_ID,
        name="SakeSensei-ImageRecognition",
        description="Target for recognize_sake_label Lambda function",
        credentialProviderConfigurations=credential_config,
        targetConfiguration={
            "mcp": {
                "lambda": {
                    "lambdaArn": LAMBDA_IMAGE_RECOGNITION_ARN,
                    "toolSchema": {
                        "inlinePayload": [
                            {
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
                            }
                        ]
                    },
                }
            }
        },
    )
    print(f"✅ Image recognition tool added (Target ID: {response['targetId']})")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Done!")
