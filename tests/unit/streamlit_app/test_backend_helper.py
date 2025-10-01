"""
Unit tests for Streamlit Backend Helper.
"""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestBackendClient:
    """Tests for BackendClient class."""

    @patch("utils.config.config")
    def test_init_with_gateway_url(self, mock_config):
        """Test BackendClient initialization with Gateway URL."""
        from utils.backend_helper import BackendClient

        mock_config.AGENTCORE_GATEWAY_URL = "https://gateway.example.com"
        mock_config.AWS_REGION = "us-west-2"

        client = BackendClient()

        assert client.use_gateway is True
        assert client.gateway_url == "https://gateway.example.com"

    @patch("utils.backend_helper.boto3")
    @patch("utils.config.config")
    def test_init_without_gateway_url(self, mock_config, mock_boto3):
        """Test BackendClient initialization without Gateway URL (fallback mode)."""
        from utils.backend_helper import BackendClient

        mock_config.AGENTCORE_GATEWAY_URL = None
        mock_config.AWS_REGION = "us-west-2"

        client = BackendClient()

        assert client.use_gateway is False
        assert mock_boto3.client.called

    @patch("utils.backend_helper.SessionManager")
    def test_get_headers_with_token(self, mock_session):
        """Test _get_headers with authentication token."""
        from utils.backend_helper import BackendClient

        mock_session.get_id_token.return_value = "test-token-123"

        with patch("utils.config.config") as mock_config:
            mock_config.AGENTCORE_GATEWAY_URL = "https://gateway.example.com"
            client = BackendClient()

        headers = client._get_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-token-123"

    @patch("utils.backend_helper.SessionManager")
    def test_get_headers_without_token(self, mock_session):
        """Test _get_headers without authentication token."""
        from utils.backend_helper import BackendClient

        mock_session.get_id_token.return_value = None

        with patch("utils.config.config") as mock_config:
            mock_config.AGENTCORE_GATEWAY_URL = "https://gateway.example.com"
            client = BackendClient()

        headers = client._get_headers()

        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers

    @patch("utils.backend_helper.boto3")
    @patch("utils.config.config")
    def test_invoke_lambda_direct_success(self, mock_config, mock_boto3):
        """Test direct Lambda invocation success."""
        from utils.backend_helper import BackendClient

        mock_config.AGENTCORE_GATEWAY_URL = None
        mock_config.AWS_REGION = "us-west-2"

        mock_lambda = MagicMock()
        mock_boto3.client.return_value = mock_lambda

        # Mock successful Lambda response
        mock_lambda.invoke.return_value = {
            "Payload": MagicMock(
                read=lambda: json.dumps({
                    "statusCode": 200,
                    "body": json.dumps({"success": True, "data": {"test": "value"}}),
                }).encode()
            )
        }

        client = BackendClient()
        result = client._invoke_lambda_direct(
            "arn:aws:lambda:us-west-2:123:function:test", {"test": "payload"}
        )

        assert result["success"] is True
        assert result["data"]["test"] == "value"

    @patch("utils.backend_helper.boto3")
    @patch("utils.config.config")
    def test_invoke_lambda_direct_error(self, mock_config, mock_boto3):
        """Test direct Lambda invocation with error."""
        from utils.backend_helper import BackendClient, BackendError

        mock_config.AGENTCORE_GATEWAY_URL = None
        mock_config.AWS_REGION = "us-west-2"

        mock_lambda = MagicMock()
        mock_boto3.client.return_value = mock_lambda

        # Mock Lambda error response
        mock_lambda.invoke.return_value = {
            "Payload": MagicMock(
                read=lambda: json.dumps({"errorMessage": "Test error"}).encode()
            )
        }

        client = BackendClient()

        with pytest.raises(BackendError, match="Lambda error: Test error"):
            client._invoke_lambda_direct(
                "arn:aws:lambda:us-west-2:123:function:test", {"test": "payload"}
            )

    @patch("utils.backend_helper.requests")
    @patch("utils.backend_helper.SessionManager")
    @patch("utils.config.config")
    def test_make_request_with_gateway(self, mock_config, mock_session, mock_requests):
        """Test _make_request using Gateway."""
        from utils.backend_helper import BackendClient

        mock_config.AGENTCORE_GATEWAY_URL = "https://gateway.example.com"
        mock_config.AWS_REGION = "us-west-2"
        mock_session.get_id_token.return_value = "test-token"

        # Mock successful Gateway response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "isError": False,
            "content": {"result": "success"},
        }
        mock_requests.post.return_value = mock_response

        client = BackendClient()
        result = client._make_request("test_tool", {"param": "value"})

        assert result["result"] == "success"
        mock_requests.post.assert_called_once()

    @patch("utils.backend_helper.boto3")
    @patch("utils.backend_helper.SessionManager")
    @patch("utils.config.config")
    def test_get_user_preferences_success(self, mock_config, mock_session, mock_boto3):
        """Test get_user_preferences success."""
        from utils.backend_helper import BackendClient

        mock_config.AGENTCORE_GATEWAY_URL = None
        mock_config.AWS_REGION = "us-west-2"
        mock_config.LAMBDA_PREFERENCE_ARN = "arn:aws:lambda:us-west-2:123:function:pref"
        mock_session.get_user_id.return_value = "test-user-123"

        mock_lambda = MagicMock()
        mock_boto3.client.return_value = mock_lambda

        # Mock Lambda response
        mock_lambda.invoke.return_value = {
            "Payload": MagicMock(
                read=lambda: json.dumps({
                    "statusCode": 200,
                    "body": json.dumps({
                        "data": {
                            "user_id": "test-user-123",
                            "flavor_preference": "rich",
                            "sweetness": 7,
                        }
                    }),
                }).encode()
            )
        }

        client = BackendClient()
        prefs = client.get_user_preferences()

        assert prefs["user_id"] == "test-user-123"
        assert prefs["flavor_preference"] == "rich"

    @patch("utils.backend_helper.boto3")
    @patch("utils.backend_helper.SessionManager")
    @patch("utils.config.config")
    def test_get_sake_recommendations(self, mock_config, mock_session, mock_boto3):
        """Test get_sake_recommendations."""
        from utils.backend_helper import BackendClient

        mock_config.AGENTCORE_GATEWAY_URL = None
        mock_config.AWS_REGION = "us-west-2"
        mock_config.LAMBDA_RECOMMENDATION_ARN = "arn:aws:lambda:us-west-2:123:function:rec"
        mock_session.get_user_id.return_value = "test-user-123"

        mock_lambda = MagicMock()
        mock_boto3.client.return_value = mock_lambda

        # Mock Lambda response
        mock_lambda.invoke.return_value = {
            "Payload": MagicMock(
                read=lambda: json.dumps({
                    "statusCode": 200,
                    "body": json.dumps({
                        "data": {
                            "recommendations": [
                                {"sake_id": "S001", "name": "獺祭", "score": 95}
                            ]
                        }
                    }),
                }).encode()
            )
        }

        client = BackendClient()
        recs = client.get_sake_recommendations(limit=5)

        assert len(recs) == 1
        assert recs[0]["name"] == "獺祭"

    @patch("utils.backend_helper.boto3")
    @patch("utils.backend_helper.SessionManager")
    @patch("utils.config.config")
    def test_recognize_sake_label(self, mock_config, mock_session, mock_boto3):
        """Test recognize_sake_label."""
        from utils.backend_helper import BackendClient

        mock_config.AGENTCORE_GATEWAY_URL = None
        mock_config.AWS_REGION = "us-west-2"
        mock_config.LAMBDA_IMAGE_RECOGNITION_ARN = (
            "arn:aws:lambda:us-west-2:123:function:img"
        )

        mock_lambda = MagicMock()
        mock_boto3.client.return_value = mock_lambda

        # Mock Lambda response
        mock_lambda.invoke.return_value = {
            "Payload": MagicMock(
                read=lambda: json.dumps({
                    "statusCode": 200,
                    "body": json.dumps({
                        "data": {
                            "sake_name": "獺祭 純米大吟醸",
                            "brewery_name": "旭酒造",
                            "confidence": "high",
                        }
                    }),
                }).encode()
            )
        }

        client = BackendClient()
        result = client.recognize_sake_label("base64encodedimage", "image/jpeg")

        assert result["sake_name"] == "獺祭 純米大吟醸"
        assert result["brewery_name"] == "旭酒造"

    @patch("utils.backend_helper.boto3")
    @patch("utils.config.config")
    def test_backend_error_exception(self, mock_config, mock_boto3):
        """Test BackendError exception."""
        from utils.backend_helper import BackendClient, BackendError

        mock_config.AGENTCORE_GATEWAY_URL = None
        mock_config.AWS_REGION = "us-west-2"

        mock_lambda = MagicMock()
        mock_boto3.client.return_value = mock_lambda

        # Mock Lambda exception
        mock_lambda.invoke.side_effect = Exception("Connection failed")

        client = BackendClient()

        with pytest.raises(BackendError, match="Lambda invocation failed"):
            client._invoke_lambda_direct(
                "arn:aws:lambda:us-west-2:123:function:test", {}
            )
