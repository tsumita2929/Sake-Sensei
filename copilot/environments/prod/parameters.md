# Production Environment Parameters

This document lists all parameters that need to be configured for the production environment.

## AWS Systems Manager Parameter Store

Create these parameters in SSM Parameter Store before deploying to production:

### Authentication Parameters

```bash
# Cognito User Pool ID
aws ssm put-parameter \
  --name "/copilot/sakesensei/prod/secrets/COGNITO_USER_POOL_ID" \
  --type "String" \
  --value "us-west-2_XXXXXXXXX" \
  --region us-west-2

# Cognito Client ID
aws ssm put-parameter \
  --name "/copilot/sakesensei/prod/secrets/COGNITO_CLIENT_ID" \
  --type "String" \
  --value "XXXXXXXXXXXXXXXXXXXXXXXXXX" \
  --region us-west-2
```

### AWS Configuration

```bash
# AWS Region
aws ssm put-parameter \
  --name "/copilot/sakesensei/prod/secrets/AWS_REGION" \
  --type "String" \
  --value "us-west-2" \
  --region us-west-2
```

### AgentCore Configuration (Optional)

```bash
# AgentCore Runtime URL (if using AgentCore)
aws ssm put-parameter \
  --name "/copilot/sakesensei/prod/secrets/AGENTCORE_RUNTIME_URL" \
  --type "String" \
  --value "https://runtime.agentcore.amazonaws.com/..." \
  --region us-west-2

# AgentCore Gateway ID
aws ssm put-parameter \
  --name "/copilot/sakesensei/prod/secrets/AGENTCORE_GATEWAY_ID" \
  --type "String" \
  --value "gateway-xxxxx" \
  --region us-west-2
```

## AWS Secrets Manager

For sensitive API keys and credentials, use Secrets Manager:

### Third-Party API Keys

```bash
# Create secret for third-party services
aws secretsmanager create-secret \
  --name SakeSensei/Production/ThirdParty/APIKeys \
  --description "Third-party API keys for production" \
  --secret-string '{
    "openai_api_key": "",
    "other_service_key": ""
  }' \
  --region us-west-2
```

### Database Credentials (if using RDS)

```bash
# Create secret for database
aws secretsmanager create-secret \
  --name SakeSensei/Production/Database/Credentials \
  --description "Database credentials for production" \
  --secret-string '{
    "username": "admin",
    "password": "SECURE_PASSWORD_HERE",
    "host": "database.xxxxx.us-west-2.rds.amazonaws.com",
    "port": 5432,
    "database": "sakesensei"
  }' \
  --region us-west-2
```

## Environment Variables (Non-Sensitive)

These can be set directly in `copilot/streamlit-app/manifest.yml`:

```yaml
variables:
  LOG_LEVEL: INFO
  ENVIRONMENT: production
  FEATURE_FLAG_NEW_UI: "false"
```

## Verification

After setting parameters, verify they exist:

```bash
# List all production parameters
aws ssm get-parameters-by-path \
  --path "/copilot/sakesensei/prod/" \
  --recursive \
  --region us-west-2

# Get specific parameter (without decryption)
aws ssm get-parameter \
  --name "/copilot/sakesensei/prod/secrets/COGNITO_USER_POOL_ID" \
  --region us-west-2

# List secrets
aws secretsmanager list-secrets \
  --filters Key=name,Values=SakeSensei/Production \
  --region us-west-2
```

## Security Best Practices

1. **Use SecureString for sensitive data**
   ```bash
   --type "SecureString"
   ```

2. **Enable encryption with KMS**
   ```bash
   --key-id "alias/aws/ssm"
   ```

3. **Set appropriate IAM policies**
   - ECS task role should have minimal required permissions
   - Use condition keys to restrict access

4. **Enable secret rotation**
   - Configure automatic rotation for database credentials
   - Rotate API keys regularly

5. **Monitor access**
   - Enable CloudTrail logging for parameter access
   - Set up CloudWatch alarms for unauthorized access

## Migration from Development

To copy parameters from dev to prod:

```bash
# Get dev parameter value
DEV_VALUE=$(aws ssm get-parameter \
  --name "/copilot/sakesensei/dev/secrets/PARAMETER_NAME" \
  --query "Parameter.Value" \
  --output text \
  --region us-west-2)

# Set prod parameter
aws ssm put-parameter \
  --name "/copilot/sakesensei/prod/secrets/PARAMETER_NAME" \
  --type "String" \
  --value "$DEV_VALUE" \
  --region us-west-2
```

**⚠️ Warning:** Review and update values for production. Do not blindly copy dev values!
