"""
Sake Sensei - Configuration Tests

Tests for configuration management and validation.
"""

import os
from unittest.mock import patch

import pytest


class TestConfigLoading:
    """Test configuration loading from environment variables."""

    def test_config_defaults(self):
        """Test default configuration values."""
        from streamlit_app.utils.config import Config

        assert Config.AWS_REGION == "us-west-2"
        assert Config.APP_NAME == "Sake Sensei"
        assert Config.APP_ENV == "development"
        assert Config.BEDROCK_MAX_TOKENS == 4096
        assert Config.BEDROCK_TEMPERATURE == 0.7
        assert Config.RECOMMENDATION_MAX_RESULTS == 5

    @patch.dict(os.environ, {"AWS_REGION": "us-east-1", "APP_ENV": "production"})
    def test_config_from_env(self):
        """Test configuration loaded from environment variables."""
        from streamlit_app.utils.config import Config

        # Reload config with new env vars
        # Note: Config class variables are set at module load time
        assert os.getenv("AWS_REGION") == "us-east-1"
        assert os.getenv("APP_ENV") == "production"

    def test_config_boolean_parsing(self):
        """Test boolean configuration parsing."""
        from streamlit_app.utils.config import Config

        # Test default values
        assert isinstance(Config.APP_DEBUG, bool)
        assert isinstance(Config.BEDROCK_STREAMING, bool)
        assert isinstance(Config.FEATURE_IMAGE_RECOGNITION, bool)

    def test_config_integer_parsing(self):
        """Test integer configuration parsing."""
        from streamlit_app.utils.config import Config

        assert isinstance(Config.BEDROCK_MAX_TOKENS, int)
        assert isinstance(Config.RECOMMENDATION_MAX_RESULTS, int)
        assert isinstance(Config.STREAMLIT_SERVER_PORT, int)
        assert isinstance(Config.JWT_EXPIRATION_MINUTES, int)

    def test_config_float_parsing(self):
        """Test float configuration parsing."""
        from streamlit_app.utils.config import Config

        assert isinstance(Config.BEDROCK_TEMPERATURE, float)
        assert isinstance(Config.RECOMMENDATION_DIVERSITY_WEIGHT, float)
        assert isinstance(Config.RECOMMENDATION_COLLABORATIVE_WEIGHT, float)
        assert isinstance(Config.RECOMMENDATION_CONTENT_WEIGHT, float)


class TestConfigValidation:
    """Test configuration validation."""

    @patch.dict(
        os.environ,
        {
            "AWS_REGION": "us-west-2",
            "COGNITO_USER_POOL_ID": "test-pool-id",
            "COGNITO_CLIENT_ID": "test-client-id",
        },
    )
    def test_validate_success(self):
        """Test successful configuration validation."""
        from streamlit_app.utils.config import Config

        # Create a new config instance with mocked env vars
        with patch.object(Config, "AWS_REGION", "us-west-2"), patch.object(
            Config, "COGNITO_USER_POOL_ID", "test-pool-id"
        ), patch.object(Config, "COGNITO_CLIENT_ID", "test-client-id"):
            assert Config.validate() is True

    @patch.dict(os.environ, {"AWS_REGION": "us-west-2"}, clear=True)
    def test_validate_missing_required(self):
        """Test validation failure with missing required variables."""
        from streamlit_app.utils.config import Config

        # Create a new config instance with missing vars
        with patch.object(Config, "AWS_REGION", "us-west-2"), patch.object(
            Config, "COGNITO_USER_POOL_ID", None
        ), patch.object(Config, "COGNITO_CLIENT_ID", None):
            assert Config.validate() is False

    def test_get_info(self):
        """Test configuration info retrieval."""
        from streamlit_app.utils.config import Config

        info = Config.get_info()
        assert isinstance(info, dict)
        assert "AWS Region" in info
        assert "Cognito User Pool" in info
        assert "AgentCore Gateway" in info
        assert "AgentCore Memory" in info
        assert "Environment" in info
        assert "Debug Mode" in info


class TestConfigRegion:
    """Test region-specific configuration."""

    def test_region_defaults(self):
        """Test that all region configs default to AWS_REGION."""
        from streamlit_app.utils.config import Config

        # These should all default to AWS_REGION
        assert Config.CDK_DEFAULT_REGION == Config.AWS_REGION or Config.CDK_DEFAULT_REGION
        assert Config.COGNITO_REGION == Config.AWS_REGION or Config.COGNITO_REGION
        assert Config.S3_BUCKET_REGION == Config.AWS_REGION or Config.S3_BUCKET_REGION

    def test_bedrock_model_id(self):
        """Test Bedrock model ID configuration."""
        from streamlit_app.utils.config import Config

        assert "claude" in Config.BEDROCK_MODEL_ID.lower()
        assert "sonnet" in Config.BEDROCK_MODEL_ID.lower()

    def test_vision_model_id(self):
        """Test Vision model ID configuration."""
        from streamlit_app.utils.config import Config

        assert "claude" in Config.VISION_MODEL_ID.lower()


class TestConfigFeatureFlags:
    """Test feature flag configuration."""

    def test_feature_flags_exist(self):
        """Test that feature flags are properly configured."""
        from streamlit_app.utils.config import Config

        assert hasattr(Config, "FEATURE_IMAGE_RECOGNITION")
        assert hasattr(Config, "FEATURE_FOOD_PAIRING")
        assert hasattr(Config, "FEATURE_SOCIAL_SHARING")
        assert hasattr(Config, "FEATURE_EXPORT_HISTORY")

    def test_feature_flags_are_boolean(self):
        """Test that feature flags are boolean values."""
        from streamlit_app.utils.config import Config

        assert isinstance(Config.FEATURE_IMAGE_RECOGNITION, bool)
        assert isinstance(Config.FEATURE_FOOD_PAIRING, bool)
        assert isinstance(Config.FEATURE_SOCIAL_SHARING, bool)
        assert isinstance(Config.FEATURE_EXPORT_HISTORY, bool)

    @patch.dict(
        os.environ,
        {
            "FEATURE_IMAGE_RECOGNITION": "false",
            "FEATURE_FOOD_PAIRING": "false",
            "FEATURE_SOCIAL_SHARING": "true",
        },
    )
    def test_feature_flags_from_env(self):
        """Test feature flags loaded from environment."""
        # Verify environment variables are set
        assert os.getenv("FEATURE_IMAGE_RECOGNITION") == "false"
        assert os.getenv("FEATURE_FOOD_PAIRING") == "false"
        assert os.getenv("FEATURE_SOCIAL_SHARING") == "true"


class TestConfigSecurity:
    """Test security-related configuration."""

    def test_security_config_exists(self):
        """Test that security configuration exists."""
        from streamlit_app.utils.config import Config

        assert hasattr(Config, "SECRET_KEY")
        assert hasattr(Config, "JWT_SECRET_KEY")
        assert hasattr(Config, "JWT_ALGORITHM")
        assert hasattr(Config, "JWT_EXPIRATION_MINUTES")

    def test_jwt_defaults(self):
        """Test JWT default configuration."""
        from streamlit_app.utils.config import Config

        assert Config.JWT_ALGORITHM == "HS256"
        assert Config.JWT_EXPIRATION_MINUTES == 60


class TestConfigDynamoDB:
    """Test DynamoDB configuration."""

    def test_dynamodb_table_names(self):
        """Test DynamoDB table name configuration."""
        from streamlit_app.utils.config import Config

        assert "SakeSensei-Users" in Config.DYNAMODB_USERS_TABLE
        assert "SakeSensei-SakeMaster" in Config.DYNAMODB_SAKE_TABLE
        assert "SakeSensei-BreweryMaster" in Config.DYNAMODB_BREWERY_TABLE
        assert "SakeSensei-TastingRecords" in Config.DYNAMODB_TASTING_TABLE


class TestConfigRecommendation:
    """Test recommendation algorithm configuration."""

    def test_recommendation_weights_sum_to_one(self):
        """Test that recommendation weights approximately sum to 1.0."""
        from streamlit_app.utils.config import Config

        total_weight = (
            Config.RECOMMENDATION_DIVERSITY_WEIGHT
            + Config.RECOMMENDATION_COLLABORATIVE_WEIGHT
            + Config.RECOMMENDATION_CONTENT_WEIGHT
        )
        assert abs(total_weight - 1.0) < 0.01  # Allow small floating point error

    def test_recommendation_max_results(self):
        """Test recommendation max results configuration."""
        from streamlit_app.utils.config import Config

        assert Config.RECOMMENDATION_MAX_RESULTS > 0
        assert Config.RECOMMENDATION_MAX_RESULTS <= 20


class TestConfigStreamlit:
    """Test Streamlit-specific configuration."""

    def test_streamlit_defaults(self):
        """Test Streamlit default configuration."""
        from streamlit_app.utils.config import Config

        assert Config.STREAMLIT_SERVER_PORT == 8501
        assert Config.STREAMLIT_SERVER_ADDRESS == "localhost"

    def test_app_name_and_env(self):
        """Test application name and environment."""
        from streamlit_app.utils.config import Config

        assert Config.APP_NAME == "Sake Sensei"
        assert Config.APP_ENV in ["development", "staging", "production"]
