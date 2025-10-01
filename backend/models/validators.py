"""
Sake Sensei - Data Validators

Common validation functions for sake, brewery, and user data.
"""

from typing import Any

# Japanese Prefectures (47 prefectures)
VALID_PREFECTURES = {
    "北海道",
    "青森県",
    "岩手県",
    "宮城県",
    "秋田県",
    "山形県",
    "福島県",
    "茨城県",
    "栃木県",
    "群馬県",
    "埼玉県",
    "千葉県",
    "東京都",
    "神奈川県",
    "新潟県",
    "富山県",
    "石川県",
    "福井県",
    "山梨県",
    "長野県",
    "岐阜県",
    "静岡県",
    "愛知県",
    "三重県",
    "滋賀県",
    "京都府",
    "大阪府",
    "兵庫県",
    "奈良県",
    "和歌山県",
    "鳥取県",
    "島根県",
    "岡山県",
    "広島県",
    "山口県",
    "徳島県",
    "香川県",
    "愛媛県",
    "高知県",
    "福岡県",
    "佐賀県",
    "長崎県",
    "熊本県",
    "大分県",
    "宮崎県",
    "鹿児島県",
    "沖縄県",
}

# Sake Categories (Special Designation Sake - 特定名称酒)
VALID_SAKE_CATEGORIES = {
    "純米大吟醸",
    "純米吟醸",
    "特別純米",
    "純米酒",
    "大吟醸",
    "吟醸",
    "特別本醸造",
    "本醸造",
    "普通酒",
}

# Serving Temperatures
VALID_TEMPERATURES = {
    "雪冷え",  # 5°C (very cold)
    "花冷え",  # 10°C (cold)
    "涼冷え",  # 15°C (cool)
    "冷酒",  # Cold sake (general)
    "常温",  # Room temperature (20°C)
    "日向燗",  # 30°C (lukewarm)
    "人肌燗",  # 35°C (body temperature)
    "ぬる燗",  # 40°C (warm)
    "上燗",  # 45°C (hot)
    "熱燗",  # 50°C (very hot)
    "飛び切り燗",  # 55°C+ (extremely hot)
}

# User Experience Levels
VALID_EXPERIENCE_LEVELS = {"beginner", "intermediate", "advanced"}


def validate_prefecture(prefecture: str) -> str:
    """Validate Japanese prefecture name.

    Args:
        prefecture: Prefecture name in Japanese

    Returns:
        The validated prefecture name

    Raises:
        ValueError: If prefecture is not valid
    """
    if prefecture not in VALID_PREFECTURES:
        valid_list = ", ".join(sorted(VALID_PREFECTURES))
        msg = f"Invalid prefecture: {prefecture}. Must be one of: {valid_list}"
        raise ValueError(msg)
    return prefecture


def validate_sake_category(category: str) -> str:
    """Validate sake category.

    Args:
        category: Sake category name

    Returns:
        The validated category name

    Raises:
        ValueError: If category is not valid
    """
    if category not in VALID_SAKE_CATEGORIES:
        valid_list = ", ".join(sorted(VALID_SAKE_CATEGORIES))
        msg = f"Invalid sake category: {category}. Must be one of: {valid_list}"
        raise ValueError(msg)
    return category


def validate_temperature(temperature: str) -> str:
    """Validate sake serving temperature.

    Args:
        temperature: Temperature description in Japanese

    Returns:
        The validated temperature

    Raises:
        ValueError: If temperature is not valid
    """
    if temperature not in VALID_TEMPERATURES:
        valid_list = ", ".join(sorted(VALID_TEMPERATURES))
        msg = f"Invalid temperature: {temperature}. Must be one of: {valid_list}"
        raise ValueError(msg)
    return temperature


def validate_experience_level(level: str) -> str:
    """Validate user experience level.

    Args:
        level: Experience level (beginner, intermediate, advanced)

    Returns:
        The validated experience level

    Raises:
        ValueError: If experience level is not valid
    """
    if level not in VALID_EXPERIENCE_LEVELS:
        valid_list = ", ".join(sorted(VALID_EXPERIENCE_LEVELS))
        msg = f"Invalid experience level: {level}. Must be one of: {valid_list}"
        raise ValueError(msg)
    return level


def validate_rating(rating: int) -> int:
    """Validate rating value.

    Args:
        rating: Rating value (1-5)

    Returns:
        The validated rating

    Raises:
        ValueError: If rating is not in valid range
    """
    if not 1 <= rating <= 5:
        msg = f"Rating must be between 1 and 5, got: {rating}"
        raise ValueError(msg)
    return rating


def validate_price(price: int) -> int:
    """Validate price value.

    Args:
        price: Price in yen

    Returns:
        The validated price

    Raises:
        ValueError: If price is not positive
    """
    if price <= 0:
        msg = f"Price must be positive, got: {price}"
        raise ValueError(msg)
    return price


def validate_alcohol_content(alcohol_content: float) -> float:
    """Validate alcohol content percentage.

    Args:
        alcohol_content: Alcohol percentage (0-100)

    Returns:
        The validated alcohol content

    Raises:
        ValueError: If alcohol content is not in valid range
    """
    if not 0 <= alcohol_content <= 100:
        msg = f"Alcohol content must be between 0 and 100, got: {alcohol_content}"
        raise ValueError(msg)
    return alcohol_content


# Pydantic validator decorators for use in models
def pydantic_prefecture_validator(_cls: Any, v: str) -> str:
    """Pydantic validator for prefecture field."""
    return validate_prefecture(v)


def pydantic_sake_category_validator(_cls: Any, v: str) -> str:
    """Pydantic validator for sake category field."""
    return validate_sake_category(v)


def pydantic_temperature_validator(_cls: Any, v: str) -> str:
    """Pydantic validator for temperature field."""
    return validate_temperature(v)


def pydantic_experience_level_validator(_cls: Any, v: str) -> str:
    """Pydantic validator for experience level field."""
    return validate_experience_level(v)
