"""
Sake Sensei - Image Recognition Lambda Handler

Recognizes sake labels using Amazon Bedrock Claude 4.5 Sonnet.
"""

import base64
import json
import os
from typing import Any

import boto3

from backend.lambdas.layer.error_handler import handle_errors
from backend.lambdas.layer.logger import get_logger
from backend.lambdas.layer.response import bad_request_response, success_response

logger = get_logger(__name__)

# Initialize AWS clients
s3_client = boto3.client("s3")
bedrock_runtime = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-west-2"))

# Bedrock model configuration
BEDROCK_MODEL_ID = "anthropic.claude-sonnet-4-5-v2:0"  # Claude 4.5 Sonnet
MAX_TOKENS = 2000
TEMPERATURE = 0.3  # Lower temperature for more consistent extraction


SYSTEM_PROMPT = """あなたは日本酒ラベルの画像認識専門家です。

日本酒のラベル画像から以下の情報を抽出してください：

1. **銘柄名** (sake_name): 日本酒の名前
2. **酒蔵名** (brewery_name): 製造している酒蔵の名前
3. **カテゴリー** (category): 純米大吟醸、大吟醸、純米吟醸、吟醸、純米酒、本醸造、普通酒など
4. **精米歩合** (polishing_ratio): もし記載があれば（例: 50%）
5. **アルコール度数** (alcohol_content): もし記載があれば（例: 15度）
6. **容量** (volume): もし記載があれば（例: 720ml、1800ml）
7. **都道府県** (prefecture): 製造地の都道府県
8. **信頼度** (confidence): 情報抽出の信頼度 (high/medium/low)

**出力形式**: 必ずJSON形式で返してください。情報が読み取れない場合は null を返してください。

例:
{
  "sake_name": "獺祭 純米大吟醸 磨き二割三分",
  "brewery_name": "旭酒造",
  "category": "junmai_daiginjo",
  "polishing_ratio": 23,
  "alcohol_content": 16.0,
  "volume": 720,
  "prefecture": "山口県",
  "confidence": "high"
}

**カテゴリーの分類**:
- junmai_daiginjo: 純米大吟醸
- daiginjo: 大吟醸
- junmai_ginjo: 純米吟醸
- ginjo: 吟醸
- junmai: 純米酒
- honjozo: 本醸造
- futsushu: 普通酒
- koshu: 古酒
- other: その他

画像を分析して、可能な限り正確に情報を抽出してください。"""


@handle_errors
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler for sake label image recognition.

    Expected input (POST /api/image-recognition):
    {
        "image_s3_key": "string",  // S3 key of uploaded image
        "bucket": "string"         // Optional, uses default if not provided
    }

    OR base64 encoded image:
    {
        "image_base64": "string",  // Base64 encoded image data
        "content_type": "string"   // image/jpeg or image/png
    }

    Returns:
        {
            "success": true,
            "data": {
                "sake_name": "string",
                "brewery_name": "string",
                "category": "string",
                "polishing_ratio": number,
                "alcohol_content": number,
                "volume": number,
                "prefecture": "string",
                "confidence": "high|medium|low"
            }
        }
    """
    # Parse request body
    body = (
        json.loads(event.get("body", "{}"))
        if isinstance(event.get("body"), str)
        else event.get("body", {})
    )

    # Get authenticated user for logging
    user_id = event.get("requestContext", {}).get("authorizer", {}).get("user_id", "anonymous")

    logger.info("Processing image recognition request", user_id=user_id)

    # Get image data
    image_base64 = None
    content_type = None

    if "image_base64" in body:
        # Direct base64 image
        image_base64 = body["image_base64"]
        content_type = body.get("content_type", "image/jpeg")
    elif "image_s3_key" in body:
        # Load image from S3
        s3_key = body["image_s3_key"]
        bucket = body.get("bucket", os.getenv("IMAGES_BUCKET", ""))

        if not bucket:
            return bad_request_response("S3 bucket not configured")

        try:
            logger.info("Loading image from S3", bucket=bucket, key=s3_key)
            response = s3_client.get_object(Bucket=bucket, Key=s3_key)
            image_bytes = response["Body"].read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            content_type = response["ContentType"]
        except Exception as e:
            logger.error("Failed to load image from S3", bucket=bucket, key=s3_key, error=str(e))
            return bad_request_response(f"Failed to load image: {str(e)}")
    else:
        return bad_request_response("Either image_base64 or image_s3_key is required")

    # Analyze image with Bedrock Claude 4.5 Sonnet
    try:
        result = analyze_sake_label(image_base64, content_type)

        logger.info(
            "Image recognition completed",
            user_id=user_id,
            sake_name=result.get("sake_name"),
            confidence=result.get("confidence"),
        )

        return success_response(result)

    except Exception as e:
        logger.error("Image recognition failed", user_id=user_id, error=str(e))
        raise


def analyze_sake_label(image_base64: str, content_type: str) -> dict[str, Any]:
    """Analyze sake label image using Bedrock Claude 4.5 Sonnet.

    Args:
        image_base64: Base64 encoded image data
        content_type: Image content type (image/jpeg or image/png)

    Returns:
        Extracted sake information
    """
    # Prepare Bedrock request
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": content_type,
                        "data": image_base64,
                    },
                },
                {
                    "type": "text",
                    "text": "この日本酒のラベル画像を分析して、JSON形式で情報を抽出してください。",
                },
            ],
        }
    ]

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "system": SYSTEM_PROMPT,
        "messages": messages,
    }

    logger.info("Invoking Bedrock Claude 4.5 Sonnet", model_id=BEDROCK_MODEL_ID)

    try:
        # Invoke Bedrock model
        response = bedrock_runtime.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(request_body),
        )

        # Parse response
        response_body = json.loads(response["body"].read())
        content = response_body.get("content", [])

        if not content:
            logger.warning("Empty response from Bedrock")
            return {
                "sake_name": None,
                "brewery_name": None,
                "category": None,
                "confidence": "low",
                "error": "No content in response",
            }

        # Extract text from response
        text_content = content[0].get("text", "")

        logger.debug("Bedrock response", text=text_content)

        # Parse JSON from response
        result = parse_bedrock_response(text_content)

        return result

    except Exception as e:
        logger.error("Bedrock invocation failed", error=str(e))
        raise


def parse_bedrock_response(text: str) -> dict[str, Any]:
    """Parse Bedrock response text to extract JSON.

    Args:
        text: Response text from Bedrock

    Returns:
        Parsed sake information
    """
    # Try to extract JSON from response
    try:
        # Look for JSON block (might be wrapped in markdown code blocks)
        if "```json" in text:
            # Extract JSON from code block
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_str = text[start:end].strip()
        elif "```" in text:
            # Extract from generic code block
            start = text.find("```") + 3
            end = text.find("```", start)
            json_str = text[start:end].strip()
        elif "{" in text and "}" in text:
            # Extract JSON directly
            start = text.find("{")
            end = text.rfind("}") + 1
            json_str = text[start:end]
        else:
            logger.warning("No JSON found in response", text=text)
            return {
                "sake_name": None,
                "brewery_name": None,
                "category": None,
                "confidence": "low",
                "error": "Could not parse response",
            }

        # Parse JSON
        result = json.loads(json_str)

        # Validate and set defaults
        return {
            "sake_name": result.get("sake_name"),
            "brewery_name": result.get("brewery_name"),
            "category": result.get("category"),
            "polishing_ratio": result.get("polishing_ratio"),
            "alcohol_content": result.get("alcohol_content"),
            "volume": result.get("volume"),
            "prefecture": result.get("prefecture"),
            "confidence": result.get("confidence", "medium"),
        }

    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from response", error=str(e), text=text)
        return {
            "sake_name": None,
            "brewery_name": None,
            "category": None,
            "confidence": "low",
            "error": f"JSON parse error: {str(e)}",
        }
