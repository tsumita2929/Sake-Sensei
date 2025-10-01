# Sake Sensei - Infrastructure

AWS CDK を使用したインフラストラクチャ定義。

**⚠️ デプロイリージョン**: このプロジェクトは **us-west-2 (Oregon)** にデプロイします。

## 📋 前提条件

- Python 3.13+
- Node.js 20+ (AWS CDK CLI用)
- AWS CLI v2
- uv (パッケージマネージャー)
- AWS アカウントと適切な権限

## 🚀 セットアップ

### 1. AWS認証情報の設定

```bash
# AWS CLIで認証情報を設定
aws configure

# または環境変数で設定
export AWS_ACCOUNT_ID="093325005283"
export AWS_REGION="us-west-2"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

### 2. 依存関係のインストール

```bash
cd infrastructure
uv sync
```

### 3. CDK ブートストラップ (初回のみ)

**⚠️ 重要**: これは AWS アカウントごとに **1回だけ** 実行します。

```bash
cd infrastructure

# デフォルトリージョン (us-west-2) でブートストラップ
uv run cdk bootstrap

# 特定のアカウント/リージョンを指定
uv run cdk bootstrap aws://093325005283/us-west-2

# 複数リージョンでブートストラップ (必要な場合)
uv run cdk bootstrap aws://093325005283/us-east-1
```

**ブートストラップで作成されるリソース:**
- CDKToolkit CloudFormation スタック
- S3 バケット (CDK アセット保存用)
- ECR リポジトリ (Docker イメージ用)
- IAM ロール (デプロイ用)

## 📦 スタック構成

このプロジェクトは3つのCDKスタックで構成されます:

### 1. Storage Stack (`SakeSensei-Dev-Storage`)
- S3 バケット (画像保存用)
- ライフサイクルルール
- CORS 設定

**リソース:**
- `sakesensei-images-{account_id}` - 画像保存バケット

### 2. Database Stack (`SakeSensei-Dev-Database`)
- DynamoDB テーブル (4個)
- グローバルセカンダリインデックス (GSI)

**テーブル:**
- `SakeSensei-Users` - ユーザープロファイル
- `SakeSensei-SakeMaster` - 日本酒マスターデータ
- `SakeSensei-BreweryMaster` - 酒蔵マスターデータ
- `SakeSensei-TastingRecords` - テイスティング記録

### 3. Auth Stack (`SakeSensei-Dev-Auth`)
- Cognito User Pool
- User Pool Client
- パスワードポリシー、MFA設定

**リソース:**
- `SakeSensei-Users-{account_id}` - User Pool
- `SakeSensei-Streamlit` - App Client

## 🔍 スタックの検証

デプロイ前にスタック定義を検証:

```bash
cd infrastructure

# CloudFormation テンプレート生成
uv run cdk synth

# 特定のスタックのみ生成
uv run cdk synth SakeSensei-Dev-Database

# 差分確認 (既存スタックとの比較)
uv run cdk diff
```

## 🚢 デプロイ

### すべてのスタックをデプロイ

```bash
cd infrastructure
uv run cdk deploy --all
```

### 個別スタックのデプロイ

```bash
# Storage スタックのみ
uv run cdk deploy SakeSensei-Dev-Storage

# Database スタックのみ
uv run cdk deploy SakeSensei-Dev-Database

# Auth スタックのみ
uv run cdk deploy SakeSensei-Dev-Auth
```

### 確認なしデプロイ (CI/CD用)

```bash
uv run cdk deploy --all --require-approval never
```

## 🗑️ スタックの削除

⚠️ **注意**: 本番環境では実行しないでください。

```bash
cd infrastructure

# すべてのスタックを削除
uv run cdk destroy --all

# 特定のスタックのみ削除
uv run cdk destroy SakeSensei-Dev-Database
```

## 📊 デプロイ後の確認

### DynamoDB テーブル確認

```bash
# テーブル一覧
aws dynamodb list-tables

# 特定テーブルの詳細
aws dynamodb describe-table --table-name SakeSensei-Users
```

### S3 バケット確認

```bash
# バケット一覧
aws s3 ls

# バケット詳細
aws s3 ls s3://sakesensei-images-{account_id}/
```

### Cognito User Pool 確認

```bash
# User Pool 一覧
aws cognito-idp list-user-pools --max-results 10

# User Pool 詳細
aws cognito-idp describe-user-pool --user-pool-id {pool_id}
```

## 🔐 セキュリティ

### IAM 権限

CDK デプロイに必要な最小権限:

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
        "iam:*",
        "ssm:GetParameter"
      ],
      "Resource": "*"
    }
  ]
}
```

### 本番環境の推奨設定

1. **Removal Policy**: `RETAIN` に設定 (データ保護)
2. **Encryption**: すべてのリソースで有効化済み
3. **Point-in-Time Recovery**: DynamoDB で有効化済み
4. **Versioning**: S3 バケットで検討
5. **MFA**: Cognito で有効化推奨

## 🐛 トラブルシューティング

### CDK コマンドが失敗する

```bash
# Node.js バージョン確認 (20.x 推奨)
node --version

# CDK バージョン確認
npx aws-cdk --version

# キャッシュクリア
rm -rf cdk.out
uv run cdk synth
```

### ブートストラップエラー

```bash
# 既存の CDKToolkit スタックを削除
aws cloudformation delete-stack --stack-name CDKToolkit

# 再度ブートストラップ
uv run cdk bootstrap
```

### デプロイ時のロールエラー

```bash
# 信頼ポリシーを再設定
uv run cdk bootstrap --trust {account_id}
```

## 📚 参考資料

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [CDK Python API Reference](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Cognito User Pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html)

## 📝 環境変数

デプロイ時に使用される環境変数:

```bash
# 必須
AWS_ACCOUNT_ID=093325005283
AWS_REGION=us-west-2

# オプション (デフォルト: dev)
APP_ENV=dev  # または prod, staging
```

## 🔄 CI/CD での使用

GitHub Actions での例:

```yaml
- name: CDK Deploy
  run: |
    cd infrastructure
    uv run cdk deploy --all --require-approval never
  env:
    AWS_ACCOUNT_ID: ${{ secrets.AWS_ACCOUNT_ID }}
    AWS_REGION: us-west-2
```

詳細は `.github/workflows/deploy-staging.yml` を参照。