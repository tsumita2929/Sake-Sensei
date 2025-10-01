#!/bin/bash

# Sake Sensei - Agent Deployment Script
# Deploy agent to Amazon Bedrock AgentCore Runtime

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REGION="${AWS_REGION:-us-west-2}"
AGENT_DIR="agent"

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_info "Checking prerequisites..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found. Copy .env.example and configure it first."
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Verify required environment variables
if [ -z "$AGENTCORE_GATEWAY_URL" ]; then
    print_warn "AGENTCORE_GATEWAY_URL not set - agent will run without Gateway tools"
fi

if [ -z "$AWS_REGION" ]; then
    print_error "AWS_REGION not set in .env"
    exit 1
fi

print_info "✓ Prerequisites check passed"

# Navigate to agent directory
cd "$AGENT_DIR"

# Install dependencies
print_info "Installing agent dependencies..."
if ! uv sync --frozen; then
    print_error "Failed to install dependencies"
    exit 1
fi

print_info "✓ Dependencies installed"

# Run code quality checks
print_info "Running code quality checks..."

if ! uv run ruff format .; then
    print_error "Ruff format failed"
    exit 1
fi

if ! uv run ruff check .; then
    print_error "Ruff check failed - fix all warnings before deploying"
    exit 1
fi

print_info "✓ Code quality checks passed"

# Test agent locally (optional)
if [ "$1" == "--test-local" ]; then
    print_info "Testing agent locally..."

    # Create test script
    cat > test_agent.py <<EOF
import asyncio
from entrypoint import agent

async def test():
    if not agent:
        print("❌ Agent not initialized")
        return False

    print("✅ Agent initialized successfully")
    print(f"Tools available: {len(agent.tools) if hasattr(agent, 'tools') else 0}")
    return True

if __name__ == "__main__":
    result = asyncio.run(test())
    exit(0 if result else 1)
EOF

    if ! uv run python test_agent.py; then
        print_error "Local agent test failed"
        rm test_agent.py
        exit 1
    fi

    rm test_agent.py
    print_info "✓ Local agent test passed"
fi

# Configure AgentCore
print_info "Configuring AgentCore..."

if ! uv run agentcore configure --entrypoint entrypoint.py --yes; then
    print_warn "AgentCore configure failed - attempting manual configuration"

    # Create .agentcore.yaml manually
    cat > .agentcore.yaml <<EOF
version: "1.0"
entrypoint: entrypoint.py
runtime: python3.12
environment:
  AWS_REGION: $AWS_REGION
  AGENTCORE_GATEWAY_URL: $AGENTCORE_GATEWAY_URL
  AGENTCORE_GATEWAY_ID: $AGENTCORE_GATEWAY_ID
  BEDROCK_MODEL_ID: anthropic.claude-sonnet-4-5-v2:0
EOF

    print_info "✓ Manual configuration created"
fi

print_info "✓ AgentCore configured"

# Deploy to AgentCore Runtime
print_info "Deploying to AgentCore Runtime..."

if ! uv run agentcore launch --region $REGION; then
    print_error "AgentCore deployment failed"
    print_error "Please check:"
    print_error "  1. AWS credentials are configured"
    print_error "  2. AgentCore Runtime is set up in $REGION"
    print_error "  3. IAM permissions are correct"
    exit 1
fi

print_info "✓ Agent deployed successfully"

# Get deployment info
print_info "Retrieving deployment information..."

RUNTIME_URL=$(uv run agentcore describe --format json 2>/dev/null | jq -r '.runtime_url // empty')
AGENT_ID=$(uv run agentcore describe --format json 2>/dev/null | jq -r '.agent_id // empty')

if [ -n "$RUNTIME_URL" ]; then
    print_info "Runtime URL: $RUNTIME_URL"
    print_info "Agent ID: $AGENT_ID"

    # Update .env file
    cd ..
    if grep -q "^AGENTCORE_RUNTIME_URL=" .env; then
        sed -i "s|^AGENTCORE_RUNTIME_URL=.*|AGENTCORE_RUNTIME_URL=$RUNTIME_URL|" .env
    else
        echo "AGENTCORE_RUNTIME_URL=$RUNTIME_URL" >> .env
    fi

    if [ -n "$AGENT_ID" ] && grep -q "^AGENTCORE_AGENT_ID=" .env; then
        sed -i "s|^AGENTCORE_AGENT_ID=.*|AGENTCORE_AGENT_ID=$AGENT_ID|" .env
    elif [ -n "$AGENT_ID" ]; then
        echo "AGENTCORE_AGENT_ID=$AGENT_ID" >> .env
    fi

    print_info "✓ Updated .env file with Runtime URL"
else
    print_warn "Could not retrieve Runtime URL automatically"
    print_info "Please update .env file manually:"
    print_info "  AGENTCORE_RUNTIME_URL=<your-runtime-url>"
fi

# Summary
echo ""
print_info "======================================"
print_info "Agent Deployment Summary"
print_info "======================================"
print_info "Region: $REGION"
print_info "Runtime URL: ${RUNTIME_URL:-Not retrieved}"
print_info "Agent ID: ${AGENT_ID:-Not retrieved}"
print_info "======================================"
echo ""
print_info "Next steps:"
echo "  1. Test the agent: uv run agentcore invoke '{\"prompt\": \"こんにちは\"}'"
echo "  2. Update Streamlit .env with AGENTCORE_RUNTIME_URL"
echo "  3. Deploy Streamlit: ./scripts/deploy.sh"
echo ""
