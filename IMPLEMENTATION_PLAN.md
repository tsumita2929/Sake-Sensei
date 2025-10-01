# Sake Sensei - AI-Driven Implementation Plan

## 概要

このドキュメントは、生成AI（Claude）を使用してSake Senseiを段階的に実装するための詳細な計画です。各タスクは小さな単位に分割され、実装後に全体計画を見直すプロセスを含みます。

## 実装原則

### 1. AI駆動開発プロセス

```
┌─────────────┐
│ Plan Review │ ←─────────────────┐
└──────┬──────┘                   │
       ▼                          │
┌─────────────┐                   │
│ Task Select │                   │
└──────┬──────┘                   │
       ▼                          │
┌─────────────┐                   │
│ AI Generate │                   │
└──────┬──────┘                   │
       ▼                          │
┌─────────────┐                   │
│   Validate  │                   │
└──────┬──────┘                   │
       ▼                          │
┌─────────────┐                   │
│   Commit    │                   │
└──────┬──────┘                   │
       ▼                          │
┌─────────────┐                   │
│ Update Plan ├───────────────────┘
└─────────────┘
```

### 2. タスク粒度の基準

- **1タスク = 1ファイル作成/編集**
- **実装時間: 5-15分**
- **テスト可能な最小単位**
- **独立してコミット可能**

## Phase 0: 基盤整備 (Foundation)

### 0.1 プロジェクト初期化
- [ ] **0.1.1** `pyproject.toml`作成 - 基本依存関係定義
- [ ] **0.1.2** `.gitignore`作成 - Python/AWS/IDE用設定
- [ ] **0.1.3** `.env.example`作成 - 必要な環境変数テンプレート
- [ ] **0.1.4** `uv sync`実行確認 - 依存関係インストール検証

### 0.2 開発環境設定
- [ ] **0.2.1** `.github/workflows`ディレクトリ作成
- [ ] **0.2.2** `pr-checks.yml`作成 - PRチェック用GitHub Actions
- [ ] **0.2.3** `.pre-commit-config.yaml`作成 - pre-commitフック設定
- [ ] **0.2.4** `Makefile`作成 - 開発コマンドショートカット

### 0.3 AWS CDK基盤
- [ ] **0.3.1** `infrastructure/app.py`作成 - CDKアプリエントリポイント
- [ ] **0.3.2** `infrastructure/cdk.json`作成 - CDK設定ファイル
- [ ] **0.3.3** `infrastructure/requirements.txt`作成 - CDK依存関係
- [ ] **0.3.4** CDKブートストラップ実行 - AWS環境準備

## Phase 1: データモデル & ストレージ層

### 1.1 DynamoDBテーブル定義
- [ ] **1.1.1** `infrastructure/stacks/__init__.py`作成
- [ ] **1.1.2** `infrastructure/stacks/database_stack.py`作成 - スタック基盤
- [ ] **1.1.3** UsersTable定義追加 - ユーザープロファイルテーブル
- [ ] **1.1.4** SakeMasterTable定義追加 - 日本酒マスターデータ
- [ ] **1.1.5** BreweryMasterTable定義追加 - 酒蔵マスターデータ
- [ ] **1.1.6** TastingRecordsTable定義追加 - テイスティング記録
- [ ] **1.1.7** GSI定義追加 - セカンダリインデックス

### 1.2 S3バケット定義
- [ ] **1.2.1** `infrastructure/stacks/storage_stack.py`作成 - S3スタック
- [ ] **1.2.2** 画像保存用バケット定義 - ラベル画像用
- [ ] **1.2.3** バケットポリシー定義 - アクセス制御
- [ ] **1.2.4** ライフサイクルルール定義 - 古い画像の自動削除

### 1.3 データモデルクラス
- [ ] **1.3.1** `backend/models/__init__.py`作成
- [ ] **1.3.2** `backend/models/user.py`作成 - Userモデルクラス
- [ ] **1.3.3** `backend/models/sake.py`作成 - Sakeモデルクラス
- [ ] **1.3.4** `backend/models/brewery.py`作成 - Breweryモデルクラス
- [ ] **1.3.5** `backend/models/tasting.py`作成 - TastingRecordモデル
- [ ] **1.3.6** `backend/models/validators.py`作成 - 入力検証ロジック

### 1.4 マスターデータ準備
- [ ] **1.4.1** `data/sake_master.json`作成 - サンプル日本酒データ(10件)
- [ ] **1.4.2** `data/brewery_master.json`作成 - サンプル酒蔵データ(5件)
- [ ] **1.4.3** `scripts/seed_data.py`作成 - データ投入スクリプト
- [ ] **1.4.4** データ投入テスト実行

## Phase 2: 認証基盤

### 2.1 Cognitoリソース定義
- [ ] **2.1.1** `infrastructure/stacks/auth_stack.py`作成 - 認証スタック
- [ ] **2.1.2** User Pool定義 - メール認証付き
- [ ] **2.1.3** User Pool Client定義 - アプリケーションクライアント
- [ ] **2.1.4** パスワードポリシー設定 - セキュリティ要件
- [ ] **2.1.5** MFAオプション設定

### 2.2 認証ヘルパー実装
- [ ] **2.2.1** `backend/auth/__init__.py`作成
- [ ] **2.2.2** `backend/auth/cognito_client.py`作成 - Cognito APIラッパー
- [ ] **2.2.3** `backend/auth/jwt_validator.py`作成 - JWT検証ロジック
- [ ] **2.2.4** `backend/auth/decorators.py`作成 - 認証デコレータ

## Phase 3: Lambda関数基盤

### 3.1 Lambda共通層
- [ ] **3.1.1** `backend/lambdas/layer/__init__.py`作成
- [ ] **3.1.2** `backend/lambdas/layer/logger.py`作成 - ロギング設定
- [ ] **3.1.3** `backend/lambdas/layer/response.py`作成 - レスポンス形式統一
- [ ] **3.1.4** `backend/lambdas/layer/error_handler.py`作成 - エラー処理
- [ ] **3.1.5** Lambdaレイヤー定義追加 (CDK)

### 3.2 Recommendation Lambda
- [ ] **3.2.1** `backend/lambdas/recommendation/handler.py`作成 - エントリポイント
- [ ] **3.2.2** `backend/lambdas/recommendation/algorithm.py`作成 - 推薦アルゴリズム基本実装
- [ ] **3.2.3** `backend/lambdas/recommendation/scorer.py`作成 - スコアリングロジック
- [ ] **3.2.4** `backend/lambdas/recommendation/requirements.txt`作成
- [ ] **3.2.5** Lambda関数定義追加 (CDK)
- [ ] **3.2.6** IAMロール定義追加

### 3.3 Preference Lambda
- [ ] **3.3.1** `backend/lambdas/preference/handler.py`作成
- [ ] **3.3.2** `backend/lambdas/preference/crud.py`作成 - CRUD操作
- [ ] **3.3.3** `backend/lambdas/preference/requirements.txt`作成
- [ ] **3.3.4** Lambda関数定義追加 (CDK)

### 3.4 Tasting Lambda
- [ ] **3.4.1** `backend/lambdas/tasting/handler.py`作成
- [ ] **3.4.2** `backend/lambdas/tasting/crud.py`作成
- [ ] **3.4.3** `backend/lambdas/tasting/analytics.py`作成 - 統計処理
- [ ] **3.4.4** `backend/lambdas/tasting/requirements.txt`作成
- [ ] **3.4.5** Lambda関数定義追加 (CDK)

### 3.5 Brewery Lambda
- [ ] **3.5.1** `backend/lambdas/brewery/handler.py`作成
- [ ] **3.5.2** `backend/lambdas/brewery/query.py`作成 - 検索ロジック
- [ ] **3.5.3** `backend/lambdas/brewery/requirements.txt`作成
- [ ] **3.5.4** Lambda関数定義追加 (CDK)

### 3.6 Image Recognition Lambda
- [ ] **3.6.1** `backend/lambdas/image_recognition/handler.py`作成
- [ ] **3.6.2** `backend/lambdas/image_recognition/bedrock_client.py`作成
- [ ] **3.6.3** `backend/lambdas/image_recognition/matcher.py`作成 - マッチングロジック
- [ ] **3.6.4** `backend/lambdas/image_recognition/requirements.txt`作成
- [ ] **3.6.5** Lambda関数定義追加 (CDK)

## Phase 4: AgentCore統合

### 4.1 AgentCore Gateway設定
- [ ] **4.1.1** `scripts/agentcore/__init__.py`作成
- [ ] **4.1.2** `scripts/agentcore/create_gateway.py`作成
- [ ] **4.1.3** `scripts/agentcore/add_gateway_targets.py`作成
- [ ] **4.1.4** Gateway作成スクリプト実行
- [ ] **4.1.5** Lambda関数をMCPツールとして登録

### 4.2 AgentCore Memory設定
- [ ] **4.2.1** `scripts/agentcore/create_memory.py`作成
- [ ] **4.2.2** Memory Store作成実行
- [ ] **4.2.3** Memory戦略設定 (SEMANTIC, USER_PREFERENCES, SUMMARY)

### 4.3 AgentCore Identity設定
- [ ] **4.3.1** `scripts/agentcore/setup_identity.py`作成
- [ ] **4.3.2** Cognito統合設定
- [ ] **4.3.3** OAuth 2.0設定確認

### 4.4 Strands Agent実装
- [ ] **4.4.1** `agent/__init__.py`作成
- [ ] **4.4.2** `agent/entrypoint.py`作成 - Runtime用エントリポイント
- [ ] **4.4.3** `agent/agent.py`作成 - Agent本体定義
- [ ] **4.4.4** `agent/system_prompt.py`作成 - システムプロンプト
- [ ] **4.4.5** `agent/memory_hook.py`作成 - Memory統合フック
- [ ] **4.4.6** `agent/tools/__init__.py`作成
- [ ] **4.4.7** `agent/tools/recommendation_tool.py`作成
- [ ] **4.4.8** `agent/requirements.txt`作成

### 4.5 Agent デプロイ
- [ ] **4.5.1** `agent/.agentcore.yaml`作成 - Agent設定
- [ ] **4.5.2** ローカルテスト実行
- [ ] **4.5.3** Runtime へのデプロイ (dev環境)

## Phase 5: Streamlit フロントエンド

### 5.1 Streamlit基本構成
- [ ] **5.1.1** `streamlit_app/__init__.py`作成
- [ ] **5.1.2** `streamlit_app/app.py`作成 - メインエントリポイント
- [ ] **5.1.3** `streamlit_app/config.py`作成 - 設定管理
- [ ] **5.1.4** `streamlit_app/.streamlit/config.toml`作成
- [ ] **5.1.5** `streamlit_app/requirements.txt`作成 (uv exportから生成)

### 5.2 認証コンポーネント
- [ ] **5.2.1** `streamlit_app/components/__init__.py`作成
- [ ] **5.2.2** `streamlit_app/components/auth.py`作成 - ログイン/サインアップUI
- [ ] **5.2.3** `streamlit_app/utils/__init__.py`作成
- [ ] **5.2.4** `streamlit_app/utils/session.py`作成 - セッション管理
- [ ] **5.2.5** `streamlit_app/utils/auth_helper.py`作成 - Cognito連携

### 5.3 AgentCore クライアント
- [ ] **5.3.1** `streamlit_app/components/agent_client.py`作成
- [ ] **5.3.2** ストリーミングレスポンス処理実装
- [ ] **5.3.3** エラーハンドリング実装

### 5.4 ページ実装: 好み調査
- [ ] **5.4.1** `streamlit_app/pages/__init__.py`作成
- [ ] **5.4.2** `streamlit_app/pages/1_🎯_Preference_Survey.py`作成
- [ ] **5.4.3** フォームコンポーネント実装
- [ ] **5.4.4** バリデーション実装
- [ ] **5.4.5** 送信処理実装

### 5.5 ページ実装: AI推薦
- [ ] **5.5.1** `streamlit_app/pages/2_🤖_AI_Recommendations.py`作成
- [ ] **5.5.2** チャットインターフェース実装
- [ ] **5.5.3** ストリーミング表示実装
- [ ] **5.5.4** `streamlit_app/components/sake_card.py`作成 - 酒カード表示

### 5.6 ページ実装: 評価
- [ ] **5.6.1** `streamlit_app/pages/3_⭐_Rating.py`作成
- [ ] **5.6.2** 評価フォーム実装
- [ ] **5.6.3** レビュー一覧表示実装

### 5.7 ページ実装: 画像認識
- [ ] **5.7.1** `streamlit_app/pages/4_📷_Image_Recognition.py`作成
- [ ] **5.7.2** 画像アップロードコンポーネント実装
- [ ] **5.7.3** 認識結果表示実装

### 5.8 ページ実装: 履歴
- [ ] **5.8.1** `streamlit_app/pages/5_📊_History.py`作成
- [ ] **5.8.2** テイスティング履歴表示実装
- [ ] **5.8.3** 統計グラフ実装
- [ ] **5.8.4** エクスポート機能実装

## Phase 6: コンテナ化とECSデプロイ

### 6.1 Docker設定
- [ ] **6.1.1** `streamlit_app/Dockerfile`作成
- [ ] **6.1.2** `.dockerignore`作成
- [ ] **6.1.3** `streamlit_app/docker-compose.yml`作成 (ローカルテスト用)
- [ ] **6.1.4** Dockerイメージビルドテスト

### 6.2 Copilot設定
- [ ] **6.2.1** `copilot/.workspace`作成
- [ ] **6.2.2** `copilot/environments/dev/addons/cf.yml`作成
- [ ] **6.2.3** `copilot/environments/dev/manifest.yml`作成
- [ ] **6.2.4** `copilot/streamlit-app/manifest.yml`作成
- [ ] **6.2.5** `copilot/streamlit-app/addons/alb.yml`作成

### 6.3 ECRとECSデプロイ
- [ ] **6.3.1** ECRリポジトリ作成
- [ ] **6.3.2** Dockerイメージプッシュ
- [ ] **6.3.3** Copilot環境作成 (dev)
- [ ] **6.3.4** Copilotサービスデプロイ
- [ ] **6.3.5** ヘルスチェック確認

## Phase 7: テスト実装

### 7.1 ユニットテスト基盤
- [ ] **7.1.1** `tests/__init__.py`作成
- [ ] **7.1.2** `tests/conftest.py`作成 - pytest設定
- [ ] **7.1.3** `tests/fixtures/__init__.py`作成
- [ ] **7.1.4** `tests/fixtures/users.py`作成 - テストデータ
- [ ] **7.1.5** `tests/fixtures/sake.py`作成

### 7.2 バックエンドユニットテスト
- [ ] **7.2.1** `tests/unit/__init__.py`作成
- [ ] **7.2.2** `tests/unit/test_models.py`作成
- [ ] **7.2.3** `tests/unit/test_auth.py`作成
- [ ] **7.2.4** `tests/unit/test_recommendation_algorithm.py`作成
- [ ] **7.2.5** `tests/unit/test_lambdas.py`作成

### 7.3 エージェントテスト
- [ ] **7.3.1** `tests/agent/__init__.py`作成
- [ ] **7.3.2** `tests/agent/test_agent_local.py`作成
- [ ] **7.3.3** `tests/agent/test_agent_runtime.py`作成

### 7.4 統合テスト
- [ ] **7.4.1** `tests/integration/__init__.py`作成
- [ ] **7.4.2** `tests/integration/test_lambda_dynamodb.py`作成
- [ ] **7.4.3** `tests/integration/test_cognito_flow.py`作成
- [ ] **7.4.4** `tests/integration/test_agentcore_gateway.py`作成

### 7.5 E2Eテスト
- [ ] **7.5.1** `tests/e2e/__init__.py`作成
- [ ] **7.5.2** `tests/e2e/test_user_journey.py`作成
- [ ] **7.5.3** `tests/e2e/test_recommendation_flow.py`作成
- [ ] **7.5.4** `tests/e2e/test_streaming.py`作成

### 7.6 スモークテスト
- [ ] **7.6.1** `tests/smoke/__init__.py`作成
- [ ] **7.6.2** `tests/smoke/test_health.py`作成
- [ ] **7.6.3** `tests/smoke/test_auth.py`作成
- [ ] **7.6.4** `tests/smoke/test_basic_flow.py`作成

## Phase 8: CI/CDパイプライン

### 8.1 GitHub Actions ワークフロー
- [ ] **8.1.1** `.github/workflows/pr-checks.yml`完成
- [ ] **8.1.2** `.github/workflows/deploy-staging.yml`作成
- [ ] **8.1.3** `.github/workflows/deploy-production.yml`作成
- [ ] **8.1.4** `.github/workflows/rollback.yml`作成

### 8.2 セキュリティスキャン
- [ ] **8.2.1** `.github/workflows/security-scan.yml`作成
- [ ] **8.2.2** Bandit設定
- [ ] **8.2.3** Safety設定
- [ ] **8.2.4** Trivy設定

## Phase 9: 監視とロギング

### 9.1 CloudWatch設定
- [ ] **9.1.1** `infrastructure/stacks/monitoring_stack.py`作成
- [ ] **9.1.2** ロググループ定義
- [ ] **9.1.3** メトリクスアラーム定義
- [ ] **9.1.4** ダッシュボード定義

### 9.2 X-Ray設定
- [ ] **9.2.1** Lambda関数にX-Ray有効化
- [ ] **9.2.2** トレーシング設定

## Phase 10: セキュリティ強化

### 10.1 WAF設定
- [ ] **10.1.1** `infrastructure/stacks/security_stack.py`作成
- [ ] **10.1.2** WAFルール定義
- [ ] **10.1.3** レート制限設定

### 10.2 Secrets Manager
- [ ] **10.2.1** API キー管理設定
- [ ] **10.2.2** ローテーション設定

## Phase 11: 本番環境準備

### 11.1 Production環境構築
- [ ] **11.1.1** `copilot/environments/prod/manifest.yml`作成
- [ ] **11.1.2** Production用パラメータ設定
- [ ] **11.1.3** Production環境デプロイ

### 11.2 ドメイン設定
- [ ] **11.2.1** Route 53設定
- [ ] **11.2.2** SSL証明書設定

## Phase 12: ドキュメント整備

### 12.1 ユーザードキュメント
- [ ] **12.1.1** `docs/user-guide.md`作成
- [ ] **12.1.2** `docs/api-reference.md`作成

### 12.2 運用ドキュメント
- [ ] **12.2.1** `docs/operations.md`作成
- [ ] **12.2.2** `docs/troubleshooting.md`作成

## 実装レビュープロセス

### 各タスク完了時のチェックリスト

1. **コード品質**
   - [ ] ruff formatでフォーマット済み
   - [ ] ruff checkでエラーなし
   - [ ] mypy型チェック通過

2. **テスト**
   - [ ] ユニットテスト作成/更新
   - [ ] テストカバレッジ70%以上

3. **ドキュメント**
   - [ ] docstring追加
   - [ ] 必要に応じてREADME更新

4. **セキュリティ**
   - [ ] センシティブ情報の確認
   - [ ] 入力検証実装

5. **計画見直し**
   - [ ] 完了タスクのマーク
   - [ ] 次タスクの詳細確認
   - [ ] 必要に応じて計画調整

## 進捗トラッキング

### Phase完了基準

- すべてのタスクにチェックマーク
- 統合テスト実行成功
- コードレビュー完了
- ドキュメント更新完了

### 全体進捗

```
Phase 0:  [          ] 0% (0/8)
Phase 1:  [          ] 0% (0/20)
Phase 2:  [          ] 0% (0/9)
Phase 3:  [          ] 0% (0/26)
Phase 4:  [          ] 0% (0/18)
Phase 5:  [          ] 0% (0/31)
Phase 6:  [          ] 0% (0/14)
Phase 7:  [          ] 0% (0/24)
Phase 8:  [          ] 0% (0/8)
Phase 9:  [          ] 0% (0/6)
Phase 10: [          ] 0% (0/5)
Phase 11: [          ] 0% (0/5)
Phase 12: [          ] 0% (0/4)
────────────────────────────────
Total:    [          ] 0% (0/178)
```

## AI実装ガイド

### タスク実装テンプレート

```markdown
## Task: [タスク番号] [タスク名]

### Input
- 依存タスク: [依存するタスク番号]
- 必要ファイル: [参照が必要なファイル]

### Output
- 作成/更新ファイル: [ファイルパス]
- 期待される機能: [機能説明]

### Implementation
[具体的な実装内容をAIに指示]

### Validation
- [ ] ファイル作成/更新完了
- [ ] シンタックスエラーなし
- [ ] インポート解決
- [ ] 基本動作確認
```

### AIプロンプト例

```
タスク0.1.1を実装してください:
- pyproject.tomlを作成
- Python 3.12を指定
- 必要な基本依存関係を含める
  - streamlit
  - boto3
  - pydantic
  - pytest (dev)
  - ruff (dev)
  - mypy (dev)
- uv package managerで管理可能な形式
```

## 次のステップ

1. **Phase 0.1.1から開始**
2. **各タスク完了後にレビュー**
3. **5タスク完了ごとに全体計画見直し**
4. **Phase完了時に統合テスト実施**