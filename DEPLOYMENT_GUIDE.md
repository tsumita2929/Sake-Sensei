# Sake Sensei - デプロイメントガイド

## 📋 概要

Sake Sensei を Amazon Bedrock AgentCore + AWS ECS にデプロイする完全ガイド。

## 🏗️ アーキテクチャ

```
User → ALB → ECS (Streamlit) → AgentCore Runtime (Agent) → Bedrock Claude 4.5
                              ↘ AgentCore Gateway (MCP) → Lambda Functions
                                                        ↘ DynamoDB
```

### 主要コンポーネント

1. **Streamlit App** (ECS Fargate)
   - UI/UXレイヤー
   - AgentCore Runtime Client
   - Backend Helper (Gateway Client)

2. **AgentCore Runtime** (Agent)
   - Strands Agent
   - Native Tools (Image Recognition)
   - Gateway Tools経由でLambda呼び出し

3. **AgentCore Gateway** (MCP)
   - Lambda Functions をMCPツールとして公開
   - Recommendation, Preference, Tasting, Brewery

4. **Backend Services**
   - Lambda Functions (5つ)
   - DynamoDB (4 tables)
   - Cognito (Authentication)

## 🚀 デプロイ手順

### 前提条件

```bash
# 必要なツール
- AWS CLI v2
- Docker
- uv (Python package manager)
- jq (JSON parser)

# 環境変数
cp .env.example .env
vi .env  # 必須項目を設定
```

### Step 1: インフラデプロイ（初回のみ）

```bash
# DynamoDB, Lambda, Cognito
cd infrastructure
uv sync
uv run cdk deploy --all

# 出力値を .env に記録
# - COGNITO_USER_POOL_ID
# - COGNITO_CLIENT_ID
# - LAMBDA_*_ARN (5つ)
# - DYNAMODB_*_TABLE (4つ)
```

### Step 2: Agentデプロイ

```bash
# Agent to AgentCore Runtime
./scripts/deploy_agent.sh

# または手動:
cd agent
uv sync
uv run ruff format . && uv run ruff check .
uv run agentcore configure --entrypoint entrypoint.py
uv run agentcore launch --region us-west-2

# Runtime URLを .env に追加:
# AGENTCORE_RUNTIME_URL=https://agent-runtime-xxx.execute-api.us-west-2.amazonaws.com
```

### Step 3: Streamlitデプロイ

```bash
# Streamlit to ECS
./scripts/deploy.sh patch

# 手動の場合:
cd streamlit_app
docker build -t sakesensei:latest .
# ECRプッシュ & ECS更新
```

### Step 4: 動作確認

```bash
# Health Check
curl http://sakese-Publi-BG2ScFFG5nfS-804827597.us-west-2.elb.amazonaws.com

# E2Eテスト
cd tests/e2e
export BASE_URL=http://...
uv run pytest test_authentication.py -v
uv run pytest test_ai_chat.py -v
```

## 🔧 トラブルシューティング

### Agent デプロイエラー

```bash
# AWS認証確認
aws sts get-caller-identity

# 手動config作成
cd agent
cat > .agentcore.yaml <<EOF
version: "1.0"
entrypoint: entrypoint.py
runtime: python3.12
EOF
uv run agentcore launch --region us-west-2
```

### Runtime 接続エラー

```bash
# Runtime URL確認
echo $AGENTCORE_RUNTIME_URL

# 手動リクエスト
curl -X POST $AGENTCORE_RUNTIME_URL/invoke \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'

# フォールバックモード
# .env の AGENTCORE_RUNTIME_URL を空に設定
```

### Streamlit 起動エラー

```bash
# CloudWatch Logs確認
aws logs tail /ecs/sakesensei-streamlit --follow

# 環境変数確認
aws ecs describe-task-definition \
  --task-definition sakesensei-streamlit-app
```

## 📊 デプロイ後チェックリスト

- [ ] ECS Service が Running
- [ ] ALB Health Check が Healthy
- [ ] Cognito ログイン成功
- [ ] AI Chat 応答（Runtime経由）
- [ ] AI Chat 応答（Bedrock直接 fallback）
- [ ] Image Recognition 動作
- [ ] Recommendations 取得
- [ ] DynamoDB 記録保存

## 🔄 更新デプロイ

### コード変更

```bash
# Streamlit
uv run ruff format streamlit_app
uv run ruff check streamlit_app
./scripts/deploy.sh patch

# Agent
cd agent
uv run ruff format . && uv run ruff check .
./scripts/deploy_agent.sh
```

## 📝 環境変数

### 必須

| 変数 | 説明 | 例 |
|------|------|-----|
| `AWS_REGION` | リージョン | `us-west-2` |
| `AWS_ACCOUNT_ID` | アカウントID | `123456789012` |
| `COGNITO_USER_POOL_ID` | Cognito Pool | `us-west-2_XXXXX` |
| `COGNITO_CLIENT_ID` | Cognito Client | `abcdef123456` |

### AgentCore（推奨）

| 変数 | 説明 | 例 |
|------|------|-----|
| `AGENTCORE_RUNTIME_URL` | Runtime API | `https://agent-runtime-xxx...` |
| `AGENTCORE_GATEWAY_URL` | Gateway API | `https://gateway-xxx...` |
| `AGENTCORE_GATEWAY_ID` | Gateway ID | `gateway-12345` |

## 🎯 次のステップ

1. **モニタリング**: CloudWatch Dashboard, Alarms, X-Ray
2. **最適化**: Auto Scaling, CloudFront CDN
3. **セキュリティ**: WAF, Secrets Manager, VPC Endpoints
4. **CI/CD**: GitHub Actions, Blue/Green Deployment

## 📚 参考資料

- [Amazon Bedrock AgentCore](https://docs.aws.amazon.com/bedrock/agentcore/)
- [Strands Agents Framework](https://github.com/anthropics/strands)
- [AWS Copilot CLI](https://aws.github.io/copilot-cli/)
- [Streamlit Docs](https://docs.streamlit.io/)

---

**最終更新**: 2025-10-01 | **バージョン**: v0.1.0
