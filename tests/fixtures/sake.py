"""Sake test fixtures."""

from datetime import datetime
from typing import Any


def sample_sake() -> dict[str, Any]:
    """Return sample sake data."""
    return {
        "sake_id": "sake-001",
        "name": "獺祭 純米大吟醸 磨き二割三分",
        "brewery_id": "brewery-001",
        "type": "junmai_daiginjo",
        "rice_polishing_ratio": 23,
        "alcohol_content": 16.0,
        "sake_meter_value": 4,
        "acidity": 1.4,
        "amino_acid": 0.8,
        "sweetness": 2,
        "richness": 2,
        "aroma_intensity": 5,
        "flavor_profile": {
            "fruity": 5,
            "floral": 4,
            "rice": 3,
            "spicy": 1,
            "umami": 2,
        },
        "description": "華やかな吟醸香と繊細な味わいが特徴の最高級純米大吟醸。",
        "price": 5280,
        "volume_ml": 720,
        "food_pairings": ["刺身", "白身魚", "フルーツ"],
        "serving_temperature": ["冷やして"],
        "image_url": "https://example.com/sake-001.jpg",
        "average_rating": 4.5,
        "rating_count": 120,
        "created_at": datetime(2025, 1, 1, 0, 0, 0).isoformat(),
        "updated_at": datetime(2025, 10, 1, 0, 0, 0).isoformat(),
    }


def sample_sake_list() -> list[dict[str, Any]]:
    """Return list of sample sake data."""
    return [
        sample_sake(),
        {
            "sake_id": "sake-002",
            "name": "久保田 萬寿",
            "brewery_id": "brewery-002",
            "type": "junmai_daiginjo",
            "rice_polishing_ratio": 50,
            "alcohol_content": 15.0,
            "sake_meter_value": 2,
            "acidity": 1.2,
            "amino_acid": 1.0,
            "sweetness": 3,
            "richness": 3,
            "aroma_intensity": 4,
            "flavor_profile": {
                "fruity": 4,
                "floral": 3,
                "rice": 4,
                "spicy": 2,
                "umami": 3,
            },
            "description": "ふくよかな香りと深い味わいの純米大吟醸。",
            "price": 3850,
            "volume_ml": 720,
            "food_pairings": ["焼き魚", "天ぷら", "鍋料理"],
            "serving_temperature": ["冷やして", "常温"],
            "image_url": "https://example.com/sake-002.jpg",
            "average_rating": 4.3,
            "rating_count": 95,
            "created_at": datetime(2025, 1, 1, 0, 0, 0).isoformat(),
            "updated_at": datetime(2025, 10, 1, 0, 0, 0).isoformat(),
        },
        {
            "sake_id": "sake-003",
            "name": "八海山 純米吟醸",
            "brewery_id": "brewery-003",
            "type": "junmai_ginjo",
            "rice_polishing_ratio": 50,
            "alcohol_content": 15.5,
            "sake_meter_value": 4,
            "acidity": 1.5,
            "amino_acid": 1.2,
            "sweetness": 2,
            "richness": 3,
            "aroma_intensity": 3,
            "flavor_profile": {
                "fruity": 3,
                "floral": 2,
                "rice": 4,
                "spicy": 2,
                "umami": 3,
            },
            "description": "すっきりとした飲み口の純米吟醸。",
            "price": 2640,
            "volume_ml": 720,
            "food_pairings": ["寿司", "刺身", "焼き鳥"],
            "serving_temperature": ["冷やして", "常温"],
            "image_url": "https://example.com/sake-003.jpg",
            "average_rating": 4.2,
            "rating_count": 150,
            "created_at": datetime(2025, 1, 1, 0, 0, 0).isoformat(),
            "updated_at": datetime(2025, 10, 1, 0, 0, 0).isoformat(),
        },
    ]


def sample_brewery() -> dict[str, Any]:
    """Return sample brewery data."""
    return {
        "brewery_id": "brewery-001",
        "name": "旭酒造",
        "prefecture": "山口県",
        "city": "岩国市",
        "established_year": 1948,
        "description": "獺祭で有名な酒蔵。純米大吟醸のみを製造。",
        "website": "https://www.asahishuzo.ne.jp",
        "sake_count": 5,
        "average_rating": 4.4,
        "created_at": datetime(2025, 1, 1, 0, 0, 0).isoformat(),
        "updated_at": datetime(2025, 10, 1, 0, 0, 0).isoformat(),
    }


def sample_tasting_record() -> dict[str, Any]:
    """Return sample tasting record data."""
    return {
        "record_id": "record-001",
        "user_id": "test-user-123",
        "sake_id": "sake-001",
        "rating": 5,
        "sweetness": 2,
        "acidity": 4,
        "richness": 2,
        "aroma_intensity": 5,
        "notes": "華やかな香りで飲みやすい。特別な日にまた飲みたい。",
        "occasion": "celebration",
        "serving_temperature": "冷やして",
        "food_pairing": "刺身",
        "image_urls": [],
        "created_at": datetime(2025, 10, 1, 0, 0, 0).isoformat(),
        "updated_at": datetime(2025, 10, 1, 0, 0, 0).isoformat(),
    }


def sample_recommendation() -> dict[str, Any]:
    """Return sample recommendation data."""
    return {
        "sake_id": "sake-001",
        "score": 0.92,
        "reasoning": "お好みの甘さ控えめで華やかな香りの日本酒です。",
        "matching_factors": ["aroma_intensity", "sweetness", "type"],
    }
