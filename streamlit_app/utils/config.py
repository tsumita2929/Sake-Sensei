"""
Sake Sensei - Configuration Management

Loads configuration from environment variables and provides app-wide settings.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """Application configuration."""

    # AWS Configuration
    AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
    AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")

    # Cognito Configuration
    COGNITO_REGION = os.getenv("COGNITO_REGION", AWS_REGION)
    COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
    COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
    COGNITO_DOMAIN = os.getenv("COGNITO_DOMAIN", "")

    # AgentCore Configuration
    AGENTCORE_GATEWAY_URL = os.getenv("AGENTCORE_GATEWAY_URL", "")
    AGENTCORE_GATEWAY_ID = os.getenv("AGENTCORE_GATEWAY_ID")
    AGENTCORE_GATEWAY_ARN = os.getenv("AGENTCORE_GATEWAY_ARN")
    AGENTCORE_RUNTIME_URL = os.getenv("AGENTCORE_RUNTIME_URL", "")
    AGENTCORE_AGENT_ID = os.getenv("AGENTCORE_AGENT_ID", "")
    AGENTCORE_MEMORY_ID = os.getenv("AGENTCORE_MEMORY_ID")

    # Lambda Function ARNs
    LAMBDA_RECOMMENDATION_ARN = os.getenv("LAMBDA_RECOMMENDATION_ARN")
    LAMBDA_PREFERENCE_ARN = os.getenv("LAMBDA_PREFERENCE_ARN")
    LAMBDA_TASTING_ARN = os.getenv("LAMBDA_TASTING_ARN")
    LAMBDA_BREWERY_ARN = os.getenv("LAMBDA_BREWERY_ARN")
    LAMBDA_IMAGE_RECOGNITION_ARN = os.getenv("LAMBDA_IMAGE_RECOGNITION_ARN")

    # DynamoDB Configuration
    DYNAMODB_USERS_TABLE = os.getenv("DYNAMODB_USERS_TABLE", "SakeSensei-Users")
    DYNAMODB_SAKE_TABLE = os.getenv("DYNAMODB_SAKE_TABLE", "SakeSensei-SakeMaster")
    DYNAMODB_BREWERY_TABLE = os.getenv("DYNAMODB_BREWERY_TABLE", "SakeSensei-BreweryMaster")
    DYNAMODB_TASTING_TABLE = os.getenv("DYNAMODB_TASTING_TABLE", "SakeSensei-TastingRecords")

    # S3 Configuration
    S3_BUCKET_IMAGES = os.getenv("S3_BUCKET_IMAGES", f"sakesensei-images-{AWS_ACCOUNT_ID}")

    # Application Configuration
    APP_NAME = os.getenv("APP_NAME", "Sake Sensei")
    APP_ENV = os.getenv("APP_ENV", "dev")
    APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"

    # Bedrock Model Configuration
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-sonnet-4-5-v2:0")
    VISION_MODEL_ID = os.getenv("VISION_MODEL_ID", "anthropic.claude-sonnet-4-5-v2:0")

    # Feature Flags
    FEATURE_IMAGE_RECOGNITION = os.getenv("FEATURE_IMAGE_RECOGNITION", "true").lower() == "true"
    FEATURE_FOOD_PAIRING = os.getenv("FEATURE_FOOD_PAIRING", "true").lower() == "true"
    FEATURE_SOCIAL_SHARING = os.getenv("FEATURE_SOCIAL_SHARING", "false").lower() == "true"
    FEATURE_EXPORT_HISTORY = os.getenv("FEATURE_EXPORT_HISTORY", "true").lower() == "true"

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present."""
        required_vars = [
            "AWS_REGION",
            "COGNITO_USER_POOL_ID",
            "COGNITO_CLIENT_ID",
        ]

        missing = []
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)

        if missing:
            print(f"⚠️  Missing required configuration: {', '.join(missing)}")
            return False

        return True

    @classmethod
    def get_info(cls) -> dict:
        """Get configuration summary for debugging."""
        return {
            "AWS Region": cls.AWS_REGION,
            "Cognito User Pool": cls.COGNITO_USER_POOL_ID,
            "AgentCore Gateway": cls.AGENTCORE_GATEWAY_ID,
            "AgentCore Memory": cls.AGENTCORE_MEMORY_ID,
            "Environment": cls.APP_ENV,
            "Debug Mode": cls.APP_DEBUG,
        }


# Create config instance
config = Config()

# Validate on import
if not config.validate():
    print("⚠️  Warning: Some required configuration is missing. App may not function correctly.")
    print("Please check your .env file and ensure all required variables are set.")
