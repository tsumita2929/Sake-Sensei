"""Smoke tests for application health checks."""

import os

import pytest
import requests


@pytest.mark.smoke
class TestHealthChecks:
    """Test basic health endpoints."""

    @pytest.fixture
    def base_url(self) -> str:
        """Get base URL from environment or use default."""
        return os.getenv(
            "APP_URL",
            "http://sakese-Publi-5SDe3QrKne55-1360562030.us-west-2.elb.amazonaws.com",
        )

    def test_streamlit_health_endpoint(self, base_url: str) -> None:
        """Test Streamlit health check endpoint."""
        response = requests.get(f"{base_url}/_stcore/health", timeout=30)
        assert response.status_code == 200

    def test_application_loads(self, base_url: str) -> None:
        """Test main application page loads."""
        response = requests.get(base_url, timeout=30)
        assert response.status_code == 200
        assert len(response.content) > 0

    def test_response_time(self, base_url: str) -> None:
        """Test response time is acceptable."""
        import time

        start = time.time()
        response = requests.get(f"{base_url}/_stcore/health", timeout=30)
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 5.0, f"Health check took {elapsed:.2f}s, expected < 5.0s"
