# AWS コスト詳細レポート

AWSの利用コストを細かく把握するためのツールです。すべてのサービスとインスタンスごとのコスト情報を収集し、Nameタグを使って分かりやすくレポートします。

## 特徴

- AWS Cost Explorer APIを使用して **課金されているすべてのサービス** を自動検出
- リソースIDを抽出し、**Nameタグ** と紐付けて表示
- 複数のAWSリージョンをカバー（全リージョン対応可能）
- コンソール、CSV、HTML形式での出力に対応
- 直感的なコマンドライン操作

## 対応サービス

このツールは、課金されているすべてのAWSサービスを自動的に検出し、以下のサービスについては詳細なNameタグ情報も収集します：

- EC2インスタンス
- EBSボリューム
- セキュリティグループ
- VPC関連リソース
- RDSインスタンス/クラスター
- S3バケット
- Lambda関数
- DynamoDBテーブル
- Elastic Load Balancer (ELB, ALB, NLB)
- ECSクラスター/タスク
- ElastiCache
- CloudFront
- SQS
- SNS
- API Gateway
- その他のAWSサービス

## インストール方法

### 必要条件

- Python 3.6以上
- AWS認証情報（~/.aws/credentials または環境変数）
- 以下のIAM権限：
  - Cost Explorer API（`ce:GetCostAndUsage`）
  - 各種AWSサービスの読み取り権限
- [Task](https://taskfile.dev/) コマンドラインツール

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/aws-resource-cost-report.git
cd aws-resource-cost-report

# セットアップを実行
task setup
```

## 使い方

### 基本的な使い方

```bash
# デフォルト（コンソール形式）でレポートを実行
task run

# または
task run:console

# CSV形式でレポートを生成（タイムスタンプ付きファイル名）
task run:csv

# HTML形式でレポートを生成（タイムスタンプ付きファイル名）
task run:html

# 全リージョンのリソースを検索（より詳細だが時間がかかる）
task run:all-regions

# カスタム引数を使用して実行
task run -- --days 90 --format html --output custom_report.html
```

### その他のタスク

```bash
# 依存パッケージを更新
task update-deps

# 生成されたレポートファイルを削除
task clean

# 開発用のセットアップ（テストやリンティングツールをインストール）
task install-dev

# テストを実行
task test

# コードリンティング
task lint

# コードフォーマット
task format
```

## AWS認証設定

このツールはAWSリソースにアクセスするため、適切な認証設定が必要です。

### IAMユーザー認証情報の設定（ローカル実行用）

1. AWSコンソールでIAMユーザーを作成し、以下の権限を付与します：
   - ReadOnlyAccess (基本的な読み取り権限)
   - `ce:GetCostAndUsage` (Cost Explorer API用)

2. AWS CLIを使用して認証情報を設定：

   ```bash
   aws configure
   ```

   プロンプトに従ってアクセスキーID、シークレットアクセスキー、リージョン（例：`ap-northeast-1`）を入力します。

3. または環境変数で設定：

   ```bash
   export AWS_ACCESS_KEY_ID=あなたのアクセスキー
   export AWS_SECRET_ACCESS_KEY=あなたのシークレットキー
   export AWS_DEFAULT_REGION=ap-northeast-1
   ```

### 必要最小限のIAMポリシー

以下は推奨される最小権限ポリシーです：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ec2:DescribeInstances",
        "ec2:DescribeTags",
        "ec2:DescribeRegions",
        "rds:DescribeDBInstances",
        "rds:DescribeDBClusters",
        "rds:ListTagsForResource",
        "s3:ListBuckets",
        "s3:GetBucketTagging",
        "lambda:ListFunctions",
        "lambda:ListTags",
        "dynamodb:ListTables",
        "dynamodb:DescribeTable",
        "dynamodb:ListTagsOfResource",
        "elasticloadbalancing:DescribeLoadBalancers",
        "elasticloadbalancing:DescribeTags",
        "ecs:ListClusters",
        "ecs:DescribeClusters",
        "ecs:ListTaskDefinitions",
        "ecs:DescribeTaskDefinition",
        "elasticache:DescribeCacheClusters",
        "elasticache:ListTagsForResource",
        "cloudfront:ListDistributions",
        "cloudfront:ListTagsForResource",
        "sqs:ListQueues",
        "sqs:ListQueueTags",
        "sns:ListTopics",
        "sns:ListTagsForResource",
        "apigateway:GET"
      ],
      "Resource": "*"
    }
  ]
}
```

## レポートの内容

生成されるレポートには以下の情報が含まれます：

- **サービス概要**: AWS課金サービス別の総コスト
- **リソース詳細**:
  - サービス名
  - 使用タイプ
  - リソースID
  - Nameタグ
  - 月額コスト

## カスタマイズ

`config.yml` ファイルを編集することで、基本的な動作をカスタマイズできます：

```yaml
# AWS リージョン設定
regions:
  # 対象リージョン（カンマ区切り、または'all'）
  include: "all"
  # 除外リージョン（カンマ区切り）
  exclude: ""

# コスト分析設定
cost_analysis:
  # リソースのタグ情報を収集する
  collect_tags: true
  # タグ情報収集時の同時実行数
  tag_collection_threads: 10

# 出力設定
output:
  # デフォルト出力形式（console, csv, html）
  default_format: "console"
  # HTMLレポートのスタイル設定
  html_style:
    # 背景色
    background_color: "#ffffff"
    # テーブルヘッダーの背景色
    header_color: "#f2f2f2"
```

## アーキテクチャ

このツールは、以下のコンポーネントで構成されています：

- **Core**: 基本クラスとユーティリティ
  - `AWSCostReport`: メインのレポートクラス
  - `ResourceIdExtractor`: リソースID抽出ユーティリティ
  - `AWSRegionManager`: リージョン管理
  - `DataProcessor`: データ処理

- **Collectors**: データ収集
  - `CostExplorerCollector`: AWS Cost Explorerからコストデータを収集
  - `TagCollector`: AWSリソースからNameタグを収集

- **Formatters**: 出力形式
  - `OutputFormatter`: コンソール、CSV、HTML形式でのレポート出力

## ヒントとコツ

- **初回実行時間**: タグ収集処理のため、初回実行は数分かかる場合があります
- **メモリ使用量**: 大規模なAWSアカウントでは、メモリ使用量が増加することがあります
- **コスト最適化**: `--all-regions`オプションを使用すると、より多くのリソースが見つかりますが、実行時間は長くなります

## トラブルシューティング

### 「ボーリングレート超過」エラー

```text
botocore.exceptions.ClientError: An error occurred (RequestLimitExceeded)
```

解決策: プログラムを再実行してください。AWS APIには制限があり、複数のリージョンで多くのリソースを検索する場合に発生することがあります。

### リソースIDが見つからない

一部のリソースでは、Cost ExplorerのデータからリソースIDを抽出できないことがあります。この場合、リソースIDと名前タグは空になります。

### 認証エラー

```text
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

解決策: AWS認証情報が正しく設定されているか確認してください。`aws configure`コマンドを実行するか、環境変数を設定してください。

## ライセンス

MIT
