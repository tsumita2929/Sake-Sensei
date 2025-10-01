"""
Unit tests for Image Recognition Lambda function.
"""

import base64
import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def lambda_context():
    """Mock Lambda context."""
    context = MagicMock()
    context.function_name = "test-function"
    context.invoked_function_arn = "arn:aws:lambda:us-west-2:123456789012:function:test"
    context.memory_limit_in_mb = 1024
    context.request_id = "test-request-id"
    return context


@pytest.fixture
def mock_bedrock():
    """Mock Bedrock Runtime client."""
    with patch("boto3.client") as mock_client:
        mock_bedrock_runtime = MagicMock()
        mock_client.return_value = mock_bedrock_runtime
        yield mock_bedrock_runtime


@pytest.fixture
def sample_image_base64():
    """Sample base64 encoded image."""
    # Create a minimal valid base64 string (represents a 1x1 pixel image)
    return base64.b64encode(b"\x89PNG\r\n\x1a\n").decode("utf-8")


class TestImageRecognitionLambda:
    """Tests for Image Recognition Lambda handler."""

    def test_handler_missing_image_data(self, lambda_context):
        """Test handler without image data."""
        from backend.lambdas.image_recognition.handler import handler

        event = {"body": json.dumps({})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "image_base64 or image_s3_key" in body["message"]

    def test_handler_with_base64_image(
        self, lambda_context, mock_bedrock, sample_image_base64
    ):
        """Test handler with base64 encoded image."""
        from backend.lambdas.image_recognition.handler import handler

        # Mock Bedrock response
        mock_bedrock.invoke_model.return_value = {
            "body": MagicMock(
                read=lambda: json.dumps({
                    "content": [
                        {
                            "text": json.dumps({
                                "sake_name": "獺祭 純米大吟醸 磨き二割三分",
                                "brewery_name": "旭酒造",
                                "category": "junmai_daiginjo",
                                "polishing_ratio": 23,
                                "alcohol_content": 16.0,
                                "confidence": "high",
                            })
                        }
                    ]
                }).encode()
            )
        }

        event = {
            "body": json.dumps({
                "image_base64": sample_image_base64,
                "content_type": "image/jpeg",
            })
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["sake_name"] == "獺祭 純米大吟醸 磨き二割三分"
        assert body["data"]["brewery_name"] == "旭酒造"
        assert body["data"]["confidence"] == "high"

    def test_handler_with_s3_image(self, lambda_context, mock_bedrock):
        """Test handler with S3 image."""
        from backend.lambdas.image_recognition.handler import handler

        # Mock S3 client
        with patch("boto3.client") as mock_s3:
            mock_s3_client = MagicMock()
            mock_s3.return_value = mock_s3_client
            mock_s3_client.get_object.return_value = {
                "Body": MagicMock(read=lambda: b"fake_image_data"),
                "ContentType": "image/jpeg",
            }

            # Mock Bedrock response
            mock_bedrock.invoke_model.return_value = {
                "body": MagicMock(
                    read=lambda: json.dumps({
                        "content": [
                            {
                                "text": json.dumps({
                                    "sake_name": "久保田 萬寿",
                                    "brewery_name": "朝日酒造",
                                    "category": "junmai_daiginjo",
                                    "confidence": "high",
                                })
                            }
                        ]
                    }).encode()
                )
            }

            event = {
                "body": json.dumps({
                    "image_s3_key": "uploads/test-image.jpg",
                    "bucket": "test-bucket",
                })
            }

            response = handler(event, lambda_context)

            assert response["statusCode"] == 200
            assert mock_s3_client.get_object.called

    def test_parse_bedrock_response_json_block(self):
        """Test parsing Bedrock response with JSON code block."""
        from backend.lambdas.image_recognition.handler import parse_bedrock_response

        text = '''```json
{
  "sake_name": "獺祭",
  "brewery_name": "旭酒造",
  "category": "junmai_daiginjo",
  "confidence": "high"
}
```'''

        result = parse_bedrock_response(text)

        assert result["sake_name"] == "獺祭"
        assert result["brewery_name"] == "旭酒造"
        assert result["confidence"] == "high"

    def test_parse_bedrock_response_plain_json(self):
        """Test parsing Bedrock response with plain JSON."""
        from backend.lambdas.image_recognition.handler import parse_bedrock_response

        text = '{"sake_name": "久保田", "brewery_name": "朝日酒造", "confidence": "medium"}'

        result = parse_bedrock_response(text)

        assert result["sake_name"] == "久保田"
        assert result["brewery_name"] == "朝日酒造"
        assert result["confidence"] == "medium"

    def test_parse_bedrock_response_no_json(self):
        """Test parsing Bedrock response without JSON."""
        from backend.lambdas.image_recognition.handler import parse_bedrock_response

        text = "This is not a JSON response"

        result = parse_bedrock_response(text)

        assert result["sake_name"] is None
        assert result["confidence"] == "low"
        assert "error" in result

    def test_analyze_sake_label(self, mock_bedrock, sample_image_base64):
        """Test sake label analysis function."""
        from backend.lambdas.image_recognition.handler import analyze_sake_label

        mock_bedrock.invoke_model.return_value = {
            "body": MagicMock(
                read=lambda: json.dumps({
                    "content": [
                        {
                            "text": json.dumps({
                                "sake_name": "八海山",
                                "brewery_name": "八海醸造",
                                "category": "junmai_ginjo",
                                "polishing_ratio": 50,
                                "confidence": "high",
                            })
                        }
                    ]
                }).encode()
            )
        }

        result = analyze_sake_label(sample_image_base64, "image/jpeg")

        assert result["sake_name"] == "八海山"
        assert result["brewery_name"] == "八海醸造"
        assert result["category"] == "junmai_ginjo"
        assert mock_bedrock.invoke_model.called

    def test_handler_bedrock_error(self, lambda_context, mock_bedrock, sample_image_base64):
        """Test handler when Bedrock returns error."""
        from backend.lambdas.image_recognition.handler import handler

        # Mock Bedrock error
        mock_bedrock.invoke_model.side_effect = Exception("Bedrock service error")

        event = {
            "body": json.dumps({
                "image_base64": sample_image_base64,
                "content_type": "image/jpeg",
            })
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 500
