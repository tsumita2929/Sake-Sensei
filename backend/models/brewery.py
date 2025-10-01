"""
Sake Sensei - Brewery Model

Pydantic models for brewery data validation and serialization.
"""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class Brewery(BaseModel):
    """Brewery master data model."""

    brewery_id: str = Field(..., description="Unique brewery identifier")
    name: str = Field(..., description="Brewery name")
    prefecture: str = Field(..., description="Prefecture location (都道府県)")
    city: str = Field(..., description="City location")
    established: int = Field(ge=1000, le=2100, description="Year established (e.g., 1868)")
    description: str = Field(..., description="Brewery description and history")
    website: HttpUrl | None = Field(None, description="Brewery website URL")
    image_url: HttpUrl | None = Field(None, description="Brewery image URL")
    specialties: list[str] = Field(default_factory=list, description="Specialty sake categories")
    awards: list[str] = Field(default_factory=list, description="Awards and recognitions")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class BreweryCreate(BaseModel):
    """Model for creating a new brewery entry."""

    name: str
    prefecture: str
    city: str
    established: int = Field(ge=1000, le=2100)
    description: str
    website: HttpUrl | None = None
    image_url: HttpUrl | None = None
    specialties: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)


class BreweryUpdate(BaseModel):
    """Model for updating brewery data."""

    name: str | None = None
    prefecture: str | None = None
    city: str | None = None
    established: int | None = Field(None, ge=1000, le=2100)
    description: str | None = None
    website: HttpUrl | None = None
    image_url: HttpUrl | None = None
    specialties: list[str] | None = None
    awards: list[str] | None = None
