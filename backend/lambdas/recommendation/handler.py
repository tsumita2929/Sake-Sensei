"""
Sake Sensei - Recommendation Lambda Handler

Provides personalized sake recommendations based on user preferences.
"""

import json
import os
from typing import Any

import boto3

# Lambda Layer imports (no 'backend.lambdas.layer' prefix in Lambda environment)
try:
    from error_handler import handle_errors
    from logger import get_logger
    from response import bad_request_response, success_response
except ImportError:
    # Fallback for local development
    from backend.lambdas.layer.error_handler import handle_errors
    from backend.lambdas.layer.logger import get_logger
    from backend.lambdas.layer.response import bad_request_response, success_response

from algorithm import RecommendationEngine

logger = get_logger(__name__)

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb")
sake_table = dynamodb.Table(os.getenv("SAKE_TABLE", "SakeSensei-SakeMaster"))
brewery_table = dynamodb.Table(os.getenv("BREWERY_TABLE", "SakeSensei-BreweryMaster"))
tasting_table = dynamodb.Table(os.getenv("TASTING_TABLE", "SakeSensei-TastingRecords"))


@handle_errors
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler for sake recommendations.

    Expected input (POST /api/recommendations):
    {
        "user_id": "string",
        "preferences": {
            "sweetness": 1-5,
            "acidity": 1-5,
            "richness": 1-5,
            "categories": ["junmai", "ginjo", ...],
            "budget": number,
            "experience_level": "beginner|intermediate|advanced"
        },
        "limit": 10  // optional
    }

    Returns:
        {
            "success": true,
            "data": {
                "recommendations": [
                    {
                        "sake_id": "string",
                        "name": "string",
                        "brewery_id": "string",
                        "category": "string",
                        "score": number,
                        "match_reason": "string"
                    }
                ]
            }
        }
    """
    # Parse request body
    body = (
        json.loads(event.get("body", "{}"))
        if isinstance(event.get("body"), str)
        else event.get("body", {})
    )

    # Extract user_id from request or authorizer context
    user_id = body.get("user_id")
    if not user_id:
        # Try to get from authorizer context if authenticated
        user_id = event.get("requestContext", {}).get("authorizer", {}).get("user_id")

    if not user_id:
        logger.warning("Missing user_id in request")
        return bad_request_response("user_id is required")

    # Extract preferences
    preferences = body.get("preferences", {})
    if not preferences:
        logger.warning("Missing preferences in request", user_id=user_id)
        return bad_request_response("preferences is required")

    # Get limit (default: 10, max: 50)
    limit = min(body.get("limit", 10), 50)

    logger.info(
        "Processing recommendation request",
        user_id=user_id,
        preferences=preferences,
        limit=limit,
    )

    # Initialize recommendation engine
    engine = RecommendationEngine(
        sake_table=sake_table,
        brewery_table=brewery_table,
        tasting_table=tasting_table,
    )

    # Get user's tasting history
    tasting_history = get_tasting_history(user_id)

    # Generate recommendations
    recommendations = engine.recommend(
        user_id=user_id,
        preferences=preferences,
        tasting_history=tasting_history,
        limit=limit,
    )

    logger.info(
        "Generated recommendations",
        user_id=user_id,
        count=len(recommendations),
    )

    return success_response({"recommendations": recommendations})


def get_tasting_history(user_id: str) -> list[dict[str, Any]]:
    """Get user's tasting history from DynamoDB.

    Args:
        user_id: User ID

    Returns:
        List of tasting records
    """
    try:
        response = tasting_table.query(
            KeyConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={":user_id": user_id},
            Limit=50,  # Get last 50 tastings
            ScanIndexForward=False,  # Sort descending by record_id (most recent first)
        )
        return response.get("Items", [])
    except Exception as e:
        logger.error("Failed to get tasting history", user_id=user_id, error=str(e))
        return []
