"""
Sake Sensei - Lambda Error Handler

Centralized error handling decorator for Lambda functions.
"""

import functools
import traceback
from collections.abc import Callable
from typing import Any, TypeVar, cast

from botocore.exceptions import ClientError
from pydantic import ValidationError

from backend.lambdas.layer.logger import get_logger
from backend.lambdas.layer.response import error_response, internal_error_response

F = TypeVar("F", bound=Callable[..., Any])

logger = get_logger(__name__)


def handle_errors[F: Callable[..., Any]](func: F) -> F:
    """Decorator to handle errors in Lambda functions.

    Catches common exceptions and returns standardized error responses.
    Logs all errors with full context.

    Usage:
        @handle_errors
        def handler(event, context):
            # Your Lambda code here
            pass

    Args:
        func: Lambda handler function

    Returns:
        Wrapped function with error handling
    """

    @functools.wraps(func)
    def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
        try:
            return func(event, context)

        except ValidationError as e:
            # Pydantic validation error
            logger.error(
                "Validation error",
                error=str(e),
                errors=e.errors(),
                path=event.get("path", "unknown"),
            )
            return error_response(
                400,
                "ValidationError",
                "Invalid request data",
                {"errors": e.errors()},
            )

        except ClientError as e:
            # AWS service error (boto3)
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            logger.error(
                "AWS service error",
                error_code=error_code,
                error_message=error_message,
                service=e.response.get("ResponseMetadata", {}).get("ServiceName", "unknown"),
                path=event.get("path", "unknown"),
            )

            # Map common AWS errors to HTTP status codes
            if error_code == "ResourceNotFoundException":
                return error_response(404, "NotFound", error_message)
            elif error_code in ["AccessDeniedException", "UnauthorizedException"]:
                return error_response(403, "Forbidden", "Access denied")
            elif error_code in ["ValidationException", "InvalidParameterException"]:
                return error_response(400, "BadRequest", error_message)
            else:
                return internal_error_response("Service error occurred")

        except KeyError as e:
            # Missing required key
            logger.error(
                "Missing required key",
                key=str(e),
                path=event.get("path", "unknown"),
                event_keys=list(event.keys()),
            )
            return error_response(400, "BadRequest", f"Missing required field: {e}")

        except ValueError as e:
            # Invalid value error
            logger.error(
                "Value error",
                error=str(e),
                path=event.get("path", "unknown"),
            )
            return error_response(400, "BadRequest", str(e))

        except Exception as e:
            # Catch-all for unexpected errors
            logger.critical(
                "Unexpected error",
                error=str(e),
                error_type=type(e).__name__,
                path=event.get("path", "unknown"),
                traceback=traceback.format_exc(),
            )
            return internal_error_response("An unexpected error occurred")

    return cast(F, wrapper)


def handle_errors_async[F: Callable[..., Any]](func: F) -> F:
    """Decorator to handle errors in async Lambda functions.

    Same as handle_errors but for async functions.

    Usage:
        @handle_errors_async
        async def handler(event, context):
            # Your async Lambda code here
            pass

    Args:
        func: Async Lambda handler function

    Returns:
        Wrapped async function with error handling
    """

    @functools.wraps(func)
    async def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
        try:
            return await func(event, context)

        except ValidationError as e:
            logger.error(
                "Validation error",
                error=str(e),
                errors=e.errors(),
                path=event.get("path", "unknown"),
            )
            return error_response(
                400,
                "ValidationError",
                "Invalid request data",
                {"errors": e.errors()},
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]

            logger.error(
                "AWS service error",
                error_code=error_code,
                error_message=error_message,
                service=e.response.get("ResponseMetadata", {}).get("ServiceName", "unknown"),
                path=event.get("path", "unknown"),
            )

            if error_code == "ResourceNotFoundException":
                return error_response(404, "NotFound", error_message)
            elif error_code in ["AccessDeniedException", "UnauthorizedException"]:
                return error_response(403, "Forbidden", "Access denied")
            elif error_code in ["ValidationException", "InvalidParameterException"]:
                return error_response(400, "BadRequest", error_message)
            else:
                return internal_error_response("Service error occurred")

        except KeyError as e:
            logger.error(
                "Missing required key",
                key=str(e),
                path=event.get("path", "unknown"),
                event_keys=list(event.keys()),
            )
            return error_response(400, "BadRequest", f"Missing required field: {e}")

        except ValueError as e:
            logger.error(
                "Value error",
                error=str(e),
                path=event.get("path", "unknown"),
            )
            return error_response(400, "BadRequest", str(e))

        except Exception as e:
            logger.critical(
                "Unexpected error",
                error=str(e),
                error_type=type(e).__name__,
                path=event.get("path", "unknown"),
                traceback=traceback.format_exc(),
            )
            return internal_error_response("An unexpected error occurred")

    return cast(F, wrapper)
