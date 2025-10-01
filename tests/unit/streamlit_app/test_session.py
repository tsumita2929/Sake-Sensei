"""
Sake Sensei - Session Management Tests

Tests for Streamlit session state management.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit session state."""
    with patch("streamlit_app.utils.session.st") as mock_st:
        mock_st.session_state = {}
        yield mock_st


class TestSessionInit:
    """Test session initialization."""

    def test_init_sets_defaults(self, mock_streamlit):
        """Test that init sets default values."""
        from streamlit_app.utils.session import SessionManager

        SessionManager.init()

        assert mock_streamlit.session_state[SessionManager.KEY_AUTHENTICATED] is False
        assert mock_streamlit.session_state[SessionManager.KEY_USER_ID] is None
        assert mock_streamlit.session_state[SessionManager.KEY_USER_EMAIL] is None
        assert mock_streamlit.session_state[SessionManager.KEY_USER_NAME] is None
        assert mock_streamlit.session_state[SessionManager.KEY_ACCESS_TOKEN] is None
        assert mock_streamlit.session_state[SessionManager.KEY_ID_TOKEN] is None
        assert mock_streamlit.session_state[SessionManager.KEY_REFRESH_TOKEN] is None
        assert mock_streamlit.session_state[SessionManager.KEY_USER_PREFERENCES] == {}
        assert mock_streamlit.session_state[SessionManager.KEY_CHAT_HISTORY] == []
        assert mock_streamlit.session_state[SessionManager.KEY_AGENT_SESSION_ID] is None

    def test_init_preserves_existing_values(self, mock_streamlit):
        """Test that init preserves existing session values."""
        from streamlit_app.utils.session import SessionManager

        mock_streamlit.session_state[SessionManager.KEY_USER_ID] = "existing-user"
        SessionManager.init()

        assert mock_streamlit.session_state[SessionManager.KEY_USER_ID] == "existing-user"


class TestSessionGetSet:
    """Test basic get/set operations."""

    def test_get_existing_value(self, mock_streamlit):
        """Test getting an existing value."""
        from streamlit_app.utils.session import SessionManager

        mock_streamlit.session_state["test_key"] = "test_value"
        result = SessionManager.get("test_key")

        assert result == "test_value"

    def test_get_nonexistent_value_with_default(self, mock_streamlit):
        """Test getting a non-existent value with default."""
        from streamlit_app.utils.session import SessionManager

        result = SessionManager.get("nonexistent", default="default_value")

        assert result == "default_value"

    def test_set_value(self, mock_streamlit):
        """Test setting a value."""
        from streamlit_app.utils.session import SessionManager

        SessionManager.set("test_key", "test_value")

        assert mock_streamlit.session_state["test_key"] == "test_value"


class TestAuthentication:
    """Test authentication-related methods."""

    def test_is_authenticated_false(self, mock_streamlit):
        """Test is_authenticated returns False by default."""
        from streamlit_app.utils.session import SessionManager

        SessionManager.init()
        assert SessionManager.is_authenticated() is False

    def test_is_authenticated_true(self, mock_streamlit):
        """Test is_authenticated returns True when authenticated."""
        from streamlit_app.utils.session import SessionManager

        mock_streamlit.session_state[SessionManager.KEY_AUTHENTICATED] = True
        assert SessionManager.is_authenticated() is True

    def test_login(self, mock_streamlit):
        """Test login sets all required fields."""
        from streamlit_app.utils.session import SessionManager

        SessionManager.login(
            user_id="test-user-id",
            email="test@example.com",
            name="Test User",
            access_token="access-token",
            id_token="id-token",
            refresh_token="refresh-token",
        )

        assert mock_streamlit.session_state[SessionManager.KEY_AUTHENTICATED] is True
        assert mock_streamlit.session_state[SessionManager.KEY_USER_ID] == "test-user-id"
        assert mock_streamlit.session_state[SessionManager.KEY_USER_EMAIL] == "test@example.com"
        assert mock_streamlit.session_state[SessionManager.KEY_USER_NAME] == "Test User"
        assert mock_streamlit.session_state[SessionManager.KEY_ACCESS_TOKEN] == "access-token"
        assert mock_streamlit.session_state[SessionManager.KEY_ID_TOKEN] == "id-token"
        assert mock_streamlit.session_state[SessionManager.KEY_REFRESH_TOKEN] == "refresh-token"

    def test_logout(self, mock_streamlit):
        """Test logout clears all fields."""
        from streamlit_app.utils.session import SessionManager

        # Set up authenticated state
        SessionManager.login(
            user_id="test-user-id",
            email="test@example.com",
            access_token="access-token",
        )
        mock_streamlit.session_state[SessionManager.KEY_CHAT_HISTORY] = [
            {"role": "user", "content": "test"}
        ]

        # Logout
        SessionManager.logout()

        assert mock_streamlit.session_state[SessionManager.KEY_AUTHENTICATED] is False
        assert mock_streamlit.session_state[SessionManager.KEY_USER_ID] is None
        assert mock_streamlit.session_state[SessionManager.KEY_USER_EMAIL] is None
        assert mock_streamlit.session_state[SessionManager.KEY_USER_NAME] is None
        assert mock_streamlit.session_state[SessionManager.KEY_ACCESS_TOKEN] is None
        assert mock_streamlit.session_state[SessionManager.KEY_ID_TOKEN] is None
        assert mock_streamlit.session_state[SessionManager.KEY_REFRESH_TOKEN] is None
        assert mock_streamlit.session_state[SessionManager.KEY_USER_PREFERENCES] == {}
        assert mock_streamlit.session_state[SessionManager.KEY_CHAT_HISTORY] == []
        assert mock_streamlit.session_state[SessionManager.KEY_AGENT_SESSION_ID] is None


class TestUserGetters:
    """Test user information getter methods."""

    def test_get_user_id(self, mock_streamlit):
        """Test getting user ID."""
        from streamlit_app.utils.session import SessionManager

        mock_streamlit.session_state[SessionManager.KEY_USER_ID] = "test-user-id"
        assert SessionManager.get_user_id() == "test-user-id"

    def test_get_user_email(self, mock_streamlit):
        """Test getting user email."""
        from streamlit_app.utils.session import SessionManager

        mock_streamlit.session_state[SessionManager.KEY_USER_EMAIL] = "test@example.com"
        assert SessionManager.get_user_email() == "test@example.com"

    def test_get_user_name(self, mock_streamlit):
        """Test getting user name."""
        from streamlit_app.utils.session import SessionManager

        mock_streamlit.session_state[SessionManager.KEY_USER_NAME] = "Test User"
        assert SessionManager.get_user_name() == "Test User"

    def test_get_access_token(self, mock_streamlit):
        """Test getting access token."""
        from streamlit_app.utils.session import SessionManager

        mock_streamlit.session_state[SessionManager.KEY_ACCESS_TOKEN] = "access-token"
        assert SessionManager.get_access_token() == "access-token"

    def test_get_id_token(self, mock_streamlit):
        """Test getting ID token."""
        from streamlit_app.utils.session import SessionManager

        mock_streamlit.session_state[SessionManager.KEY_ID_TOKEN] = "id-token"
        assert SessionManager.get_id_token() == "id-token"

    def test_get_user_info(self, mock_streamlit):
        """Test getting user info dictionary."""
        from streamlit_app.utils.session import SessionManager

        SessionManager.login(user_id="test-id", email="test@example.com", name="Test User")

        user_info = SessionManager.get_user_info()

        assert user_info["user_id"] == "test-id"
        assert user_info["email"] == "test@example.com"
        assert user_info["name"] == "Test User"


class TestPreferences:
    """Test user preferences management."""

    def test_set_preferences(self, mock_streamlit):
        """Test setting user preferences."""
        from streamlit_app.utils.session import SessionManager

        prefs = {"taste": "fruity", "aroma": "strong"}
        SessionManager.set_preferences(prefs)

        assert mock_streamlit.session_state[SessionManager.KEY_USER_PREFERENCES] == prefs

    def test_get_preferences(self, mock_streamlit):
        """Test getting user preferences."""
        from streamlit_app.utils.session import SessionManager

        prefs = {"taste": "fruity", "aroma": "strong"}
        mock_streamlit.session_state[SessionManager.KEY_USER_PREFERENCES] = prefs

        result = SessionManager.get_preferences()

        assert result == prefs

    def test_get_preferences_empty(self, mock_streamlit):
        """Test getting preferences when none are set."""
        from streamlit_app.utils.session import SessionManager

        result = SessionManager.get_preferences()

        assert result == {}


class TestChatHistory:
    """Test chat history management."""

    def test_add_chat_message(self, mock_streamlit):
        """Test adding a chat message."""
        from streamlit_app.utils.session import SessionManager

        mock_streamlit.session_state[SessionManager.KEY_CHAT_HISTORY] = []

        SessionManager.add_chat_message("user", "Hello")
        SessionManager.add_chat_message("assistant", "Hi there!")

        history = mock_streamlit.session_state[SessionManager.KEY_CHAT_HISTORY]
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hello"}
        assert history[1] == {"role": "assistant", "content": "Hi there!"}

    def test_add_chat_message_initializes_history(self, mock_streamlit):
        """Test adding a chat message initializes history if not present."""
        from streamlit_app.utils.session import SessionManager

        SessionManager.add_chat_message("user", "Hello")

        assert SessionManager.KEY_CHAT_HISTORY in mock_streamlit.session_state
        assert len(mock_streamlit.session_state[SessionManager.KEY_CHAT_HISTORY]) == 1

    def test_get_chat_history(self, mock_streamlit):
        """Test getting chat history."""
        from streamlit_app.utils.session import SessionManager

        history = [{"role": "user", "content": "Hello"}]
        mock_streamlit.session_state[SessionManager.KEY_CHAT_HISTORY] = history

        result = SessionManager.get_chat_history()

        assert result == history

    def test_get_chat_history_empty(self, mock_streamlit):
        """Test getting empty chat history."""
        from streamlit_app.utils.session import SessionManager

        result = SessionManager.get_chat_history()

        assert result == []

    def test_clear_chat_history(self, mock_streamlit):
        """Test clearing chat history."""
        from streamlit_app.utils.session import SessionManager

        mock_streamlit.session_state[SessionManager.KEY_CHAT_HISTORY] = [
            {"role": "user", "content": "Hello"}
        ]

        SessionManager.clear_chat_history()

        assert mock_streamlit.session_state[SessionManager.KEY_CHAT_HISTORY] == []


class TestAgentSession:
    """Test AgentCore session management."""

    def test_set_agent_session_id(self, mock_streamlit):
        """Test setting AgentCore session ID."""
        from streamlit_app.utils.session import SessionManager

        SessionManager.set_agent_session_id("test-session-id")

        assert mock_streamlit.session_state[SessionManager.KEY_AGENT_SESSION_ID] == "test-session-id"

    def test_get_agent_session_id(self, mock_streamlit):
        """Test getting AgentCore session ID."""
        from streamlit_app.utils.session import SessionManager

        mock_streamlit.session_state[SessionManager.KEY_AGENT_SESSION_ID] = "test-session-id"

        result = SessionManager.get_agent_session_id()

        assert result == "test-session-id"

    def test_get_agent_session_id_none(self, mock_streamlit):
        """Test getting AgentCore session ID when not set."""
        from streamlit_app.utils.session import SessionManager

        result = SessionManager.get_agent_session_id()

        assert result is None
