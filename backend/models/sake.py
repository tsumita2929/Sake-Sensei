"""
Sake Sensei - Sake Model

Pydantic models for sake data validation and serialization.
"""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class SakeCharacteristics(BaseModel):
    """Sake taste characteristics."""

    sweetness: int = Field(ge=1, le=5, description="Sweetness level (1=dry, 5=sweet)")
    acidity: int = Field(ge=1, le=5, description="Acidity level")
    body: int = Field(ge=1, le=5, description="Body weight (1=light, 5=heavy)")
    aroma: str = Field(..., description="Aroma description")


class Sake(BaseModel):
    """Sake master data model."""

    sake_id: str = Field(..., description="Unique sake identifier")
    name: str = Field(..., description="Sake name")
    brewery_id: str = Field(..., description="Brewery identifier")
    category: str = Field(..., description="Sake category (純米大吟醸, etc.)")
    price: int = Field(gt=0, description="Price in yen")
    alcohol_content: float = Field(ge=0, le=100, description="Alcohol percentage")
    characteristics: SakeCharacteristics
    pairings: list[str] = Field(default_factory=list, description="Food pairings")
    description: str = Field(..., description="Sake description")
    image_url: HttpUrl | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class SakeCreate(BaseModel):
    """Model for creating a new sake entry."""

    name: str
    brewery_id: str
    category: str
    price: int = Field(gt=0)
    alcohol_content: float = Field(ge=0, le=100)
    characteristics: SakeCharacteristics
    pairings: list[str] = Field(default_factory=list)
    description: str
    image_url: HttpUrl | None = None


class SakeUpdate(BaseModel):
    """Model for updating sake data."""

    name: str | None = None
    category: str | None = None
    price: int | None = Field(None, gt=0)
    alcohol_content: float | None = Field(None, ge=0, le=100)
    characteristics: SakeCharacteristics | None = None
    pairings: list[str] | None = None
    description: str | None = None
    image_url: HttpUrl | None = None
