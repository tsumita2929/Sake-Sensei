"""
Sake Sensei - Bedrock Client

Direct Bedrock API client for AI-powered sake recommendations.
"""

from collections.abc import Generator
from typing import Any

import boto3
from utils.config import config


class BedrockClient:
    """Client for Amazon Bedrock streaming API."""

    def __init__(self):
        """Initialize Bedrock client."""
        self.client = boto3.client("bedrock-runtime", region_name=config.AWS_REGION)
        self.model_id = config.BEDROCK_MODEL_ID

    def _build_system_prompt(self) -> str:
        """Build system prompt for sake recommendations."""
        return """あなたは「Sake Sensei」という日本酒の専門家AIアシスタントです。

# あなたの役割
- 日本酒初心者から愛好家まで、幅広いユーザーに日本酒の魅力を伝える
- ユーザーの好みや状況に合わせて、最適な日本酒を提案する
- 日本酒の文化や歴史、製造方法についてわかりやすく説明する

# 対応できること
- 日本酒の銘柄や蔵元の情報提供
- ユーザーの好みに基づいた日本酒の推薦
- 料理とのペアリング提案
- 日本酒の飲み方や保存方法のアドバイス
- 日本酒の歴史や文化についての説明

# トーン
- 丁寧で親しみやすい
- 専門用語を使う場合は、必ず説明を加える
- ユーザーの質問に対して、具体的で実用的な情報を提供する

# 制約
- 根拠のない情報は提供しない
- わからないことは正直に「わかりません」と答える
- アルコールの過度な摂取を推奨しない
"""

    def _build_messages(
        self, prompt: str, chat_history: list[dict[str, str]] | None = None
    ) -> list[dict[str, Any]]:
        """Build messages array for Bedrock API."""
        messages = []

        # Add chat history if available
        if chat_history:
            for msg in chat_history:
                role = "assistant" if msg["role"] == "assistant" else "user"
                messages.append({"role": role, "content": [{"text": msg["content"]}]})

        # Add current user message (content must be a list)
        messages.append({"role": "user", "content": [{"text": prompt}]})

        return messages

    def invoke_streaming(
        self,
        prompt: str,
        chat_history: list[dict[str, str]] | None = None,
        user_context: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any]]:
        """
        Invoke Bedrock with streaming response.

        Args:
            prompt: User prompt/message
            chat_history: Previous conversation history
            user_context: Additional user context (preferences, etc.)

        Yields:
            Streaming response events
        """
        try:
            # Build request
            messages = self._build_messages(prompt, chat_history)
            system_prompt = self._build_system_prompt()

            # Add user context to system prompt if available
            if user_context:
                context_str = "\n\n# ユーザー情報\n"
                if user_context.get("preferences"):
                    prefs = user_context["preferences"]
                    context_str += f"- 好みの味わい: {prefs.get('taste', '未設定')}\n"
                    context_str += f"- 好みの香り: {prefs.get('aroma', '未設定')}\n"
                system_prompt += context_str

            # Invoke Bedrock with streaming
            # Note: Sonnet 4.5 only allows temperature OR topP, not both
            response = self.client.converse_stream(
                modelId=self.model_id,
                messages=messages,
                system=[{"text": system_prompt}],
                inferenceConfig={
                    "maxTokens": 2048,
                    "temperature": 0.7,
                },
            )

            # Process streaming response
            stream = response.get("stream")
            if stream:
                for event in stream:
                    if "contentBlockDelta" in event:
                        delta = event["contentBlockDelta"]["delta"]
                        if "text" in delta:
                            yield {"type": "chunk", "data": delta["text"]}

                    elif "messageStop" in event:
                        yield {"type": "complete", "final_response": ""}

                    elif "metadata" in event:
                        metadata = event["metadata"]
                        if "usage" in metadata:
                            yield {"type": "metadata", "usage": metadata["usage"]}

        except Exception as e:
            yield {"type": "error", "error": f"Bedrock API error: {str(e)}"}

    def invoke_simple(
        self,
        prompt: str,
        chat_history: list[dict[str, str]] | None = None,
        user_context: dict[str, Any] | None = None,
    ) -> str:
        """
        Invoke Bedrock with simple non-streaming response.

        Args:
            prompt: User prompt/message
            chat_history: Previous conversation history
            user_context: Additional user context

        Returns:
            Complete response text
        """
        full_response = ""

        for event in self.invoke_streaming(prompt, chat_history, user_context):
            if event.get("type") == "chunk":
                full_response += event.get("data", "")
            elif event.get("type") == "error":
                return f"エラー: {event.get('error', 'Unknown error')}"

        return full_response
