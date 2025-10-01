"""
Sake Sensei - Authentication Decorators

Decorators for protecting Lambda functions and Streamlit pages.
"""

import functools
from collections.abc import Callable
from typing import Any, TypeVar, cast

import jwt

from backend.auth.jwt_validator import JWTValidator

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


def require_auth[F: Callable[..., Any]](func: F) -> F:
    """Decorator to require authentication for Lambda functions.

    Expects Authorization header with Bearer token.
    Injects 'user_id' and 'claims' into event context.

    Args:
        func: Lambda handler function

    Returns:
        Decorated function

    Example:
        @require_auth
        def handler(event, context):
            user_id = event['requestContext']['authorizer']['user_id']
            return {'statusCode': 200, 'body': f'Hello {user_id}'}
    """

    @functools.wraps(func)
    def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
        """Wrapper function for authentication."""
        # Extract token from Authorization header
        headers = event.get("headers", {})
        auth_header = headers.get("Authorization") or headers.get("authorization", "")

        if not auth_header.startswith("Bearer "):
            return {
                "statusCode": 401,
                "body": '{"error": "Missing or invalid Authorization header"}',
                "headers": {"Content-Type": "application/json"},
            }

        token = auth_header.replace("Bearer ", "")

        # Validate token
        try:
            validator = JWTValidator()
            claims = validator.validate_access_token(token)

            # Inject user info into event context
            if "requestContext" not in event:
                event["requestContext"] = {}
            if "authorizer" not in event["requestContext"]:
                event["requestContext"]["authorizer"] = {}

            event["requestContext"]["authorizer"]["user_id"] = claims["sub"]
            event["requestContext"]["authorizer"]["claims"] = claims

            # Call original function
            return func(event, context)

        except jwt.ExpiredSignatureError:
            return {
                "statusCode": 401,
                "body": '{"error": "Token has expired"}',
                "headers": {"Content-Type": "application/json"},
            }
        except jwt.InvalidTokenError as e:
            return {
                "statusCode": 401,
                "body": f'{{"error": "Invalid token: {e}"}}',
                "headers": {"Content-Type": "application/json"},
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": f'{{"error": "Authentication error: {e}"}}',
                "headers": {"Content-Type": "application/json"},
            }

    return cast(F, wrapper)


def require_role(allowed_roles: list[str]) -> Callable[[F], F]:
    """Decorator to require specific roles (based on Cognito groups).

    Args:
        allowed_roles: List of allowed Cognito group names

    Returns:
        Decorator function

    Example:
        @require_role(['admin', 'moderator'])
        def handler(event, context):
            return {'statusCode': 200, 'body': 'Admin access granted'}
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
            """Wrapper function for role-based access control."""
            # Extract token from Authorization header
            headers = event.get("headers", {})
            auth_header = headers.get("Authorization") or headers.get("authorization", "")

            if not auth_header.startswith("Bearer "):
                return {
                    "statusCode": 401,
                    "body": '{"error": "Missing or invalid Authorization header"}',
                    "headers": {"Content-Type": "application/json"},
                }

            token = auth_header.replace("Bearer ", "")

            # Validate token and check roles
            try:
                validator = JWTValidator()
                claims = validator.validate_access_token(token)

                # Extract Cognito groups from claims
                user_groups = claims.get("cognito:groups", [])

                # Check if user has any of the allowed roles
                if not any(role in user_groups for role in allowed_roles):
                    return {
                        "statusCode": 403,
                        "body": '{"error": "Insufficient permissions"}',
                        "headers": {"Content-Type": "application/json"},
                    }

                # Inject user info into event context
                if "requestContext" not in event:
                    event["requestContext"] = {}
                if "authorizer" not in event["requestContext"]:
                    event["requestContext"]["authorizer"] = {}

                event["requestContext"]["authorizer"]["user_id"] = claims["sub"]
                event["requestContext"]["authorizer"]["claims"] = claims
                event["requestContext"]["authorizer"]["roles"] = user_groups

                # Call original function
                return func(event, context)

            except jwt.ExpiredSignatureError:
                return {
                    "statusCode": 401,
                    "body": '{"error": "Token has expired"}',
                    "headers": {"Content-Type": "application/json"},
                }
            except jwt.InvalidTokenError as e:
                return {
                    "statusCode": 401,
                    "body": f'{{"error": "Invalid token: {e}"}}',
                    "headers": {"Content-Type": "application/json"},
                }
            except Exception as e:
                return {
                    "statusCode": 500,
                    "body": f'{{"error": "Authentication error: {e}"}}',
                    "headers": {"Content-Type": "application/json"},
                }

        return cast(F, wrapper)

    return decorator


def get_current_user_id(event: dict[str, Any]) -> str | None:
    """Extract user ID from authenticated Lambda event.

    Args:
        event: Lambda event (must be decorated with @require_auth)

    Returns:
        User ID or None if not authenticated
    """
    try:
        return event["requestContext"]["authorizer"]["user_id"]
    except (KeyError, TypeError):
        return None


def get_current_user_claims(event: dict[str, Any]) -> dict[str, Any] | None:
    """Extract user claims from authenticated Lambda event.

    Args:
        event: Lambda event (must be decorated with @require_auth)

    Returns:
        User claims dictionary or None if not authenticated
    """
    try:
        return event["requestContext"]["authorizer"]["claims"]
    except (KeyError, TypeError):
        return None
