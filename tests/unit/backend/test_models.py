"""Unit tests for data models."""

import pytest

from tests.fixtures.sake import sample_brewery, sample_sake, sample_tasting_record
from tests.fixtures.users import sample_user, sample_user_preference


@pytest.mark.unit
class TestUserModel:
    """Test User model validation."""

    def test_user_model_valid(self) -> None:
        """Test valid user model."""
        user = sample_user()
        assert user["user_id"] == "test-user-123"
        assert user["email"] == "test@example.com"
        assert "created_at" in user

    def test_user_preference_model_valid(self) -> None:
        """Test valid user preference model."""
        pref = sample_user_preference()
        assert pref["user_id"] == "test-user-123"
        assert 1 <= pref["sweetness"] <= 5
        assert 1 <= pref["acidity"] <= 5
        assert 1 <= pref["richness"] <= 5
        assert 1 <= pref["aroma_intensity"] <= 5


@pytest.mark.unit
class TestSakeModel:
    """Test Sake model validation."""

    def test_sake_model_valid(self) -> None:
        """Test valid sake model."""
        sake = sample_sake()
        assert sake["sake_id"] == "sake-001"
        assert sake["name"]
        assert sake["type"] == "junmai_daiginjo"
        assert 1 <= sake["sweetness"] <= 5
        assert 1 <= sake["acidity"] <= 5
        assert 1 <= sake["richness"] <= 5
        assert 1 <= sake["aroma_intensity"] <= 5

    def test_sake_flavor_profile(self) -> None:
        """Test sake flavor profile structure."""
        sake = sample_sake()
        flavor = sake["flavor_profile"]
        assert "fruity" in flavor
        assert "floral" in flavor
        assert "rice" in flavor
        assert "spicy" in flavor
        assert "umami" in flavor
        assert all(1 <= v <= 5 for v in flavor.values())

    def test_sake_price_positive(self) -> None:
        """Test sake price is positive."""
        sake = sample_sake()
        assert sake["price"] > 0
        assert sake["volume_ml"] > 0


@pytest.mark.unit
class TestBreweryModel:
    """Test Brewery model validation."""

    def test_brewery_model_valid(self) -> None:
        """Test valid brewery model."""
        brewery = sample_brewery()
        assert brewery["brewery_id"] == "brewery-001"
        assert brewery["name"]
        assert brewery["prefecture"]
        assert brewery["established_year"] > 0


@pytest.mark.unit
class TestTastingRecordModel:
    """Test Tasting Record model validation."""

    def test_tasting_record_valid(self) -> None:
        """Test valid tasting record."""
        record = sample_tasting_record()
        assert record["record_id"]
        assert record["user_id"]
        assert record["sake_id"]
        assert 1 <= record["rating"] <= 5

    def test_tasting_record_attributes(self) -> None:
        """Test tasting record attributes."""
        record = sample_tasting_record()
        assert 1 <= record["sweetness"] <= 5
        assert 1 <= record["acidity"] <= 5
        assert 1 <= record["richness"] <= 5
        assert 1 <= record["aroma_intensity"] <= 5
        assert isinstance(record["notes"], str)
        assert isinstance(record["image_urls"], list)
