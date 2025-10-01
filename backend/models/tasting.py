"""
Sake Sensei - Tasting Record Model

Pydantic models for tasting record data validation and serialization.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class FlavorProfile(BaseModel):
    """Flavor profile ratings for a sake tasting."""

    sweetness: int = Field(ge=1, le=5, description="Sweetness level (1=dry, 5=sweet)")
    acidity: int = Field(ge=1, le=5, description="Acidity level")
    body: int = Field(ge=1, le=5, description="Body weight (1=light, 5=heavy)")
    aroma_intensity: int = Field(ge=1, le=5, description="Aroma intensity (1=subtle, 5=strong)")


class TastingRecord(BaseModel):
    """Tasting record model."""

    user_id: str = Field(..., description="User identifier")
    record_id: str = Field(..., description="Unique tasting record identifier")
    sake_id: str = Field(..., description="Sake identifier")
    rating: int = Field(ge=1, le=5, description="Overall rating (1-5)")
    notes: str = Field(default="", description="Tasting notes and impressions")
    flavor_profile: FlavorProfile = Field(..., description="Detailed flavor ratings")
    photos: list[str] = Field(default_factory=list, description="S3 keys for tasting photos")
    visited_at: datetime = Field(..., description="Date and time of tasting")
    location: str | None = Field(None, description="Location where sake was tasted")
    price_paid: int | None = Field(None, gt=0, description="Actual price paid in yen")
    temperature: str | None = Field(
        None, description="Serving temperature (冷酒, 常温, 熱燗, etc.)"
    )
    pairing: str | None = Field(None, description="Food pairing during tasting")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class TastingRecordCreate(BaseModel):
    """Model for creating a new tasting record."""

    sake_id: str
    rating: int = Field(ge=1, le=5)
    notes: str = ""
    flavor_profile: FlavorProfile
    photos: list[str] = Field(default_factory=list)
    visited_at: datetime
    location: str | None = None
    price_paid: int | None = Field(None, gt=0)
    temperature: str | None = None
    pairing: str | None = None


class TastingRecordUpdate(BaseModel):
    """Model for updating a tasting record."""

    rating: int | None = Field(None, ge=1, le=5)
    notes: str | None = None
    flavor_profile: FlavorProfile | None = None
    photos: list[str] | None = None
    visited_at: datetime | None = None
    location: str | None = None
    price_paid: int | None = Field(None, gt=0)
    temperature: str | None = None
    pairing: str | None = None
