"""
Sake Sensei - Recommendation Algorithm

Content-based filtering algorithm for sake recommendations.
"""

from typing import Any


class RecommendationEngine:
    """Recommendation engine using content-based filtering."""

    def __init__(
        self,
        sake_table: Any,
        brewery_table: Any,
        tasting_table: Any,
    ) -> None:
        """Initialize recommendation engine.

        Args:
            sake_table: DynamoDB table for sake master data
            brewery_table: DynamoDB table for brewery master data
            tasting_table: DynamoDB table for tasting records
        """
        self.sake_table = sake_table
        self.brewery_table = brewery_table
        self.tasting_table = tasting_table

    def recommend(
        self,
        user_id: str,
        preferences: dict[str, Any],
        tasting_history: list[dict[str, Any]],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Generate sake recommendations.

        Args:
            user_id: User ID
            preferences: User preferences (sweetness, acidity, etc.)
            tasting_history: User's past tasting records
            limit: Maximum number of recommendations

        Returns:
            List of recommended sake with scores
        """
        # Get all sake from database
        all_sake = self._get_all_sake()

        # Filter by budget if specified
        budget = preferences.get("budget")
        if budget:
            all_sake = [s for s in all_sake if s.get("price", 0) <= budget]

        # Filter by preferred categories if specified
        preferred_categories = preferences.get("categories", [])
        if preferred_categories:
            all_sake = [s for s in all_sake if s.get("category") in preferred_categories]

        # Filter out already tasted sake
        tasted_sake_ids = {record.get("sake_id") for record in tasting_history}
        candidate_sake = [s for s in all_sake if s.get("sake_id") not in tasted_sake_ids]

        # Score each sake based on preferences
        scored_sake = []
        for sake in candidate_sake:
            score = self._calculate_score(sake, preferences, tasting_history)
            match_reason = self._generate_match_reason(sake, preferences)

            scored_sake.append(
                {
                    "sake_id": sake["sake_id"],
                    "name": sake["name"],
                    "brewery_id": sake["brewery_id"],
                    "category": sake["category"],
                    "price": sake.get("price", 0),
                    "sweetness": sake.get("sweetness", 3),
                    "acidity": sake.get("acidity", 3),
                    "richness": sake.get("richness", 3),
                    "score": round(score, 2),
                    "match_reason": match_reason,
                }
            )

        # Sort by score descending and return top N
        scored_sake.sort(key=lambda x: x["score"], reverse=True)
        return scored_sake[:limit]

    def _get_all_sake(self) -> list[dict[str, Any]]:
        """Get all sake from DynamoDB.

        Returns:
            List of all sake records
        """
        try:
            response = self.sake_table.scan()
            return response.get("Items", [])
        except Exception:
            return []

    def _calculate_score(
        self,
        sake: dict[str, Any],
        preferences: dict[str, Any],
        tasting_history: list[dict[str, Any]],
    ) -> float:
        """Calculate recommendation score for a sake.

        Args:
            sake: Sake record
            preferences: User preferences
            tasting_history: User's tasting history

        Returns:
            Score (0-100)
        """
        score = 0.0

        # Taste profile matching (60% weight)
        taste_score = self._calculate_taste_match(sake, preferences)
        score += taste_score * 0.6

        # Experience level matching (20% weight)
        experience_score = self._calculate_experience_match(sake, preferences)
        score += experience_score * 0.2

        # Diversity bonus (10% weight) - prefer sake from different breweries
        diversity_score = self._calculate_diversity_score(sake, tasting_history)
        score += diversity_score * 0.1

        # Popularity bonus (10% weight) - based on rating if available
        popularity_score = sake.get("rating", 3.0) * 20  # Scale 0-5 to 0-100
        score += popularity_score * 0.1

        return min(score, 100.0)

    def _calculate_taste_match(
        self,
        sake: dict[str, Any],
        preferences: dict[str, Any],
    ) -> float:
        """Calculate taste profile match score.

        Args:
            sake: Sake record
            preferences: User preferences

        Returns:
            Score (0-100)
        """
        # Get user's preferred taste values (1-5 scale)
        pref_sweetness = preferences.get("sweetness", 3)
        pref_acidity = preferences.get("acidity", 3)
        pref_richness = preferences.get("richness", 3)

        # Get sake's taste profile
        sake_sweetness = sake.get("sweetness", 3)
        sake_acidity = sake.get("acidity", 3)
        sake_richness = sake.get("richness", 3)

        # Calculate distance for each dimension (0-4 scale)
        sweetness_diff = abs(pref_sweetness - sake_sweetness)
        acidity_diff = abs(pref_acidity - sake_acidity)
        richness_diff = abs(pref_richness - sake_richness)

        # Average difference (lower is better)
        avg_diff = (sweetness_diff + acidity_diff + richness_diff) / 3

        # Convert to score (0-100, where 0 diff = 100 score)
        score = 100 - (avg_diff * 25)  # Max diff is 4, so multiply by 25

        return max(score, 0.0)

    def _calculate_experience_match(
        self,
        sake: dict[str, Any],
        preferences: dict[str, Any],
    ) -> float:
        """Calculate experience level match score.

        Args:
            sake: Sake record
            preferences: User preferences

        Returns:
            Score (0-100)
        """
        experience_level = preferences.get("experience_level", "beginner")
        sake_category = sake.get("category", "")

        # Beginner-friendly categories
        beginner_categories = ["junmai", "honjozo", "futsushu"]
        # Advanced categories
        advanced_categories = ["daiginjo", "junmai_daiginjo", "koshu"]

        if experience_level == "beginner":
            return 100.0 if sake_category in beginner_categories else 50.0
        elif experience_level == "intermediate":
            return 80.0  # Intermediate users can try anything
        elif experience_level == "advanced":
            return 100.0 if sake_category in advanced_categories else 70.0
        else:
            return 50.0

    def _calculate_diversity_score(
        self,
        sake: dict[str, Any],
        tasting_history: list[dict[str, Any]],
    ) -> float:
        """Calculate diversity bonus score.

        Rewards sake from breweries the user hasn't tried yet.

        Args:
            sake: Sake record
            tasting_history: User's tasting history

        Returns:
            Score (0-100)
        """
        if not tasting_history:
            return 100.0  # Maximum diversity for new users

        # Get breweries the user has tried
        tried_breweries = {record.get("brewery_id") for record in tasting_history}

        # Give bonus if this is a new brewery
        if sake.get("brewery_id") not in tried_breweries:
            return 100.0
        else:
            return 50.0

    def _generate_match_reason(
        self,
        sake: dict[str, Any],
        preferences: dict[str, Any],
    ) -> str:
        """Generate human-readable match reason.

        Args:
            sake: Sake record
            preferences: User preferences

        Returns:
            Match reason string
        """
        reasons = []

        # Taste match
        pref_sweetness = preferences.get("sweetness", 3)
        sake_sweetness = sake.get("sweetness", 3)
        if abs(pref_sweetness - sake_sweetness) <= 1:
            if sake_sweetness <= 2:
                reasons.append("辛口でスッキリ")
            elif sake_sweetness >= 4:
                reasons.append("甘口でまろやか")
            else:
                reasons.append("バランスの良い味わい")

        # Category match
        category = sake.get("category", "")
        if category in ["daiginjo", "junmai_daiginjo"]:
            reasons.append("華やかな香り")
        elif category == "junmai":
            reasons.append("お米の旨味")

        # Default reason
        if not reasons:
            reasons.append("おすすめの一本")

        return "、".join(reasons)
