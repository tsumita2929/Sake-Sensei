# Sake Sensei - Deployment Guide

このガイドでは、Sake SenseiアプリケーションをAWS ECS (Fargate) にデプロイする手順を説明します。

## 前提条件

### 必要なツール

- [AWS CLI](https://aws.amazon.com/cli/) v2.x以降
- [AWS Copilot CLI](https://aws.github.io/copilot-cli/) v1.30以降
- [Docker](https://www.docker.com/) v20.x以降
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### AWS認証情報

```bash
# AWS認証情報が設定されていることを確認
aws sts get-caller-identity

# 出力例:
# {
#     "UserId": "AIDAXXXXXXXXXXXXXXXXX",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-user"
# }
```

### 環境変数の準備

`.env.example`を参考に`.env`ファイルを作成し、以下の値を設定してください：

```bash
# AWS設定
AWS_REGION=us-west-2
AWS_ACCOUNT_ID=your-aws-account-id

# Cognito設定（Phase 2で取得済み）
COGNITO_USER_POOL_ID=us-west-2_XXXXXXXXX
COGNITO_CLIENT_ID=your-cognito-client-id
COGNITO_CLIENT_SECRET=your-cognito-client-secret

# Lambda ARN（Phase 3で取得済み）
LAMBDA_RECOMMENDATION_ARN=arn:aws:lambda:...
LAMBDA_PREFERENCE_ARN=arn:aws:lambda:...
LAMBDA_TASTING_ARN=arn:aws:lambda:...
LAMBDA_BREWERY_ARN=arn:aws:lambda:...
LAMBDA_IMAGE_RECOGNITION_ARN=arn:aws:lambda:...

# AgentCore設定（Phase 4で取得済み）
AGENTCORE_GATEWAY_ID=your-gateway-id
AGENTCORE_RUNTIME_URL=https://agent-runtime.bedrock.amazonaws.com
AGENTCORE_GATEWAY_URL=https://gateway.bedrock.amazonaws.com
```

## デプロイ手順

### Step 1: インフラストラクチャのデプロイ

CDKスタックをデプロイします（まだ完了していない場合）：

```bash
cd infrastructure
uv run cdk deploy --all

# 以下のスタックがデプロイされます:
# - SakeSensei-Storage: DynamoDB, S3
# - SakeSensei-Auth: Cognito User Pool
# - SakeSensei-Database: DynamoDB追加テーブル
# - SakeSensei-Lambda: Lambda関数（5個）
```

### Step 2: AWS Systems Manager Parameter Storeに環境変数を保存

Copilotがシークレットを読み込めるように、Parameter Storeに保存します：

```bash
# 環境変数をParameter Storeに保存
aws ssm put-parameter \
  --name "/copilot/sakesensei/dev/secrets/COGNITO_USER_POOL_ID" \
  --value "YOUR_USER_POOL_ID" \
  --type "String"

aws ssm put-parameter \
  --name "/copilot/sakesensei/dev/secrets/COGNITO_CLIENT_ID" \
  --value "YOUR_CLIENT_ID" \
  --type "String"

aws ssm put-parameter \
  --name "/copilot/sakesensei/dev/secrets/COGNITO_CLIENT_SECRET" \
  --value "YOUR_CLIENT_SECRET" \
  --type "SecureString"

aws ssm put-parameter \
  --name "/copilot/sakesensei/dev/secrets/AGENTCORE_RUNTIME_URL" \
  --value "https://agent-runtime.bedrock.amazonaws.com" \
  --type "String"

aws ssm put-parameter \
  --name "/copilot/sakesensei/dev/secrets/AGENTCORE_GATEWAY_URL" \
  --value "https://gateway.bedrock.amazonaws.com" \
  --type "String"

aws ssm put-parameter \
  --name "/copilot/sakesensei/dev/secrets/AGENTCORE_GATEWAY_ID" \
  --value "YOUR_GATEWAY_ID" \
  --type "String"

# Lambda ARNsも同様に保存
aws ssm put-parameter \
  --name "/copilot/sakesensei/dev/secrets/LAMBDA_RECOMMENDATION_ARN" \
  --value "YOUR_LAMBDA_ARN" \
  --type "String"

# 残りのLambda ARNsも同様に保存...
```

または、一括設定スクリプトを使用：

```bash
# スクリプトに実行権限を付与
chmod +x scripts/deploy/setup_ssm_parameters.sh

# スクリプトを実行
./scripts/deploy/setup_ssm_parameters.sh dev
```

### Step 3: Copilot初期化

```bash
# Copilotアプリケーションを初期化（初回のみ）
copilot app init sakesensei

# 開発環境を作成（初回のみ）
copilot env init --name dev \
  --profile default \
  --default-config

# 環境をデプロイ
copilot env deploy --name dev
```

### Step 4: Dockerイメージのビルドとプッシュ

```bash
# ECRにイメージをプッシュ
chmod +x scripts/deploy/push_to_ecr.sh
./scripts/deploy/push_to_ecr.sh v1.0.0
```

または、手動でプッシュ：

```bash
# ECRにログイン
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-west-2.amazonaws.com

# イメージをビルド
cd streamlit_app
docker build -t sakesensei:v1.0.0 .

# タグ付け
docker tag sakesensei:v1.0.0 \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-west-2.amazonaws.com/sakesensei:v1.0.0

# プッシュ
docker push \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-west-2.amazonaws.com/sakesensei:v1.0.0
```

### Step 5: Copilotサービスの初期化とデプロイ

```bash
# サービスを初期化（初回のみ）
copilot svc init \
  --name streamlit-app \
  --svc-type "Load Balanced Web Service" \
  --dockerfile ./streamlit_app/Dockerfile

# サービスをデプロイ
copilot svc deploy \
  --name streamlit-app \
  --env dev \
  --tag v1.0.0
```

### Step 6: デプロイの確認

```bash
# デプロイ状態を確認
copilot svc status --name streamlit-app --env dev

# サービスログを確認
copilot svc logs --name streamlit-app --env dev --follow

# サービスURLを取得
copilot svc show --name streamlit-app --env dev
```

## トラブルシューティング

### サービスが起動しない場合

```bash
# ECS タスクのログを確認
copilot svc logs --name streamlit-app --env dev --since 1h

# ECS タスク定義を確認
aws ecs describe-task-definition \
  --task-definition sakesensei-dev-streamlit-app \
  --query 'taskDefinition.containerDefinitions[0]'
```

### ヘルスチェックが失敗する場合

```bash
# コンテナ内でヘルスチェックエンドポイントをテスト
copilot svc exec --name streamlit-app --env dev \
  --command "curl -f http://localhost:8501/_stcore/health"
```

### IAM権限エラーの場合

`copilot/streamlit-app/addons/iam-policy.yml`を確認し、必要な権限が付与されているか確認してください。

## アップデート手順

### コードの更新

```bash
# 1. コードを更新
git pull origin main

# 2. 新しいイメージをビルド・プッシュ
./scripts/deploy/push_to_ecr.sh v1.0.1

# 3. サービスを再デプロイ
copilot svc deploy --name streamlit-app --env dev --tag v1.0.1
```

### 環境変数の更新

```bash
# Parameter Storeの値を更新
aws ssm put-parameter \
  --name "/copilot/sakesensei/dev/secrets/COGNITO_CLIENT_ID" \
  --value "NEW_CLIENT_ID" \
  --type "String" \
  --overwrite

# サービスを再起動（環境変数を再読み込み）
copilot svc deploy --name streamlit-app --env dev --force
```

## ロールバック

```bash
# 以前のバージョンにロールバック
copilot svc deploy --name streamlit-app --env dev --tag v1.0.0
```

## リソースのクリーンアップ

```bash
# サービスを削除
copilot svc delete --name streamlit-app --env dev

# 環境を削除
copilot env delete --name dev

# アプリケーションを削除
copilot app delete

# CDKスタックを削除
cd infrastructure
uv run cdk destroy --all
```

## 本番環境へのデプロイ

本番環境へのデプロイ手順：

```bash
# 本番環境を作成
copilot env init --name prod --profile default --prod

# 本番環境用のParameter Storeを設定
./scripts/deploy/setup_ssm_parameters.sh prod

# 本番環境にデプロイ
copilot env deploy --name prod
copilot svc deploy --name streamlit-app --env prod --tag v1.0.0
```

## モニタリングとログ

### CloudWatch Logs

```bash
# ログストリームを確認
copilot svc logs --name streamlit-app --env dev --follow
```

### CloudWatch Metrics

```bash
# CloudWatch コンソールでメトリクスを確認
# https://console.aws.amazon.com/cloudwatch/
```

### X-Ray トレーシング

Copilotは自動的にX-Rayトレーシングを有効化します。

## セキュリティ考慮事項

1. **HTTPS通信**: ALBは自動的にHTTPSリスナーを設定します
2. **シークレット管理**: すべての機密情報はParameter Store（SecureString）に保存
3. **IAM最小権限**: addonsで定義されたポリシーは最小権限の原則に従う
4. **VPC分離**: ECSタスクはプライベートサブネットで実行

## 参考リンク

- [AWS Copilot CLI ドキュメント](https://aws.github.io/copilot-cli/)
- [Streamlit ドキュメント](https://docs.streamlit.io/)
- [Amazon ECS ドキュメント](https://docs.aws.amazon.com/ecs/)
- [AWS CDK ドキュメント](https://docs.aws.amazon.com/cdk/)