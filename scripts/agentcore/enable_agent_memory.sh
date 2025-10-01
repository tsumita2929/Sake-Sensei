#!/bin/bash

# Enable Bedrock Agent Memory Configuration

set -e

AGENT_ID="PPMCFA1HXB"
REGION="us-west-2"

echo "Enabling Memory Configuration for Bedrock Agent..."
echo "Agent ID: $AGENT_ID"
echo "Region: $REGION"

# Create memory configuration JSON
cat > /tmp/memory-config.json <<'EOF'
{
  "enabledMemoryTypes": ["SESSION_SUMMARY"],
  "sessionSummaryConfiguration": {
    "maxRecentSessions": 5
  },
  "storageDays": 30
}
EOF

# Update agent with memory configuration
aws bedrock-agent update-agent \
  --agent-id "$AGENT_ID" \
  --agent-name "SakeSensei" \
  --foundation-model "us.anthropic.claude-sonnet-4-5-20250929-v1:0" \
  --instruction "You are Sake Sensei (酒先生), an expert AI assistant specializing in Japanese sake recommendations and education." \
  --agent-resource-role-arn "arn:aws:iam::047786098634:role/service-role/AmazonBedrockExecutionRoleForAgents_34E4TZZHFA4" \
  --memory-configuration file:///tmp/memory-config.json \
  --region "$REGION" \
  --output json

echo ""
echo "✅ Memory configuration enabled!"
echo ""
echo "Memory Settings:"
echo "  - Type: SESSION_SUMMARY"
echo "  - Max Recent Sessions: 5"
echo "  - Storage Days: 30"
echo ""
echo "Preparing agent..."

# Prepare agent
aws bedrock-agent prepare-agent \
  --agent-id "$AGENT_ID" \
  --region "$REGION" \
  --output json

echo "✅ Agent prepared with memory configuration!"

# Verify memory configuration
echo ""
echo "Verifying memory configuration..."
aws bedrock-agent get-agent \
  --agent-id "$AGENT_ID" \
  --region "$REGION" \
  --output json | jq '.agent.memoryConfiguration'

rm -f /tmp/memory-config.json

echo ""
echo "🎉 Bedrock Agent Memory setup complete!"
