"""
Sake Sensei - Bedrock Agent Client

Client for invoking Amazon Bedrock Agents directly.
"""

from collections.abc import Generator
from typing import Any

import boto3
from botocore.config import Config
from utils.config import config


class BedrockAgentClient:
    """Client for invoking Amazon Bedrock Agents."""

    def __init__(self) -> None:
        """Initialize Bedrock Agent Runtime client."""
        self.agent_id = config.AGENTCORE_AGENT_ID
        self.agent_alias_id = config.AGENTCORE_AGENT_ALIAS_ID
        self.region = config.AWS_REGION

        # Create Bedrock Agent Runtime client
        bedrock_config = Config(
            region_name=self.region,
            signature_version="v4",
            retries={"max_attempts": 3, "mode": "adaptive"},
        )
        self.client = boto3.client("bedrock-agent-runtime", config=bedrock_config)

        # Session cache
        self.session_id: str | None = None

    def _ensure_session(self) -> str:
        """Ensure a session exists and return session ID."""
        if not self.session_id:
            response = self.client.create_session(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
            )
            self.session_id = response["sessionIdentifier"]
        return self.session_id

    def invoke_agent_streaming(
        self,
        prompt: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any]]:
        """
        Invoke Bedrock Agent with streaming response.

        Args:
            prompt: User input text
            session_id: Optional session ID (will create if not provided)
            context: Additional context (not used in current Bedrock Agent API)

        Yields:
            Streaming response events
        """
        # Mark context as unused (required for API compatibility)
        _ = context

        # Use provided session or create/reuse existing
        if session_id:
            self.session_id = session_id
        else:
            session_id = self._ensure_session()

        try:
            # Create invocation
            response = self.client.create_invocation(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionIdentifier=session_id,
                inputText=prompt,
            )

            # Stream response events
            invocation_id = response["invocationIdentifier"]

            # Poll for events (Bedrock Agent uses event stream)
            yield from self._stream_invocation_events(invocation_id)

        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "message": f"Bedrock Agent invocation error: {str(e)}",
            }

    def _stream_invocation_events(self, invocation_id: str) -> Generator[dict[str, Any]]:
        """
        Stream invocation events using list-invocation-steps.

        Args:
            invocation_id: Invocation identifier

        Yields:
            Event dictionaries
        """
        try:
            # Get invocation steps
            response = self.client.list_invocation_steps(invocationIdentifier=invocation_id)

            # Process steps
            for step in response.get("invocationSteps", []):
                # Extract text from step
                step_type = step.get("stepType")

                if step_type == "ORCHESTRATION":
                    # Agent reasoning step
                    observation = step.get("observation", {})
                    thought = observation.get("thought", {})
                    if thought_text := thought.get("text"):
                        yield {
                            "type": "thinking",
                            "content": thought_text,
                        }

                elif step_type == "TOOL_INVOCATION":
                    # Tool execution step
                    tool_invocation = step.get("toolInvocation", {})
                    tool_name = tool_invocation.get("toolName", "unknown_tool")
                    yield {
                        "type": "tool_use",
                        "tool_name": tool_name,
                        "content": f"Using tool: {tool_name}",
                    }

                elif step_type == "RESPONSE":
                    # Final response step
                    response_data = step.get("response", {})
                    if response_text := response_data.get("text"):
                        yield {
                            "type": "text",
                            "content": response_text,
                        }

            # Mark completion
            yield {"type": "complete"}

        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "message": f"Error streaming invocation events: {str(e)}",
            }

    def reset_session(self) -> None:
        """Reset the current session."""
        self.session_id = None
