# AWS認証設定ガイド

このガイドでは、AWS リソース・コスト レポートツールで利用できるAWS認証方法について詳しく説明します。特にGitHub ActionsからAWSリソースへ安全にアクセスするためのOIDC認証設定に重点を置いています。

## 認証方法の比較

| 認証方法 | 利点 | 欠点 | 推奨用途 |
|---------|------|------|---------|
| IAMアクセスキー | 設定が簡単 | 長期的な認証情報の保存によるセキュリティリスク | ローカル開発・テスト |
| 環境変数 | スクリプト実行時に柔軟に設定可能 | CIパイプラインで使用する場合はシークレット管理が必要 | ローカル開発・テスト |
| OIDC認証 | 認証情報の保存不要<br>一時的な認証情報を使用<br>きめ細かなアクセス制御 | 初期設定が複雑 | GitHubActions自動実行 |

## OIDC認証設定手順（詳細版）

OIDC (OpenID Connect) を使用したGitHub Actions認証は、AWSへの安全なアクセスを実現する最新の方法です。以下の手順で設定します。

### 1. AWSアカウントでのIDプロバイダー作成

1. AWSコンソールにログインし、IAMサービスに移動します。
2. 左側のナビゲーションメニューから「アイデンティティプロバイダー」を選択します。
3. 「プロバイダーを追加」ボタンをクリックします。
4. プロバイダータイプとして「OpenID Connect」を選択します。
5. 以下の情報を入力します：
   - プロバイダーURL: `https://token.actions.githubusercontent.com`
   - 対象者: `sts.amazonaws.com`
6. 「サムプリントを取得」ボタンをクリックし、サムプリントが自動的に入力されることを確認します。
7. 「プロバイダーの追加」ボタンをクリックして保存します。

### 2. IAMロールの作成

1. IAMコンソールで「ロール」を選択し、「ロールの作成」をクリックします。
2. 信頼されたエンティティタイプとして「ウェブアイデンティティ」を選択します。
3. 以下の信頼関係を設定します：
   - アイデンティティプロバイダー: `token.actions.githubusercontent.com`
   - 対象者: `sts.amazonaws.com`
   - GitHub組織/リポジトリの設定:
     - オプション1: 特定のリポジトリのみ許可 `repo:your-org/aws-resource-cost-report:*`
     - オプション2: 特定のブランチのみ許可 `repo:your-org/aws-resource-cost-report:ref:refs/heads/master`
4. 「次へ」をクリックし、必要なアクセス権限ポリシーを追加します。

### 3. 必要なポリシーの追加

このツールには以下のアクセス権限が必要です：

#### オプション1: AWS管理ポリシーを使用する場合

1. `ReadOnlyAccess` ポリシーを検索して選択します（基本的な読み取り権限）
2. 「次へ」をクリックします。

#### オプション2: カスタムポリシーを作成する場合

1. 「ポリシーの作成」をクリックし、以下のJSON形式のポリシーを作成します：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ec2:DescribeInstances",
        "rds:DescribeDBInstances",
        "s3:ListBuckets",
        "s3:GetBucketLocation",
        "elasticache:DescribeCacheClusters",
        "elb:DescribeLoadBalancers",
        "elbv2:DescribeLoadBalancers",
        "cloudwatch:GetMetricStatistics"
      ],
      "Resource": "*"
    }
  ]
}
```

2. ポリシー名（例：`AWSResourceCostReportPolicy`）を入力し、ポリシーを作成します。
3. 作成したポリシーを検索して選択し、「次へ」をクリックします。

### 4. ロールの作成を完了

1. ロール名（例：`GitHubActionsAWSResourceReport`）を入力します。
2. 説明を入力します（例：「GitHub ActionsからAWSリソース・コストレポート生成用のロール」）。
3. 信頼関係と追加したポリシーを確認します。
4. 「ロールの作成」ボタンをクリックします。
5. 作成したロールのARNをメモしておきます（例：`arn:aws:iam::123456789012:role/GitHubActionsAWSResourceReport`）。

### 5. GitHubリポジトリの設定

1. GitHubでリポジトリに移動します。
2. 「Settings」タブをクリックします。
3. 左側のメニューから「Secrets and variables」→「Actions」を選択します。
4. 「Variables」タブを選択します。
5. 「New repository variable」ボタンをクリックし、以下の変数を追加します：
   - 名前: `AWS_ROLE_ARN`
   - 値: 上記でメモしたIAMロールのARN
6. 同様に、もう一つの変数を追加します：
   - 名前: `AWS_REGION`
   - 値: 使用するAWSリージョン（例：`ap-northeast-1`）

### 6. ワークフローファイルの確認

ワークフローファイル（`.github/workflows/generate-report.yml`）に以下の設定が含まれていることを確認します：

```yaml
permissions:
  id-token: write  # OIDC認証に必要
  contents: write  # リポジトリへのコミット権限

jobs:
  generate-report:
    # ...
    steps:
      # ...
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}
```

## IAMアクセスキーによる認証（ローカル開発用）

GitHub Actions以外の環境（ローカル開発など）では、従来のIAMアクセスキーを使用することもできます。

### IAMユーザーの作成と権限設定

1. IAMコンソールで「ユーザー」を選択し、「ユーザーを作成」をクリックします。
2. ユーザー名を入力し、「次へ」をクリックします。
3. 「ポリシーを直接アタッチする」を選択し、必要なポリシーを追加します（上記のカスタムポリシーと同様）。
4. 「次へ」→「ユーザーの作成」と進みます。
5. 「アクセスキーの作成」を選択します。
6. 用途に「コマンドラインインターフェイス（CLI）」を選択します。
7. オプションで説明を入力し、「アクセスキーの作成」をクリックします。
8. アクセスキーIDとシークレットアクセスキーを安全な場所に保存します。

### 認証情報の設定

以下のいずれかの方法で認証情報を設定します：

#### 方法1: AWS設定ファイル

```bash
aws configure
```

プロンプトに従ってアクセスキーID、シークレットアクセスキー、リージョン、出力形式を入力します。

#### 方法2: 環境変数

```bash
export AWS_ACCESS_KEY_ID=あなたのアクセスキー
export AWS_SECRET_ACCESS_KEY=あなたのシークレットキー
export AWS_DEFAULT_REGION=ap-northeast-1
```

## トラブルシューティング

### OIDC認証の問題

1. **認証エラー（アクセス拒否）**: IAMロールの信頼関係ポリシーが正しく設定されているか確認してください。特にGitHubリポジトリのパスが正確に設定されていることを確認します。

2. **ロールの引き受けができない**: ワークフローファイルの `permissions` セクションに `id-token: write` が含まれていることを確認してください。

3. **リージョン関連のエラー**: GitHub変数 `AWS_REGION` が正しく設定されているか確認してください。

4. **権限不足のエラー**: IAMロールに必要なすべての権限が付与されているか確認してください。

### IAMアクセスキー認証の問題

1. **認証情報が見つからない**: 環境変数または AWS 設定ファイルが正しく設定されているか確認してください。

2. **権限不足**: IAMユーザーに必要な権限がすべて付与されているか確認してください。

3. **期限切れのアクセスキー**: アクセスキーが有効であることを確認し、必要に応じて新しいキーを生成してください。
