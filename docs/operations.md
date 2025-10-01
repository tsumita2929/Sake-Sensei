# Sake Sensei Operations Guide

This guide covers deployment, monitoring, maintenance, and operational procedures for Sake Sensei.

## Table of Contents

1. [Deployment](#deployment)
2. [Monitoring](#monitoring)
3. [Maintenance](#maintenance)
4. [Backup & Recovery](#backup--recovery)
5. [Security Operations](#security-operations)
6. [Performance Tuning](#performance-tuning)
7. [Cost Optimization](#cost-optimization)

## Deployment

### Prerequisites

- AWS CLI configured
- uv installed
- Docker installed
- AWS Copilot CLI installed
- Appropriate IAM permissions

### Infrastructure Deployment

#### 1. Deploy CDK Stacks

```bash
cd infrastructure
uv sync
uv run cdk bootstrap  # First time only
uv run cdk deploy --all
```

Stacks deployed:
- `SakeSenseiStorageStack` - S3 buckets
- `SakeSenseiDatabaseStack` - DynamoDB tables
- `SakeSenseiAuthStack` - Cognito User Pool
- `SakeSenseiLambdaStack` - Lambda functions
- `SakeSenseiMonitoringStack` - CloudWatch resources
- `SakeSenseiSecurityStack` - WAF, Secrets Manager

#### 2. Deploy AgentCore Resources

```bash
# Create Gateway
cd scripts
python create_gateway.py

# Add Lambda tools to Gateway
python add_gateway_targets.py

# Create Memory Store
python create_memory.py

# Configure Identity
python setup_identity.py

# Deploy Agent
cd ../agent
uv run agentcore configure --entrypoint entrypoint.py
uv run agentcore launch --environment production
```

#### 3. Deploy Frontend (ECS)

```bash
# Set up Copilot environment
copilot env init --name prod --profile default

# Deploy service
copilot deploy --name streamlit-app --env prod
```

### CI/CD Deployment

Deployment is automated via GitHub Actions:

- **PR Checks:** `.github/workflows/pr-checks.yml`
- **Staging:** `.github/workflows/deploy-staging.yml` (on push to main)
- **Production:** `.github/workflows/deploy-production.yml` (manual trigger)

#### Staging Deployment

Automatic on merge to `main`:

```bash
git checkout main
git pull
# Changes are automatically deployed to staging
```

#### Production Deployment

Manual trigger via GitHub Actions:

1. Go to Actions → Deploy to Production
2. Click "Run workflow"
3. Enter version (git SHA or tag)
4. Approve deployment
5. Monitor deployment progress

### Rollback Procedures

If deployment fails or issues are detected:

```bash
# Via GitHub Actions
# Actions → Rollback Deployment → Run workflow
# Select environment and target version

# Or via Copilot CLI
copilot svc rollback --name streamlit-app --env prod

# Or via AWS ECS
aws ecs update-service \
  --cluster sakesensei-prod \
  --service streamlit-app \
  --task-definition sakesensei-prod-streamlit-app:PREVIOUS_REVISION
```

## Monitoring

### CloudWatch Dashboard

Access: AWS Console → CloudWatch → Dashboards → `SakeSensei-Monitoring`

**Widgets:**
- Lambda invocations and errors
- Lambda duration (P99)
- ECS CPU/Memory utilization
- ALB request count and errors
- ALB response time

### CloudWatch Alarms

Active alarms send notifications to SNS topic `SakeSensei-Alarms`.

**Critical Alarms:**
- Lambda error rate > 5% (2 consecutive periods)
- Lambda duration P99 > 3s
- Lambda throttles > 10
- ECS CPU > 80%
- ECS Memory > 80%
- ALB 5XX errors > 10 (5 min)
- ALB P99 response time > 5s

### Logs

**CloudWatch Log Groups:**
- `/aws/lambda/SakeSensei-Recommendation`
- `/aws/lambda/SakeSensei-Preference`
- `/aws/lambda/SakeSensei-Tasting`
- `/aws/lambda/SakeSensei-Brewery`
- `/aws/lambda/SakeSensei-ImageRecognition`
- `/ecs/sakesensei/streamlit-app`
- `/agentcore/sakesensei/agent`

**Log Retention:** 30 days

**Querying Logs:**

```bash
# Search for errors in last hour
aws logs filter-log-events \
  --log-group-name /aws/lambda/SakeSensei-Recommendation \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR"

# Tail ECS logs
copilot svc logs --name streamlit-app --env prod --follow
```

### X-Ray Tracing

View distributed traces: AWS Console → X-Ray → Traces

**Use Cases:**
- Identify slow Lambda functions
- Analyze request flow
- Debug errors across services

### Metrics to Monitor

**Daily:**
- Error rates (should be < 1%)
- P99 latency (should be < 3s)
- Concurrent users
- Failed login attempts

**Weekly:**
- Cost trends
- Capacity utilization
- Security scan results

**Monthly:**
- Performance trends
- User growth
- Feature usage

## Maintenance

### Regular Tasks

#### Daily
- Check CloudWatch alarms
- Review error logs
- Monitor cost dashboard

#### Weekly
- Review security scan results (Bandit, Safety, Trivy)
- Check for dependency updates
- Review performance metrics

#### Monthly
- Update dependencies
- Review and rotate secrets
- Cost optimization review
- Backup verification

### Dependency Updates

```bash
# Check for updates
cd /path/to/SakeSensei
uv sync --upgrade

# Run tests
uv run pytest

# Deploy to staging
git checkout -b deps/update-YYYY-MM
git add pyproject.toml uv.lock
git commit -m "chore: update dependencies"
git push origin deps/update-YYYY-MM
# Create PR, merge after CI passes
```

### Database Maintenance

DynamoDB is managed by AWS, but monitor:

**Metrics:**
- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- ThrottledRequests
- UserErrors

**Actions:**
- Review access patterns
- Optimize queries
- Consider on-demand vs. provisioned capacity

### Secret Rotation

```bash
# Rotate AgentCore API key
aws secretsmanager rotate-secret \
  --secret-id SakeSensei/AgentCore/APIKey \
  --rotation-lambda-arn arn:aws:lambda:...

# Verify rotation
aws secretsmanager describe-secret \
  --secret-id SakeSensei/AgentCore/APIKey
```

## Backup & Recovery

### DynamoDB Backups

**Point-in-Time Recovery (PITR):** Enabled on all tables

**On-Demand Backups:**

```bash
# Create backup
aws dynamodb create-backup \
  --table-name SakeSensei-TastingRecords \
  --backup-name TastingRecords-$(date +%Y%m%d)

# List backups
aws dynamodb list-backups \
  --table-name SakeSensei-TastingRecords

# Restore from backup
aws dynamodb restore-table-from-backup \
  --target-table-name SakeSensei-TastingRecords-Restored \
  --backup-arn arn:aws:dynamodb:...
```

### S3 Backups

**Versioning:** Enabled on images bucket

**Cross-Region Replication:** Optional (for disaster recovery)

### Configuration Backups

All infrastructure is defined as code:
- CDK stacks in `infrastructure/`
- Copilot manifests in `copilot/`
- Version controlled in Git

## Security Operations

### Security Monitoring

**AWS Security Hub:** Centralized security findings

**GuardDuty:** Threat detection (optional)

**CloudTrail:** API activity logging

### Security Scans

Automated via GitHub Actions (`.github/workflows/security-scan.yml`):

**Daily Scans:**
- Bandit (code security)
- Safety (dependency vulnerabilities)
- Trivy (container/filesystem)
- Gitleaks (secret scanning)

**Review Process:**
1. Check GitHub Security tab
2. Review SARIF reports in artifacts
3. Prioritize CRITICAL/HIGH findings
4. Create issues for remediation
5. Deploy fixes

### Incident Response

**Security Incident Playbook:**

1. **Detect:** Via CloudWatch Alarms, Security Hub, or user report
2. **Assess:** Severity and scope
3. **Contain:** Block malicious IPs via WAF
4. **Investigate:** Check CloudTrail, logs
5. **Remediate:** Deploy fixes
6. **Document:** Post-mortem report

### WAF Management

**View blocked requests:**

```bash
aws wafv2 get-sampled-requests \
  --web-acl-arn arn:aws:wafv2:... \
  --rule-metric-name RateLimitRule \
  --scope REGIONAL \
  --time-window StartTime=...,EndTime=... \
  --max-items 100
```

**Add IP to block list:**

```bash
# Create IP set
aws wafv2 create-ip-set \
  --name SakeSensei-BlockedIPs \
  --scope REGIONAL \
  --ip-address-version IPV4 \
  --addresses 192.0.2.1/32 203.0.113.0/24

# Add to WAF rule (update Web ACL)
```

## Performance Tuning

### Lambda Optimization

**Memory Allocation:**

```bash
# Update Lambda memory (higher memory = more CPU)
aws lambda update-function-configuration \
  --function-name SakeSensei-ImageRecognition \
  --memory-size 2048  # Increase for image processing
```

**Concurrency:**

```bash
# Set reserved concurrency
aws lambda put-function-concurrency \
  --function-name SakeSensei-Recommendation \
  --reserved-concurrent-executions 50
```

### ECS Optimization

**Task Definition:**

Edit `copilot/streamlit-app/manifest.yml`:

```yaml
cpu: 1024      # 1 vCPU
memory: 2048   # 2 GB

# Autoscaling
count:
  range:
    min: 2
    max: 10
    spot_from: 4  # Use Spot instances for cost savings
  cpu_percentage: 70
  memory_percentage: 80
```

### Database Optimization

**Index Strategy:**
- Use Global Secondary Indexes (GSI) for query patterns
- Avoid scans; use query operations

**Access Patterns:**
- Review most common queries
- Optimize partition key design
- Consider caching frequently accessed data

## Cost Optimization

### Current Costs (Estimate)

| Service | Monthly Cost |
|---------|--------------|
| ECS Fargate | $30-50 |
| Lambda | $10-20 |
| DynamoDB | $5-15 |
| S3 | $1-5 |
| CloudWatch | $5-10 |
| Route 53 | $0.50 |
| **Total** | **~$52-100** |

### Optimization Strategies

1. **Use Spot Instances** for ECS tasks (40-70% savings)
2. **Lambda Memory** tuning (balance cost vs. performance)
3. **DynamoDB On-Demand** for unpredictable traffic
4. **S3 Intelligent-Tiering** for images
5. **CloudWatch Log Retention** (30 days vs. indefinite)

### Cost Monitoring

```bash
# Get cost and usage
aws ce get-cost-and-usage \
  --time-period Start=2025-10-01,End=2025-10-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

**Set up Budget Alerts:**

AWS Console → AWS Budgets → Create budget

## Health Checks

### Application Health

**ECS Health Check:**
- Endpoint: `/_stcore/health`
- Expected: HTTP 200
- Interval: 30 seconds

**Lambda Health:**
- Check CloudWatch metrics for errors
- Review X-Ray service map

### Smoke Tests

Run after deployment:

```bash
cd tests/smoke
uv run pytest --base-url https://sakesensei.com
```

## Disaster Recovery

### RTO/RPO Targets

- **RTO (Recovery Time Objective):** 4 hours
- **RPO (Recovery Point Objective):** 1 hour

### DR Plan

1. **Infrastructure:** Redeploy via CDK (< 1 hour)
2. **Data:** Restore from DynamoDB PITR (< 1 hour)
3. **Application:** Deploy latest Docker image (< 30 minutes)
4. **DNS:** Update Route 53 if needed (< 5 minutes)

## Runbooks

### Deploy New Version

1. Create and test PR
2. Merge to main (auto-deploys to staging)
3. Verify staging
4. Trigger production deployment workflow
5. Monitor CloudWatch dashboard
6. Run smoke tests

### Scale Up for High Traffic

```bash
# Increase ECS task count
copilot svc update --name streamlit-app --env prod
# Edit manifest.yml to increase max tasks

# Increase Lambda concurrency
aws lambda put-function-concurrency \
  --function-name SakeSensei-Recommendation \
  --reserved-concurrent-executions 100
```

### Update Environment Variables

```bash
# Update SSM parameter
aws ssm put-parameter \
  --name "/copilot/sakesensei/prod/secrets/PARAM_NAME" \
  --value "new-value" \
  --overwrite

# Redeploy service
copilot svc deploy --name streamlit-app --env prod
```

---

For troubleshooting, see [Troubleshooting Guide](troubleshooting.md).

Last Updated: 2025-10-01
