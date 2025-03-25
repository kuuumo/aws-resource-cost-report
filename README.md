# AWS リソース棚卸しツール

## 概要

AWSアカウント内のリソースを網羅的に収集し、サービス名やリソース名、タグなどの詳細情報を含めた棚卸しレポートを生成するツールです。
CSVまたはJSON形式でレポートを出力し、各サービスのリソース管理・コスト管理に活用できます。

新機能として、リソース変更の時系列追跡、サマリーレポート、およびリソース変更の影響分析機能が追加されました。

## 機能

- 多種多様なAWSサービスからリソース情報を一括収集
- リソースの名前やIDだけでなく、詳細設定やタグ情報も収集
- CSV形式とJSON形式での出力に対応
- サマリーレポート、トレンドレポート、変更レポートの生成
- リソースコストの概算と変更による影響の可視化
- レポートのマークダウン形式とHTML形式での出力に対応
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
  - pandas
  - matplotlib
  - markdown

## インストール

```bash
# 必要ライブラリのインストール
pip install -r requirements.txt
```

## 使い方

### 基本的な使い方

```bash
# デフォルト設定で実行
python src/main.py

# CSV形式のみで出力
python src/main.py --format csv

# JSON形式のみで出力
python src/main.py --format json

# 特定のリージョンで実行
python src/main.py --region ap-northeast-1

# 特定のプロファイルで実行
python src/main.py --profile myprofile
```

### レポート生成

```bash
# すべてのレポートを生成（デフォルト）
python src/main.py --report all

# サマリーレポートのみ生成
python src/main.py --report summary

# トレンドレポートのみ生成
python src/main.py --report trend

# コストレポートのみ生成
python src/main.py --report cost

# マークダウン形式のみで出力
python src/main.py --report-format markdown

# HTML形式のみで出力
python src/main.py --report-format html

# 変更レポートの生成（直近2回分のデータを比較）
python src/main.py --compare
```

### Taskfile を使った実行

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

## 出力ディレクトリ構造

```
output/
├── raw/                     # 生データ（Git管理外）
│   ├── YYYY-MM-DD/          # 日付ごとのフォルダ
│   │   ├── ec2.json
│   │   ├── s3.json
│   │   └── all_resources.json
├── processed/               # 処理済みデータ（Git管理内）
│   ├── summary.json         # 最新のサマリー情報
│   ├── trends/              # トレンドデータ
│   │   ├── monthly_cost.json
│   │   ├── resource_count.json
│   └── reports/             # レポートファイル
│       ├── cost_by_service.md
│       ├── resource_changes.md
│       └── graphs/          # グラフファイル
└── config/                  # 設定ファイル（Git管理内）
    ├── report_config.json   # レポート設定
    └── alert_thresholds.json # アラートしきい値
```

## テスト

テストはPyTestフレームワークを使用しています。テストを実行するには以下のコマンドを使用します。

```bash
# すべてのテストを実行
pytest tests/

# 単体テストのみ実行
pytest tests/unit/

# 統合テストのみ実行
pytest tests/integration/

# 特定のテストファイルを実行
pytest tests/unit/test_data_processor.py
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

### 新しいAWSサービスのサポートを追加

新しいAWSサービスのサポートを追加するには、以下の手順を実行します：

1. `src/collectors/` ディレクトリに新しいコレクタークラスを作成
2. `src/collector.py` ファイルのコレクターリストに新しいコレクターを追加

### レポート設定のカスタマイズ

レポートの設定は `output/config/report_config.json` ファイルで変更できます：

```json
{
  "report_formats": ["markdown", "html"],
  "show_cost_info": true,
  "include_graphs": true,
  "graph_formats": ["png"],
  "detail_level": "medium"
}
```

## ライセンス

このプロジェクトはMITライセンスの下で提供されています。
