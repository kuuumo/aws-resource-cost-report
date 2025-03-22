# AWS リソース・コスト レポート

AWSのリソース利用状況と費用を定期的に調査し、マークダウン形式でレポートを生成するツールです。

## 概要

本ツールは以下の機能を提供します：

- AWS Cost Explorer APIを使用して、リソースごとのコスト情報を取得
- AWS Resource Explorerを使用して、現在利用中のリソースの詳細情報を取得
- 取得したデータを分析し、リソースタイプ、インスタンスタイプ、リージョンごとのコスト分析
- 定期的なレポート生成（GitHub Actionsによる自動実行）
- マークダウン形式でのレポート出力

## 前提条件

- AWSアカウントへのアクセス権限
- 適切なIAMポリシー設定（Cost Explorer, Resource Explorer, その他必要なAWSサービスへのアクセス）
- GitHub ActionsでのOICD認証設定

## セットアップ方法

### 1. AWS側の設定 (OIDC認証)

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

### 2. GitHubリポジトリの設定

1. このリポジトリをクローンまたはフォークします。
2. GitHub リポジトリの `Settings > Secrets and variables > Actions` に移動します。
3. 「Variables」タブで以下の変数を追加します：
   - `AWS_ROLE_ARN`: 上記で作成したIAMロールのARN
   - `AWS_REGION`: 使用するAWSリージョン（例：`ap-northeast-1`）

4. 必要に応じて `.github/workflows/generate-report.yml` ファイルの実行スケジュールを調整します。

## 使用方法

### 手動実行

1. 以下のコマンドを実行してスクリプトを手動で実行します：

```bash
python src/main.py
```

2. `reports/` ディレクトリに生成されたレポートを確認します。

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
   - インスタンスタイプ
   - リージョン
   - 料金体系（オンデマンド/リザーブド/スポット）
   - 利用開始日
   - 月間コスト

4. **コスト最適化の推奨事項**
   - 低利用リソースの特定
   - コスト削減のための推奨事項

## カスタマイズ

- `config.yml` ファイルを編集することで、レポートの内容やフォーマットをカスタマイズできます。
- 追加のAWSサービスを調査対象に加える場合は、`src/collectors/` ディレクトリにコレクターを追加します。

## トラブルシューティング

### OIDC認証の問題

GitHub Actionsでの認証に問題がある場合:

1. IAMロールの信頼関係ポリシーが正しく設定されているか確認します。
2. リポジトリ変数 `AWS_ROLE_ARN` と `AWS_REGION` が正しく設定されているか確認します。
3. ワークフローの権限設定 (`permissions`) が正しいか確認します。

## ライセンス

MIT
