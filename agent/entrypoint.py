"""
Sake Sensei - AgentCore Runtime Entrypoint

Main entry point for the Sake Sensei agent running on Amazon Bedrock AgentCore Runtime.
"""

import logging
import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from dotenv import load_dotenv
from mcp.client.streamable_http import streamablehttp_client

# Import Strands Agents SDK
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

# Import system prompt
from agent.system_prompt import SAKE_SENSEI_SYSTEM_PROMPT

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Set logging level for specific libraries
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.INFO)
logging.getLogger("strands").setLevel(logging.INFO)

# Initialize the AgentCore Runtime App
app = BedrockAgentCoreApp()

# Configuration
GATEWAY_URL = os.getenv("AGENTCORE_GATEWAY_URL", os.getenv("MCP_SERVER_URL"))
GATEWAY_ID = os.getenv("AGENTCORE_GATEWAY_ID")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-sonnet-4-5-v2:0")

logger.info(f"Gateway URL: {GATEWAY_URL}")
logger.info(f"Gateway ID: {GATEWAY_ID}")
logger.info(f"Model ID: {MODEL_ID}")

# Configure conversation management
conversation_manager = SlidingWindowConversationManager(
    window_size=20,  # Keep last 20 messages for context
)

# Global agent and MCP client
agent = None
mcp_client = None


def get_auth_token():
    """
    Get authentication token for Gateway access.
    In AgentCore Runtime, tokens are typically provided via environment or context.
    """
    # Check if token is provided in environment
    token = os.getenv("BEARER_TOKEN") or os.getenv("GATEWAY_TOKEN")

    if token:
        logger.info("Using authentication token from environment")
        return token

    # In production AgentCore Runtime, identity is handled automatically
    # This is a placeholder for local testing
    logger.warning("No authentication token found. Gateway may require authentication.")
    return None


def initialize_agent():
    """Initialize the Strands Agent with MCP tools from Gateway."""
    global agent, mcp_client

    try:
        logger.info("Initializing Sake Sensei Agent...")

        # Get authentication token
        auth_token = get_auth_token()
        headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

        # Create MCP client connected to Gateway
        logger.info(f"Connecting to Gateway at {GATEWAY_URL}")
        try:
            mcp_client = MCPClient(
                lambda: streamablehttp_client(url=f"{GATEWAY_URL}/mcp", headers=headers)
            )

            # Enter context manager
            mcp_client.__enter__()

            # List available tools
            logger.info("Fetching tools from Gateway...")
            tools = mcp_client.list_tools_sync()
            logger.info(f"Loaded {len(tools)} tools from Gateway")

            # Log tool names
            if tools:
                tool_names = []
                for tool in tools:
                    if hasattr(tool, "schema") and hasattr(tool.schema, "name"):
                        tool_names.append(tool.schema.name)
                    elif hasattr(tool, "_name"):
                        tool_names.append(tool._name)
                logger.info(f"Available tools: {', '.join(tool_names)}")

        except Exception as e:
            logger.error(f"Error connecting to Gateway: {e}", exc_info=True)
            logger.warning("Agent will run without MCP tools")
            tools = []

        # Create Bedrock model
        logger.info(f"Initializing Bedrock model: {MODEL_ID}")
        model = BedrockModel(model_id=MODEL_ID)

        # Create Strands Agent
        agent = Agent(
            model=model,
            tools=tools,
            conversation_manager=conversation_manager,
            system_prompt=SAKE_SENSEI_SYSTEM_PROMPT,
        )

        logger.info("✅ Sake Sensei Agent initialized successfully!")
        return agent, mcp_client

    except Exception as e:
        logger.error(f"❌ Error initializing agent: {e}", exc_info=True)
        return None, None


# Initialize agent at module load
logger.info("Starting Sake Sensei Agent initialization...")
agent, mcp_client = initialize_agent()

if not agent:
    logger.error("❌ Failed to initialize agent. Application may not function correctly.")


@app.entrypoint
async def process_request(payload):
    """
    Main entrypoint for AgentCore Runtime requests.

    Args:
        payload: Request payload containing user prompt and context

    Yields:
        Streaming response chunks from the agent
    """
    global agent, mcp_client

    try:
        # Extract user message from payload
        user_message = payload.get("prompt", "")
        logger.info(f"Received request: {user_message[:100]}...")

        # Check if agent is initialized
        if not agent:
            logger.warning("Agent not initialized, attempting re-initialization...")
            agent, mcp_client = initialize_agent()

            if not agent:
                error_msg = "Agent initialization failed. Please check Gateway connectivity."
                logger.error(error_msg)
                yield {"error": error_msg}
                return

        # Process message with streaming
        logger.info("Processing message with Sake Sensei Agent...")
        try:
            # Stream response from agent
            stream = agent.stream_async(user_message)

            async for event in stream:
                logger.debug(f"Event: {event}")

                # Handle different event types
                if "data" in event:
                    # Text chunk from the model
                    chunk = event["data"]
                    yield {"type": "chunk", "data": chunk}

                elif "current_tool_use" in event:
                    # Tool invocation
                    tool_info = event["current_tool_use"]
                    yield {
                        "type": "tool_use",
                        "tool_name": tool_info.get("name", "unknown"),
                        "tool_input": tool_info.get("input", {}),
                        "tool_id": tool_info.get("toolUseId", ""),
                    }

                elif "reasoning" in event and event["reasoning"]:
                    # Model reasoning (Claude Extended Thinking)
                    yield {"type": "reasoning", "reasoning_text": event.get("reasoningText", "")}

                elif "result" in event:
                    # Final result
                    result = event["result"]
                    if hasattr(result, "message") and hasattr(result.message, "content"):
                        if (
                            isinstance(result.message.content, list)
                            and len(result.message.content) > 0
                        ):
                            final_response = result.message.content[0].get("text", "")
                        else:
                            final_response = str(result.message.content)
                    else:
                        final_response = str(result)

                    yield {"type": "complete", "final_response": final_response}

                else:
                    # Pass through other events
                    yield event

        except Exception as e:
            logger.error(f"Error during agent processing: {e}", exc_info=True)
            yield {"error": f"Error processing request: {str(e)}"}

    except Exception as e:
        logger.error(f"Error in entrypoint: {e}", exc_info=True)
        yield {"error": f"Request processing error: {str(e)}"}


if __name__ == "__main__":
    # Run the AgentCore Runtime App
    logger.info("🍶 Starting Sake Sensei Agent on AgentCore Runtime...")
    app.run()
