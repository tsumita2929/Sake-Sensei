"""Unit tests for validation utilities."""

import pytest

from streamlit_app.utils.validation import (
    validate_email,
    validate_image_file,
    validate_password,
    validate_rating,
    validate_sake_name,
)


@pytest.mark.unit
class TestValidation:
    """Test validation functions."""

    def test_validate_email_valid(self) -> None:
        """Test valid email addresses."""
        is_valid, _ = validate_email("user@example.com")
        assert is_valid is True

        is_valid, _ = validate_email("test.user+tag@domain.co.jp")
        assert is_valid is True

    def test_validate_email_invalid(self) -> None:
        """Test invalid email addresses."""
        is_valid, error = validate_email("")
        assert is_valid is False
        assert error != ""

        is_valid, error = validate_email("invalid-email")
        assert is_valid is False

        is_valid, error = validate_email("@example.com")
        assert is_valid is False

    def test_validate_password_valid(self) -> None:
        """Test valid passwords."""
        is_valid, _ = validate_password("StrongPass123!")
        assert is_valid is True

    def test_validate_password_too_short(self) -> None:
        """Test password too short."""
        is_valid, error = validate_password("Short1!")
        assert is_valid is False
        assert "at least 8 characters" in error

    def test_validate_password_no_uppercase(self) -> None:
        """Test password without uppercase."""
        is_valid, error = validate_password("password123!")
        assert is_valid is False

    def test_validate_password_no_number(self) -> None:
        """Test password without number."""
        is_valid, error = validate_password("Password!")
        assert is_valid is False

    def test_validate_rating_valid(self) -> None:
        """Test valid ratings."""
        for rating in [1, 2, 3, 4, 5]:
            is_valid, _ = validate_rating(rating)
            assert is_valid is True

    def test_validate_rating_invalid(self) -> None:
        """Test invalid ratings."""
        is_valid, error = validate_rating(0)
        assert is_valid is False

        is_valid, error = validate_rating(6)
        assert is_valid is False

        is_valid, error = validate_rating(-1)
        assert is_valid is False

    def test_validate_sake_name_valid(self) -> None:
        """Test valid sake names."""
        is_valid, _ = validate_sake_name("獺祭 純米大吟醸")
        assert is_valid is True

    def test_validate_sake_name_empty(self) -> None:
        """Test empty sake name."""
        is_valid, error = validate_sake_name("")
        assert is_valid is False

        is_valid, error = validate_sake_name("   ")
        assert is_valid is False

    def test_validate_image_file_valid(self) -> None:
        """Test valid image files."""
        is_valid, _ = validate_image_file("photo.jpg", 1024 * 1024)
        assert is_valid is True

        is_valid, _ = validate_image_file("image.png", 2 * 1024 * 1024)
        assert is_valid is True

    def test_validate_image_file_invalid_extension(self) -> None:
        """Test invalid file extension."""
        is_valid, error = validate_image_file("document.pdf", 1024)
        assert is_valid is False
        assert "Unsupported format" in error

    def test_validate_image_file_too_large(self) -> None:
        """Test file too large."""
        is_valid, error = validate_image_file("large.jpg", 20 * 1024 * 1024, max_size_mb=10)
        assert is_valid is False
        assert "too large" in error
