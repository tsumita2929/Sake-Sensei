"""Local agent tests without AgentCore Runtime."""

import pytest


@pytest.mark.agent
class TestAgentLocal:
    """Test agent functionality locally without deploying to Runtime."""

    def test_system_prompt_exists(self) -> None:
        """Test system prompt is defined."""
        from agent.system_prompt import SAKE_SENSEI_SYSTEM_PROMPT

        assert SAKE_SENSEI_SYSTEM_PROMPT
        assert isinstance(SAKE_SENSEI_SYSTEM_PROMPT, str)
        assert len(SAKE_SENSEI_SYSTEM_PROMPT) > 100
        assert "sake" in SAKE_SENSEI_SYSTEM_PROMPT.lower() or "日本酒" in SAKE_SENSEI_SYSTEM_PROMPT

    def test_system_prompt_contains_tools(self) -> None:
        """Test system prompt mentions tools."""
        from agent.system_prompt import SAKE_SENSEI_SYSTEM_PROMPT

        # Should mention MCP tools or Lambda functions
        assert any(
            keyword in SAKE_SENSEI_SYSTEM_PROMPT.lower()
            for keyword in ["tool", "function", "recommendation", "mcp"]
        )

    def test_agent_entrypoint_file_exists(self) -> None:
        """Test agent entrypoint file exists."""
        import os

        entrypoint_path = os.path.join(os.path.dirname(__file__), "../../agent/entrypoint.py")
        assert os.path.exists(entrypoint_path)

        # Check it has required imports/components
        with open(entrypoint_path) as f:
            content = f.read()
            assert "BedrockAgentCoreApp" in content or "Agent" in content
            assert "SAKE_SENSEI_SYSTEM_PROMPT" in content

    def test_agent_requirements_file_exists(self) -> None:
        """Test agent requirements.txt exists."""
        import os

        requirements_path = os.path.join(os.path.dirname(__file__), "../../agent/requirements.txt")
        assert os.path.exists(requirements_path)

        with open(requirements_path) as f:
            content = f.read()
            assert len(content) > 0


@pytest.mark.agent
class TestAgentConfiguration:
    """Test agent configuration and setup."""

    def test_agent_has_system_prompt(self) -> None:
        """Test agent system prompt is comprehensive."""
        from agent.system_prompt import SAKE_SENSEI_SYSTEM_PROMPT

        # Check for key sections
        assert "sake sensei" in SAKE_SENSEI_SYSTEM_PROMPT.lower()
        assert "tool" in SAKE_SENSEI_SYSTEM_PROMPT.lower()
        assert "recommendation" in SAKE_SENSEI_SYSTEM_PROMPT.lower()

    def test_system_prompt_has_personality(self) -> None:
        """Test system prompt defines agent personality."""
        from agent.system_prompt import SAKE_SENSEI_SYSTEM_PROMPT

        # Should have personality traits
        assert any(
            trait in SAKE_SENSEI_SYSTEM_PROMPT.lower()
            for trait in ["knowledgeable", "friendly", "expert", "sensei"]
        )

    def test_system_prompt_lists_tools(self) -> None:
        """Test system prompt lists available tools."""
        from agent.system_prompt import SAKE_SENSEI_SYSTEM_PROMPT

        # Should mention the main tools
        tools = [
            "recommendation",
            "preference",
            "tasting",
            "brewery",
        ]
        for tool in tools:
            assert tool in SAKE_SENSEI_SYSTEM_PROMPT.lower()
