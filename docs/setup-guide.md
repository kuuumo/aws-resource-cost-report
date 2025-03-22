# セットアップガイド

このガイドでは、AWS リソース・コスト レポートツールのセットアップ方法について説明します。

## 前提条件

本ツールを使用するためには、以下が必要です：

- AWSアカウント
- GitHubアカウント
- Pythonの実行環境（バージョン3.8以上）

## インストール手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/kuuumo/aws-resource-cost-report.git
cd aws-resource-cost-report
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

> requirements.txtが存在しない場合は、以下のコマンドを実行してください：
> ```bash
> pip install boto3 requests
> ```

## AWS認証情報の設定

AWS認証情報を設定する方法は2つあります：

### オプション1: 資格情報ファイルの使用（ローカル実行時）

1. AWS CLIをインストールしていない場合は[インストール](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)します。

2. 以下のコマンドを実行して資格情報を設定します：

   ```bash
   aws configure
   ```

   プロンプトに従って、AWS Access Key ID、AWS Secret Access Key、リージョン、出力形式を入力します。

### オプション2: 環境変数の使用（ローカル実行時）

ターミナルで以下のコマンドを実行します：

```bash
export AWS_ACCESS_KEY_ID=あなたのアクセスキー
export AWS_SECRET_ACCESS_KEY=あなたのシークレットキー
export AWS_DEFAULT_REGION=ap-northeast-1
```

### オプション3: OIDC認証の設定（GitHub Actions自動実行用）

OIDC認証を使用すると、AWS認証情報をGitHubに保存せずに安全にAWSリソースにアクセスできます。詳細な設定方法は[認証設定ガイド](authentication.md)を参照してください。

## 必要なAWSアクセス権限

このツールを実行するためには、以下のAWS権限が必要です：

- `ce:GetCostAndUsage` - コスト情報の取得
- `ec2:DescribeInstances` - EC2インスタンス情報の取得
- `rds:DescribeDBInstances` - RDSインスタンス情報の取得
- `s3:ListBuckets` - S3バケット一覧の取得
- `s3:GetBucketLocation` - S3バケットのリージョン情報取得
- `elasticache:DescribeCacheClusters` - ElastiCacheクラスター情報の取得
- `elb:DescribeLoadBalancers` - Classic Load Balancer情報の取得
- `elbv2:DescribeLoadBalancers` - ALB/NLB情報の取得

以下のようなIAMポリシーを作成することをお勧めします：

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
        "elbv2:DescribeLoadBalancers"
      ],
      "Resource": "*"
    }
  ]
}
```

## 設定ファイルのカスタマイズ

`config.yml`ファイルを編集することで、レポートの内容や対象リージョンをカスタマイズできます：

```yaml
# AWS リージョン設定
regions:
  # 対象リージョン（カンマ区切り、または'all'）
  include: "all"
  # 除外リージョン（カンマ区切り）
  exclude: ""

# コスト分析設定
cost_analysis:
  # 分析したいリソースタイプを有効/無効に設定
  ec2_instance_types: true
  rds_instance_types: true
  # ...その他の設定...
```

## GitHub Actionsによる自動実行の設定

定期的な自動実行を設定するには：

1. フォークしたリポジトリの `.github/workflows/generate-report.yml` ファイルを必要に応じて編集します（スケジュールなど）。

2. [認証設定ガイド](authentication.md)に従ってOIDC認証を設定します。

3. GitHub リポジトリの `Settings > Secrets and variables > Actions` に変数を設定します。

これでセットアップは完了です。詳しい使用方法については[使用方法ガイド](usage-guide.md)を参照してください。
