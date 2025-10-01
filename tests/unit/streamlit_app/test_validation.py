"""Unit tests for validation utilities."""

import pytest

from streamlit_app.utils.validation import (
    sanitize_text_input,
    validate_email,
    validate_image_file,
    validate_name,
    validate_password,
    validate_preferences,
    validate_rating,
    validate_sake_name,
    validate_tasting_record,
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

    def test_validate_email_too_long(self) -> None:
        """Test email too long."""
        is_valid, error = validate_email("a" * 256)
        assert is_valid is False

    def test_validate_password_too_long(self) -> None:
        """Test password too long."""
        is_valid, error = validate_password("A" * 130 + "a1")
        assert is_valid is False

    def test_validate_password_no_lowercase(self) -> None:
        """Test password without lowercase."""
        is_valid, error = validate_password("ABCD1234")
        assert is_valid is False

    def test_validate_password_empty(self) -> None:
        """Test empty password."""
        is_valid, error = validate_password("")
        assert is_valid is False

    def test_validate_name_valid(self) -> None:
        """Test valid name."""
        is_valid, _ = validate_name("John Doe")
        assert is_valid is True

    def test_validate_name_empty(self) -> None:
        """Test empty name."""
        is_valid, error = validate_name("")
        assert is_valid is False

    def test_validate_name_too_short(self) -> None:
        """Test name too short."""
        is_valid, error = validate_name("A")
        assert is_valid is False

    def test_validate_name_too_long(self) -> None:
        """Test name too long."""
        is_valid, error = validate_name("A" * 101)
        assert is_valid is False

    def test_validate_preferences_valid(self) -> None:
        """Test valid preferences."""
        is_valid, _ = validate_preferences({"sake_types": ["junmai"]})
        assert is_valid is True

    def test_validate_preferences_invalid(self) -> None:
        """Test invalid preferences."""
        is_valid, errors = validate_preferences({"sake_types": "junmai"})
        assert is_valid is False

    def test_validate_tasting_record_valid(self) -> None:
        """Test valid tasting record."""
        is_valid, _ = validate_tasting_record({"sake_name": "獺祭"})
        assert is_valid is True

    def test_validate_tasting_record_missing_name(self) -> None:
        """Test tasting record missing name."""
        is_valid, errors = validate_tasting_record({})
        assert is_valid is False

    def test_validate_tasting_record_empty_name(self) -> None:
        """Test tasting record empty name."""
        is_valid, errors = validate_tasting_record({"sake_name": ""})
        assert is_valid is False

    def test_validate_tasting_record_non_string(self) -> None:
        """Test tasting record non-string name."""
        is_valid, errors = validate_tasting_record({"sake_name": 123})
        assert is_valid is False

    def test_validate_tasting_record_too_short(self) -> None:
        """Test tasting record name too short."""
        is_valid, errors = validate_tasting_record({"sake_name": "A"})
        assert is_valid is False

    def test_validate_tasting_record_too_long(self) -> None:
        """Test tasting record name too long."""
        is_valid, errors = validate_tasting_record({"sake_name": "A" * 201})
        assert is_valid is False

    def test_validate_sake_name_too_short(self) -> None:
        """Test sake name too short."""
        is_valid, error = validate_sake_name("A")
        assert is_valid is False

    def test_validate_sake_name_too_long(self) -> None:
        """Test sake name too long."""
        is_valid, error = validate_sake_name("A" * 201)
        assert is_valid is False

    def test_validate_rating_non_integer(self) -> None:
        """Test rating non-integer."""
        is_valid, error = validate_rating(3.5)
        assert is_valid is False

    def test_validate_image_file_no_file(self) -> None:
        """Test no file selected."""
        is_valid, error = validate_image_file("", 0)
        assert is_valid is False

    def test_sanitize_text_input_normal(self) -> None:
        """Test sanitize normal text."""
        result = sanitize_text_input("  Normal text  ")
        assert result == "Normal text"

    def test_sanitize_text_input_empty(self) -> None:
        """Test sanitize empty text."""
        result = sanitize_text_input("")
        assert result == ""

    def test_sanitize_text_input_null_bytes(self) -> None:
        """Test sanitize removes null bytes."""
        result = sanitize_text_input("Text\x00with\x00nulls")
        assert "\x00" not in result

    def test_sanitize_text_input_truncate(self) -> None:
        """Test sanitize truncates long text."""
        result = sanitize_text_input("A" * 2000, max_length=100)
        assert len(result) == 100
