#!/bin/bash
# Sake Sensei - Setup AWS Systems Manager Parameter Store

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="sakesensei"
ENV_NAME=${1:-dev}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Sake Sensei - SSM Parameter Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Environment:${NC} $ENV_NAME"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Load environment variables from .env
set -a
source .env
set +a

# Function to create or update parameter
put_parameter() {
    local name=$1
    local value=$2
    local type=${3:-String}

    if [ -z "$value" ]; then
        echo -e "  ${YELLOW}⚠ Skipping $name (value not set)${NC}"
        return
    fi

    aws ssm put-parameter \
        --name "/copilot/${APP_NAME}/${ENV_NAME}/secrets/$name" \
        --value "$value" \
        --type "$type" \
        --overwrite \
        --no-cli-pager \
        > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ $name${NC}"
    else
        echo -e "  ${RED}✗ Failed to set $name${NC}"
    fi
}

echo -e "${GREEN}Setting up SSM parameters...${NC}"
echo ""

# Cognito Parameters
echo -e "${YELLOW}Cognito Parameters:${NC}"
put_parameter "COGNITO_USER_POOL_ID" "$COGNITO_USER_POOL_ID" "String"
put_parameter "COGNITO_CLIENT_ID" "$COGNITO_CLIENT_ID" "String"
put_parameter "COGNITO_CLIENT_SECRET" "$COGNITO_CLIENT_SECRET" "SecureString"

echo ""

# AgentCore Parameters
echo -e "${YELLOW}AgentCore Parameters:${NC}"
put_parameter "AGENTCORE_RUNTIME_URL" "$AGENTCORE_RUNTIME_URL" "String"
put_parameter "AGENTCORE_GATEWAY_URL" "$AGENTCORE_GATEWAY_URL" "String"
put_parameter "AGENTCORE_GATEWAY_ID" "$AGENTCORE_GATEWAY_ID" "String"
put_parameter "AGENTCORE_AGENT_ID" "$AGENTCORE_AGENT_ID" "String"
put_parameter "AGENTCORE_MEMORY_ID" "$AGENTCORE_MEMORY_ID" "String"

echo ""

# Lambda ARNs
echo -e "${YELLOW}Lambda Function ARNs:${NC}"
put_parameter "LAMBDA_RECOMMENDATION_ARN" "$LAMBDA_RECOMMENDATION_ARN" "String"
put_parameter "LAMBDA_PREFERENCE_ARN" "$LAMBDA_PREFERENCE_ARN" "String"
put_parameter "LAMBDA_TASTING_ARN" "$LAMBDA_TASTING_ARN" "String"
put_parameter "LAMBDA_BREWERY_ARN" "$LAMBDA_BREWERY_ARN" "String"
put_parameter "LAMBDA_IMAGE_RECOGNITION_ARN" "$LAMBDA_IMAGE_RECOGNITION_ARN" "String"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SSM Parameters setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Parameters are stored at:"
echo -e "  ${YELLOW}/copilot/${APP_NAME}/${ENV_NAME}/secrets/*${NC}"
echo ""
echo -e "To verify, run:"
echo -e "  ${GREEN}aws ssm get-parameters-by-path --path /copilot/${APP_NAME}/${ENV_NAME}/secrets${NC}"
echo ""