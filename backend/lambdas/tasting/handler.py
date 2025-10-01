"""
Sake Sensei - Tasting Lambda Handler

Manages tasting records for users.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any

import boto3
from pydantic import ValidationError

# Lambda Layer imports
try:
    from error_handler import handle_errors
    from logger import get_logger
    from response import (
        bad_request_response,
        created_response,
        no_content_response,
        not_found_response,
        success_response,
        unauthorized_response,
    )
except ImportError:
    from backend.lambdas.layer.error_handler import handle_errors
    from backend.lambdas.layer.logger import get_logger
    from backend.lambdas.layer.response import (
        bad_request_response,
        created_response,
        no_content_response,
        not_found_response,
        success_response,
        unauthorized_response,
    )

try:
    from tasting import TastingRecord
except ImportError:
    from backend.models.tasting import TastingRecord

logger = get_logger(__name__)

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb")
tasting_table = dynamodb.Table(os.getenv("TASTING_TABLE", "SakeSensei-TastingRecords"))


@handle_errors
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler for tasting record management.

    Supported operations:
    - GET /api/tasting/{user_id} - List user's tasting records
    - GET /api/tasting/{user_id}/{record_id} - Get specific tasting record
    - POST /api/tasting - Create new tasting record
    - PUT /api/tasting/{user_id}/{record_id} - Update tasting record
    - DELETE /api/tasting/{user_id}/{record_id} - Delete tasting record

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    http_method = event.get("httpMethod", "GET")
    path_parameters = event.get("pathParameters", {})
    user_id = path_parameters.get("user_id")
    record_id = path_parameters.get("record_id")

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
    if http_method == "GET" and record_id:
        return handle_get_record(user_id, record_id, auth_user_id)
    elif http_method == "GET":
        return handle_list_records(user_id, auth_user_id, event.get("queryStringParameters", {}))
    elif http_method == "POST":
        return handle_create_record(body, auth_user_id)
    elif http_method == "PUT":
        return handle_update_record(user_id, record_id, body, auth_user_id)
    elif http_method == "DELETE":
        return handle_delete_record(user_id, record_id, auth_user_id)
    else:
        return bad_request_response(f"Unsupported method: {http_method}")


def handle_list_records(
    user_id: str | None,
    auth_user_id: str | None,
    query_params: dict[str, Any],
) -> dict[str, Any]:
    """List user's tasting records.

    Args:
        user_id: User ID from path parameter
        auth_user_id: Authenticated user ID
        query_params: Query parameters (limit, last_key)

    Returns:
        List of tasting records
    """
    if not user_id:
        return bad_request_response("user_id is required")

    # Verify user can only access their own records
    if auth_user_id and auth_user_id != user_id:
        logger.warning(
            "Unauthorized tasting access attempt",
            auth_user_id=auth_user_id,
            target_user_id=user_id,
        )
        return unauthorized_response("Cannot access other user's tasting records")

    limit = int(query_params.get("limit", 20))
    last_key = query_params.get("last_key")

    logger.info("Listing tasting records", user_id=user_id, limit=limit)

    try:
        query_params_dict: dict[str, Any] = {
            "KeyConditionExpression": "user_id = :user_id",
            "ExpressionAttributeValues": {":user_id": user_id},
            "Limit": limit,
            "ScanIndexForward": False,  # Sort descending (newest first)
        }

        if last_key:
            query_params_dict["ExclusiveStartKey"] = json.loads(last_key)

        response = tasting_table.query(**query_params_dict)

        records = response.get("Items", [])
        next_key = response.get("LastEvaluatedKey")

        result = {"records": records, "count": len(records)}
        if next_key:
            result["next_key"] = json.dumps(next_key)

        logger.info("Retrieved tasting records", user_id=user_id, count=len(records))

        return success_response(result)

    except Exception as e:
        logger.error("Failed to list tasting records", user_id=user_id, error=str(e))
        raise


def handle_get_record(
    user_id: str | None,
    record_id: str | None,
    auth_user_id: str | None,
) -> dict[str, Any]:
    """Get specific tasting record.

    Args:
        user_id: User ID
        record_id: Record ID
        auth_user_id: Authenticated user ID

    Returns:
        Tasting record or error
    """
    if not user_id or not record_id:
        return bad_request_response("user_id and record_id are required")

    # Verify user can only access their own records
    if auth_user_id and auth_user_id != user_id:
        return unauthorized_response("Cannot access other user's tasting records")

    logger.info("Getting tasting record", user_id=user_id, record_id=record_id)

    try:
        response = tasting_table.get_item(Key={"user_id": user_id, "record_id": record_id})

        if "Item" not in response:
            logger.warning("Tasting record not found", user_id=user_id, record_id=record_id)
            return not_found_response("Tasting record")

        return success_response({"record": response["Item"]})

    except Exception as e:
        logger.error(
            "Failed to get tasting record",
            user_id=user_id,
            record_id=record_id,
            error=str(e),
        )
        raise


def handle_create_record(body: dict[str, Any], auth_user_id: str | None) -> dict[str, Any]:
    """Create new tasting record.

    Args:
        body: Request body with tasting record data
        auth_user_id: Authenticated user ID

    Returns:
        Created record or error
    """
    user_id = body.get("user_id")
    if not user_id:
        # Use authenticated user ID if not provided
        user_id = auth_user_id

    if not user_id:
        return bad_request_response("user_id is required")

    # Generate record_id
    record_id = f"R{uuid.uuid4().hex[:12]}"
    tasting_date = body.get("tasting_date", datetime.utcnow().isoformat())

    # Prepare record data
    record_data = {
        "user_id": user_id,
        "record_id": record_id,
        "tasting_date": tasting_date,
        **body,
    }

    # Validate using Pydantic model
    try:
        record = TastingRecord(**record_data)
    except ValidationError as e:
        logger.warning("Invalid tasting record data", user_id=user_id, errors=e.errors())
        raise

    logger.info("Creating tasting record", user_id=user_id, record_id=record_id)

    try:
        # Save to DynamoDB
        tasting_table.put_item(Item=record.model_dump())

        logger.info("Tasting record created", user_id=user_id, record_id=record_id)

        return created_response(
            {"record": record.model_dump()},
            location=f"/api/tasting/{user_id}/{record_id}",
        )

    except Exception as e:
        logger.error("Failed to create tasting record", user_id=user_id, error=str(e))
        raise


def handle_update_record(
    user_id: str | None,
    record_id: str | None,
    body: dict[str, Any],
    auth_user_id: str | None,
) -> dict[str, Any]:
    """Update tasting record.

    Args:
        user_id: User ID
        record_id: Record ID
        body: Request body with updated data
        auth_user_id: Authenticated user ID

    Returns:
        Updated record or error
    """
    if not user_id or not record_id:
        return bad_request_response("user_id and record_id are required")

    # Verify user can only update their own records
    if auth_user_id and auth_user_id != user_id:
        return unauthorized_response("Cannot update other user's tasting records")

    # Check if record exists
    existing = tasting_table.get_item(Key={"user_id": user_id, "record_id": record_id})
    if "Item" not in existing:
        return not_found_response("Tasting record")

    # Merge with existing data
    updated_data = {**existing["Item"], **body}

    # Validate using Pydantic model
    try:
        record = TastingRecord(**updated_data)
    except ValidationError as e:
        logger.warning("Invalid tasting record data", user_id=user_id, errors=e.errors())
        raise

    logger.info("Updating tasting record", user_id=user_id, record_id=record_id)

    try:
        # Update in DynamoDB
        tasting_table.put_item(Item=record.model_dump())

        logger.info("Tasting record updated", user_id=user_id, record_id=record_id)

        return success_response({"record": record.model_dump()})

    except Exception as e:
        logger.error(
            "Failed to update tasting record",
            user_id=user_id,
            record_id=record_id,
            error=str(e),
        )
        raise


def handle_delete_record(
    user_id: str | None,
    record_id: str | None,
    auth_user_id: str | None,
) -> dict[str, Any]:
    """Delete tasting record.

    Args:
        user_id: User ID
        record_id: Record ID
        auth_user_id: Authenticated user ID

    Returns:
        No content response or error
    """
    if not user_id or not record_id:
        return bad_request_response("user_id and record_id are required")

    # Verify user can only delete their own records
    if auth_user_id and auth_user_id != user_id:
        return unauthorized_response("Cannot delete other user's tasting records")

    logger.info("Deleting tasting record", user_id=user_id, record_id=record_id)

    try:
        # Check if record exists
        existing = tasting_table.get_item(Key={"user_id": user_id, "record_id": record_id})
        if "Item" not in existing:
            return not_found_response("Tasting record")

        # Delete from DynamoDB
        tasting_table.delete_item(Key={"user_id": user_id, "record_id": record_id})

        logger.info("Tasting record deleted", user_id=user_id, record_id=record_id)

        return no_content_response()

    except Exception as e:
        logger.error(
            "Failed to delete tasting record",
            user_id=user_id,
            record_id=record_id,
            error=str(e),
        )
        raise
