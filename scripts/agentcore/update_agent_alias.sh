#!/bin/bash

# Update Agent Alias to use DRAFT version with Memory

set -e

AGENT_ID="PPMCFA1HXB"
ALIAS_ID="7ET27D1YKD"
REGION="us-west-2"

echo "Updating Agent Alias to use DRAFT version with Memory..."
echo "Agent ID: $AGENT_ID"
echo "Alias ID: $ALIAS_ID"

# Create routing configuration JSON
cat > /tmp/routing-config.json <<'EOF'
[
  {
    "agentVersion": "DRAFT"
  }
]
EOF

# Update alias
aws bedrock-agent update-agent-alias \
  --agent-id "$AGENT_ID" \
  --agent-alias-id "$ALIAS_ID" \
  --agent-alias-name "production" \
  --routing-configuration file:///tmp/routing-config.json \
  --region "$REGION" \
  --output json

echo ""
echo "✅ Agent alias updated to use DRAFT version!"
echo ""
echo "Verifying alias configuration..."

aws bedrock-agent get-agent-alias \
  --agent-id "$AGENT_ID" \
  --agent-alias-id "$ALIAS_ID" \
  --region "$REGION" \
  --output json | jq '.agentAlias | {agentAliasId, agentAliasStatus, routingConfiguration}'

rm -f /tmp/routing-config.json

echo ""
echo "🎉 Agent deployment complete with Memory enabled!"
