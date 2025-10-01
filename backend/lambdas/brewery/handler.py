"""
Sake Sensei - Brewery Lambda Handler

Provides brewery information and sake listings.
"""

import os
from typing import Any

import boto3

from backend.lambdas.layer.error_handler import handle_errors
from backend.lambdas.layer.logger import get_logger
from backend.lambdas.layer.response import (
    bad_request_response,
    not_found_response,
    success_response,
)

logger = get_logger(__name__)

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb")
brewery_table = dynamodb.Table(os.getenv("BREWERY_TABLE", "SakeSensei-BreweryMaster"))
sake_table = dynamodb.Table(os.getenv("SAKE_TABLE", "SakeSensei-SakeMaster"))


@handle_errors
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler for brewery information.

    Supported operations:
    - GET /api/brewery - List all breweries (with optional prefecture filter)
    - GET /api/brewery/{brewery_id} - Get brewery details
    - GET /api/brewery/{brewery_id}/sake - List sake from brewery

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    http_method = event.get("httpMethod", "GET")
    path_parameters = event.get("pathParameters", {})
    brewery_id = path_parameters.get("brewery_id")
    query_params = event.get("queryStringParameters", {}) or {}

    # Check if this is a sake listing request
    path = event.get("path", "")
    is_sake_list = path.endswith("/sake")

    # Route to appropriate handler
    if http_method == "GET" and brewery_id and is_sake_list:
        return handle_list_brewery_sake(brewery_id)
    elif http_method == "GET" and brewery_id:
        return handle_get_brewery(brewery_id)
    elif http_method == "GET":
        return handle_list_breweries(query_params)
    else:
        return bad_request_response(f"Unsupported method or path: {http_method} {path}")


def handle_list_breweries(query_params: dict[str, Any]) -> dict[str, Any]:
    """List all breweries with optional prefecture filter.

    Args:
        query_params: Query parameters (prefecture, limit)

    Returns:
        List of breweries
    """
    prefecture = query_params.get("prefecture")
    limit = int(query_params.get("limit", 50))

    logger.info("Listing breweries", prefecture=prefecture, limit=limit)

    try:
        if prefecture:
            # Query by prefecture using GSI
            response = brewery_table.query(
                IndexName="PrefectureIndex",
                KeyConditionExpression="prefecture = :pref",
                ExpressionAttributeValues={":pref": prefecture},
                Limit=limit,
            )
        else:
            # Scan all breweries
            response = brewery_table.scan(Limit=limit)

        breweries = response.get("Items", [])

        logger.info("Retrieved breweries", count=len(breweries))

        return success_response({"breweries": breweries, "count": len(breweries)})

    except Exception as e:
        logger.error("Failed to list breweries", error=str(e))
        raise


def handle_get_brewery(brewery_id: str) -> dict[str, Any]:
    """Get brewery details.

    Args:
        brewery_id: Brewery ID

    Returns:
        Brewery details or error
    """
    if not brewery_id:
        return bad_request_response("brewery_id is required")

    logger.info("Getting brewery details", brewery_id=brewery_id)

    try:
        response = brewery_table.get_item(Key={"brewery_id": brewery_id})

        if "Item" not in response:
            logger.warning("Brewery not found", brewery_id=brewery_id)
            return not_found_response("Brewery")

        brewery = response["Item"]

        # Get sake count for this brewery
        sake_response = sake_table.query(
            IndexName="BreweryIndex",
            KeyConditionExpression="brewery_id = :brewery_id",
            ExpressionAttributeValues={":brewery_id": brewery_id},
            Select="COUNT",
        )

        brewery["sake_count"] = sake_response.get("Count", 0)

        logger.info("Retrieved brewery details", brewery_id=brewery_id)

        return success_response({"brewery": brewery})

    except Exception as e:
        logger.error("Failed to get brewery", brewery_id=brewery_id, error=str(e))
        raise


def handle_list_brewery_sake(brewery_id: str) -> dict[str, Any]:
    """List all sake from a specific brewery.

    Args:
        brewery_id: Brewery ID

    Returns:
        List of sake from brewery
    """
    if not brewery_id:
        return bad_request_response("brewery_id is required")

    logger.info("Listing sake for brewery", brewery_id=brewery_id)

    try:
        # Verify brewery exists
        brewery_response = brewery_table.get_item(Key={"brewery_id": brewery_id})
        if "Item" not in brewery_response:
            logger.warning("Brewery not found", brewery_id=brewery_id)
            return not_found_response("Brewery")

        # Query sake by brewery
        response = sake_table.query(
            IndexName="BreweryIndex",
            KeyConditionExpression="brewery_id = :brewery_id",
            ExpressionAttributeValues={":brewery_id": brewery_id},
        )

        sake_list = response.get("Items", [])

        logger.info(
            "Retrieved sake for brewery",
            brewery_id=brewery_id,
            count=len(sake_list),
        )

        return success_response(
            {
                "brewery_id": brewery_id,
                "sake": sake_list,
                "count": len(sake_list),
            }
        )

    except Exception as e:
        logger.error("Failed to list brewery sake", brewery_id=brewery_id, error=str(e))
        raise
