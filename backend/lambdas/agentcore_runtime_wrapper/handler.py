"""
AgentCore Runtime Wrapper for Bedrock Agent

Provides an AgentCore Runtime-compatible API wrapper around Amazon Bedrock Agent.
"""

import json
import logging
import os
from typing import Any

import boto3
from botocore.config import Config

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get configuration from environment
AGENT_ID = os.environ.get("BEDROCK_AGENT_ID", "PPMCFA1HXB")
AGENT_ALIAS_ID = os.environ.get("BEDROCK_AGENT_ALIAS_ID", "7ET27D1YKD")
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-west-2")

# Create Bedrock Agent Runtime client
bedrock_config = Config(
    region_name=AWS_REGION,
    signature_version="v4",
    retries={"max_attempts": 3, "mode": "adaptive"},
)
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", config=bedrock_config)

# Session storage (in-memory, use DynamoDB for production)
sessions = {}


def create_session(agent_id: str, agent_alias_id: str) -> str:
    """Create a new Bedrock Agent session."""
    try:
        response = bedrock_agent_runtime.create_session(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
        )
        session_id = response["sessionIdentifier"]
        sessions[session_id] = {
            "agentId": agent_id,
            "agentAliasId": agent_alias_id,
            "created_at": response.get("createdAt"),
        }
        logger.info(f"Created session: {session_id}")
        return session_id
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        raise


def invoke_agent(
    agent_id: str, agent_alias_id: str, session_id: str, input_text: str
) -> dict[str, Any]:
    """Invoke Bedrock Agent and return invocation ID."""
    try:
        response = bedrock_agent_runtime.create_invocation(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionIdentifier=session_id,
            inputText=input_text,
        )
        invocation_id = response["invocationIdentifier"]
        logger.info(f"Created invocation: {invocation_id}")
        return {"invocationId": invocation_id, "sessionId": session_id}
    except Exception as e:
        logger.error(f"Error invoking agent: {e}", exc_info=True)
        raise


def get_invocation_steps(invocation_id: str) -> list[dict[str, Any]]:
    """Get invocation steps (events) from Bedrock Agent."""
    try:
        response = bedrock_agent_runtime.list_invocation_steps(invocationIdentifier=invocation_id)
        steps = response.get("invocationSteps", [])
        logger.info(f"Retrieved {len(steps)} steps for invocation {invocation_id}")
        return steps
    except Exception as e:
        logger.error(f"Error getting invocation steps: {e}", exc_info=True)
        return []


def convert_steps_to_events(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Bedrock Agent steps to AgentCore Runtime-compatible events."""
    events = []

    for step in steps:
        step_type = step.get("stepType")

        if step_type == "ORCHESTRATION":
            # Agent reasoning/thinking
            observation = step.get("observation", {})
            thought = observation.get("thought", {})
            if thought_text := thought.get("text"):
                events.append({"type": "thinking", "content": thought_text})

        elif step_type == "TOOL_INVOCATION":
            # Tool use
            tool_invocation = step.get("toolInvocation", {})
            tool_name = tool_invocation.get("toolName", "unknown_tool")
            tool_input = tool_invocation.get("input", {})
            events.append({"type": "tool_use", "tool_name": tool_name, "tool_input": tool_input})

        elif step_type == "TOOL_RESULT":
            # Tool result
            tool_result = step.get("toolResult", {})
            result_content = tool_result.get("content", "")
            events.append({"type": "tool_result", "content": result_content})

        elif step_type == "RESPONSE":
            # Final response
            response_data = step.get("response", {})
            if response_text := response_data.get("text"):
                events.append({"type": "text", "content": response_text})

    # Add completion event
    events.append({"type": "complete"})

    return events


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler for AgentCore Runtime Wrapper."""
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Parse request
        if "body" in event:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        # Extract parameters
        prompt = body.get("prompt", "")
        session_id = body.get("session_id")
        _ = body.get("context", {})  # Context reserved for future use

        if not prompt:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing required parameter: prompt"}),
            }

        # Create session if not provided
        if not session_id:
            session_id = create_session(AGENT_ID, AGENT_ALIAS_ID)

        # Invoke agent
        invocation_result = invoke_agent(AGENT_ID, AGENT_ALIAS_ID, session_id, prompt)
        invocation_id = invocation_result["invocationId"]

        # Get invocation steps
        steps = get_invocation_steps(invocation_id)

        # Convert to events
        events = convert_steps_to_events(steps)

        # Return response
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "session_id": session_id,
                    "invocation_id": invocation_id,
                    "events": events,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Internal server error: {str(e)}"}),
        }
