"""
Sake Sensei - AgentCore Runtime Client

Client for communicating with Sake Sensei Strands Agent on AgentCore Runtime.
"""

import json
from collections.abc import Generator
from typing import Any

import requests
import streamlit as st
from utils.config import config
from utils.session import SessionManager


class AgentCoreClient:
    """Client for AgentCore Runtime communication."""

    def __init__(self):
        """Initialize AgentCore client."""
        self.runtime_url = config.AGENTCORE_RUNTIME_URL
        self.agent_id = config.AGENTCORE_AGENT_ID
        self.gateway_url = config.AGENTCORE_GATEWAY_URL

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

    def invoke_agent(
        self,
        prompt: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any]]:
        """
        Invoke agent with streaming response.

        Args:
            prompt: User prompt/message
            session_id: Optional session ID for conversation continuity
            context: Optional additional context

        Yields:
            Streaming response chunks
        """
        # Build request payload
        payload = {
            "prompt": prompt,
            "userId": SessionManager.get_user_id(),
        }

        if session_id:
            payload["sessionId"] = session_id

        if context:
            payload["context"] = context

        try:
            # Make streaming request to AgentCore Runtime
            response = requests.post(
                f"{self.runtime_url}/invoke",
                json=payload,
                headers=self._get_headers(),
                stream=True,
                timeout=60,
            )

            if response.status_code != 200:
                yield {
                    "type": "error",
                    "error": f"Agent invocation failed: {response.status_code} {response.text}",
                }
                return

            # Process streaming response
            for line in response.iter_lines():
                if line:
                    try:
                        # Parse JSON event
                        event = json.loads(line.decode("utf-8"))
                        yield event

                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue

        except requests.exceptions.Timeout:
            yield {"type": "error", "error": "Request timeout. Please try again."}

        except requests.exceptions.RequestException as e:
            yield {"type": "error", "error": f"Network error: {str(e)}"}

        except Exception as e:
            yield {"type": "error", "error": f"Unexpected error: {str(e)}"}

    def invoke_agent_simple(self, prompt: str, session_id: str | None = None) -> str:
        """
        Invoke agent with simple non-streaming response.

        Args:
            prompt: User prompt/message
            session_id: Optional session ID

        Returns:
            Final agent response text
        """
        full_response = ""

        for event in self.invoke_agent(prompt, session_id):
            event_type = event.get("type", "")

            if event_type == "chunk":
                full_response += event.get("data", "")

            elif event_type == "complete":
                final = event.get("final_response", "")
                if final:
                    full_response = final

            elif event_type == "error":
                full_response = f"エラー: {event.get('error', 'Unknown error')}"
                break

        return full_response


class AgentChat:
    """Chat interface component for agent interaction."""

    def __init__(self):
        """Initialize chat interface."""
        self.client = AgentCoreClient()

    def render(self):
        """Render chat interface."""
        st.markdown("### 💬 Sake Sensei に質問")

        # Display chat history
        chat_history = SessionManager.get_chat_history()

        if chat_history:
            st.markdown("#### 会話履歴")
            for message in chat_history:
                role = message["role"]
                content = message["content"]

                if role == "user":
                    st.markdown(f"**あなた**: {content}")
                else:
                    st.markdown(f"**Sake Sensei**: {content}")

            st.markdown("---")

        # Chat input
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "質問を入力してください",
                placeholder="例: 辛口の日本酒でおすすめはありますか？",
                height=100,
                key="chat_input",
            )

            col1, col2, col3 = st.columns([2, 1, 1])

            with col2:
                clear_button = st.form_submit_button("履歴クリア", use_container_width=True)

            with col3:
                submit_button = st.form_submit_button(
                    "送信", use_container_width=True, type="primary"
                )

            if clear_button:
                SessionManager.clear_chat_history()
                st.rerun()

            if submit_button and user_input:
                # Add user message to history
                SessionManager.add_chat_message("user", user_input)

                # Get session ID
                session_id = SessionManager.get_agent_session_id()
                if not session_id:
                    import uuid

                    session_id = str(uuid.uuid4())
                    SessionManager.set_agent_session_id(session_id)

                # Show spinner while processing
                with st.spinner("Sake Sensei が考え中..."):
                    try:
                        # Invoke agent with streaming
                        response_placeholder = st.empty()
                        full_response = ""

                        for event in self.client.invoke_agent(user_input, session_id):
                            event_type = event.get("type", "")

                            if event_type == "chunk":
                                chunk = event.get("data", "")
                                full_response += chunk
                                response_placeholder.markdown(f"**Sake Sensei**: {full_response}")

                            elif event_type == "tool_use":
                                tool_name = event.get("tool_name", "unknown")
                                st.info(f"🔧 ツール使用中: {tool_name}")

                            elif event_type == "complete":
                                final = event.get("final_response", "")
                                if final:
                                    full_response = final
                                    response_placeholder.markdown(
                                        f"**Sake Sensei**: {full_response}"
                                    )

                            elif event_type == "error":
                                error_msg = event.get("error", "Unknown error")
                                st.error(f"❌ エラー: {error_msg}")
                                full_response = f"エラーが発生しました: {error_msg}"

                        # Add agent response to history
                        if full_response:
                            SessionManager.add_chat_message("assistant", full_response)

                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ エラーが発生しました: {str(e)}")


def render_agent_chat():
    """Render agent chat interface (helper function)."""
    chat = AgentChat()
    chat.render()
