"""User test fixtures."""

from datetime import datetime
from typing import Any


def sample_user() -> dict[str, Any]:
    """Return sample user data."""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "username": "testuser",
        "created_at": datetime(2025, 1, 1, 0, 0, 0).isoformat(),
        "last_login": datetime(2025, 10, 1, 0, 0, 0).isoformat(),
    }


def sample_user_preference() -> dict[str, Any]:
    """Return sample user preference data."""
    return {
        "user_id": "test-user-123",
        "sweetness": 3,
        "acidity": 4,
        "richness": 3,
        "aroma_intensity": 4,
        "preferred_types": ["junmai_daiginjo", "daiginjo"],
        "disliked_ingredients": [],
        "price_range_min": 1000,
        "price_range_max": 5000,
        "occasion": "dinner",
        "experience_level": "intermediate",
        "updated_at": datetime(2025, 10, 1, 0, 0, 0).isoformat(),
    }


def sample_cognito_user() -> dict[str, Any]:
    """Return sample Cognito user attributes."""
    return {
        "sub": "test-user-123",
        "email": "test@example.com",
        "email_verified": "true",
        "cognito:username": "testuser",
    }
