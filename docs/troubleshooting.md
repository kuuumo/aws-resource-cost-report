# トラブルシューティングガイド

AWS リソース・コスト レポートツールの使用中に発生する可能性がある一般的な問題と解決方法についてのガイドです。

## AWS認証関連の問題

### アクセス権限エラー

**問題**: AWS APIへのアクセス時に権限エラーが発生する

```
botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling the GetCostAndUsage operation: User: arn:aws:iam::123456789012:user/username is not authorized to perform: ce:GetCostAndUsage
```

**解決策**:
1. IAMユーザーまたはロールに必要な権限が付与されているか確認します。以下の権限が必要です：
   - `ce:GetCostAndUsage`
   - `ec2:DescribeInstances`
   - その他使用するAWSサービスのAPI権限
2. IAMポリシーの例（最小権限）：

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

### AWS認証情報が見つからない

**問題**: AWS認証情報が見つからないエラーが表示される

```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**解決策**:
1. 環境変数が正しく設定されているか確認します：
   ```bash
   export AWS_ACCESS_KEY_ID=あなたのアクセスキー
   export AWS_SECRET_ACCESS_KEY=あなたのシークレットキー
   export AWS_DEFAULT_REGION=ap-northeast-1
   ```

2. AWS CLIの設定が正しいか確認します：
   ```bash
   aws configure list
   ```

3. GitHub Actionsでの実行時は、シークレットまたはOIDC設定が正しく設定されているか確認します。

### OIDC認証の問題

**問題**: GitHub ActionsからのOIDC認証が機能しない

**解決策**:
1. IAMアイデンティティプロバイダーが正しく設定されているか確認します：
   - プロバイダーURL: `https://token.actions.githubusercontent.com`
   - 対象者: `sts.amazonaws.com`

2. IAMロールの信頼関係ポリシーが正しく設定されているか確認します：
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
         },
         "Action": "sts:AssumeRoleWithWebIdentity",
         "Condition": {
           "StringEquals": {
             "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
           },
           "StringLike": {
             "token.actions.githubusercontent.com:sub": "repo:your-org/aws-resource-cost-report:*"
           }
         }
       }
     ]
   }
   ```

3. GitHubリポジトリの変数が正しく設定されているか確認します：
   - `AWS_ROLE_ARN`
   - `AWS_REGION`

4. GitHub Actions ワークフローファイルに必要な権限が設定されているか確認します：
   ```yaml
   permissions:
     id-token: write
     contents: write
   ```

## API制限とエラー

### リクエスト数の制限に達した

**問題**: AWSのAPI制限に達してエラーが発生する

```
botocore.exceptions.ClientError: An error occurred (ThrottlingException) when calling the DescribeInstances operation: Rate exceeded
```

**解決策**:
1. リトライロジックを実装している場合は、スクリプトを再実行してください
2. 多数のリージョンやリソースを処理する場合は、対象を絞り込みます：
   ```bash
   python src/main.py --regions ap-northeast-1,us-east-1
   ```
3. `config.yml` で必要なリソースタイプのみ分析するように設定します

### Cost Explorer APIの制限

**問題**: Cost Explorer APIのエラーや制限に関する問題

**解決策**:
1. Cost Explorer APIの日次クォータを確認してください（デフォルトでは1日あたり約1,000リクエスト）
2. 複数のアカウントや長期間のコストデータを分析する場合は、Cost and Usage Report (CUR) の使用を検討してください
3. 分析期間を短くして、より小さな時間範囲で実行することを試みてください

## データ収集関連の問題

### 特定のリージョンでのデータ収集エラー

**問題**: 特定のAWSリージョンでデータ収集エラーが発生する

```
Error collecting EC2 instances in region ap-east-1: EndpointConnectionError: Could not connect to the endpoint URL: "https://ec2.ap-east-1.amazonaws.com"
```

**解決策**:
1. アカウントでそのリージョンが有効になっているか確認します
2. リージョンへのネットワーク接続を確認します
3. 問題のあるリージョンを除外してスクリプトを実行します：
   ```bash
   python src/main.py --regions all
   ```
   そして `config.yml` ファイルで除外リージョンを設定します：
   ```yaml
   regions:
     include: "all"
     exclude: "ap-east-1,me-south-1"
   ```

### S3バケットサイズの取得エラー

**問題**: S3バケットのサイズ情報が取得できない

```
Error getting bucket size for my-bucket: AccessDenied
```

**解決策**:
1. CloudWatch メトリクスへのアクセス権があることを確認します：
   - `cloudwatch:GetMetricStatistics` 権限が必要です
2. バケットに関連するメトリクスが有効になっているか確認します
3. 権限の問題が解決しない場合は、`src/collectors/resource_explorer.py` で S3 バケットサイズの取得部分をトライ/キャッチブロックで囲むよう修正し、エラー発生時にデフォルト値を設定します

### 大量のリソース処理時のメモリエラー

**問題**: 大規模なAWS環境で実行時にメモリエラーが発生する

```
MemoryError: ...
```

**解決策**:
1. スクリプトを実行するマシンまたは環境のメモリ制限を増やします
2. 処理するリージョンやリソースタイプを制限します
3. 並列処理の同時実行数を減らします（`src/collectors/resource_explorer.py`の`ThreadPoolExecutor`の`max_workers`パラメータを調整）

## レポート生成関連の問題

### 不完全なレポート

**問題**: 生成されたレポートにいくつかのセクションが欠けている

**解決策**:
1. ログをチェックして、データ収集中にエラーが発生していないか確認します
2. `config.yml` ファイルで、すべての必要なセクションが有効になっているか確認します：
   ```yaml
   report:
     sections:
       summary: true
       service_costs: true
       region_costs: true
       ec2_instances: true
       rds_instances: true
       other_resources: true
       daily_trends: true
       optimization_recommendations: true
   ```
3. 不足しているセクションに関連するデータが正しく収集されているか確認します

### コスト情報の不一致

**問題**: レポートのコスト情報がAWSコンソールの表示と一致しない

**解決策**:
1. 分析期間が正しく設定されているか確認します：
   ```bash
   python src/main.py --start-date 2025-01-01 --end-date 2025-01-31
   ```
2. AWS Cost Explorerの設定（償却オプションなど）を確認します
3. AWS Cost Explorerの更新タイミングを考慮してください（通常、コストデータは24〜48時間遅れで更新されます）
4. 複雑な料金体系（リザーブドインスタンス、Savings Plans、クレジットなど）がある場合、コストの計算方法に違いがある可能性があります

### 文字化けの問題

**問題**: 日本語等の非ASCII文字がレポートで文字化けする

**解決策**:
1. ファイルが正しいエンコーディング（UTF-8）で保存されているか確認します：
   ```python
   with open(output_file, 'w', encoding='utf-8') as f:
       f.write(report_content)
   ```
2. レポートファイルが正しいエンコーディングで読み込まれているか確認します
3. 特に問題のある文字（特殊記号など）があれば、それらをエスケープまたは置換します

## GitHub Actions関連の問題

### ワークフローの自動実行が動作しない

**問題**: スケジュールされたGitHub Actions ワークフローが実行されない

**解決策**:
1. ワークフローファイルの構文が正しいか確認します
2. クーロン式が正しく設定されているか確認します：
   ```yaml
   on:
     schedule:
       - cron: '0 9 * * 1'  # 毎週月曜日の午前9時(UTC)
   ```
3. リポジトリが最近アクティブであるか確認します（長期間非アクティブなリポジトリではスケジュールされたワークフローが停止されることがあります）
4. GitHub Actionsのステータスページを確認して、サービス自体に問題がないか確認します

### コミット権限エラー

**問題**: GitHub Actionsがリポジトリにコミットできない

```
error: failed to push some refs to 'https://github.com/your-org/aws-resource-cost-report.git'
```

**解決策**:
1. ワークフローファイルで正しい権限が設定されているか確認します：
   ```yaml
   permissions:
     contents: write
   ```
2. 正しいGitのユーザー名とメールアドレスが設定されているか確認します：
   ```bash
   git config --local user.email "actions@github.com"
   git config --local user.name "GitHub Actions"
   ```
3. リポジトリの設定で、GitHub Actionsによるコミットが許可されているか確認します（ブランチ保護ルールがある場合）

### ワークフロー実行のタイムアウト

**問題**: GitHub Actions ワークフローが長時間実行後にタイムアウトする

**解決策**:
1. GitHub Actionsのタイムアウト制限（デフォルトは6時間）を考慮して、処理を最適化します
2. 大規模な環境の場合は、リージョンやリソースタイプを限定します
3. ワークフローのタイムアウト設定を調整します：
   ```yaml
   jobs:
     generate-report:
       runs-on: ubuntu-latest
       timeout-minutes: 360  # 6時間
   ```
4. 複数のジョブに分割して、並列実行することを検討します

## インストール関連の問題

### 依存関係のインストールエラー

**問題**: 依存パッケージのインストール時にエラーが発生する

```
ERROR: Could not find a version that satisfies the requirement boto3
```

**解決策**:
1. Pythonのバージョンが互換性があるか確認します（Python 3.8以上を推奨）
2. pipが最新かどうか確認し、必要に応じて更新します：
   ```bash
   python -m pip install --upgrade pip
   ```
3. 仮想環境を使用して、依存関係の競合を避けます：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Python関連のエラー

**問題**: Pythonスクリプト実行時に構文エラーが発生する

```
SyntaxError: invalid syntax
```

**解決策**:
1. 使用しているPythonのバージョンを確認します（Python 3.8以上を推奨）：
   ```bash
   python --version
   ```
2. コードに互換性の問題がないか確認します
3. ソースコードを修正して、使用しているPythonバージョンと互換性があるようにします

## 一般的なトラブルシューティング手順

問題が発生した場合、以下の一般的なトラブルシューティング手順を試してください：

1. **ログの確認**: スクリプトは詳細なログを出力します。エラーメッセージやワーニングをチェックしてください。

2. **デバッグモードの有効化**: より詳細なログを取得するために、ロギングレベルを変更します：
   ```python
   logging.basicConfig(
       level=logging.DEBUG,  # INFOからDEBUGに変更
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

3. **段階的な実行**: 問題を特定するために、スクリプトの一部だけを実行してみてください：
   ```python
   # 例：Cost Explorerデータのみ収集
   cost_collector = CostExplorerCollector(args.start_date, args.end_date)
   cost_data = cost_collector.collect()
   print(json.dumps(cost_data, indent=2, default=str))
   ```

4. **最新バージョンの使用**: リポジトリの最新バージョンを使用していることを確認してください：
   ```bash
   git pull origin master
   ```

5. **クリーンインストール**: 依存関係の問題がある場合は、クリーンインストールを試してください：
   ```bash
   python -m pip uninstall -y boto3 botocore
   python -m pip install boto3
   ```

6. **AWS CLIでのテスト**: AWS APIが正しく機能しているか確認するために、AWS CLIを使用してテストします：
   ```bash
   aws ce get-cost-and-usage --time-period Start=2025-01-01,End=2025-01-31 --granularity MONTHLY --metrics UnblendedCost
   ```

それでも問題が解決しない場合は、GitHubリポジトリで新しいIssueを作成し、以下の情報を提供してください：
- 使用しているPythonのバージョン
- 使用しているboto3のバージョン
- 発生したエラーメッセージの全文
- 実行したコマンドとパラメータ
- `config.yml` ファイルの内容（機密情報を除く）
