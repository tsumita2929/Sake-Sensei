"""Sake Sensei - Input Validation"""

import re


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def validate_email(email: str) -> tuple[bool, str]:
    """Validate email address format."""
    if not email:
        return False, "Email is required"
    if len(email) > 255:
        return False, "Email is too long"
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    if not password:
        return False, "Password is required"
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if len(password) > 128:
        return False, "Password is too long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain digit"
    return True, ""


def validate_name(name: str) -> tuple[bool, str]:
    """Validate user name."""
    if not name:
        return False, "Name is required"
    if len(name) < 2:
        return False, "Name is too short"
    if len(name) > 100:
        return False, "Name is too long"
    return True, ""


def validate_preferences(preferences: dict) -> tuple[bool, list[str]]:
    """Validate user preferences data."""
    errors: list[str] = []
    if "sake_types" in preferences and not isinstance(preferences["sake_types"], list):
        errors.append("sake_types must be a list")
    return len(errors) == 0, errors


def validate_tasting_record(record: dict) -> tuple[bool, list[str]]:
    """Validate tasting record data."""
    errors: list[str] = []
    if "sake_name" not in record or not record["sake_name"]:
        errors.append("sake_name is required")
    if "sake_name" in record:
        if not isinstance(record["sake_name"], str):
            errors.append("sake_name must be a string")
        elif len(record["sake_name"]) < 2:
            errors.append("sake_name is too short")
        elif len(record["sake_name"]) > 200:
            errors.append("sake_name is too long")
    return len(errors) == 0, errors


def validate_sake_name(name: str) -> tuple[bool, str]:
    """Validate sake name."""
    if not name:
        return False, "Sake name is required"
    if not name.strip():
        return False, "Sake name is required"
    if len(name) < 2:
        return False, "Sake name is too short"
    if len(name) > 200:
        return False, "Sake name is too long"
    return True, ""


def validate_rating(rating: int) -> tuple[bool, str]:
    """Validate rating value."""
    if not isinstance(rating, int):
        return False, "Rating must be an integer"
    if rating < 1 or rating > 5:
        return False, "Rating must be between 1 and 5"
    return True, ""


def validate_image_file(file_name: str, file_size: int, max_size_mb: int = 10) -> tuple[bool, str]:
    """Validate uploaded image file."""
    if not file_name:
        return False, "No file selected"

    allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]
    file_ext = "." + file_name.split(".")[-1].lower() if "." in file_name else ""

    if file_ext not in allowed_extensions:
        return False, f"Unsupported format. Use: {', '.join(allowed_extensions)}"

    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        return False, f"File too large (max {max_size_mb}MB)"

    return True, ""


def sanitize_text_input(text: str, max_length: int = 1000) -> str:
    """Sanitize text input."""
    if not text:
        return ""
    text = text.replace("\x00", "")
    if len(text) > max_length:
        text = text[:max_length]
    return text.strip()
