"""
Sake Sensei - Lambda Response Formatter

Standardized HTTP response formatting for Lambda functions.
"""

import json
from typing import Any


def create_response(
    status_code: int,
    body: dict[str, Any] | list[Any] | str,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Create a standardized Lambda HTTP response.

    Args:
        status_code: HTTP status code
        body: Response body (dict, list, or string)
        headers: Additional headers to include

    Returns:
        Lambda response dictionary with statusCode, body, and headers

    Example:
        return create_response(200, {"message": "Success", "data": {...}})
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }

    if headers:
        default_headers.update(headers)

    # Convert body to JSON string if not already a string
    response_body = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)

    return {
        "statusCode": status_code,
        "body": response_body,
        "headers": default_headers,
    }


def error_response(
    status_code: int,
    error: str,
    message: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standardized error response.

    Args:
        status_code: HTTP error status code (400, 401, 403, 404, 500, etc.)
        error: Error type/code (e.g., "ValidationError", "Unauthorized")
        message: Human-readable error message
        details: Additional error details

    Returns:
        Lambda error response dictionary

    Example:
        return error_response(400, "ValidationError", "Invalid sake_id format")
    """
    body: dict[str, Any] = {"error": error}

    if message:
        body["message"] = message

    if details:
        body["details"] = details

    return create_response(status_code, body)


def success_response(data: Any, message: str | None = None) -> dict[str, Any]:
    """Create a 200 OK success response.

    Args:
        data: Response data
        message: Optional success message

    Returns:
        Lambda response dictionary with 200 status

    Example:
        return success_response({"sake_id": "S001", "name": "獺祭"})
    """
    body: dict[str, Any] = {"success": True, "data": data}

    if message:
        body["message"] = message

    return create_response(200, body)


def created_response(data: Any, location: str | None = None) -> dict[str, Any]:
    """Create a 201 Created response.

    Args:
        data: Created resource data
        location: Optional Location header for new resource

    Returns:
        Lambda response dictionary with 201 status

    Example:
        return created_response(
            {"record_id": "R123"},
            location="/api/tasting/R123"
        )
    """
    headers = {}
    if location:
        headers["Location"] = location

    body = {"success": True, "data": data}

    return create_response(201, body, headers)


def no_content_response() -> dict[str, Any]:
    """Create a 204 No Content response.

    Returns:
        Lambda response dictionary with 204 status and empty body

    Example:
        # DELETE operation succeeded
        return no_content_response()
    """
    return {"statusCode": 204, "body": "", "headers": {}}


def bad_request_response(message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a 400 Bad Request response.

    Args:
        message: Error message
        details: Optional validation error details

    Returns:
        Lambda response dictionary with 400 status
    """
    return error_response(400, "BadRequest", message, details)


def unauthorized_response(message: str = "Unauthorized") -> dict[str, Any]:
    """Create a 401 Unauthorized response.

    Args:
        message: Error message

    Returns:
        Lambda response dictionary with 401 status
    """
    return error_response(401, "Unauthorized", message)


def forbidden_response(message: str = "Forbidden") -> dict[str, Any]:
    """Create a 403 Forbidden response.

    Args:
        message: Error message

    Returns:
        Lambda response dictionary with 403 status
    """
    return error_response(403, "Forbidden", message)


def not_found_response(resource: str = "Resource") -> dict[str, Any]:
    """Create a 404 Not Found response.

    Args:
        resource: Resource type that was not found

    Returns:
        Lambda response dictionary with 404 status
    """
    return error_response(404, "NotFound", f"{resource} not found")


def internal_error_response(message: str = "Internal server error") -> dict[str, Any]:
    """Create a 500 Internal Server Error response.

    Args:
        message: Error message

    Returns:
        Lambda response dictionary with 500 status
    """
    return error_response(500, "InternalError", message)
