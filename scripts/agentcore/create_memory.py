#!/usr/bin/env python3
"""
Sake Sensei - Create AgentCore Memory

Creates an AgentCore Memory store for user preferences and conversation history.
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
MEMORY_NAME = os.getenv(
    "MEMORY_NAME", "SakeSensei_Memory"
)  # No hyphens, only underscores/alphanumeric
MEMORY_DESCRIPTION = os.getenv(
    "MEMORY_DESCRIPTION", "Memory store for Sake Sensei user preferences and conversation history"
)
# eventExpiryDuration is in days (min 7, max 365)
raw_days = int(os.getenv("AGENTCORE_MEMORY_TTL", "86400")) // 86400
EVENT_EXPIRY_DAYS = max(7, min(raw_days, 365))  # Clamp between 7 and 365


def create_memory():
    """Create AgentCore Memory with strategies for user preferences and conversation history."""

    print(f"Creating AgentCore Memory: {MEMORY_NAME}")
    print(f"Region: {AWS_REGION}")
    print(f"Event expiry: {EVENT_EXPIRY_DAYS} days")

    # Initialize Bedrock Agent client
    try:
        client = boto3.client(
            "bedrock-agent",
            region_name=AWS_REGION,
        )
    except Exception as e:
        print(f"Error initializing bedrock-agentcore-control client: {e}")
        sys.exit(1)

    # Define memory strategies for Sake Sensei
    # Note: Each strategy is a separate dict with only one key (tagged union)
    strategies = [
        {
            "semanticMemoryStrategy": {
                "name": "sake_preferences_facts",
                "description": "Extracts and stores factual information about user sake preferences",
                "namespaces": ["sake/user/{actorId}/preferences"],
            }
        },
        {
            "summaryMemoryStrategy": {
                "name": "conversation_summary",
                "description": "Captures summaries of sake recommendation conversations",
                "namespaces": ["sake/user/{actorId}/{sessionId}"],
            }
        },
        {
            "userPreferenceMemoryStrategy": {
                "name": "user_sake_preferences",
                "description": "Stores user sake preferences and tasting history",
                "namespaces": ["sake/user/{actorId}/profile"],
            }
        },
    ]

    # Create Memory
    try:
        print("\nCreating memory resource...")
        # eventExpiryDuration is in days (max 365)

        response = client.create_memory(
            name=MEMORY_NAME,
            description=MEMORY_DESCRIPTION,
            memoryStrategies=strategies,
            eventExpiryDuration=EVENT_EXPIRY_DAYS,
        )

        # Extract memory info from response
        memory_id = response.get("id") or response.get("memoryId")
        memory_arn = response.get("arn") or response.get("memoryArn")
        status = response.get("status", "CREATING")

        print("\n✅ Memory created successfully!")
        print(f"Memory ID: {memory_id}")
        print(f"Memory ARN: {memory_arn}")
        print(f"Status: {status}")

        # Update .env file
        env_file = project_root / ".env"
        if env_file.exists():
            try:
                set_key(str(env_file), "AGENTCORE_MEMORY_ID", memory_id)
                set_key(str(env_file), "AGENTCORE_MEMORY_ARN", memory_arn)
                print(f"\n✅ Updated {env_file} with memory information")
            except Exception as e:
                print(f"\n⚠️  Warning: Failed to update .env file: {e}")
        else:
            print(f"\n⚠️  Warning: .env file not found at {env_file}")
            print("Please manually add:")
            print(f"  AGENTCORE_MEMORY_ID={memory_id}")
            print(f"  AGENTCORE_MEMORY_ARN={memory_arn}")

        # Check memory status
        print("\nChecking memory status...")
        try:
            status_response = client.get_memory(memoryId=memory_id)
            memory_data = status_response.get("memory", {})
            current_status = memory_data.get("status", "UNKNOWN")
            strategies = memory_data.get("strategies", [])

            print(f"Memory status: {current_status}")
            print(f"Configured strategies: {len(strategies)}")

            if current_status == "ACTIVE":
                print("✅ Memory is active and ready to use!")
            elif current_status == "CREATING":
                print("⚠️  Memory is still being created. It should be ready shortly.")
            else:
                print(f"⚠️  Memory is in {current_status} state.")
        except Exception as e:
            print(f"⚠️  Could not check memory status: {e}")
            print("Memory creation initiated. Check status manually if needed.")

        return memory_id

    except Exception as e:
        error_msg = str(e)
        if "AlreadyExistsException" in error_msg or "already exists" in error_msg.lower():
            print(f"\n⚠️  Memory '{MEMORY_NAME}' already exists")
            print("Attempting to retrieve existing memory ID...")

            try:
                # List memories to find existing one
                list_response = client.list_memories()
                memories = list_response.get("memories", [])

                for memory in memories:
                    # Memory ID format: {NAME}-{SUFFIX}
                    memory_id = memory.get("id", "")
                    if memory_id.startswith(MEMORY_NAME):
                        memory_arn = memory.get("arn", "")
                        print(f"✅ Found existing memory: {memory_id}")
                        print(f"   ARN: {memory_arn}")

                        # Update .env file
                        env_file = project_root / ".env"
                        if env_file.exists():
                            set_key(str(env_file), "AGENTCORE_MEMORY_ID", memory_id)
                            set_key(str(env_file), "AGENTCORE_MEMORY_ARN", memory_arn)
                            print("✅ Updated .env with existing memory information")

                        return memory_id

                print("❌ Could not find existing memory in list")
                sys.exit(1)

            except Exception as list_error:
                print(f"❌ Error listing memories: {list_error}")
                sys.exit(1)
        else:
            print(f"\n❌ Error creating memory: {e}")
            sys.exit(1)


if __name__ == "__main__":
    create_memory()
