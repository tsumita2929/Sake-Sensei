# Sake Sensei - Implementation Rules

## 🔰 **MANDATORY: Amazon Bedrock AgentCore First Principle**

**⚠️ 最重要実装原則: すべてのAI機能実装において、Amazon Bedrock AgentCoreの利用可能性を必ず最初に確認し、優先的に使用すること**

### BedrockAgentCore優先順位

1. **最優先**: Amazon Bedrock AgentCore の既存機能を確認
   - Bedrock Agent (Memory, Tools, Knowledge Bases)
   - AWS CLI (`aws bedrock-agent`, `aws bedrock-agent-runtime`)
   - CloudFormation/CDKリソース
   - boto3 SDK

2. **代替手段**: AgentCoreで実装できない場合のみ、以下を検討
   - DynamoDB + Lambda による自作実装
   - サードパーティライブラリ

3. **実装前チェックリスト**:
   - [ ] AWS CLIで該当機能の存在を確認 (`aws bedrock-agent help`)
   - [ ] CloudFormation/CDKでのリソース定義方法を確認
   - [ ] boto3 APIドキュメントを確認
   - [ ] AgentCoreで実装できない場合のみ、代替手段を検討

### BedrockAgentCore実装例

**✅ 正しい実装 (AgentCore優先)**:
```python
# Memory機能: Bedrock Agent Memory を使用
aws bedrock-agent update-agent \
  --agent-id AGENT_ID \
  --memory-configuration '{
    "enabledMemoryTypes": ["SESSION_SUMMARY"],
    "sessionSummaryConfiguration": {"maxRecentSessions": 5},
    "storageDays": 30
  }'
```

**❌ 誤った実装 (AgentCore確認なし)**:
```python
# 独自DynamoDBテーブルでMemory実装 (AgentCore確認前)
dynamodb.create_table(TableName='CustomMemory', ...)
```

### 実装時の判断フロー

```
新機能実装が必要
    ↓
AWS CLI/boto3 で BedrockAgentCore を確認
    ↓
    ├─ 利用可能 → AgentCore APIを使用 ✅
    │   └─ CloudFormation/CDK で定義
    │
    └─ 利用不可 → 代替実装を検討
        └─ ドキュメントに理由を記載
```

## 📋 Implementation Process (AI-Driven)

### 実装フロー

```mermaid
graph TD
    A[IMPLEMENTATION_PLAN.md確認] --> B[タスク選択]
    B --> C[AIによるコード生成]
    C --> D[コード検証]
    D --> E{テスト成功?}
    E -->|Yes| F[コミット]
    E -->|No| C
    F --> G[タスク完了マーク]
    G --> H[計画見直し]
    H --> B
```

### タスク実装ルール

1. **タスク粒度**: 1タスク = 1ファイル作成/編集 (5-15分)
2. **実装順序**: IMPLEMENTATION_PLAN.mdのPhase順に実施
3. **依存関係**: 依存タスクの完了を確認してから実施
4. **検証必須**: 各タスク後にruff/mypy/pytestを実行
5. **自動継続**: ユーザー確認なしで次タスクへ自動進行
6. **自動見直し**: 5タスク完了ごとに自動で計画評価・調整
7. **TASK_TRACKER.md更新必須**: 各タスク完了時およびPhase完了時に必ずTASK_TRACKER.mdを更新

### AI自律実装プロセス (MANDATORY)

**⚠️ 重要: AIは以下のプロセスを自律的に実行し、ユーザーに継続/見直しの確認を求めてはならない**

#### 実装サイクル
```
タスクN実装 → 検証 → 完了マーク → TASK_TRACKER更新
    ↓
タスクN+1へ自動継続
    ↓
5タスク完了？
    ↓ Yes
自動計画見直し → 調整（必要な場合のみ） → 継続
    ↓ No
継続
```

#### 自動判断基準

**継続する条件（ユーザー確認不要）:**
- タスクが正常に完了
- 依存関係が解決済み
- 次タスクの実装が可能

**停止する条件（ユーザー報告必要）:**
- エラーで実装不可能
- 設計上の重大な問題発見
- 外部リソースへのアクセスが必要（AWS認証情報など）

**自動見直し時の判断:**
- 新たな技術的制約の発見 → 計画調整
- より効率的な実装順序の発見 → 順序変更
- 不要なタスクの発見 → タスク削除
- 実装済み機能との重複発見 → タスクスキップ

#### 進捗報告のタイミング

- **5タスクごと**: 簡潔な進捗サマリー + 計画見直し結果
- **Phaseごと**: Phase完了報告 + 統合テスト結果
- **エラー時**: 即座にブロッカー報告

**報告フォーマット:**
```
✅ Phase X.Y 完了 (N/M タスク)
🔄 次: Phase X.Z (自動継続中)
⚠️ 調整: [あれば記載]
```

### AIへの実装指示テンプレート

```
タスク[番号]を実装:
- ファイル: [パス]
- 目的: [機能説明]
- 依存: [依存タスク]
- 検証: ruff format, ruff check, mypy
```

### コミットメッセージ規則

```
feat: [Phase X.Y] タスク名
例: feat: [Phase 0.1] Create pyproject.toml with basic dependencies
```

## ⚠️ Mandatory Requirements

### Package Manager: uv

This project **MUST** use **uv** for all package management operations.

- ❌ Do NOT use `pip install`, `poetry`, or `pipenv`
- ✅ Use `uv add`, `uv sync`, `uv run` for all operations
- All team members must have uv installed before contributing

**Basic commands:**

```bash
uv sync                    # Sync dependencies
uv add <package>          # Add dependency
uv add --dev <package>    # Add dev dependency
uv run <command>          # Run command in venv
```

### Linter/Formatter: Ruff

This project **MUST** use **Ruff** for code quality.

- ❌ Do NOT use `black`, `flake8`, `isort` separately
- ✅ Use `uv run ruff format` and `uv run ruff check`
- All code must pass ruff checks before committing

**Basic commands:**

```bash
uv run ruff format .      # Format code
uv run ruff check .       # Check linting
uv run ruff check --fix . # Auto-fix issues
```

## Technology Stack

### Frontend

- **Streamlit** (Python 3.12) on **ECS Fargate**
- **Container Orchestration**: AWS Copilot CLI
- **Load Balancer**: Application Load Balancer (ALB)
- **Authentication**: AWS Cognito via AgentCore Identity

### Agentic Framework

- **Strands Agents** on Amazon Bedrock AgentCore Runtime
- **Model**: Claude Sonnet 4.5 via Amazon Bedrock
- **Services**: Runtime, Gateway (MCP), Memory, Identity, Observability

### ⚠️ MANDATORY: AgentCore Integration Policy

**ALL AI services in this project MUST use Amazon Bedrock AgentCore.**

#### Required Integration Approach

1. **Primary Method (Recommended)**: **AgentCore Gateway (MCP)**
   - All Lambda functions should be exposed as MCP tools via AgentCore Gateway
   - Gateway provides unified authentication, authorization, and observability
   - Enables seamless tool composition and agent orchestration

2. **Temporary Fallback (During Setup)**: **Direct Lambda Invocation**
   - Used ONLY when AgentCore Gateway is not yet configured
   - `backend_helper.py` automatically falls back to direct Lambda calls
   - Should be migrated to Gateway as soon as possible

#### Implementation Status

- ✅ **AI Chat (Bedrock Converse API)**: Using Claude Sonnet 4.5 via Bedrock Runtime
- ⚠️ **Backend Lambda Tools**: Currently using direct Lambda invocation (fallback mode)
- 🚧 **AgentCore Gateway**: Pending setup (see `scripts/agentcore/create_gateway.py`)

#### Migration Path to Full AgentCore Integration

1. **Create AgentCore Gateway**:
   ```bash
   # Set required environment variables in .env
   export GATEWAY_ROLE_ARN=arn:aws:iam::ACCOUNT:role/AgentCoreGatewayRole

   # Run gateway creation script
   uv run python scripts/agentcore/create_gateway.py
   ```

2. **Register Lambda Functions as MCP Tools**:
   ```bash
   uv run python scripts/agentcore/add_gateway_targets.py
   ```

3. **Update SSM Parameters** with Gateway URL:
   ```bash
   aws ssm put-parameter \
     --name /copilot/applications/sakesensei/environments/dev/secrets/AGENTCORE_GATEWAY_URL \
     --value "https://gateway.bedrock.amazonaws.com/gateway/GATEWAY_ID" \
     --type String \
     --overwrite
   ```

4. **Deploy and Test**: Backend automatically switches to Gateway mode when URL is configured

#### Code Guidelines

- **New Features**: MUST use AgentCore Gateway from the start
- **AI Services**: MUST use Bedrock Runtime (Claude Sonnet 4.5)
- **No Direct Model Calls**: Always use Bedrock Runtime, never call model APIs directly
- **Tool Design**: Design Lambda functions with MCP tool interface in mind

### Backend

- **Lambda Functions**: Recommendation, Preference, Tasting, Brewery, Image Recognition
- **Database**: Amazon DynamoDB
- **Storage**: Amazon S3
- **Security**: AWS WAF, HTTPS

### AWS Region Configuration

**⚠️ IMPORTANT: This project deploys to `us-west-2` (Oregon) by default.**

- **Primary Region**: `us-west-2` (US West - Oregon)
- **Reason**:
  - Bedrock Claude 4.5 Sonnet availability
  - Lower latency for North American users
  - Cost-effective pricing tier
- **Configuration**:
  - **ALL region settings are in `.env` file**
  - Default: `AWS_REGION=us-west-2` in `.env.example`
  - To change region: Update `AWS_REGION` in `.env` and re-deploy
  - **NEVER hardcode region names in source code**

**Supported Services in us-west-2:**
- ✅ Amazon Bedrock (Claude 4.5 Sonnet)
- ✅ Amazon DynamoDB
- ✅ Amazon S3
- ✅ Amazon Cognito
- ✅ AWS Lambda
- ✅ Amazon ECS Fargate

**Region Change Procedure:**
1. Update `AWS_REGION` in `.env`
2. Verify Bedrock model availability in new region
3. Run `uv run cdk destroy --all` (if previously deployed)
4. Run `uv run cdk deploy --all` with new region
5. Update all AgentCore resources with new region endpoints

### Directory Structure

```text
SakeSensei/
├── streamlit_app/
│   ├── app.py                          # Main Streamlit app
│   ├── Dockerfile                      # Container image definition
│   ├── requirements.txt                # Python dependencies (generated from uv)
│   ├── pages/
│   │   ├── preference_survey.py        # User preference survey page
│   │   ├── recommendations.py          # AI-powered recommendations page
│   │   ├── rating.py                   # Sake rating and feedback page
│   │   ├── image_recognition.py        # Label photo upload and recognition
│   │   └── history.py                  # Tasting history and analytics
│   ├── components/
│   │   ├── auth.py                     # Cognito authentication UI
│   │   ├── agent_client.py             # AgentCore Runtime client
│   │   └── sake_card.py                # Sake display component
│   └── utils/
│       ├── config.py                   # App configuration
│       └── session.py                  # Session state management
├── agent/
│   ├── agent.py                        # Main Strands Agent definition
│   ├── entrypoint.py                   # AgentCore Runtime entrypoint (@app.entrypoint)
│   ├── system_prompt.py                # Agent system prompt and instructions
│   ├── memory_hook.py                  # AgentCore Memory integration hooks
│   ├── tools/                          # Custom agent tools
│   │   └── recommendation_tool.py      # Recommendation generation tool
│   └── requirements.txt                # Agent dependencies
├── backend/
│   ├── lambdas/
│   │   ├── recommendation/             # Recommendation engine Lambda
│   │   │   ├── handler.py              # Lambda handler (MCP tool format)
│   │   │   ├── algorithm.py            # Recommendation algorithm
│   │   │   └── requirements.txt
│   │   ├── preference/                 # User preference management
│   │   │   ├── handler.py
│   │   │   └── requirements.txt
│   │   ├── tasting/                    # Tasting record management
│   │   │   ├── handler.py
│   │   │   └── requirements.txt
│   │   ├── brewery/                    # Brewery information
│   │   │   ├── handler.py
│   │   │   └── requirements.txt
│   │   └── image_recognition/          # Image recognition Lambda
│   │       ├── handler.py
│   │       └── requirements.txt
│   └── infrastructure/
│       ├── dynamodb.yaml               # DynamoDB table definitions
│       ├── waf.yaml                    # WAF rules
│       └── iam_roles.yaml              # IAM roles for AgentCore
├── copilot/
│   ├── .workspace                      # Copilot workspace config
│   ├── environments/
│   │   ├── dev/
│   │   │   └── manifest.yml            # Dev environment config
│   │   └── prod/
│   │       └── manifest.yml            # Prod environment config
│   └── streamlit-app/
│       ├── manifest.yml                # ECS service definition
│       └── addons/
│           └── alb.yml                 # ALB configuration
├── scripts/
│   ├── create_gateway.py               # Create AgentCore Gateway
│   ├── add_gateway_targets.py          # Add Lambda targets to Gateway
│   ├── create_memory.py                # Create AgentCore Memory store
│   ├── setup_identity.py               # Setup AgentCore Identity with Cognito
│   ├── enable_observability.py         # Enable AgentCore Observability
│   └── deploy_agent.py                 # Deploy agent to Runtime
├── data/
│   ├── sake_master.json                # Sake master data
│   └── brewery_master.json             # Brewery master data
├── tests/
│   ├── unit/                           # Unit tests
│   ├── integration/                    # Integration tests
│   ├── e2e/                            # End-to-end tests
│   └── agent/                          # Agent-specific tests
│       ├── test_agent_local.py         # Test agent locally
│       └── test_agent_runtime.py       # Test deployed agent
├── .streamlit/
│   └── config.toml
├── pyproject.toml                      # uv package management
├── .env.example
├── .agentcore.yaml                     # AgentCore configuration (generated)
├── DESIGN.md
├── REQUIREMENTS.md
├── TASKS.md
└── CLAUDE.md
```

## Naming Conventions

### Python

- **Files**: `snake_case` (e.g., `api_client.py`)
- **Functions**: `snake_case` (e.g., `get_recommendations()`)
- **Classes**: `PascalCase` (e.g., `CognitoAuth`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `USERS_TABLE`)

### AWS Resources

- Use `kebab-case` with project prefix
- Examples: `SakeSensei-Users`, `sakesensei-recommendation`

### GraphQL

- **Types**: `PascalCase` (e.g., `User`, `Sake`)
- **Fields/Queries**: `camelCase` (e.g., `userId`, `getRecommendations`)

## Code Style

### Python

- Follow **PEP 8** style guide
- Use **type hints** for all function signatures
- Maximum line length: **100 characters**
- Add **docstrings** for all public functions and classes
- Use **Ruff** for linting and formatting

### ⚠️ Ruff Warnings Must Be Fixed

**MANDATORY**: All ruff warnings MUST be fixed before deployment. Do NOT ignore any warnings.

- `ARG002` (Unused arguments): Either use the argument or mark with `_ = arg_name`
- `F401` (Unused imports): Remove all unused imports
- `UP028` (yield over for loop): Use `yield from` instead of `for` loop with `yield`
- `SIM116` (if/elif chains): Can be ignored if code is more readable with if/elif
- All other warnings: Must be fixed

**Process**:
1. Run `uv run ruff check --fix` to auto-fix
2. Manually fix remaining warnings
3. Verify with `uv run ruff check` - MUST show "All checks passed!"
4. Only then proceed to deployment

### Other Formats

- **GraphQL**: 2 spaces indentation, PascalCase types, camelCase fields
- **YAML**: 2 spaces indentation, kebab-case keys
- **JSON**: 2 spaces indentation

## Environment Configuration

### ⚠️ MANDATORY: All Environment-Specific Settings in .env

**CRITICAL RULE**: All environment-specific configurations MUST be defined in the `.env` file. Never hardcode region names, endpoints, or account-specific values in source code.

#### Required Setup

1. **Copy `.env.example` to `.env`**:
   ```bash
   cp .env.example .env
   ```

2. **Configure all required variables** in `.env`:
   ```bash
   # AWS Configuration
   AWS_REGION=us-west-2                    # Required: Deployment region
   AWS_ACCOUNT_ID=123456789012             # Required: Your AWS account ID

   # Cognito (after CDK deployment)
   COGNITO_USER_POOL_ID=us-west-2_XXXXX    # Required
   COGNITO_CLIENT_ID=your-client-id        # Required

   # AgentCore (after setup scripts)
   AGENTCORE_GATEWAY_ID=your-gateway-id    # Required
   AGENTCORE_GATEWAY_URL=https://...       # Required
   AGENTCORE_MEMORY_ID=your-memory-id      # Required

   # Lambda ARNs (after CDK deployment)
   LAMBDA_RECOMMENDATION_ARN=arn:aws:lambda:...
   LAMBDA_PREFERENCE_ARN=arn:aws:lambda:...
   # ... (see .env.example for full list)
   ```

3. **Never commit `.env` file** (already in `.gitignore`)

#### Configuration Categories

| Category | Variables | Source |
|----------|-----------|--------|
| **AWS Core** | `AWS_REGION`, `AWS_ACCOUNT_ID` | Manual setup |
| **Cognito** | `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID` | From CDK outputs |
| **AgentCore** | `AGENTCORE_GATEWAY_ID`, `AGENTCORE_MEMORY_ID` | From setup scripts |
| **Lambda ARNs** | `LAMBDA_*_ARN` (5 functions) | From CDK outputs |
| **DynamoDB** | `DYNAMODB_*_TABLE` (4 tables) | From CDK outputs |
| **Features** | `FEATURE_*` flags | Optional configuration |

#### Region Configuration

**Default Region**: `us-west-2` (Oregon)

To deploy to a different region:
1. Update `AWS_REGION` in `.env`
2. Verify Bedrock Claude 4.5 Sonnet availability in target region
3. Update all region-specific URLs and endpoints
4. Re-deploy infrastructure with new region

**Supported Services by Region** (verify before changing):
- ✅ us-west-2: All services supported (recommended)
- ⚠️ Other regions: Check Bedrock model availability

#### Loading Configuration

All configuration is loaded through `streamlit_app/utils/config.py`:

```python
from streamlit_app.utils.config import config

# Access configuration
region = config.AWS_REGION
cognito_pool = config.COGNITO_USER_POOL_ID
gateway_url = config.AGENTCORE_GATEWAY_URL
```

**Configuration Validation**: On app startup, `config.validate()` checks for required variables.

#### Environment-Specific Files

| File | Purpose | Contains |
|------|---------|----------|
| `.env` | **Local development** | Your actual values (DO NOT COMMIT) |
| `.env.example` | **Template** | Example values with documentation |
| `copilot/*/manifest.yml` | **ECS deployment** | References to SSM parameters |
| `infrastructure/app.py` | **CDK deployment** | Reads from environment or uses defaults |

#### Deployment Checklist

- [ ] `.env` file created with all required variables
- [ ] CDK deployed and outputs recorded in `.env`
- [ ] AgentCore resources created and IDs added to `.env`
- [ ] SSM parameters configured for ECS (see `scripts/deploy/setup_ssm_parameters.sh`)
- [ ] No hardcoded regions, account IDs, or endpoints in source code

#### Troubleshooting

**Issue**: "Missing required configuration"
- **Solution**: Check `.env` file exists and contains all variables from `.env.example`

**Issue**: "Region mismatch errors"
- **Solution**: Ensure `AWS_REGION` matches in `.env`, CDK deployment, and all AWS resources

**Issue**: "AgentCore gateway not found"
- **Solution**: Run setup scripts and update `AGENTCORE_GATEWAY_ID` in `.env`

## Development Guidelines

### Error Handling

- Always catch specific exceptions before generic ones
- Log errors with context using Python logging module
- Return user-friendly error messages in Streamlit
- Use try-except blocks for all external API calls

### Logging

- Use Python's built-in `logging` module
- Set appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Include contextual information in logs
- Never log sensitive data (tokens, passwords)

### Environment Variables

**⚠️ CRITICAL: All environment-specific configuration MUST be in `.env` file**

- **Local Development**: Use `.env` file (never commit to git)
- **Production/ECS**: Use AWS Systems Manager Parameter Store
- **CI/CD**: Use GitHub Secrets and inject via workflows
- **Configuration Loading**: All code uses `streamlit_app/utils/config.py`

**Required Variables** (see `.env.example` for complete list):
- `AWS_REGION` - Deployment region
- `AWS_ACCOUNT_ID` - Your AWS account
- `COGNITO_USER_POOL_ID` - After CDK deployment
- `COGNITO_CLIENT_ID` - After CDK deployment
- `AGENTCORE_GATEWAY_ID` - After gateway creation
- `AGENTCORE_GATEWAY_URL` - Gateway endpoint
- `AGENTCORE_MEMORY_ID` - After memory creation
- `LAMBDA_*_ARN` - All 5 Lambda function ARNs

**Production Deployment**:
1. Store sensitive values in AWS Secrets Manager
2. Use SSM Parameter Store for non-sensitive config
3. Reference in `copilot/streamlit-app/manifest.yml`
4. See `scripts/deploy/setup_ssm_parameters.sh`

## Testing

### Testing Requirements

- **Unit Tests**: Use pytest with pytest-asyncio, 70% coverage minimum
- **Integration Tests**: Test Lambda + DynamoDB, Gateway tool invocations
- **E2E Tests**: Use Selenium/Playwright for Streamlit UI testing
- **Test Naming**: `test_<module_name>.py`

### Running Tests

```bash
uv run pytest                    # Run all tests
uv run pytest --cov              # Run with coverage
uv run pytest tests/unit/ -v     # Run specific test directory
```

## Security

### Required Security Practices

1. **Never commit secrets** - Use environment variables
2. **Validate all inputs** - Sanitize before processing
3. **Use IAM roles** - No hardcoded credentials
4. **Enable encryption** - DynamoDB and S3 at rest
5. **HTTPS only** - All communications over TLS
6. **Rate limiting** - Implement WAF rules
7. **Log security events** - Track auth failures

## Performance

### Optimization Guidelines

1. **DynamoDB**: Efficient key design, avoid scans
2. **Lambda**: Optimize memory, use connection pooling
3. **Streamlit**: Use `@st.cache_data` for expensive operations
4. **Bedrock**: Batch API calls when possible
5. **S3**: Use CloudFront CDN for image delivery

### Streaming Performance Targets

- **TTFT (Time to First Token)**: < 500ms
- **Token Throughput**: 20-50 tokens/second
- **Total Response Time**: < 3 seconds

## Deployment

### Deployment Workflow

1. **Infrastructure (IaC)**: Deploy DynamoDB, Lambda, S3, Cognito via AWS CDK
2. **Lambda Functions**: Package with `uv export` and deploy via CDK
3. **AgentCore Services**: Create Gateway, Memory, Identity via scripts
4. **Agent**: Deploy to Runtime with `agentcore launch`
5. **Frontend**: Build Docker image and deploy to ECS Fargate via Copilot CLI

### Key Commands

```bash
# Deploy infrastructure (CDK)
cd infrastructure
uv run cdk deploy --all

# Deploy agent
cd agent
uv run agentcore configure --entrypoint entrypoint.py
uv run agentcore launch

# Test agent
uv run agentcore invoke '{"prompt": "Recommend sake"}'

# Run app locally
uv run streamlit run streamlit_app/app.py

# Deploy Streamlit app (Copilot)
cd streamlit_app
copilot init --app sakesensei --name streamlit-app --type "Load Balanced Web Service" --dockerfile ./Dockerfile
copilot env init --name dev --profile default --default-config
copilot deploy --env dev
```

## Monitoring

### Monitoring Requirements

- **CloudWatch Logs**: All Lambda and agent execution logs
- **CloudWatch Metrics**: API latency, error rates, invocation counts
- **CloudWatch Alarms**: Alert on errors >5%, latency >3s
- **X-Ray**: Distributed tracing for performance analysis

## Git Workflow

### Workflow Requirements

- **Branching**: Use `feature/`, `bugfix/`, `hotfix/` prefixes
- **Commits**: Use conventional commit format
- **Pull Requests**: Required for all changes
- **Code Review**: At least one approval required

### Pre-commit Checklist

```bash
uv run ruff format .         # Format code
uv run ruff check --fix .    # Lint code
uv run mypy streamlit_app    # Type check
uv run pytest                # Run tests
```

## CI/CD Pipeline

### Pipeline Architecture

```
┌────────────────┐
│  Pull Request  │
└───────┬────────┘
        │
        ▼
┌────────────────────────────────────────┐
│  GitHub Actions: PR Checks             │
├────────────────────────────────────────┤
│  • Lint (ruff format, ruff check)     │
│  • Type check (mypy)                   │
│  • Unit tests (pytest)                 │
│  • Security scan (bandit)              │
│  • Docker build (validation)           │
│  • Agent local test                    │
└────────────────┬───────────────────────┘
                 │
                 ▼
         ┌──────────────┐
         │ Merge to Main│
         └──────┬───────┘
                │
                ▼
┌────────────────────────────────────────┐
│  GitHub Actions: Deploy to Staging     │
├────────────────────────────────────────┤
│  1. CDK Deploy (Infrastructure)        │
│  2. Lambda Deploy (Backend)            │
│  3. Gateway Update (AgentCore)         │
│  4. Agent Deploy (Runtime - Staging)   │
│  5. Docker Build & Push (ECR)          │
│  6. Copilot Deploy (ECS - Staging)     │
│  7. E2E Tests                          │
│  8. Slack Notification                 │
└────────────────┬───────────────────────┘
                 │
                 ▼
         ┌──────────────┐
         │Manual Approval│
         └──────┬────────┘
                │
                ▼
┌────────────────────────────────────────┐
│  GitHub Actions: Deploy to Production  │
├────────────────────────────────────────┤
│  1. Agent Deploy (Runtime - Prod)      │
│  2. Copilot Deploy (ECS - Prod)        │
│  3. Smoke Tests                        │
│  4. Team Notification                  │
└────────────────────────────────────────┘
```

### GitHub Actions Workflows

#### `.github/workflows/pr-checks.yml`

```yaml
name: Pull Request Checks

on:
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: uv run ruff format --check .
      - run: uv run ruff check .

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: uv run mypy streamlit_app backend

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: uv run pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: uv run bandit -r streamlit_app backend agent

  docker-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - name: Build Docker image
        working-directory: streamlit_app
        run: docker build -t sakesensei:pr-${{ github.event.pull_request.number }} .

  agent-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - name: Test agent locally
        working-directory: agent
        run: uv run pytest tests/test_agent_local.py
```

#### `.github/workflows/deploy-staging.yml`

```yaml
name: Deploy to Staging

on:
  push:
    branches: [main]

jobs:
  deploy-infra:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1
      - name: Deploy CDK stacks
        working-directory: infrastructure
        run: |
          uv sync
          uv run cdk deploy --all --require-approval never

  deploy-agent:
    needs: deploy-infra
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Deploy agent to Runtime
        working-directory: agent
        run: |
          uv sync
          uv run agentcore configure --entrypoint entrypoint.py
          uv run agentcore launch --environment staging

  deploy-frontend:
    needs: deploy-agent
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1
      - name: Install Copilot
        run: |
          curl -Lo copilot https://github.com/aws/copilot-cli/releases/latest/download/copilot-linux
          chmod +x copilot
          sudo mv copilot /usr/local/bin/copilot
      - name: Build and push Docker image
        run: |
          aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin ${{ secrets.ECR_REGISTRY }}
          cd streamlit_app
          docker build -t sakesensei:${{ github.sha }} .
          docker tag sakesensei:${{ github.sha }} ${{ secrets.ECR_REGISTRY }}/sakesensei:${{ github.sha }}
          docker tag sakesensei:${{ github.sha }} ${{ secrets.ECR_REGISTRY }}/sakesensei:latest
          docker push ${{ secrets.ECR_REGISTRY }}/sakesensei:${{ github.sha }}
          docker push ${{ secrets.ECR_REGISTRY }}/sakesensei:latest
      - name: Deploy to ECS via Copilot
        run: |
          copilot deploy --env dev --tag ${{ github.sha }}

  e2e-tests:
    needs: deploy-frontend
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - name: Run E2E tests
        run: uv run pytest tests/e2e/ --base-url ${{ secrets.STAGING_URL }}

  notify:
    needs: e2e-tests
    runs-on: ubuntu-latest
    steps:
      - name: Slack notification
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "✅ Staging deployment successful: ${{ github.sha }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

#### `.github/workflows/deploy-production.yml`

```yaml
name: Deploy to Production

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy (git SHA or tag)'
        required: true

jobs:
  approve:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: echo "Production deployment approved"

  deploy-agent:
    needs: approve
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.inputs.version }}
      - uses: astral-sh/setup-uv@v1
      - name: Deploy agent to production Runtime
        working-directory: agent
        run: |
          uv sync
          uv run agentcore launch --environment production

  deploy-frontend:
    needs: deploy-agent
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.inputs.version }}
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1
      - name: Install Copilot
        run: |
          curl -Lo copilot https://github.com/aws/copilot-cli/releases/latest/download/copilot-linux
          chmod +x copilot
          sudo mv copilot /usr/local/bin/copilot
      - name: Deploy to production ECS
        run: |
          copilot deploy --env prod --tag ${{ github.event.inputs.version }}

  smoke-tests:
    needs: deploy-frontend
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - name: Run smoke tests
        run: uv run pytest tests/smoke/ --base-url ${{ secrets.PRODUCTION_URL }}

  notify:
    needs: smoke-tests
    runs-on: ubuntu-latest
    steps:
      - name: Slack notification
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "🚀 Production deployment successful: ${{ github.event.inputs.version }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Rollback Procedures

#### Rollback ECS Service

```bash
# List recent revisions
copilot svc status --env prod

# Rollback to previous version
copilot svc rollback --env prod

# Or rollback to specific revision
copilot svc rollback --env prod --revision 5
```

#### Rollback Agent

```bash
cd agent

# List agent versions
uv run agentcore list-versions

# Rollback to previous version
uv run agentcore rollback --version <previous-version>
```

#### Rollback Infrastructure

```bash
cd infrastructure

# View stack changes
uv run cdk diff

# Rollback by redeploying previous code
git checkout <previous-commit>
uv run cdk deploy --all
```

### Environment Variables

#### GitHub Secrets Required

- `AWS_ACCESS_KEY_ID`: AWS access key for CI/CD
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for CI/CD
- `ECR_REGISTRY`: ECR registry URL (e.g., `123456789.dkr.ecr.ap-northeast-1.amazonaws.com`)
- `STAGING_URL`: Staging environment URL
- `PRODUCTION_URL`: Production environment URL
- `SLACK_WEBHOOK_URL`: Slack webhook for notifications

#### AWS Parameter Store (Runtime)

- `/sakesensei/dev/cognito_user_pool_id`
- `/sakesensei/dev/cognito_client_id`
- `/sakesensei/dev/agentcore_runtime_url`
- `/sakesensei/prod/cognito_user_pool_id`
- `/sakesensei/prod/cognito_client_id`
- `/sakesensei/prod/agentcore_runtime_url`

## Additional Guidelines

### Documentation

- Add docstrings to all public functions and classes
- Explain complex logic with comments
- Keep README up-to-date with setup instructions

### Accessibility

- Use semantic HTML elements in Streamlit
- Ensure WCAG AA color contrast compliance
- Test keyboard navigation
- Provide alt text for images

---

**For detailed implementation examples and code samples, see:**

- `REQUIREMENTS.md` - Requirements, data models, architecture details
- `DESIGN.md` - Detailed design patterns and implementation guide
- Official docs for technology-specific guidance
