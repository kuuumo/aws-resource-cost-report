# AWS リソースコスト報告ツール ユーザーガイド

## はじめに

AWS リソースコスト報告ツールは、AWS環境内のリソースを収集し、詳細な棚卸しレポートを生成するツールです。このガイドでは、ツールのインストール方法、基本的な使用方法、および主要な機能について説明します。

## インストール

### 前提条件

- Python 3.8以上
- AWS CLI設定（アクセスキーまたはIAMロール）
- AWS必要権限設定済み

### インストール手順

1. リポジトリをクローン：

```bash
git clone https://github.com/your-organization/aws-resource-cost-report.git
cd aws-resource-cost-report
```

2. 必要なライブラリをインストール：

```bash
pip install -r requirements.txt
```

3. AWSクレデンシャル設定（未設定の場合）：

```bash
aws configure
# または特定のプロファイルを設定
aws configure --profile myprofile
```

### 必要なAWS権限

このツールを実行するには、以下のAWS権限が必要です：

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
        "...他のサービスの読み取り権限..."
      ],
      "Resource": "*"
    }
  ]
}
```

> **注意**: 実際の運用では、必要最小限の権限に絞ることをお勧めします。

## 基本的な使い方

### コマンドライン引数

```bash
# デフォルト設定で実行
python src/main.py

# 特定のプロファイルを使用して実行
python src/main.py --profile myprofile

# 特定のリージョンのリソースを収集
python src/main.py --region ap-northeast-1

# 出力形式を指定して実行
python src/main.py --format json
python src/main.py --format csv
python src/main.py --format both

# 特定のレポートタイプだけを生成
python src/main.py --report summary
python src/main.py --report trend
python src/main.py --report cost
python src/main.py --report all

# レポート形式の指定
python src/main.py --report-format markdown
python src/main.py --report-format html
python src/main.py --report-format both

# リソース収集をスキップしてレポート生成のみ行う
python src/main.py --no-collect

# 直近の2回分のデータを比較して変更レポートを生成
python src/main.py --compare
```

### Taskfileを使った実行（オプション）

Taskfileがインストールされている場合、以下のコマンドも利用可能です：

```bash
# デフォルト設定で実行
task run

# CSVのみで出力
task run:csv

# 特定のリージョンで実行
task run:region REGION=ap-northeast-1

# 特定のプロファイルで実行
task run:profile PROFILE=myprofile
```

## 出力ファイル

### ディレクトリ構造

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

### 主要な出力ファイル

1. **生データ（raw/）**：
   - 日付ごとのディレクトリにサービスごとのJSONファイルとして保存
   - `all_resources.json`はその日のすべてのリソースを含む統合ファイル

2. **処理済みデータ（processed/）**：
   - `summary.json`: 最新のリソースサマリー情報
   - `trends/monthly_cost.json`: 月次コストのトレンドデータ
   - `trends/resource_count.json`: リソース数のトレンドデータ

3. **レポートファイル（reports/）**：
   - `resource_summary_YYYY-MM-DD.md`: リソースサマリーレポート（マークダウン）
   - `resource_summary_YYYY-MM-DD.html`: リソースサマリーレポート（HTML）
   - `resource_trends_YYYY-MM-DD.md`: リソーストレンドレポート
   - `cost_report_YYYY-MM_YYYY-MM-DD.md`: コストレポート
   - `changes_YYYY-MM-DD_to_YYYY-MM-DD.md`: 変更レポート
   - `graphs/`: 生成されたグラフ画像

## レポートの種類と機能

### 1. サマリーレポート

サマリーレポートには、リソースの総数、サービスごとのリソース数、リージョン別の分布、タグの使用状況などが含まれます。

**サンプル出力**:

```markdown
# AWS リソースサマリーレポート
生成日時: 2025-03-27T12:00:00+09:00
データ取得日: 2025-03-27
合計リソース数: 153

## リソースタイプ別サマリー

| リソースタイプ | 件数 |
|--------------|------|
| EC2_Instances | 42 |
| S3_Buckets | 15 |
| RDS_Instances | 8 |
| ... | ... |
```

### 2. トレンドレポート

トレンドレポートは、リソース数とコストの時系列変化を表示します。

**サンプル出力**:

```markdown
# AWS リソーストレンドレポート
生成日時: 2025-03-27T12:00:00+09:00

## リソース数のトレンド

| 日付 | 合計リソース数 | EC2_Instances | S3_Buckets | RDS_Instances | ... |
|------|--------------|--------------|-----------|--------------|-----|
| 2025-02-01 | 142 | 40 | 14 | 8 | ... |
| 2025-02-15 | 147 | 41 | 15 | 8 | ... |
| 2025-03-01 | 150 | 42 | 15 | 8 | ... |
| 2025-03-15 | 153 | 42 | 15 | 8 | ... |
```

### 3. 変更レポート

変更レポートは、2つの日付間のリソースの追加、削除、変更を詳細に報告します。

**サンプル出力**:

```markdown
# AWS リソース変更レポート (2025-02-01 から 2025-03-01)
生成日時: 2025-03-27T12:00:00+09:00
期間: 28 日間

## 変更サマリー

* 追加されたリソース: **11**
* 削除されたリソース: **3**
* 変更されたリソース: **5**
* 推定コスト影響: **増加 $125.50/月**
```

### 4. コストレポート

コストレポートは、リソースのコスト推定と内訳を提供します。

**サンプル出力**:

```markdown
# AWS リソースコストレポート
生成日時: 2025-03-27T12:00:00+09:00
対象月: 2025-03

## 月次コスト総額

**合計: $1250.75**

## サービス別コスト

| サービス | コスト | 割合 |
|----------|--------|------|
| EC2 | $450.23 | 36.00% |
| RDS | $320.15 | 25.60% |
| S3 | $125.75 | 10.05% |
| ... | ... | ... |
```

## 設定ファイルのカスタマイズ

### レポート設定ファイル（report_config.json）

レポートの動作をカスタマイズするには、`output/config/report_config.json`を編集します。

```json
{
  "report_formats": ["markdown", "html"],
  "show_cost_info": true,
  "include_graphs": true,
  "graph_formats": ["png"],
  "detail_level": "medium"
}
```

**設定オプション**:

- `report_formats`: 生成するレポート形式（"markdown", "html", または両方）
- `show_cost_info`: コスト情報を表示するかどうか（true/false）
- `include_graphs`: グラフを生成するかどうか（true/false）
- `graph_formats`: グラフの形式（"png", "svg", "pdf"）
- `detail_level`: レポートの詳細レベル（"low", "medium", "high"）

### アラートしきい値設定（alert_thresholds.json）

リソース変更やコスト変動に関するアラートしきい値を設定するには、`output/config/alert_thresholds.json`を編集します。

```json
{
  "cost_increase": {
    "warning": 10,
    "critical": 20
  },
  "resource_increase": {
    "warning": 5,
    "critical": 10
  },
  "security_changes": {
    "warning": 1,
    "critical": 3
  }
}
```

**設定オプション**:

- `cost_increase`: コスト増加のアラートしきい値（パーセント）
- `resource_increase`: リソース増加のアラートしきい値（パーセント）
- `security_changes`: セキュリティ関連の変更に対するアラートしきい値（変更数）

## 推奨される使用パターン

### 1. 日次スキャンと週次レポート

```bash
# 日次スキャン（生データのみ収集）
0 1 * * * cd /path/to/aws-resource-cost-report && python src/main.py --format json

# 週次レポート生成（月曜日に実行）
0 2 * * 1 cd /path/to/aws-resource-cost-report && python src/main.py --no-collect --report all --compare
```

### 2. マルチアカウント・マルチリージョン対応

複数のAWSアカウントとリージョンをスキャンする例：

```bash
#!/bin/bash
REGIONS=("ap-northeast-1" "us-east-1" "eu-west-1")
PROFILES=("prod" "dev" "staging")

for profile in "${PROFILES[@]}"; do
  for region in "${REGIONS[@]}"; do
    echo "Scanning $profile account in $region region..."
    python src/main.py --profile $profile --region $region
  done
done
```

### 3. CI/CD環境への統合

GitLab CIの例（`.gitlab-ci.yml`）：

```yaml
aws-resource-scan:
  image: python:3.9
  script:
    - pip install -r requirements.txt
    - python src/main.py --profile $AWS_PROFILE --region $AWS_REGION
  artifacts:
    paths:
      - output/processed/reports/
  only:
    - schedules
```

## トラブルシューティング

### よくある問題と解決策

1. **AWS認証エラー**

   **症状**: `botocore.exceptions.NoCredentialsError`や認証関連のエラーが発生する。
   
   **解決策**:
   - AWS CLIが正しく設定されているか確認（`aws configure list`）
   - 一時的な認証情報が期限切れでないか確認
   - 適切なプロファイルを指定しているか確認

2. **権限不足エラー**

   **症状**: `botocore.exceptions.ClientError: AccessDenied`エラーが発生する。
   
   **解決策**:
   - 使用しているIAMユーザー/ロールに必要な権限があるか確認
   - 特定のサービスに対するDescribe/List権限を追加

3. **メモリ不足エラー**

   **症状**: 大きなAWS環境でメモリエラーが発生する。
   
   **解決策**:
   - `python -m src.main --region <region>` のように実行してプロセスにより多くのメモリを割り当てる
   - 大規模環境では、単一リージョンずつスキャンする

4. **レポート生成エラー**

   **症状**: レポート生成中にエラーが発生する。
   
   **解決策**:
   - 必要なライブラリがすべてインストールされているか確認
   - `--no-collect`オプションでレポート生成のみを実行して問題を切り分ける

## 更新履歴

| 日付 | バージョン | 説明 | 作成者 |
|------|------------|------|--------|
| 2025-03-27 | 1.0 | 初期バージョン | - |
