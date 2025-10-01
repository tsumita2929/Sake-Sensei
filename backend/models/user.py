"""
Sake Sensei - User Model

Pydantic models for user data validation and serialization.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserPreferences(BaseModel):
    """User preferences for sake recommendations."""

    sweetness: int = Field(ge=1, le=5, description="Sweetness preference (1=dry, 5=sweet)")
    budget: int = Field(gt=0, description="Maximum budget in yen")
    experience_level: str = Field(pattern="^(beginner|intermediate|advanced)$")
    avoid_categories: list[str] = Field(default_factory=list)


class User(BaseModel):
    """User profile model."""

    user_id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    preferences: UserPreferences | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class UserCreate(BaseModel):
    """Model for creating a new user."""

    email: EmailStr
    preferences: UserPreferences | None = None


class UserUpdate(BaseModel):
    """Model for updating user data."""

    preferences: UserPreferences | None = None
