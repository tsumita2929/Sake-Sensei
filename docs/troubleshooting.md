# Sake Sensei Troubleshooting Guide

This guide helps diagnose and resolve common issues in Sake Sensei deployment and operation.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Authentication Issues](#authentication-issues)
3. [Lambda Function Errors](#lambda-function-errors)
4. [Agent Issues](#agent-issues)
5. [Frontend (Streamlit) Issues](#frontend-streamlit-issues)
6. [Database Issues](#database-issues)
7. [Deployment Issues](#deployment-issues)
8. [Performance Issues](#performance-issues)
9. [Security Issues](#security-issues)
10. [Network & Connectivity](#network--connectivity)
11. [Monitoring & Logging](#monitoring--logging)
12. [Error Code Reference](#error-code-reference)

---

## Quick Diagnostics

### Health Check Commands

```bash
# Check ECS service status
copilot svc status --name streamlit-app --env prod

# Check Lambda function status
aws lambda get-function --function-name SakeSensei-Recommendation

# Check DynamoDB table status
aws dynamodb describe-table --table-name SakeSensei-Users

# Check recent errors in logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/SakeSensei-Recommendation \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR"

# Check CloudWatch alarms
aws cloudwatch describe-alarms \
  --state-value ALARM \
  --query 'MetricAlarms[*].[AlarmName,StateReason]' \
  --output table
```

### Service Map

```
User → ALB → ECS (Streamlit) → AgentCore Runtime → Agent
                              → Lambda Functions → DynamoDB
                              → Cognito (Auth)
                              → S3 (Images)
```

---

## Authentication Issues

### Issue: Users Cannot Sign Up

**Symptoms:**
- "User already exists" error for new users
- "Invalid verification code" error
- Email verification not arriving

**Diagnosis:**

```bash
# Check Cognito User Pool configuration
aws cognito-idp describe-user-pool \
  --user-pool-id us-west-2_XXXXXXXXX

# Check user status
aws cognito-idp admin-get-user \
  --user-pool-id us-west-2_XXXXXXXXX \
  --username user@example.com
```

**Solutions:**

1. **User already exists:**
   ```bash
   # Delete existing user (if appropriate)
   aws cognito-idp admin-delete-user \
     --user-pool-id us-west-2_XXXXXXXXX \
     --username user@example.com
   ```

2. **Email not arriving:**
   - Check SES sending limits (sandbox mode allows only verified emails)
   - Verify SES is out of sandbox:
     ```bash
     aws sesv2 get-account
     ```
   - Check spam folder
   - Verify email configuration in Cognito User Pool

3. **Invalid verification code:**
   - Code expires after 24 hours
   - Resend code:
     ```bash
     aws cognito-idp resend-confirmation-code \
       --client-id XXXXXXXXXXXXXXXXXXXXXXXXXX \
       --username user@example.com
     ```

### Issue: Users Cannot Sign In

**Symptoms:**
- "Incorrect username or password"
- "User is not confirmed"
- "User does not exist"

**Diagnosis:**

```bash
# Check user status
aws cognito-idp admin-get-user \
  --user-pool-id us-west-2_XXXXXXXXX \
  --username user@example.com \
  --query 'UserStatus'
```

**Solutions:**

1. **User not confirmed:**
   ```bash
   # Force confirm user (admin action)
   aws cognito-idp admin-confirm-sign-up \
     --user-pool-id us-west-2_XXXXXXXXX \
     --username user@example.com
   ```

2. **User locked out:**
   ```bash
   # Reset password and unlock
   aws cognito-idp admin-reset-user-password \
     --user-pool-id us-west-2_XXXXXXXXX \
     --username user@example.com
   ```

3. **Check CloudWatch logs for auth failures:**
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/cognito/userpools/us-west-2_XXXXXXXXX \
     --start-time $(date -u -d '1 hour ago' +%s)000 \
     --filter-pattern "failed"
   ```

### Issue: JWT Token Validation Fails

**Symptoms:**
- "Invalid token" errors
- "Token expired" errors
- 401 Unauthorized responses

**Diagnosis:**

```python
# Decode JWT to check expiration
import jwt
import json

token = "eyJraWQiOiI..."
decoded = jwt.decode(token, options={"verify_signature": False})
print(json.dumps(decoded, indent=2))
```

**Solutions:**

1. **Token expired:**
   - Tokens expire after 1 hour by default
   - Implement token refresh logic in frontend
   - Check token refresh interval in Cognito

2. **Clock skew:**
   - Ensure server time is synchronized (NTP)
   - Allow 5-minute clock skew tolerance

3. **Invalid audience:**
   - Verify `aud` claim matches Cognito Client ID
   - Check token is from correct User Pool

---

## Lambda Function Errors

### Issue: Lambda Function Timeout

**Symptoms:**
- "Task timed out after X seconds"
- Partial responses
- 504 Gateway Timeout errors

**Diagnosis:**

```bash
# Check Lambda duration metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=SakeSensei-Recommendation \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Average,Maximum

# Check X-Ray trace for slow operations
aws xray get-trace-summaries \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --filter-expression 'duration > 3'
```

**Solutions:**

1. **Increase timeout:**
   ```bash
   aws lambda update-function-configuration \
     --function-name SakeSensei-Recommendation \
     --timeout 30  # Increase to 30 seconds
   ```

2. **Optimize cold start:**
   - Increase memory allocation (more CPU):
     ```bash
     aws lambda update-function-configuration \
       --function-name SakeSensei-ImageRecognition \
       --memory-size 2048
     ```
   - Enable provisioned concurrency:
     ```bash
     aws lambda put-provisioned-concurrency-config \
       --function-name SakeSensei-Recommendation \
       --provisioned-concurrent-executions 2 \
       --qualifier $LATEST
     ```

3. **Optimize code:**
   - Import only necessary modules
   - Move initialization outside handler
   - Use connection pooling for DynamoDB
   - Cache frequently accessed data

### Issue: Lambda Function Throttling

**Symptoms:**
- "Rate exceeded" errors
- 429 Too Many Requests
- Intermittent failures during high traffic

**Diagnosis:**

```bash
# Check throttle metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Throttles \
  --dimensions Name=FunctionName,Value=SakeSensei-Recommendation \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Sum

# Check current concurrency
aws lambda get-function-concurrency \
  --function-name SakeSensei-Recommendation
```

**Solutions:**

1. **Increase reserved concurrency:**
   ```bash
   aws lambda put-function-concurrency \
     --function-name SakeSensei-Recommendation \
     --reserved-concurrent-executions 50
   ```

2. **Request service quota increase:**
   - Navigate to Service Quotas console
   - Request increase for "Concurrent executions" in Lambda
   - Default is 1000 per region

3. **Implement exponential backoff:**
   ```python
   import time
   from botocore.exceptions import ClientError

   def invoke_with_retry(lambda_client, function_name, payload, max_retries=3):
       for attempt in range(max_retries):
           try:
               response = lambda_client.invoke(
                   FunctionName=function_name,
                   Payload=payload
               )
               return response
           except ClientError as e:
               if e.response['Error']['Code'] == 'TooManyRequestsException':
                   if attempt < max_retries - 1:
                       time.sleep(2 ** attempt)  # Exponential backoff
                       continue
               raise
   ```

### Issue: Lambda Function Returning Errors

**Symptoms:**
- 500 Internal Server Error
- "An error occurred" messages
- Empty or malformed responses

**Diagnosis:**

```bash
# Check recent errors
aws logs tail /aws/lambda/SakeSensei-Recommendation --follow --filter-pattern "ERROR"

# Get specific invocation logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/SakeSensei-Recommendation \
  --start-time $(date -u -d '5 minutes ago' +%s)000 \
  --filter-pattern "RequestId: <request-id-from-error>"
```

**Solutions:**

1. **Check dependencies:**
   - Ensure all required packages are in Lambda layer or deployment package
   - Verify package versions match `requirements.txt`

2. **Check environment variables:**
   ```bash
   aws lambda get-function-configuration \
     --function-name SakeSensei-Recommendation \
     --query 'Environment.Variables'
   ```

3. **Test locally:**
   ```bash
   cd backend/lambdas/recommendation
   uv run python -c "from handler import handler; print(handler({'user_id': 'test'}, {}))"
   ```

4. **Check IAM permissions:**
   ```bash
   # Get function role
   ROLE_ARN=$(aws lambda get-function-configuration \
     --function-name SakeSensei-Recommendation \
     --query 'Role' --output text)

   # Check role policies
   aws iam list-attached-role-policies \
     --role-name $(echo $ROLE_ARN | cut -d'/' -f2)
   ```

---

## Agent Issues

### Issue: Agent Not Responding

**Symptoms:**
- Agent conversation hangs
- No response from agent
- Timeout errors in Streamlit

**Diagnosis:**

```bash
# Check agent logs
aws logs tail /agentcore/sakesensei/agent --follow

# Check AgentCore Runtime status
# (via AWS Console → Bedrock → AgentCore → Runtime)

# Test agent directly
cd agent
uv run agentcore invoke '{"prompt": "Hello, recommend me a sake"}'
```

**Solutions:**

1. **Verify AgentCore Runtime is deployed:**
   ```bash
   uv run agentcore status
   ```

2. **Check agent configuration:**
   ```bash
   cat .agentcore.yaml
   ```

3. **Redeploy agent:**
   ```bash
   cd agent
   uv run agentcore configure --entrypoint entrypoint.py
   uv run agentcore launch --environment production
   ```

4. **Check Gateway targets:**
   ```bash
   cd scripts
   python add_gateway_targets.py --list
   ```

### Issue: Agent Providing Incorrect Recommendations

**Symptoms:**
- Recommendations don't match user preferences
- Agent ignoring tasting history
- Generic or irrelevant responses

**Diagnosis:**

1. **Check user preferences in DynamoDB:**
   ```bash
   aws dynamodb get-item \
     --table-name SakeSensei-Users \
     --key '{"user_id": {"S": "user-123"}}'
   ```

2. **Check tasting history:**
   ```bash
   aws dynamodb query \
     --table-name SakeSensei-TastingRecords \
     --key-condition-expression "user_id = :uid" \
     --expression-attribute-values '{":uid": {"S": "user-123"}}'
   ```

3. **Review agent system prompt:**
   ```bash
   cat agent/system_prompt.py
   ```

**Solutions:**

1. **Update system prompt:**
   - Edit `agent/system_prompt.py`
   - Add more specific instructions
   - Include examples of good recommendations

2. **Improve memory integration:**
   - Verify Memory store is configured:
     ```bash
     cd scripts
     python create_memory.py --status
     ```
   - Check memory hooks in `agent/memory_hook.py`

3. **Test recommendation Lambda directly:**
   ```bash
   aws lambda invoke \
     --function-name SakeSensei-Recommendation \
     --payload '{"user_id": "user-123", "preferences": {...}}' \
     output.json
   cat output.json
   ```

### Issue: Gateway Tool Invocation Failing

**Symptoms:**
- "Tool not found" errors
- "Gateway unreachable" errors
- Agent can't access Lambda functions

**Diagnosis:**

```bash
# List Gateway targets
cd scripts
python add_gateway_targets.py --list

# Test Gateway connectivity
aws bedrock-agent-runtime invoke-gateway \
  --gateway-id gateway-xxxxx \
  --tool-name get_recommendations \
  --input '{"user_id": "test"}'
```

**Solutions:**

1. **Re-add Lambda targets to Gateway:**
   ```bash
   cd scripts
   python add_gateway_targets.py
   ```

2. **Check Lambda permissions for Gateway:**
   - Verify Lambda resource policy allows Gateway invocation
   - Check IAM role attached to Gateway

3. **Verify Gateway ID in agent configuration:**
   ```bash
   grep gateway .agentcore.yaml
   ```

---

## Frontend (Streamlit) Issues

### Issue: Streamlit App Not Loading

**Symptoms:**
- 502 Bad Gateway
- 503 Service Unavailable
- Connection refused errors

**Diagnosis:**

```bash
# Check ECS service status
copilot svc status --name streamlit-app --env prod

# Check ECS task logs
copilot svc logs --name streamlit-app --env prod --follow

# Check ALB target health
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn>

# Check running tasks
aws ecs list-tasks \
  --cluster sakesensei-prod \
  --service-name streamlit-app
```

**Solutions:**

1. **Service not running:**
   ```bash
   # Restart service
   copilot svc deploy --name streamlit-app --env prod
   ```

2. **Health check failing:**
   - Check health check endpoint is accessible:
     ```bash
     # SSH into ECS task or check logs
     curl http://localhost:8501/_stcore/health
     ```
   - Adjust health check parameters in `copilot/streamlit-app/manifest.yml`:
     ```yaml
     http:
       healthcheck:
         path: /_stcore/health
         healthy_threshold: 3
         unhealthy_threshold: 3
         interval: 30s
         timeout: 10s
     ```

3. **Insufficient resources:**
   - Check CPU/Memory utilization:
     ```bash
     aws ecs describe-services \
       --cluster sakesensei-prod \
       --services streamlit-app \
       --query 'services[0].deployments[0].desiredCount'
     ```
   - Scale up:
     ```bash
     # Edit manifest.yml
     count:
       range:
         min: 2
         max: 10

     # Redeploy
     copilot svc deploy --name streamlit-app --env prod
     ```

### Issue: Streamlit App Slow Performance

**Symptoms:**
- Pages take long to load
- Slow response to user interactions
- High latency

**Diagnosis:**

```bash
# Check ECS CPU/Memory metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=streamlit-app \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Average,Maximum

# Check ALB response time
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Average,Maximum
```

**Solutions:**

1. **Optimize Streamlit caching:**
   ```python
   import streamlit as st

   @st.cache_data(ttl=3600)  # Cache for 1 hour
   def load_sake_data():
       # Expensive operation
       return data

   @st.cache_resource
   def get_lambda_client():
       # Reuse Lambda client
       return boto3.client('lambda')
   ```

2. **Increase ECS task size:**
   ```yaml
   # In copilot/streamlit-app/manifest.yml
   cpu: 1024      # 1 vCPU (from 512)
   memory: 2048   # 2 GB (from 1024)
   ```

3. **Enable autoscaling:**
   ```yaml
   count:
     range:
       min: 2
       max: 10
     cpu_percentage: 70
     memory_percentage: 80
   ```

4. **Use CloudFront CDN** for static assets:
   - Create CloudFront distribution pointing to ALB
   - Cache images and static files at edge locations

### Issue: Session State Issues

**Symptoms:**
- User logged out unexpectedly
- Data not persisting across page refreshes
- Session variables resetting

**Diagnosis:**

```python
# Add debugging to Streamlit app
import streamlit as st

st.write("Session State:", st.session_state)
st.write("Session ID:", st.runtime.scriptrunner.get_script_run_ctx().session_id)
```

**Solutions:**

1. **Use st.session_state correctly:**
   ```python
   # Initialize session state
   if 'user_id' not in st.session_state:
       st.session_state.user_id = None

   # Access and modify
   st.session_state.user_id = "user-123"
   ```

2. **Persist auth token:**
   ```python
   # Store JWT in session state
   if 'access_token' not in st.session_state:
       st.session_state.access_token = None

   # Check token expiration
   import jwt

   def is_token_valid(token):
       try:
           jwt.decode(token, options={"verify_signature": False})
           return True
       except jwt.ExpiredSignatureError:
           return False
   ```

3. **Handle session expiration gracefully:**
   ```python
   if st.session_state.access_token and not is_token_valid(st.session_state.access_token):
       st.session_state.access_token = None
       st.warning("Your session has expired. Please sign in again.")
       st.stop()
   ```

---

## Database Issues

### Issue: DynamoDB Throttling

**Symptoms:**
- "ProvisionedThroughputExceededException"
- Read/write operations failing
- Slow database responses

**Diagnosis:**

```bash
# Check consumed capacity
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=SakeSensei-Users \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Sum,Average

# Check throttled requests
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ThrottledRequests \
  --dimensions Name=TableName,Value=SakeSensei-Users \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Sum
```

**Solutions:**

1. **Switch to On-Demand billing:**
   ```bash
   aws dynamodb update-table \
     --table-name SakeSensei-Users \
     --billing-mode PAY_PER_REQUEST
   ```

2. **Increase provisioned capacity:**
   ```bash
   aws dynamodb update-table \
     --table-name SakeSensei-Users \
     --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=5
   ```

3. **Use exponential backoff:**
   ```python
   import boto3
   from botocore.config import Config

   config = Config(
       retries={
           'max_attempts': 10,
           'mode': 'adaptive'
       }
   )

   dynamodb = boto3.resource('dynamodb', config=config)
   ```

4. **Optimize query patterns:**
   - Use Query instead of Scan
   - Add appropriate indexes (GSI/LSI)
   - Batch operations with batch_get_item/batch_write_item

### Issue: Data Not Found

**Symptoms:**
- "Item not found" errors
- Empty query results
- Missing user data

**Diagnosis:**

```bash
# Check if item exists
aws dynamodb get-item \
  --table-name SakeSensei-Users \
  --key '{"user_id": {"S": "user-123"}}' \
  --consistent-read

# Scan table (use sparingly)
aws dynamodb scan \
  --table-name SakeSensei-Users \
  --max-items 10

# Check table item count
aws dynamodb describe-table \
  --table-name SakeSensei-Users \
  --query 'Table.ItemCount'
```

**Solutions:**

1. **Verify correct partition key:**
   ```python
   # Correct
   table.get_item(Key={'user_id': 'user-123'})

   # Incorrect (will fail)
   table.get_item(Key={'username': 'user@example.com'})
   ```

2. **Check for eventual consistency:**
   - Use `ConsistentRead=True` for get_item
   - Wait briefly after write before reading

3. **Verify GSI for queries:**
   ```bash
   # List table indexes
   aws dynamodb describe-table \
     --table-name SakeSensei-TastingRecords \
     --query 'Table.GlobalSecondaryIndexes[*].IndexName'
   ```

### Issue: DynamoDB Backup/Restore

**Symptoms:**
- Need to recover deleted data
- Need to restore to previous state

**Diagnosis:**

```bash
# Check Point-in-Time Recovery status
aws dynamodb describe-continuous-backups \
  --table-name SakeSensei-Users

# List available backups
aws dynamodb list-backups \
  --table-name SakeSensei-Users
```

**Solutions:**

1. **Enable Point-in-Time Recovery:**
   ```bash
   aws dynamodb update-continuous-backups \
     --table-name SakeSensei-Users \
     --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
   ```

2. **Restore from PITR:**
   ```bash
   aws dynamodb restore-table-to-point-in-time \
     --source-table-name SakeSensei-Users \
     --target-table-name SakeSensei-Users-Restored \
     --restore-date-time $(date -u -d '1 hour ago' --iso-8601)
   ```

3. **Restore from backup:**
   ```bash
   aws dynamodb restore-table-from-backup \
     --target-table-name SakeSensei-Users-Restored \
     --backup-arn arn:aws:dynamodb:us-west-2:ACCOUNT_ID:table/SakeSensei-Users/backup/BACKUP_ID
   ```

---

## Deployment Issues

### Issue: CDK Deployment Fails

**Symptoms:**
- "CREATE_FAILED" status
- Resource already exists errors
- IAM permission errors

**Diagnosis:**

```bash
# Check stack status
aws cloudformation describe-stacks \
  --stack-name SakeSenseiStorageStack \
  --query 'Stacks[0].StackStatus'

# Check stack events
aws cloudformation describe-stack-events \
  --stack-name SakeSenseiStorageStack \
  --max-items 20 \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'

# View detailed error
cdk diff
```

**Solutions:**

1. **Resource already exists:**
   ```bash
   # Import existing resource into stack
   aws cloudformation import-stack-resources \
     --stack-name SakeSenseiStorageStack \
     --resources-to-import file://resources.json
   ```

2. **IAM permission denied:**
   - Check CloudFormation execution role has necessary permissions
   - Add required policies to deployment role

3. **Rollback failed stack:**
   ```bash
   # Delete failed stack
   aws cloudformation delete-stack --stack-name SakeSenseiStorageStack

   # Wait for deletion
   aws cloudformation wait stack-delete-complete \
     --stack-name SakeSenseiStorageStack

   # Redeploy
   cd infrastructure
   uv run cdk deploy SakeSenseiStorageStack
   ```

4. **Check CDK bootstrap:**
   ```bash
   cdk bootstrap aws://ACCOUNT_ID/us-west-2
   ```

### Issue: Copilot Deployment Fails

**Symptoms:**
- ECS service fails to start
- Docker build errors
- Task definition registration fails

**Diagnosis:**

```bash
# Check deployment status
copilot svc status --name streamlit-app --env prod

# View deployment logs
copilot svc logs --name streamlit-app --env prod --follow

# Check CloudFormation stack
aws cloudformation describe-stack-events \
  --stack-name sakesensei-prod-streamlit-app \
  --max-items 20
```

**Solutions:**

1. **Docker build fails:**
   ```bash
   # Build locally to debug
   cd streamlit_app
   docker build -t sakesensei:debug .

   # Test container
   docker run -p 8501:8501 sakesensei:debug
   ```

2. **Task definition invalid:**
   - Check `copilot/streamlit-app/manifest.yml` syntax
   - Validate CPU/memory combinations
   - Ensure image URI is correct

3. **Service fails to stabilize:**
   - Check health check configuration
   - Verify security group allows ALB → ECS traffic
   - Check ECS task logs for application errors

4. **Rollback deployment:**
   ```bash
   copilot svc rollback --name streamlit-app --env prod
   ```

### Issue: GitHub Actions Workflow Fails

**Symptoms:**
- Workflow run fails
- Build errors
- Deployment errors

**Diagnosis:**

```bash
# View workflow runs
gh run list --workflow deploy-staging.yml

# View specific run
gh run view <run-id>

# Download logs
gh run download <run-id>
```

**Solutions:**

1. **Check GitHub Secrets:**
   - Navigate to Settings → Secrets and variables → Actions
   - Verify all required secrets are set:
     - AWS_ACCESS_KEY_ID
     - AWS_SECRET_ACCESS_KEY
     - ECR_REGISTRY
     - STAGING_URL
     - PRODUCTION_URL

2. **Workflow syntax error:**
   ```bash
   # Validate workflow locally
   act -l  # List jobs
   act -j test  # Run specific job
   ```

3. **Permission errors:**
   - Check IAM user/role permissions
   - Verify OIDC provider is configured (if using OIDC)

4. **Re-run workflow:**
   ```bash
   gh run rerun <run-id>
   ```

---

## Performance Issues

### Issue: High Latency

**Symptoms:**
- Slow API responses (>3 seconds)
- Poor user experience
- Timeout warnings

**Diagnosis:**

```bash
# Check ALB metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Average,p99

# Check Lambda duration
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=SakeSensei-Recommendation \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Average,p99

# Analyze X-Ray traces
aws xray get-service-graph \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s)
```

**Solutions:**

1. **Optimize Lambda cold starts:**
   - Increase memory allocation
   - Use provisioned concurrency
   - Reduce deployment package size
   - Use Lambda layers for dependencies

2. **Optimize database queries:**
   - Use Query instead of Scan
   - Add appropriate indexes
   - Enable DAX (DynamoDB Accelerator) for read-heavy workloads
   - Use batch operations

3. **Add caching:**
   - Use ElastiCache (Redis/Memcached) for frequently accessed data
   - Cache API responses in Streamlit with `@st.cache_data`
   - Use CloudFront for static content

4. **Enable compression:**
   - Enable gzip compression on ALB
   - Compress large payloads in Lambda responses

### Issue: High CPU/Memory Usage

**Symptoms:**
- ECS tasks being killed (OOM)
- High CPU utilization (>80%)
- Autoscaling triggered frequently

**Diagnosis:**

```bash
# Check ECS metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=streamlit-app \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Average,Maximum

aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=streamlit-app \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Average,Maximum
```

**Solutions:**

1. **Increase task size:**
   ```yaml
   # copilot/streamlit-app/manifest.yml
   cpu: 2048      # 2 vCPU
   memory: 4096   # 4 GB
   ```

2. **Optimize code:**
   - Profile code to identify bottlenecks
   - Use efficient algorithms
   - Avoid memory leaks
   - Close connections properly

3. **Use Spot instances for cost savings:**
   ```yaml
   count:
     range:
       min: 2
       max: 10
       spot_from: 4  # Use Spot for scale-out
   ```

---

## Security Issues

### Issue: WAF Blocking Legitimate Traffic

**Symptoms:**
- 403 Forbidden errors
- "Request blocked by AWS WAF"
- Users unable to access site

**Diagnosis:**

```bash
# Check blocked requests
aws wafv2 get-sampled-requests \
  --web-acl-arn <web-acl-arn> \
  --rule-metric-name RateLimitRule \
  --scope REGIONAL \
  --time-window StartTime=$(date -u -d '1 hour ago' +%s),EndTime=$(date -u +%s) \
  --max-items 100

# Check WAF logs
aws logs tail /aws/wafv2/regional/sakesensei --follow
```

**Solutions:**

1. **Whitelist IP:**
   ```bash
   # Create IP set
   aws wafv2 create-ip-set \
     --name SakeSensei-AllowedIPs \
     --scope REGIONAL \
     --ip-address-version IPV4 \
     --addresses 203.0.113.0/24

   # Add to WAF rule (update Web ACL with higher priority rule)
   ```

2. **Adjust rate limit:**
   - Edit `infrastructure/stacks/security_stack.py`
   - Increase rate limit threshold
   - Redeploy security stack

3. **Disable specific rule temporarily:**
   ```bash
   # Update Web ACL to override rule action to COUNT
   aws wafv2 update-web-acl \
     --id <web-acl-id> \
     --scope REGIONAL \
     --rules <updated-rules-json>
   ```

### Issue: Suspicious Activity Detected

**Symptoms:**
- Unusual traffic patterns
- High error rates from specific IPs
- Potential security breach

**Diagnosis:**

```bash
# Check CloudTrail for unauthorized API calls
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=DeleteUser \
  --start-time $(date -u -d '24 hours ago' --iso-8601) \
  --max-results 50

# Check GuardDuty findings (if enabled)
aws guardduty list-findings \
  --detector-id <detector-id> \
  --finding-criteria '{"Criterion":{"severity":{"Gte":7}}}'

# Check failed auth attempts
aws logs filter-log-events \
  --log-group-name /aws/cognito/userpools/us-west-2_XXXXXXXXX \
  --filter-pattern "failed" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

**Solutions:**

1. **Block malicious IPs:**
   ```bash
   # Add to WAF IP block list
   aws wafv2 update-ip-set \
     --name SakeSensei-BlockedIPs \
     --scope REGIONAL \
     --id <ip-set-id> \
     --addresses 198.51.100.0/24 192.0.2.1/32
   ```

2. **Rotate credentials:**
   ```bash
   # Rotate API keys in Secrets Manager
   aws secretsmanager rotate-secret \
     --secret-id SakeSensei/AgentCore/APIKey

   # Rotate Cognito client secret (if applicable)
   aws cognito-idp update-user-pool-client \
     --user-pool-id us-west-2_XXXXXXXXX \
     --client-id XXXXXXXXXXXXXXXXXXXXXXXXXX \
     --generate-secret
   ```

3. **Enable MFA:**
   ```bash
   # Enable MFA for Cognito User Pool
   aws cognito-idp set-user-pool-mfa-config \
     --user-pool-id us-west-2_XXXXXXXXX \
     --mfa-configuration OPTIONAL \
     --software-token-mfa-configuration Enabled=true
   ```

4. **Review and restrict IAM policies:**
   - Apply principle of least privilege
   - Remove unnecessary permissions
   - Enable CloudTrail logging

---

## Network & Connectivity

### Issue: Cannot Connect to Services

**Symptoms:**
- Connection timeout
- Network unreachable
- DNS resolution failures

**Diagnosis:**

```bash
# Test DNS resolution
dig sakesensei.com
nslookup sakesensei.com

# Test HTTPS connectivity
curl -I https://sakesensei.com

# Check security group rules
aws ec2 describe-security-groups \
  --group-ids <security-group-id> \
  --query 'SecurityGroups[0].IpPermissions'

# Check VPC endpoints (if using)
aws ec2 describe-vpc-endpoints \
  --query 'VpcEndpoints[*].[VpcEndpointId,ServiceName,State]'
```

**Solutions:**

1. **DNS not resolving:**
   - Check Route 53 hosted zone records
   - Verify name servers are correct
   - Wait for DNS propagation (up to 48 hours)

2. **Security group blocking traffic:**
   ```bash
   # Add inbound rule for HTTPS
   aws ec2 authorize-security-group-ingress \
     --group-id <security-group-id> \
     --protocol tcp \
     --port 443 \
     --cidr 0.0.0.0/0
   ```

3. **ALB not routing traffic:**
   - Check listener rules
   - Verify target group health
   - Check ALB security group

### Issue: SSL/TLS Certificate Errors

**Symptoms:**
- "Certificate not trusted" warnings
- "Certificate expired" errors
- Mixed content warnings

**Diagnosis:**

```bash
# Check certificate details
openssl s_client -connect sakesensei.com:443 -servername sakesensei.com

# Check ACM certificate status
aws acm describe-certificate \
  --certificate-arn <certificate-arn>

# List certificates
aws acm list-certificates
```

**Solutions:**

1. **Certificate expired:**
   - ACM certificates auto-renew if DNS validation records are present
   - Verify CNAME validation records in Route 53

2. **Certificate not covering domain:**
   - Request new certificate with correct domain
   - Add Subject Alternative Names (SANs)

3. **Mixed content (HTTPS page loading HTTP resources):**
   - Ensure all resources loaded via HTTPS
   - Update hardcoded HTTP URLs to HTTPS
   - Configure ALB to redirect HTTP → HTTPS

---

## Monitoring & Logging

### Issue: Logs Not Appearing

**Symptoms:**
- CloudWatch log groups empty
- Cannot find recent logs
- Missing error logs

**Diagnosis:**

```bash
# Check if log group exists
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/SakeSensei

# Check log streams
aws logs describe-log-streams \
  --log-group-name /aws/lambda/SakeSensei-Recommendation \
  --order-by LastEventTime \
  --descending \
  --max-items 5

# Check IAM permissions for logging
aws iam get-role-policy \
  --role-name <lambda-execution-role> \
  --policy-name CloudWatchLogsPolicy
```

**Solutions:**

1. **Log group doesn't exist:**
   ```bash
   # Create log group
   aws logs create-log-group \
     --log-group-name /aws/lambda/SakeSensei-Recommendation

   # Set retention
   aws logs put-retention-policy \
     --log-group-name /aws/lambda/SakeSensei-Recommendation \
     --retention-in-days 30
   ```

2. **IAM permissions missing:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "logs:CreateLogGroup",
           "logs:CreateLogStream",
           "logs:PutLogEvents"
         ],
         "Resource": "arn:aws:logs:*:*:*"
       }
     ]
   }
   ```

3. **Check application logging:**
   ```python
   import logging

   logger = logging.getLogger()
   logger.setLevel(logging.INFO)

   def handler(event, context):
       logger.info(f"Processing event: {event}")
       # ... rest of handler
   ```

### Issue: CloudWatch Alarms Not Triggering

**Symptoms:**
- Alarms in "INSUFFICIENT_DATA" state
- Expected alarms not firing
- No SNS notifications received

**Diagnosis:**

```bash
# Check alarm state
aws cloudwatch describe-alarms \
  --alarm-names SakeSensei-Lambda-ErrorAlarm

# Check alarm history
aws cloudwatch describe-alarm-history \
  --alarm-name SakeSensei-Lambda-ErrorAlarm \
  --history-item-type StateUpdate \
  --max-records 10

# Check SNS subscriptions
aws sns list-subscriptions-by-topic \
  --topic-arn <alarm-topic-arn>
```

**Solutions:**

1. **Insufficient data:**
   - Wait for metric data to populate
   - Adjust evaluation period
   - Check metric exists and has data

2. **SNS subscription not confirmed:**
   ```bash
   # Resend confirmation email
   aws sns subscribe \
     --topic-arn <topic-arn> \
     --protocol email \
     --notification-endpoint your-email@example.com

   # Check email and confirm subscription
   ```

3. **Alarm threshold too high:**
   - Review alarm configuration
   - Adjust threshold to appropriate level
   - Test alarm with manual metric data:
     ```bash
     aws cloudwatch put-metric-data \
       --namespace Custom/Testing \
       --metric-name TestMetric \
       --value 100
     ```

---

## Error Code Reference

### HTTP Status Codes

| Code | Meaning | Common Causes | Solution |
|------|---------|---------------|----------|
| 400 | Bad Request | Invalid input, malformed JSON | Validate request payload |
| 401 | Unauthorized | Invalid/expired JWT token | Refresh authentication token |
| 403 | Forbidden | WAF block, insufficient permissions | Check WAF rules, verify IAM policy |
| 404 | Not Found | Resource doesn't exist | Verify resource ID, check DynamoDB |
| 429 | Too Many Requests | Rate limiting, throttling | Implement backoff, increase limits |
| 500 | Internal Server Error | Lambda error, uncaught exception | Check Lambda logs, fix code |
| 502 | Bad Gateway | ALB → ECS connection failed | Check target health, security groups |
| 503 | Service Unavailable | ECS tasks not running | Check ECS service status, scale up |
| 504 | Gateway Timeout | Request took too long | Increase timeout, optimize code |

### AWS Service Error Codes

#### DynamoDB

| Error Code | Meaning | Solution |
|------------|---------|----------|
| `ProvisionedThroughputExceededException` | Exceeded RCU/WCU | Increase capacity or switch to on-demand |
| `ResourceNotFoundException` | Table/item not found | Verify table name, check item exists |
| `ConditionalCheckFailedException` | Condition not met | Review condition expression |
| `ValidationException` | Invalid parameter | Check request syntax |

#### Lambda

| Error Code | Meaning | Solution |
|------------|---------|----------|
| `TooManyRequestsException` | Concurrency limit reached | Increase reserved concurrency |
| `ResourceConflictException` | Function being updated | Wait and retry |
| `InvalidParameterValueException` | Invalid configuration | Check function configuration |
| `RequestEntityTooLargeException` | Payload too large (>6 MB) | Reduce payload size |

#### Cognito

| Error Code | Meaning | Solution |
|------------|---------|----------|
| `UserNotFoundException` | User doesn't exist | Verify username |
| `NotAuthorizedException` | Incorrect password | Check credentials |
| `UserNotConfirmedException` | Email not verified | Resend confirmation code |
| `CodeMismatchException` | Invalid verification code | Request new code |
| `ExpiredCodeException` | Verification code expired | Request new code |

#### Bedrock AgentCore

| Error Code | Meaning | Solution |
|------------|---------|----------|
| `ThrottlingException` | Rate limit exceeded | Implement backoff retry |
| `ValidationException` | Invalid request | Check request format |
| `ResourceNotFoundException` | Agent/Gateway not found | Verify resource ID |
| `ServiceQuotaExceededException` | Service limit reached | Request quota increase |

### Application Error Codes

Custom error codes used in SakeSensei:

| Code | Message | Meaning | Solution |
|------|---------|---------|----------|
| `SS-001` | User preferences not found | User hasn't completed survey | Complete preference survey |
| `SS-002` | Invalid sake ID | Sake doesn't exist in database | Verify sake ID |
| `SS-003` | Agent invocation failed | AgentCore error | Check agent logs |
| `SS-004` | Recommendation generation failed | Algorithm error | Check Lambda logs |
| `SS-005` | Image recognition failed | Image processing error | Retry with different image |
| `SS-006` | Tasting record creation failed | Database error | Check DynamoDB logs |
| `SS-007` | Invalid authentication token | JWT validation failed | Re-authenticate |
| `SS-008` | Gateway tool not found | Lambda not registered | Re-run add_gateway_targets.py |

---

## Getting Additional Help

### Check Documentation

- **User Guide**: `docs/user-guide.md`
- **API Reference**: `docs/api-reference.md`
- **Operations Guide**: `docs/operations.md`
- **Domain/SSL Setup**: `docs/domain-ssl-setup.md`

### AWS Support Resources

- **AWS Support Console**: https://console.aws.amazon.com/support/
- **AWS Forums**: https://forums.aws.amazon.com/
- **AWS Documentation**: https://docs.aws.amazon.com/

### Service-Specific Documentation

- **Streamlit**: https://docs.streamlit.io/
- **Amazon Bedrock**: https://docs.aws.amazon.com/bedrock/
- **AWS Lambda**: https://docs.aws.amazon.com/lambda/
- **Amazon DynamoDB**: https://docs.aws.amazon.com/dynamodb/
- **AWS Copilot**: https://aws.github.io/copilot-cli/

### Contact Information

- **Email Support**: support@sakesensei.com
- **Bug Reports**: bugs@sakesensei.com
- **Feature Requests**: features@sakesensei.com

---

**Last Updated**: 2025-10-01
