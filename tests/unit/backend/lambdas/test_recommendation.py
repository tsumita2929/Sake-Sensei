"""
Unit tests for Recommendation Lambda function.
"""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestRecommendationLambda:
    """Tests for Recommendation Lambda handler."""

    def test_handler_missing_user_id(self, lambda_context):
        """Test handler with missing user_id."""
        from backend.lambdas.recommendation.handler import handler

        event = {"body": json.dumps({})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "BadRequest"
        assert "user_id" in body["message"]

    def test_handler_with_preferences(self, lambda_context, mock_dynamodb_table):
        """Test handler with user preferences."""
        from backend.lambdas.recommendation.handler import handler

        # Mock user preferences
        mock_dynamodb_table.get_item.return_value = {
            "Item": {
                "user_id": "test_user",
                "flavor_preference": "light",
                "sweetness": 3,
                "dryness": 7,
            }
        }

        # Mock sake database query
        mock_dynamodb_table.scan.return_value = {
            "Items": [
                {
                    "sake_id": "S001",
                    "name": "獺祭",
                    "category": "junmai_daiginjo",
                    "flavor_profile": {"sweetness": 3, "dryness": 7, "umami": 5},
                }
            ]
        }

        event = {"body": json.dumps({"user_id": "test_user"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "data" in body
        assert "recommendations" in body["data"]

    def test_handler_invalid_limit(self, lambda_context):
        """Test handler with invalid limit parameter."""
        from backend.lambdas.recommendation.handler import handler

        event = {"body": json.dumps({"user_id": "test_user", "limit": -1})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 400

    def test_handler_with_category_filter(self, lambda_context, mock_dynamodb_table):
        """Test handler with category filter."""
        from backend.lambdas.recommendation.handler import handler

        mock_dynamodb_table.get_item.return_value = {"Item": {"user_id": "test_user"}}
        mock_dynamodb_table.scan.return_value = {"Items": []}

        event = {
            "body": json.dumps({"user_id": "test_user", "category": "junmai_daiginjo"})
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200


class TestRecommendationAlgorithm:
    """Tests for recommendation algorithm."""

    def test_calculate_match_score(self):
        """Test match score calculation."""
        from backend.lambdas.recommendation.algorithm import RecommendationEngine

        engine = RecommendationEngine()

        user_prefs = {"sweetness": 5, "dryness": 5, "umami": 5}
        sake_profile = {"sweetness": 5, "dryness": 5, "umami": 5}

        score = engine._calculate_match_score(user_prefs, sake_profile)

        # Perfect match should have high score
        assert score > 0.9

    def test_calculate_match_score_mismatch(self):
        """Test match score with mismatched profiles."""
        from backend.lambdas.recommendation.algorithm import RecommendationEngine

        engine = RecommendationEngine()

        user_prefs = {"sweetness": 1, "dryness": 1, "umami": 1}
        sake_profile = {"sweetness": 10, "dryness": 10, "umami": 10}

        score = engine._calculate_match_score(user_prefs, sake_profile)

        # Mismatch should have low score
        assert score < 0.5

    def test_recommend_with_empty_sake_list(self):
        """Test recommendation with empty sake list."""
        from backend.lambdas.recommendation.algorithm import RecommendationEngine

        engine = RecommendationEngine()

        recommendations = engine.recommend(
            user_preferences={"sweetness": 5}, sake_list=[], limit=5
        )

        assert len(recommendations) == 0

    def test_recommend_respects_limit(self):
        """Test that recommendation respects limit parameter."""
        from backend.lambdas.recommendation.algorithm import RecommendationEngine

        engine = RecommendationEngine()

        sake_list = [
            {
                "sake_id": f"S{i:03d}",
                "name": f"Sake {i}",
                "flavor_profile": {"sweetness": i % 10, "dryness": 10 - (i % 10)},
            }
            for i in range(20)
        ]

        recommendations = engine.recommend(
            user_preferences={"sweetness": 5, "dryness": 5}, sake_list=sake_list, limit=5
        )

        assert len(recommendations) <= 5
