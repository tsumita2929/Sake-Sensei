"""
Sake Sensei - Preference Lambda Handler

Manages user preference settings for sake recommendations.
"""

import json
import os
from typing import Any

import boto3
from pydantic import ValidationError

from backend.lambdas.layer.error_handler import handle_errors
from backend.lambdas.layer.logger import get_logger
from backend.lambdas.layer.response import (
    bad_request_response,
    not_found_response,
    success_response,
    unauthorized_response,
)
from backend.models.user import UserPreferences

logger = get_logger(__name__)

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb")
users_table = dynamodb.Table(os.getenv("USERS_TABLE", "SakeSensei-Users"))


@handle_errors
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler for user preference management.

    Supported operations:
    - GET /api/preferences/{user_id} - Get user preferences
    - PUT /api/preferences/{user_id} - Update user preferences
    - POST /api/preferences - Create initial preferences (from survey)

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    http_method = event.get("httpMethod", "GET")
    path_parameters = event.get("pathParameters", {})
    user_id = path_parameters.get("user_id")

    # Get authenticated user from authorizer
    auth_user_id = event.get("requestContext", {}).get("authorizer", {}).get("user_id")

    # Parse request body for POST/PUT
    body = {}
    if http_method in ["POST", "PUT"]:
        body = (
            json.loads(event.get("body", "{}"))
            if isinstance(event.get("body"), str)
            else event.get("body", {})
        )

    # Route to appropriate handler
    if http_method == "GET":
        return handle_get_preferences(user_id, auth_user_id)
    elif http_method == "PUT":
        return handle_update_preferences(user_id, body, auth_user_id)
    elif http_method == "POST":
        return handle_create_preferences(body, auth_user_id)
    else:
        return bad_request_response(f"Unsupported method: {http_method}")


def handle_get_preferences(user_id: str | None, auth_user_id: str | None) -> dict[str, Any]:
    """Get user preferences.

    Args:
        user_id: User ID from path parameter
        auth_user_id: Authenticated user ID

    Returns:
        User preferences or error response
    """
    if not user_id:
        return bad_request_response("user_id is required")

    # Verify user can only access their own preferences
    if auth_user_id and auth_user_id != user_id:
        logger.warning(
            "Unauthorized preference access attempt",
            auth_user_id=auth_user_id,
            target_user_id=user_id,
        )
        return unauthorized_response("Cannot access other user's preferences")

    logger.info("Getting user preferences", user_id=user_id)

    try:
        response = users_table.get_item(Key={"user_id": user_id})

        if "Item" not in response:
            logger.warning("User not found", user_id=user_id)
            return not_found_response("User")

        user = response["Item"]
        preferences = user.get("preferences", {})

        return success_response({"preferences": preferences})

    except Exception as e:
        logger.error("Failed to get preferences", user_id=user_id, error=str(e))
        raise


def handle_update_preferences(
    user_id: str | None, body: dict[str, Any], auth_user_id: str | None
) -> dict[str, Any]:
    """Update user preferences.

    Args:
        user_id: User ID from path parameter
        body: Request body with preferences
        auth_user_id: Authenticated user ID

    Returns:
        Updated preferences or error response
    """
    if not user_id:
        return bad_request_response("user_id is required")

    # Verify user can only update their own preferences
    if auth_user_id and auth_user_id != user_id:
        logger.warning(
            "Unauthorized preference update attempt",
            auth_user_id=auth_user_id,
            target_user_id=user_id,
        )
        return unauthorized_response("Cannot update other user's preferences")

    # Extract preferences from body
    preferences_data = body.get("preferences", {})
    if not preferences_data:
        return bad_request_response("preferences is required")

    # Validate preferences using Pydantic model
    try:
        preferences = UserPreferences(**preferences_data)
    except ValidationError as e:
        logger.warning("Invalid preferences data", user_id=user_id, errors=e.errors())
        raise

    logger.info("Updating user preferences", user_id=user_id)

    try:
        # Update preferences in DynamoDB
        response = users_table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET preferences = :prefs, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":prefs": preferences.model_dump(),
                ":updated_at": body.get("updated_at", ""),
            },
            ReturnValues="ALL_NEW",
        )

        updated_preferences = response["Attributes"].get("preferences", {})

        logger.info("Preferences updated successfully", user_id=user_id)

        return success_response({"preferences": updated_preferences})

    except Exception as e:
        logger.error("Failed to update preferences", user_id=user_id, error=str(e))
        raise


def handle_create_preferences(body: dict[str, Any], auth_user_id: str | None) -> dict[str, Any]:
    """Create initial user preferences (from survey).

    Args:
        body: Request body with user_id and preferences
        auth_user_id: Authenticated user ID

    Returns:
        Created preferences or error response
    """
    user_id = body.get("user_id")
    if not user_id:
        # Use authenticated user ID if not provided
        user_id = auth_user_id

    if not user_id:
        return bad_request_response("user_id is required")

    # Extract preferences from body
    preferences_data = body.get("preferences", {})
    if not preferences_data:
        return bad_request_response("preferences is required")

    # Validate preferences using Pydantic model
    try:
        preferences = UserPreferences(**preferences_data)
    except ValidationError as e:
        logger.warning("Invalid preferences data", user_id=user_id, errors=e.errors())
        raise

    logger.info("Creating user preferences", user_id=user_id)

    try:
        # Create or update user record with preferences
        users_table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET preferences = :prefs, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":prefs": preferences.model_dump(),
                ":updated_at": body.get("updated_at", ""),
            },
        )

        logger.info("Preferences created successfully", user_id=user_id)

        return success_response({"preferences": preferences.model_dump()})

    except Exception as e:
        logger.error("Failed to create preferences", user_id=user_id, error=str(e))
        raise
