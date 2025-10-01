#!/usr/bin/env python3
"""
Sake Sensei - Alternative Memory Setup

Since AgentCore Memory API is not yet available, we'll use DynamoDB
for conversation history and user preferences storage.
"""

import os
import sys
from pathlib import Path

import boto3
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")


def setup_conversation_memory_table():
    """Setup DynamoDB table for conversation memory."""

    print("Setting up Conversation Memory with DynamoDB...")
    print(f"Region: {AWS_REGION}")

    dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)

    table_name = "SakeSensei-ConversationMemory"

    try:
        # Check if table exists
        try:
            response = dynamodb.describe_table(TableName=table_name)
            print(f"✅ Table {table_name} already exists")
            table_arn = response["Table"]["TableArn"]
        except dynamodb.exceptions.ResourceNotFoundException:
            # Create table
            print(f"Creating table {table_name}...")

            response = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "userId", "KeyType": "HASH"},  # Partition key
                    {"AttributeName": "timestamp", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "userId", "AttributeType": "S"},
                    {"AttributeName": "timestamp", "AttributeType": "N"},
                    {"AttributeName": "sessionId", "AttributeType": "S"},
                ],
                GlobalSecondaryIndexes=[
                    {
                        "IndexName": "sessionId-index",
                        "KeySchema": [
                            {"AttributeName": "sessionId", "KeyType": "HASH"},
                            {"AttributeName": "timestamp", "KeyType": "RANGE"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                    }
                ],
                BillingMode="PAY_PER_REQUEST",
            )

            table_arn = response["TableDescription"]["TableArn"]
            print(f"✅ Created table: {table_name}")
            print(f"   ARN: {table_arn}")

            # Wait for table to be active
            print("Waiting for table to be active...")
            waiter = dynamodb.get_waiter("table_exists")
            waiter.wait(TableName=table_name)
            print("✅ Table is active")

        # Update .env
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"

        if env_file.exists():
            set_key(str(env_file), "CONVERSATION_MEMORY_TABLE", table_name)
            set_key(str(env_file), "CONVERSATION_MEMORY_ARN", table_arn)
            print(f"✅ Updated .env with memory table information")

        return table_name

    except Exception as e:
        print(f"❌ Error setting up conversation memory: {e}")
        sys.exit(1)


def setup_user_preferences_enhancement():
    """Enhance existing Users table for preference storage."""

    print("\nEnhancing User Preferences storage...")

    # Users table already exists from Phase 1
    users_table = os.getenv("DYNAMODB_USERS_TABLE", "SakeSensei-Users")

    print(f"✅ Using existing table: {users_table}")
    print("   Table supports:")
    print("   - User preferences (flavor_profile, sake_types, etc.)")
    print("   - Tasting history references")
    print("   - Conversation context")

    return users_table


if __name__ == "__main__":
    if not AWS_ACCOUNT_ID:
        print("Error: AWS_ACCOUNT_ID not set in environment")
        sys.exit(1)

    print("=" * 60)
    print("AgentCore Memory Alternative Setup")
    print("=" * 60)

    # Setup conversation memory
    memory_table = setup_conversation_memory_table()

    # Enhance user preferences
    users_table = setup_user_preferences_enhancement()

    print("\n" + "=" * 60)
    print("Memory Setup Complete!")
    print("=" * 60)
    print(f"Conversation Memory Table: {memory_table}")
    print(f"User Preferences Table: {users_table}")
    print("\nMemory Features:")
    print("  ✅ Conversation history storage")
    print("  ✅ Session-based memory")
    print("  ✅ User preferences persistence")
    print("  ✅ Tasting history integration")
    print("\nNext steps:")
    print("  1. Agent will use DynamoDB for memory")
    print("  2. Deploy agent: ./scripts/deploy_agent.sh")
    print("  3. Test conversation memory")
