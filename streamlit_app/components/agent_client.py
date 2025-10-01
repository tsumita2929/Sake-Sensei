"""
Sake Sensei - AI Agent Client

Client for AI-powered sake recommendations using AgentCore Runtime.
"""

from collections.abc import Generator
from typing import Any

import streamlit as st
from components.agentcore_runtime_client import AgentCoreRuntimeClient
from components.bedrock_agent_client import BedrockAgentClient
from components.bedrock_client import BedrockClient
from utils.config import config
from utils.session import SessionManager


class AgentCoreClient:
    """Client for AI agent communication via AgentCore Runtime or Bedrock Agent."""

    def __init__(self) -> None:
        """Initialize AI client."""
        # Priority: AgentCore Runtime > Bedrock Agent > Bedrock Direct
        self.runtime_url = config.AGENTCORE_RUNTIME_URL
        self.agent_id = config.AGENTCORE_AGENT_ID
        self.use_runtime = bool(self.runtime_url)
        self.use_bedrock_agent = bool(self.agent_id) and not self.use_runtime

        if self.use_runtime:
            # Use AgentCore Runtime (preferred)
            self.runtime_client = AgentCoreRuntimeClient()
        elif self.use_bedrock_agent:
            # Use Bedrock Agent (fallback 1)
            self.bedrock_agent_client = BedrockAgentClient()
        else:
            # Use direct Bedrock (fallback 2 - legacy)
            self.bedrock_client = BedrockClient()

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
        try:
            # Priority: AgentCore Runtime > Bedrock Agent > Bedrock Direct
            if self.use_runtime:
                # Use AgentCore Runtime (preferred)
                user_context = context or {}

                # Add user preferences
                preferences = SessionManager.get_preferences()
                if preferences:
                    user_context["preferences"] = preferences

                # Add chat history
                chat_history = SessionManager.get_chat_history()
                if chat_history:
                    user_context["chat_history"] = chat_history

                # Invoke AgentCore Runtime
                yield from self.runtime_client.invoke_agent_streaming(
                    prompt=prompt, session_id=session_id, context=user_context
                )

            elif self.use_bedrock_agent:
                # Use Bedrock Agent (fallback 1)
                yield from self.bedrock_agent_client.invoke_agent_streaming(
                    prompt=prompt, session_id=session_id, context=context
                )

            else:
                # Use direct Bedrock (fallback 2 - legacy)
                chat_history = SessionManager.get_chat_history()

                user_context = {}
                preferences = SessionManager.get_preferences()
                if preferences:
                    user_context["preferences"] = preferences

                yield from self.bedrock_client.invoke_streaming(
                    prompt=prompt, chat_history=chat_history, user_context=user_context
                )

        except Exception as e:
            yield {"type": "error", "error": f"AI error: {str(e)}"}

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

    def __init__(self) -> None:
        """Initialize chat interface."""
        self.client = AgentCoreClient()

    def render(self) -> None:
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


def render_agent_chat() -> None:
    """Render agent chat interface (helper function)."""
    chat = AgentChat()
    chat.render()
