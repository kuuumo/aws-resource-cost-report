# AWS リソース・コスト レポート

AWSのリソース利用状況と費用を定期的に調査し、マークダウン形式でレポートを生成するツールです。

## 概要

本ツールは以下の機能を提供します：

- AWS Cost Explorer APIを使用して、課金されているすべてのサービスとリソースごとのコスト情報を自動検出・取得
- 検出されたリソースに対して適切なAWS SDKを使って詳細情報を動的に収集
- 取得したデータを分析し、リソースタイプ、インスタンスタイプ、リージョンごとのコスト分析
- 定期的なレポート生成（GitHub Actionsによる自動実行）
- マークダウン形式でのレポート出力

本ツールの特徴として、**明示的に指定していないAWSサービスも自動的に検出・収集**するため、見過ごされがちなリソースも可視化できます。

## 前提条件

- AWSアカウントへのアクセス権限（ローカルテストモードの場合は不要）
- 適切なIAMポリシー設定（Cost Explorer, その他必要なAWSサービスへのアクセス）
- GitHub ActionsでのOICD認証設定
- Python 3.6以上
- asdf（Pythonバージョン管理）
- Task CLI（タスク実行）

## セットアップと使用方法

このプロジェクトはTaskfileを使用して操作を簡素化しています。
詳細な環境構築手順は[セットアップガイド](setup-guide.md)を参照してください。

### インストールと準備

```bash
# 1. Task CLIのインストール（Homebrewを使用）
brew install go-task/tap/go-task

# 2. プロジェクトディレクトリに移動
cd /path/to/aws-resource-cost-report

# 3. セットアップを実行（asdfとvenvを使用）
task setup
```

### プロジェクトの実行

```bash
# AWSアクセス権がある環境で実行
task run
```

### その他のタスク

```bash
# 依存パッケージの更新
task update-deps

# 生成されたレポートファイルのクリーンアップ
task clean
```

生成されたレポートは `reports/` ディレクトリに保存されます。

### AWS側の設定 (OIDC認証)

GitHub ActionsからAWSリソースへ安全にアクセスするために、OIDC (OpenID Connect) 認証を設定します。

#### IAMアイデンティティプロバイダーの作成

1. AWSコンソールにログインし、IAMコンソールに移動します。
2. 左側のナビゲーションメニューから「アイデンティティプロバイダー」を選択します。
3. 「プロバイダーを追加」をクリックし、以下の情報を入力します:
   - プロバイダータイプ: OpenID Connect
   - プロバイダーのURL: `https://token.actions.githubusercontent.com`
   - 対象者: `sts.amazonaws.com`
4. 「プロバイダーを追加」をクリックして保存します。

#### IAMロールの作成

1. IAMコンソールから「ロール」を選択し、「ロールの作成」をクリックします。
2. 信頼されたエンティティタイプとして「ウェブアイデンティティ」を選択します。
3. 以下の情報を設定します:
   - アイデンティティプロバイダー: `token.actions.githubusercontent.com`
   - 対象者: `sts.amazonaws.com`
   - GitHub組織/リポジトリ: あなたのリポジトリパス（例: `your-org/aws-resource-cost-report`）
4. 「次へ」をクリックし、以下のAWSマネージドポリシーをアタッチします:
   - `ReadOnlyAccess`（基本的な読み取り権限として）
5. さらに、以下のカスタムポリシーを作成してアタッチします（Cost Explorerへのアクセス用）:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ce:GetCostAndUsage"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

6. ロール名（例: `GitHubActionsAWSReportRole`）を入力し、ロールを作成します。
7. 作成したロールのARNをメモします（例: `arn:aws:iam::123456789012:role/GitHubActionsAWSReportRole`）。

### GitHubリポジトリの設定

1. このリポジトリをクローンまたはフォークします。
2. GitHub リポジトリの `Settings > Secrets and variables > Actions` に移動します。
3. 「Variables」タブで以下の変数を追加します：
   - `AWS_ROLE_ARN`: 上記で作成したIAMロールのARN
   - `AWS_REGION`: 使用するAWSリージョン（例：`ap-northeast-1`）

4. 必要に応じて `.github/workflows/generate-report.yml` ファイルの実行スケジュールを調整します。

### GitHub Actionsによる自動実行

- デフォルトでは毎週月曜日の午前9時（UTC）に自動実行されます。
- GitHub リポジトリの "Actions" タブから手動で実行することもできます。
- 生成されたレポートは `reports/` ディレクトリに保存され、コミットされます。

## レポートの内容

生成されるレポートには以下の情報が含まれます：

1. **概要**
   - 総コスト
   - 前月比
   - 最もコストがかかっているサービス・リソース

2. **サービス別コスト内訳**
   - EC2, RDS, S3などのサービス別コスト
   - 前月比の増減

3. **リソース詳細**
   - 検出されたすべてのAWSリソースの情報（EC2、RDS、S3、DynamoDB、Lambda、ECS、EKSなど）
   - インスタンスタイプ、リージョン、ステータスなどの詳細情報
   - 利用開始日
   - 月間コスト

4. **コスト最適化の推奨事項**
   - 低利用リソースの特定
   - コスト削減のための推奨事項

5. **未カバーリソース**
   - 課金されているが詳細情報を収集できないリソースのリスト
   - 対応する推定コスト

## カスタマイズ

- `config.yml` ファイルを編集することで、レポートの内容やフォーマットをカスタマイズできます。
- 追加のAWSサービスも自動的に検出・収集されますが、特定のサービスの詳細な情報を収集したい場合は、`src/collectors/uncovered_resources_detector.py`に収集メソッドを追加することができます。

## トラブルシューティング

### 実行に関する問題

- 依存パッケージの問題がある場合は、`task update-deps` を実行してください。
- 環境に問題がある場合は、`task setup` を再実行してください。
- その他の一般的な問題については[セットアップガイド](setup-guide.md)のトラブルシューティングセクションを参照してください。

### OIDC認証の問題

GitHub Actionsでの認証に問題がある場合:

1. IAMロールの信頼関係ポリシーが正しく設定されているか確認します。
2. リポジトリ変数 `AWS_ROLE_ARN` と `AWS_REGION` が正しく設定されているか確認します。
3. ワークフローの権限設定 (`permissions`) が正しいか確認します。

## ライセンス

MIT
