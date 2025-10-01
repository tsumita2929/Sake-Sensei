"""
Sake Sensei - AgentCore Runtime Client

Client for invoking Sake Sensei Agent on Amazon Bedrock AgentCore Runtime.
"""

import json
import logging
from collections.abc import Generator
from typing import Any

import requests
from utils.config import config
from utils.session import SessionManager

logger = logging.getLogger(__name__)


class AgentCoreRuntimeClient:
    """Client for AgentCore Runtime API."""

    def __init__(self) -> None:
        """Initialize AgentCore Runtime client."""
        self.runtime_url = config.AGENTCORE_RUNTIME_URL
        self.agent_id = config.AGENTCORE_AGENT_ID
        self.timeout = 60  # Longer timeout for agent processing

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

    def invoke_agent_streaming(
        self,
        prompt: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any]]:
        """
        Invoke AgentCore Runtime with streaming response.

        Args:
            prompt: User prompt/message
            session_id: Optional session ID for conversation continuity
            context: Optional additional context

        Yields:
            Streaming response events from agent
        """
        if not self.runtime_url:
            yield {
                "type": "error",
                "error": "AgentCore Runtime URL not configured. Set AGENTCORE_RUNTIME_URL in .env",
            }
            return

        try:
            # Build request payload
            payload = {
                "prompt": prompt,
            }

            if session_id:
                payload["session_id"] = session_id

            if context:
                payload["context"] = context

            # Make streaming POST request
            logger.info(f"Invoking AgentCore Runtime: {self.runtime_url}")

            response = requests.post(
                f"{self.runtime_url}/invoke",
                json=payload,
                headers=self._get_headers(),
                stream=True,
                timeout=self.timeout,
            )

            if response.status_code != 200:
                error_msg = f"AgentCore Runtime error: {response.status_code} {response.text}"
                logger.error(error_msg)
                yield {"type": "error", "error": error_msg}
                return

            # Process streaming response (Server-Sent Events format)
            for line in response.iter_lines():
                if not line:
                    continue

                line_str = line.decode("utf-8")

                # Skip SSE comments
                if line_str.startswith(":"):
                    continue

                # Parse SSE data
                if line_str.startswith("data: "):
                    data_str = line_str[6:]  # Remove "data: " prefix

                    try:
                        event: dict[str, Any] = json.loads(data_str)
                        yield event

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse SSE data: {e}, data: {data_str}")
                        continue

        except requests.exceptions.Timeout:
            yield {"type": "error", "error": "Request timeout. Agent took too long to respond."}

        except requests.exceptions.RequestException as e:
            yield {"type": "error", "error": f"Network error: {str(e)}"}

        except Exception as e:
            logger.error(f"Unexpected error invoking agent: {e}", exc_info=True)
            yield {"type": "error", "error": f"Unexpected error: {str(e)}"}

    def invoke_agent_simple(
        self,
        prompt: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Invoke agent with simple non-streaming response.

        Args:
            prompt: User prompt/message
            session_id: Optional session ID
            context: Optional context

        Returns:
            Final agent response text
        """
        full_response = ""

        for event in self.invoke_agent_streaming(prompt, session_id, context):
            event_type = event.get("type", "")

            if event_type == "chunk":
                full_response += event.get("data", "")

            elif event_type == "complete":
                final = event.get("final_response", "")
                if final:
                    full_response = final

            elif event_type == "error":
                return f"エラー: {event.get('error', 'Unknown error')}"

        return full_response
