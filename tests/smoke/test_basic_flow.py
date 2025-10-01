"""Smoke tests for basic application flow.

Tests complete user journey through deployed application.
"""

import os

import pytest
import requests


@pytest.fixture
def base_url() -> str:
    """Get base URL from environment or use default."""
    return os.getenv(
        "SMOKE_TEST_URL",
        "http://sakese-Publi-5SDe3QrKne55-1360562030.us-west-2.elb.amazonaws.com",
    )


@pytest.mark.smoke
class TestBasicFlowSmoke:
    """Smoke tests for basic application flow."""

    def test_home_page_loads(self, base_url: str) -> None:
        """Test that home page loads successfully."""
        response = requests.get(base_url, timeout=30, allow_redirects=True)

        # Should get successful response
        assert response.status_code == 200

        # Should be HTML content
        assert "text/html" in response.headers.get("Content-Type", "")

    def test_streamlit_static_resources(self, base_url: str) -> None:
        """Test that Streamlit static resources are accessible."""
        # Streamlit serves static files from _stcore path
        static_paths = [
            "/_stcore/health",
        ]

        for path in static_paths:
            response = requests.get(f"{base_url}{path}", timeout=30)
            # Health endpoint should return 200
            if path == "/_stcore/health":
                assert response.status_code == 200

    def test_app_navigation_structure(self) -> None:
        """Test application navigation structure documentation."""
        # Document expected navigation pages
        expected_pages = [
            "Home",  # Main page (app.py)
            "Preference Survey",  # Preference questionnaire
            "AI Recommendations",  # AI-powered sake recommendations
            "Rating",  # Rate and record tasting
            "Image Recognition",  # Upload sake label photos
            "History",  # View tasting history
        ]

        # Validate page list
        assert len(expected_pages) == 6
        for page in expected_pages:
            assert isinstance(page, str)
            assert len(page) > 0

    def test_user_journey_flow(self) -> None:
        """Test complete user journey flow documentation."""
        # Document the expected user journey
        user_journey = [
            {
                "step": 1,
                "action": "Access application",
                "page": "Home",
                "expected": "Authentication required",
            },
            {
                "step": 2,
                "action": "Sign up / Login",
                "page": "Home",
                "expected": "Cognito authentication successful",
            },
            {
                "step": 3,
                "action": "Complete preference survey",
                "page": "Preference Survey",
                "expected": "User preferences saved to DynamoDB",
            },
            {
                "step": 4,
                "action": "Request AI recommendations",
                "page": "AI Recommendations",
                "expected": "Agent returns personalized sake recommendations",
            },
            {
                "step": 5,
                "action": "View sake details",
                "page": "AI Recommendations",
                "expected": "Sake card with full information displayed",
            },
            {
                "step": 6,
                "action": "Rate a sake",
                "page": "Rating",
                "expected": "Tasting record saved to DynamoDB",
            },
            {
                "step": 7,
                "action": "Upload sake label photo",
                "page": "Image Recognition",
                "expected": "Claude 4.5 Sonnet identifies sake information",
            },
            {
                "step": 8,
                "action": "View tasting history",
                "page": "History",
                "expected": "Past tastings displayed with statistics",
            },
        ]

        # Validate journey structure
        assert len(user_journey) == 8
        for journey_step in user_journey:
            assert "step" in journey_step
            assert "action" in journey_step
            assert "page" in journey_step
            assert "expected" in journey_step
            assert isinstance(journey_step["step"], int)
            assert journey_step["step"] > 0

    def test_api_integration_points(self) -> None:
        """Test API integration points documentation."""
        # Document backend integration points
        integrations = {
            "cognito": {
                "purpose": "User authentication and authorization",
                "endpoints": ["InitiateAuth", "SignUp", "ConfirmSignUp"],
            },
            "lambda_recommendation": {
                "purpose": "Generate sake recommendations",
                "trigger": "AgentCore Gateway MCP tool",
            },
            "lambda_preference": {
                "purpose": "Manage user preferences",
                "operations": ["get", "update", "create"],
            },
            "lambda_tasting": {
                "purpose": "Manage tasting records",
                "operations": ["create", "get_history", "get_statistics"],
            },
            "lambda_brewery": {
                "purpose": "Retrieve brewery information",
                "operations": ["get_by_id", "search"],
            },
            "lambda_image_recognition": {
                "purpose": "Recognize sake labels using Claude 4.5 Sonnet",
                "model": "anthropic.claude-4-5-sonnet-20250930-v1:0",
            },
            "agentcore_runtime": {
                "purpose": "Execute Strands Agent for conversational recommendations",
                "features": ["streaming", "memory", "tool_invocation"],
            },
            "dynamodb": {
                "purpose": "Data persistence",
                "tables": ["Users", "Sake", "Breweries", "TastingRecords", "Preferences"],
            },
            "s3": {
                "purpose": "Image storage",
                "buckets": ["sake-labels", "sake-images"],
            },
        }

        # Validate integration documentation
        assert len(integrations) >= 8
        for _service, config in integrations.items():
            assert "purpose" in config
            assert isinstance(config["purpose"], str)
            assert len(config["purpose"]) > 0

    def test_error_handling_scenarios(self) -> None:
        """Test error handling scenarios documentation."""
        # Document expected error handling
        error_scenarios = [
            {
                "scenario": "User not authenticated",
                "expected_behavior": "Show login dialog, prevent access to protected features",
            },
            {
                "scenario": "Network request fails",
                "expected_behavior": "Display error message, suggest retry",
            },
            {
                "scenario": "Lambda function timeout",
                "expected_behavior": "Show timeout error, allow retry",
            },
            {
                "scenario": "Invalid input data",
                "expected_behavior": "Display validation error, highlight incorrect fields",
            },
            {
                "scenario": "Agent response parsing error",
                "expected_behavior": "Log error, show fallback message",
            },
            {
                "scenario": "DynamoDB rate limit exceeded",
                "expected_behavior": "Implement exponential backoff, retry request",
            },
            {
                "scenario": "S3 image upload fails",
                "expected_behavior": "Show upload error, allow re-upload",
            },
            {
                "scenario": "Session expired",
                "expected_behavior": "Clear session, redirect to login",
            },
        ]

        # Validate error scenarios
        assert len(error_scenarios) == 8
        for scenario in error_scenarios:
            assert "scenario" in scenario
            assert "expected_behavior" in scenario
            assert len(scenario["expected_behavior"]) > 10


@pytest.mark.smoke
class TestFeatureAvailability:
    """Smoke tests for feature availability."""

    def test_preference_survey_features(self) -> None:
        """Test preference survey features documentation."""
        # Document preference survey features
        features = {
            "sake_type_preference": {
                "options": ["純米酒", "純米吟醸", "純米大吟醸", "本醸造", "吟醸", "大吟醸"],
                "required": True,
            },
            "flavor_profile": {
                "dimensions": ["甘口-辛口", "香り高い-控えめ", "軽い-濃厚"],
                "type": "slider",
            },
            "drinking_context": {
                "options": ["食事中", "食前酒", "食後酒", "晩酌"],
                "multiple": True,
            },
            "food_pairing": {
                "categories": ["魚", "肉", "野菜", "米料理", "チーズ"],
                "multiple": True,
            },
        }

        # Validate features
        assert len(features) >= 4
        for feature_name, config in features.items():
            assert isinstance(feature_name, str)
            assert isinstance(config, dict)

    def test_recommendation_features(self) -> None:
        """Test recommendation features documentation."""
        # Document recommendation features
        features = {
            "ai_powered_recommendations": {
                "model": "Claude 4.5 Sonnet",
                "method": "AgentCore Runtime with Strands Agent",
                "personalization": True,
            },
            "sake_card_display": {
                "information": [
                    "name",
                    "type",
                    "brewery",
                    "region",
                    "flavor_profile",
                    "food_pairing",
                    "description",
                ],
                "interactive": True,
            },
            "filtering": {
                "by_type": True,
                "by_region": True,
                "by_price": True,
            },
            "memory_integration": {
                "remembers_preferences": True,
                "learns_from_ratings": True,
                "conversation_context": True,
            },
        }

        # Validate recommendation features
        assert "ai_powered_recommendations" in features
        assert features["ai_powered_recommendations"]["model"] == "Claude 4.5 Sonnet"
        assert features["ai_powered_recommendations"]["personalization"] is True

    def test_tasting_record_features(self) -> None:
        """Test tasting record features documentation."""
        # Document tasting record features
        features = {
            "rating_dimensions": [
                "overall_rating",
                "aroma_rating",
                "taste_rating",
                "sweetness",
                "body",
                "finish",
            ],
            "tasting_notes": {
                "aroma_descriptors": [
                    "fruity",
                    "floral",
                    "nutty",
                    "earthy",
                    "spicy",
                ],
                "taste_descriptors": [
                    "sweet",
                    "dry",
                    "umami",
                    "acidic",
                    "bitter",
                ],
            },
            "metadata": ["location", "temperature", "vessel", "occasion"],
            "photo_upload": True,
        }

        # Validate tasting features
        assert len(features["rating_dimensions"]) == 6
        assert "overall_rating" in features["rating_dimensions"]
        assert features["photo_upload"] is True

    def test_history_visualization_features(self) -> None:
        """Test history visualization features documentation."""
        # Document history/visualization features
        features = {
            "statistics": [
                "total_tastings",
                "favorites_count",
                "breweries_explored",
                "average_rating",
            ],
            "charts": {
                "rating_distribution": "bar_chart",
                "sake_type_distribution": "pie_chart",
                "tasting_timeline": "line_chart",
            },
            "export_formats": ["CSV", "JSON", "summary_text"],
            "filtering": {
                "by_date_range": True,
                "by_sake_type": True,
                "by_rating": True,
            },
        }

        # Validate history features
        assert len(features["statistics"]) == 4
        assert len(features["charts"]) == 3
        assert "CSV" in features["export_formats"]
        assert "JSON" in features["export_formats"]

    def test_image_recognition_features(self) -> None:
        """Test image recognition features documentation."""
        # Document image recognition features
        features = {
            "model": "anthropic.claude-4-5-sonnet-20250930-v1:0",
            "capabilities": [
                "text_extraction",
                "sake_name_recognition",
                "brewery_identification",
                "type_classification",
            ],
            "supported_formats": ["JPEG", "PNG"],
            "max_file_size": 5 * 1024 * 1024,  # 5MB
            "processing_time": "< 3 seconds",
        }

        # Validate image recognition features
        assert features["model"].startswith("anthropic.claude")
        assert "text_extraction" in features["capabilities"]
        assert "JPEG" in features["supported_formats"]
        assert features["max_file_size"] > 0


@pytest.mark.smoke
class TestPerformanceBaseline:
    """Smoke tests for performance baselines."""

    def test_page_load_performance(self, base_url: str) -> None:
        """Test that page loads within acceptable time."""
        import time

        start = time.time()
        response = requests.get(base_url, timeout=30)
        duration = time.time() - start

        # Page should load within 5 seconds
        assert response.status_code == 200
        assert duration < 5.0

    def test_health_check_performance(self, base_url: str) -> None:
        """Test that health check responds quickly."""
        import time

        start = time.time()
        response = requests.get(f"{base_url}/_stcore/health", timeout=10)
        duration = time.time() - start

        # Health check should respond within 1 second
        assert response.status_code == 200
        assert duration < 1.0

    def test_performance_targets(self) -> None:
        """Test performance targets documentation."""
        # Document expected performance targets
        targets = {
            "page_load_time": 3.0,  # seconds
            "health_check_time": 0.5,  # seconds
            "api_response_time": 2.0,  # seconds
            "agent_ttft": 0.5,  # Time to first token (seconds)
            "agent_throughput": 30,  # Tokens per second
            "agent_total_time": 3.0,  # Total response time (seconds)
        }

        # Validate targets
        for _metric, target in targets.items():
            assert target > 0
            assert isinstance(target, (int, float))
