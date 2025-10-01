# Sake Sensei - セットアップガイド

Phase 4 (AgentCore統合) を開始する前に完了すべき環境設定。

## 📋 前提条件チェックリスト

### 1. ローカル開発環境

- [x] Python 3.13+ インストール済み
- [x] uv インストール済み (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [x] AWS CLI v2 インストール済み
- [x] Node.js 20+ インストール済み (CDK用)
- [ ] Docker Desktop インストール済み (Phase 6で必要)

### 2. AWS認証情報設定

#### 2.1 AWS CLIの設定

```bash
# AWS CLIで認証情報を設定
aws configure

# 入力内容:
AWS Access Key ID: [YOUR_ACCESS_KEY]
AWS Secret Access Key: [YOUR_SECRET_KEY]
Default region name: us-west-2
Default output format: json
```

#### 2.2 必要なIAM権限

デプロイユーザー/ロールに以下の権限が必要:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:*",
        "s3:*",
        "dynamodb:*",
        "cognito-idp:*",
        "lambda:*",
        "iam:*",
        "bedrock:*",
        "bedrock-agentcore-control:*",
        "logs:*",
        "ec2:DescribeAvailabilityZones"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. 環境変数設定

#### 3.1 .envファイル作成

```bash
# .env.exampleをコピー
cp .env.example .env

# 必須項目を編集
vi .env
```

#### 3.2 初期設定時の必須変数

```bash
# AWS基本設定
AWS_REGION=us-west-2
AWS_ACCOUNT_ID=093325005283  # ← あなたのAWSアカウントID

# アプリケーション設定
APP_ENV=dev
```

**AWSアカウントIDの確認方法:**
```bash
aws sts get-caller-identity --query Account --output text
```

---

## 🚀 Phase 4開始前の必須手順

### Step 1: CDKブートストラップ (初回のみ)

```bash
cd infrastructure

# us-west-2リージョンでブートストラップ
uv run cdk bootstrap

# 出力例:
# ✅ Environment aws://093325005283/us-west-2 bootstrapped.
```

**⚠️ 注意**: ブートストラップはAWSアカウントごとに1回だけ実行します。

### Step 2: インフラストラクチャのデプロイ

```bash
cd infrastructure

# すべてのCDKスタックをデプロイ
uv run cdk deploy --all

# 確認プロンプトで "y" を入力
```

**デプロイ対象 (4スタック):**
1. `SakeSensei-Dev-Storage` - S3バケット
2. `SakeSensei-Dev-Database` - DynamoDB 4テーブル
3. `SakeSensei-Dev-Auth` - Cognito User Pool
4. `SakeSensei-Dev-Lambda` - Lambda Layer + 5 Functions

**デプロイ所要時間**: 約10-15分

### Step 3: デプロイ結果の確認と環境変数更新

#### 3.1 Cognito User Pool情報の取得

```bash
# User Pool IDの取得
aws cognito-idp list-user-pools --max-results 10 --query 'UserPools[?Name==`SakeSensei-Users`].Id' --output text

# App Client IDの取得
USER_POOL_ID="us-west-2_XXXXXXXXX"  # ↑で取得したID
aws cognito-idp list-user-pool-clients --user-pool-id $USER_POOL_ID --query 'UserPoolClients[0].ClientId' --output text
```

#### 3.2 Lambda ARNの取得

```bash
# すべてのSake Sensei Lambda関数のARN取得
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `SakeSensei`)].FunctionArn' --output table
```

#### 3.3 .envファイル更新

取得した値を`.env`に追加:

```bash
# Cognito設定
COGNITO_REGION=us-west-2
COGNITO_USER_POOL_ID=us-west-2_XXXXXXXXX
COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxx

# Lambda ARN (デプロイ結果から取得)
LAMBDA_RECOMMENDATION_ARN=arn:aws:lambda:us-west-2:ACCOUNT:function:SakeSensei-Recommendation
LAMBDA_PREFERENCE_ARN=arn:aws:lambda:us-west-2:ACCOUNT:function:SakeSensei-Preference
LAMBDA_TASTING_ARN=arn:aws:lambda:us-west-2:ACCOUNT:function:SakeSensei-Tasting
LAMBDA_BREWERY_ARN=arn:aws:lambda:us-west-2:ACCOUNT:function:SakeSensei-Brewery
LAMBDA_IMAGE_RECOGNITION_ARN=arn:aws:lambda:us-west-2:ACCOUNT:function:SakeSensei-ImageRecognition
```

### Step 4: IAMロール作成 (AgentCore Gateway用)

#### 4.1 信頼ポリシー作成

`gateway-trust-policy.json` を作成:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

#### 4.2 権限ポリシー作成

`gateway-permissions-policy.json` を作成:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "arn:aws:lambda:us-west-2:*:function:SakeSensei-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-sonnet-4-5-v2:0"
      ]
    }
  ]
}
```

#### 4.3 ロール作成

```bash
# ロール作成
aws iam create-role \
  --role-name SakeSensei-AgentCore-Gateway-Role \
  --assume-role-policy-document file://gateway-trust-policy.json

# 権限ポリシーをアタッチ
aws iam put-role-policy \
  --role-name SakeSensei-AgentCore-Gateway-Role \
  --policy-name SakeSensei-Gateway-Permissions \
  --policy-document file://gateway-permissions-policy.json

# ロールARN取得
aws iam get-role \
  --role-name SakeSensei-AgentCore-Gateway-Role \
  --query 'Role.Arn' \
  --output text
```

#### 4.4 .envに追加

```bash
# Gateway IAMロール
GATEWAY_ROLE_ARN=arn:aws:iam::093325005283:role/SakeSensei-AgentCore-Gateway-Role
```

### Step 5: Bedrock AgentCore サービス確認

```bash
# AgentCoreサービスが利用可能か確認
aws bedrock-agentcore-control list-gateways --region us-west-2

# エラーが出る場合:
# - サービスがus-west-2で利用可能か確認
# - IAM権限を確認
# - Bedrockのモデルアクセス設定を確認
```

**⚠️ 注意**: Bedrock AgentCoreはプレビューサービスの可能性があります。利用できない場合は以下を確認:

1. AWS Bedrock コンソール → Model access → Claude 4.5 Sonnetを有効化
2. AgentCore機能へのアクセス権限を確認
3. 必要に応じてAWSサポートに問い合わせ

---

## ✅ 環境設定確認チェックリスト

Phase 4開始前に以下を確認:

- [ ] AWS CLI設定完了 (`aws sts get-caller-identity` が成功)
- [ ] .envファイルに `AWS_ACCOUNT_ID` 設定済み
- [ ] CDK bootstrap完了
- [ ] 4つのCDKスタックがデプロイ済み (`uv run cdk list` で確認)
- [ ] Cognito User Pool ID/Client ID取得済み
- [ ] Lambda関数5個のARN取得済み
- [ ] Gateway用IAMロール作成済み
- [ ] .envに全ての必須変数設定済み
- [ ] `bedrock-agentcore-control` サービスにアクセス可能

---

## 🚀 Phase 4開始コマンド

環境設定完了後、Phase 4を開始:

```bash
# Gateway作成
uv run python scripts/agentcore/create_gateway.py

# 成功すると:
# ✅ Gateway created successfully!
# Gateway ID: gw-xxxxxxxxxxxxx
# Gateway ARN: arn:aws:bedrock-agentcore:us-west-2:...
```

---

## 🐛 トラブルシューティング

### CDKデプロイエラー

```bash
# スタックの状態確認
aws cloudformation describe-stacks --query 'Stacks[?starts_with(StackName, `SakeSensei`)].{Name:StackName,Status:StackStatus}'

# スタック削除（必要な場合）
uv run cdk destroy SakeSensei-Dev-Lambda
```

### Cognito情報が見つからない

```bash
# すべてのUser Pool一覧
aws cognito-idp list-user-pools --max-results 20

# 特定のUser Pool詳細
aws cognito-idp describe-user-pool --user-pool-id us-west-2_XXXXXXXXX
```

### Lambda関数が見つからない

```bash
# Lambda関数一覧
aws lambda list-functions --query 'Functions[].FunctionName' --output table

# 特定の関数詳細
aws lambda get-function --function-name SakeSensei-Recommendation
```

### bedrock-agentcore-control が使えない

```bash
# AWS CLIのバージョン確認
aws --version  # 最新版にアップデート推奨

# サービスエンドポイント確認
aws bedrock-agentcore-control help

# リージョン別の利用可否を確認
# (ドキュメント確認が必要)
```

---

## 📚 参考資料

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS Cognito User Pools](https://docs.aws.amazon.com/cognito/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)

---

**最終更新**: 2025-09-30
**対象Phase**: Phase 4 (AgentCore統合)
**前提**: Phase 0-3完了済み