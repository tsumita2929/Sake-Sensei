"""
Sake Sensei - Image Recognition Tool

MCP tool for recognizing sake labels from images using Bedrock Claude 4.5 Sonnet.
"""

import base64
import json
import logging
from typing import Any

import boto3
from mcp import Tool

logger = logging.getLogger(__name__)

# Bedrock model configuration
BEDROCK_MODEL_ID = "anthropic.claude-sonnet-4-5-v2:0"
MAX_TOKENS = 2000
TEMPERATURE = 0.3

SYSTEM_PROMPT = """あなたは日本酒ラベルの画像認識専門家です。

日本酒のラベル画像から以下の情報を抽出してください:

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


class ImageRecognitionTool(Tool):
    """MCP tool for sake label image recognition."""

    def __init__(self, aws_region: str = "us-west-2"):
        """
        Initialize image recognition tool.

        Args:
            aws_region: AWS region for Bedrock service
        """
        super().__init__(
            name="recognize_sake_label",
            description="Recognize sake information from a label image",
            input_schema={
                "type": "object",
                "properties": {
                    "image_base64": {
                        "type": "string",
                        "description": "Base64-encoded image data",
                    },
                    "media_type": {
                        "type": "string",
                        "description": "Image media type (image/jpeg, image/png, etc.)",
                        "default": "image/jpeg",
                    },
                },
                "required": ["image_base64"],
            },
        )
        self.bedrock_runtime = boto3.client("bedrock-runtime", region_name=aws_region)

    async def run(self, image_base64: str, media_type: str = "image/jpeg") -> dict[str, Any]:
        """
        Run image recognition on sake label.

        Args:
            image_base64: Base64-encoded image data
            media_type: Image media type

        Returns:
            Extracted sake information
        """
        logger.info("Running sake label recognition...")

        try:
            # Prepare Bedrock request with converse API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": media_type.split("/")[-1],  # jpeg or png
                                "source": {"bytes": base64.b64decode(image_base64)},
                            }
                        },
                        {
                            "text": "この日本酒のラベル画像を分析して、JSON形式で情報を抽出してください。"
                        },
                    ],
                }
            ]

            # Invoke Bedrock model using converse API
            logger.info(f"Invoking Bedrock model: {BEDROCK_MODEL_ID}")
            response = self.bedrock_runtime.converse(
                modelId=BEDROCK_MODEL_ID,
                messages=messages,
                system=[{"text": SYSTEM_PROMPT}],
                inferenceConfig={
                    "maxTokens": MAX_TOKENS,
                    "temperature": TEMPERATURE,
                },
            )

            # Parse response
            output_message = response.get("output", {}).get("message", {})
            content = output_message.get("content", [])

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
            text_content = ""
            for block in content:
                if "text" in block:
                    text_content += block["text"]

            logger.debug(f"Bedrock response: {text_content}")

            # Parse JSON from response
            result = self._parse_response(text_content)

            logger.info(
                f"Recognition completed: {result.get('sake_name')} "
                f"(confidence: {result.get('confidence')})"
            )

            return result

        except Exception as e:
            logger.error(f"Image recognition failed: {e}", exc_info=True)
            return {
                "sake_name": None,
                "brewery_name": None,
                "category": None,
                "confidence": "low",
                "error": str(e),
            }

    def _parse_response(self, text: str) -> dict[str, Any]:
        """
        Parse Bedrock response text to extract JSON.

        Args:
            text: Response text from Bedrock

        Returns:
            Parsed sake information
        """
        # Try to extract JSON from response
        try:
            # Look for JSON block (might be wrapped in markdown code blocks)
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                json_str = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                json_str = text[start:end].strip()
            elif "{" in text and "}" in text:
                start = text.find("{")
                end = text.rfind("}") + 1
                json_str = text[start:end]
            else:
                logger.warning(f"No JSON found in response: {text}")
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
            logger.error(f"Failed to parse JSON: {e}, text: {text}")
            return {
                "sake_name": None,
                "brewery_name": None,
                "category": None,
                "confidence": "low",
                "error": f"JSON parse error: {str(e)}",
            }


# Factory function for MCP server integration
def create_image_recognition_tool(aws_region: str = "us-west-2") -> ImageRecognitionTool:
    """
    Create image recognition tool instance.

    Args:
        aws_region: AWS region for Bedrock

    Returns:
        ImageRecognitionTool instance
    """
    return ImageRecognitionTool(aws_region=aws_region)
