# AWS リソース棚卸しツール

## 概要

AWSアカウント内のリソースを網羅的に収集し、サービス名やリソース名、タグなどの詳細情報を含めた棚卸しレポートを生成するツールです。
CSVまたはJSON形式でレポートを出力し、各サービスのリソース管理・コスト管理に活用できます。

## 機能

- 多種多様なAWSサービスからリソース情報を一括収集
- リソースの名前やIDだけでなく、詳細設定やタグ情報も収集
- CSV形式とJSON形式での出力に対応
- CLIツールとして実行可能で、バッチ処理やCI/CDパイプラインへの統合が容易

## 対応サービス

- Amazon EC2（インスタンス、ボリューム、セキュリティグループ、ロードバランサーなど）
- Amazon S3（バケット）
- Amazon RDS（DBインスタンス、DBクラスター、スナップショットなど）
- AWS Lambda（関数、レイヤー、イベントソースマッピング）
- Amazon DynamoDB（テーブル、グローバルテーブル、バックアップ）
- Amazon CloudFront（ディストリビューション、キャッシュポリシーなど）
- Amazon Route 53（ホストゾーン、ヘルスチェック、ドメインなど）
- AWS IAM（ユーザー、グループ、ロール、ポリシーなど）
- Amazon CloudWatch（アラーム、ダッシュボード、ロググループ、イベントルール）
- Amazon ElastiCache（クラスター、レプリケーショングループなど）
- Amazon SNS（トピック、サブスクリプション）
- Amazon SQS（キュー）

※ 今後も随時対応サービスを拡充予定

## 必要条件

- Python 3.8以上
- AWS CLI設定（アクセスキーまたはIAMロール）
- 必要なPythonパッケージ：
  - boto3
  - botocore

## インストール

```bash
# 必要ライブラリのインストール
pip install boto3 botocore
```

## 使い方

### 基本的な使い方

```bash
# デフォルト設定で実行
task run

# CSV形式のみで出力
task run:csv

# 特定のリージョンで実行
task run:region REGION=ap-northeast-1

# 特定のプロファイルで実行
task run:profile PROFILE=myprofile
```

### 出力ファイル

実行すると、以下のディレクトリに結果ファイルが出力されます：

```text
output/
  ├── aws_resources_YYYYMMDD_HHMMSS.json  # JSON形式（全リソース情報）
  ├── EC2_Instances_YYYYMMDD_HHMMSS.csv   # CSV形式（EC2インスタンス情報）
  ├── S3_Buckets_YYYYMMDD_HHMMSS.csv      # CSV形式（S3バケット情報）
  └── ...                                 # その他のサービス別CSVファイル
```

## AWS権限

このツールを実行するには、以下の権限が必要です：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "s3:List*",
        "s3:GetBucket*",
        "rds:Describe*",
        "lambda:List*",
        "lambda:Get*",
        "dynamodb:List*",
        "dynamodb:Describe*",
        "cloudfront:List*",
        "cloudfront:Get*",
        "route53:List*",
        "route53:Get*",
        "route53domains:List*",
        "iam:List*",
        "iam:Get*",
        "cloudwatch:Describe*",
        "cloudwatch:List*",
        "logs:Describe*",
        "logs:List*",
        "events:List*",
        "events:Describe*",
        "elasticache:Describe*",
        "sns:List*",
        "sns:Get*",
        "sqs:List*",
        "sqs:Get*"
      ],
      "Resource": "*"
    }
  ]
}
```

## カスタマイズ

新しいAWSサービスのサポートを追加するには、以下の手順を実行します：

1. `src/collectors/` ディレクトリに新しいコレクタークラスを作成
2. `src/collector.py` ファイルのコレクターリストに新しいコレクターを追加

## ライセンス

このプロジェクトはMITライセンスの下で提供されています。
