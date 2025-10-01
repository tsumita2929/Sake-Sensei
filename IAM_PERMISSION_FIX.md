# IAM Permission修正完了レポート

**実施日時**: 2025-10-01 10:50 UTC
**問題**: StreamlitアプリからLambda呼び出しでAccessDeniedエラー

## ❌ 発生したエラー

```
AccessDeniedException: User: arn:aws:sts::047786098634:assumed-role/sakesensei-dev-streamlit-app-TaskRole-TLgOqA4dIuux/xxx
is not authorized to perform: lambda:InvokeFunction on resource: arn:aws:lambda:us-west-2:047786098634:function:SakeSensei-Preference
because no identity-based policy allows the lambda:InvokeFunction action
```

## 🔍 根本原因

### Lambda関数の命名規則ミスマッチ
- **実際のLambda関数名**: `SakeSensei-*` （大文字S）
- **IAMポリシーのパターン**: `sakesensei-*` （小文字s）

### Lambda関数一覧
```
SakeSensei-Recommendation
SakeSensei-Preference
SakeSensei-Tasting
SakeSensei-Brewery
SakeSensei-ImageRecognition
SakeSensei-AgentCoreRuntime
```

### 既存のIAMポリシー（v1）
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "InvokeLambdaFunctions",
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction",
                "lambda:InvokeAsync"
            ],
            "Resource": [
                "arn:aws:lambda:us-west-2:047786098634:function:sakesensei-*"
            ]
        }
    ]
}
```

**問題点**: `sakesensei-*` パターンでは `SakeSensei-*` 関数にマッチしない（大文字小文字区別）

## ✅ 解決方法

### 更新したIAMポリシー（v2）

**ポリシーARN**: `arn:aws:iam::047786098634:policy/sakesensei-dev-streamlit-app-AddonsStack-1WCC7XE96E2A1-LambdaInvokePolicy-tWQZkbh5ET1I`

**新しいポリシー内容**:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "InvokeLambdaFunctions",
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction",
                "lambda:InvokeAsync"
            ],
            "Resource": [
                "arn:aws:lambda:us-west-2:047786098634:function:sakesensei-*",
                "arn:aws:lambda:us-west-2:047786098634:function:SakeSensei-*"
            ]
        }
    ]
}
```

**変更点**:
- ✅ `SakeSensei-*` パターンを追加
- ✅ 両方の命名規則（大文字・小文字）をサポート

### 実施したコマンド

```bash
# 1. IAMポリシー新バージョン作成
aws iam create-policy-version \
  --policy-arn arn:aws:iam::047786098634:policy/sakesensei-dev-streamlit-app-AddonsStack-1WCC7XE96E2A1-LambdaInvokePolicy-tWQZkbh5ET1I \
  --policy-document file:///tmp/lambda-invoke-policy.json \
  --set-as-default

# 2. ECSサービス再デプロイ（新ポリシー反映）
aws ecs update-service \
  --cluster sakesensei-dev-Cluster-RTWl4gZThPq4 \
  --service sakesensei-dev-streamlit-app-Service-IYtH6sHrR5S3 \
  --force-new-deployment
```

## 📊 修正結果

### IAMポリシー
- **バージョン**: v1 → v2
- **デフォルトバージョン**: v2
- **許可リソース**:
  - ✅ `arn:aws:lambda:us-west-2:047786098634:function:sakesensei-*`
  - ✅ `arn:aws:lambda:us-west-2:047786098634:function:SakeSensei-*`

### ECSデプロイ
- **Status**: COMPLETED
- **Running Tasks**: 1/1
- **Rollout State**: COMPLETED

### Lambda呼び出しテスト
```
✅ Lambda invoke successful!
Status Code: 200
Function: SakeSensei-Preference
```

**AccessDeniedエラー解決確認済み**

## 🔧 影響を受けたリソース

### IAMロール
- **Role Name**: `sakesensei-dev-streamlit-app-TaskRole-TLgOqA4dIuux`
- **Role ARN**: `arn:aws:iam::047786098634:role/sakesensei-dev-streamlit-app-TaskRole-TLgOqA4dIuux`
- **使用サービス**: ECS Fargate (Streamlit App)

### Lambda関数（全5関数がアクセス可能に）
1. `SakeSensei-Recommendation` ✅
2. `SakeSensei-Preference` ✅
3. `SakeSensei-Tasting` ✅
4. `SakeSensei-Brewery` ✅
5. `SakeSensei-ImageRecognition` ✅

## 📝 今後の推奨事項

### 命名規則の統一
- **Lambda関数**: 現在は `SakeSensei-*` （大文字S）
- **他のリソース**: `sakesensei-*` （小文字s）
- **推奨**: どちらかに統一するか、両方のパターンを常にサポート

### IAMポリシー管理
- CloudFormation/CDKでポリシーを管理する場合、両方のパターンを含める
- 手動作成の場合、命名規則を事前確認

### テスト改善
- Lambda呼び出しの統合テストを追加
- IAMポリシー変更時の権限確認を自動化

## ✅ 完了確認

- [x] IAMポリシーv2作成（両方のパターンを許可）
- [x] デフォルトバージョンをv2に設定
- [x] ECSサービス再デプロイ
- [x] デプロイ完了確認（COMPLETED）
- [x] Lambda呼び出しテスト成功

---

**修正担当**: Claude Code Assistant
**完了日時**: 2025-10-01 10:50 UTC
