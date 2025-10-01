"""
Sake Sensei - Backend API Helper

Helper functions for calling Lambda functions via AgentCore Gateway.
"""

import json
from datetime import datetime
from typing import Any

import requests
from utils.config import config
from utils.session import SessionManager


class BackendError(Exception):
    """Custom exception for backend API errors."""

    pass


class BackendClient:
    """Client for backend Lambda function calls via AgentCore Gateway."""

    def __init__(self):
        """Initialize backend client."""
        self.gateway_url = config.AGENTCORE_GATEWAY_URL
        self.timeout = 30

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
        }

        # Add ID token for authentication
        id_token = SessionManager.get_id_token()
        if id_token:
            headers["Authorization"] = f"Bearer {id_token}"

        return headers

    def _make_request(
        self, tool_name: str, parameters: dict[str, Any], timeout: int | None = None
    ) -> dict[str, Any]:
        """
        Make request to Gateway tool.

        Args:
            tool_name: MCP tool name
            parameters: Tool parameters
            timeout: Request timeout in seconds

        Returns:
            Tool response data

        Raises:
            BackendError: On API errors
        """
        try:
            response = requests.post(
                f"{self.gateway_url}/invoke-tool",
                json={"tool": tool_name, "arguments": parameters},
                headers=self._get_headers(),
                timeout=timeout or self.timeout,
            )

            if response.status_code != 200:
                raise BackendError(f"API request failed: {response.status_code} {response.text}")

            result = response.json()

            # Check for tool execution errors
            if result.get("isError"):
                raise BackendError(
                    f"Tool execution failed: {result.get('content', 'Unknown error')}"
                )

            return result.get("content", {})

        except requests.exceptions.Timeout:
            raise BackendError("Request timeout. Please try again.")

        except requests.exceptions.RequestException as e:
            raise BackendError(f"Network error: {str(e)}")

        except json.JSONDecodeError:
            raise BackendError("Invalid response from server")

    # Preference Management

    def get_user_preferences(self, user_id: str | None = None) -> dict[str, Any] | None:
        """
        Get user preferences.

        Args:
            user_id: User ID (defaults to current user)

        Returns:
            User preferences or None if not found
        """
        uid = user_id or SessionManager.get_user_id()
        if not uid:
            raise BackendError("User ID not available")

        try:
            result = self._make_request(
                "manage_user_preferences", {"action": "get", "user_id": uid}
            )
            return result.get("preferences")

        except BackendError as e:
            if "not found" in str(e).lower():
                return None
            raise

    def save_user_preferences(
        self, preferences: dict[str, Any], user_id: str | None = None
    ) -> bool:
        """
        Save user preferences.

        Args:
            preferences: User preference data
            user_id: User ID (defaults to current user)

        Returns:
            True if successful
        """
        uid = user_id or SessionManager.get_user_id()
        if not uid:
            raise BackendError("User ID not available")

        result = self._make_request(
            "manage_user_preferences",
            {"action": "update", "user_id": uid, "preferences": preferences},
        )

        return result.get("success", False)

    # Sake Recommendations

    def get_recommendations(
        self, preferences: dict[str, Any] | None = None, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Get sake recommendations.

        Args:
            preferences: User preferences (optional)
            limit: Number of recommendations

        Returns:
            List of recommended sake
        """
        user_id = SessionManager.get_user_id()
        if not user_id:
            raise BackendError("User ID not available")

        params: dict[str, Any] = {"user_id": user_id, "limit": limit}

        if preferences:
            params["preferences"] = preferences

        result = self._make_request("get_sake_recommendations", params)
        return result.get("recommendations", [])

    # Tasting Records

    def create_tasting_record(self, record: dict[str, Any]) -> str:
        """
        Create tasting record.

        Args:
            record: Tasting record data

        Returns:
            Created record ID
        """
        user_id = SessionManager.get_user_id()
        if not user_id:
            raise BackendError("User ID not available")

        # Add user_id and timestamp if not present
        record["user_id"] = user_id
        if "tasted_at" not in record:
            record["tasted_at"] = datetime.now().isoformat()

        result = self._make_request(
            "manage_tasting_records", {"action": "create", "record": record}
        )

        return result.get("record_id", "")

    def get_tasting_records(
        self, user_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get tasting records for user.

        Args:
            user_id: User ID (defaults to current user)
            limit: Maximum number of records

        Returns:
            List of tasting records
        """
        uid = user_id or SessionManager.get_user_id()
        if not uid:
            raise BackendError("User ID not available")

        result = self._make_request(
            "manage_tasting_records", {"action": "list", "user_id": uid, "limit": limit}
        )

        return result.get("records", [])

    def get_tasting_statistics(self, user_id: str | None = None) -> dict[str, Any]:
        """
        Get tasting statistics for user.

        Args:
            user_id: User ID (defaults to current user)

        Returns:
            Statistics dictionary
        """
        uid = user_id or SessionManager.get_user_id()
        if not uid:
            raise BackendError("User ID not available")

        result = self._make_request(
            "manage_tasting_records", {"action": "statistics", "user_id": uid}
        )

        return result.get("statistics", {})

    # Brewery Information

    def get_brewery_info(self, brewery_id: str) -> dict[str, Any] | None:
        """
        Get brewery information.

        Args:
            brewery_id: Brewery ID

        Returns:
            Brewery information or None if not found
        """
        try:
            result = self._make_request("get_brewery_info", {"brewery_id": brewery_id})
            return result.get("brewery")

        except BackendError as e:
            if "not found" in str(e).lower():
                return None
            raise

    def search_breweries(
        self, prefecture: str | None = None, name: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Search breweries.

        Args:
            prefecture: Filter by prefecture
            name: Search by name

        Returns:
            List of matching breweries
        """
        params: dict[str, Any] = {"action": "search"}

        if prefecture:
            params["prefecture"] = prefecture

        if name:
            params["name"] = name

        result = self._make_request("get_brewery_info", params)
        return result.get("breweries", [])

    # Image Recognition

    def recognize_sake_label(
        self, image_data: str, media_type: str = "image/jpeg"
    ) -> dict[str, Any]:
        """
        Recognize sake from label image.

        Args:
            image_data: Base64-encoded image data
            media_type: Image media type (image/jpeg, image/png, etc.)

        Returns:
            Recognition result with sake information
        """
        result = self._make_request(
            "recognize_sake_label",
            {"image_data": image_data, "media_type": media_type},
            timeout=60,  # Image recognition may take longer
        )

        return result


# Global client instance
backend_client = BackendClient()
