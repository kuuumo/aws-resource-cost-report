# カスタマイズガイド

このガイドでは、AWS リソース・コスト レポートツールのカスタマイズ方法について説明します。設定ファイルの編集やソースコードの拡張により、ツールを自身のニーズに合わせて調整できます。

## 設定ファイルによるカスタマイズ

### config.yml ファイルの概要

プロジェクトルートにある `config.yml` ファイルを編集することで、レポートの内容や分析対象を簡単にカスタマイズできます。このファイルは以下のセクションで構成されています：

- **regions**: 分析対象のAWSリージョン設定
- **cost_analysis**: コスト分析の対象となるリソースタイプ設定
- **resource_analysis**: リソース詳細分析の設定
- **optimization**: コスト最適化推奨事項の設定
- **report**: レポート出力形式や含めるセクションの設定

### リージョン設定のカスタマイズ

分析対象のAWSリージョンを制限または拡張できます：

```yaml
regions:
  # 対象リージョン（カンマ区切り、または'all'）
  include: "ap-northeast-1,us-east-1,eu-west-1"
  # 除外リージョン（カンマ区切り）
  exclude: "ap-south-1,sa-east-1"
```

- `include: "all"` を設定すると、すべてのAWSリージョンが分析対象になります
- 一部のリージョンのみ分析する場合は、カンマ区切りでリージョンコードを指定します
- `exclude` を設定すると、指定したリージョンが分析対象から除外されます

### コスト分析設定のカスタマイズ

コスト分析の対象となるリソースタイプを選択できます：

```yaml
cost_analysis:
  # EC2インスタンスのタイプ別コスト分析
  ec2_instance_types: true
  # RDSインスタンスのタイプ別コスト分析
  rds_instance_types: true
  # EBSボリュームのタイプ別コスト分析
  ebs_volume_types: false
  # S3バケットのストレージクラス別コスト分析
  s3_storage_classes: true
```

各項目を `true` または `false` に設定することで、特定のリソースタイプのコスト分析を有効/無効にできます。

### リソース分析設定のカスタマイズ

レポートに含めるリソースタイプの詳細情報を選択できます：

```yaml
resource_analysis:
  # EC2インスタンスの詳細分析
  ec2_instances: true
  # RDSインスタンスの詳細分析
  rds_instances: true
  # EBSボリュームの詳細分析
  ebs_volumes: false
  # S3バケットの詳細分析
  s3_buckets: true
  # ElastiCacheクラスターの詳細分析
  elasticache_clusters: true
  # ロードバランサーの詳細分析
  load_balancers: true
```

各項目を `true` または `false` に設定することで、特定のリソースタイプの詳細情報をレポートに含めるかどうか選択できます。

### 最適化推奨設定のカスタマイズ

コスト最適化推奨事項の基準を調整できます：

```yaml
optimization:
  # 停止中のEC2インスタンスの検出
  stopped_ec2_instances: true
  # 低使用率のEC2インスタンスの検出（CPU使用率閾値）
  low_utilization_ec2_threshold: 5.0
  # 未使用のEBSボリュームの検出
  unused_ebs_volumes: true
  # 旧世代のインスタンスタイプの検出
  old_generation_instances: true
  # リザーブドインスタンスのカバレッジ分析
  reserved_instance_coverage: true
```

- `stopped_ec2_instances`: 停止中のEC2インスタンスを検出して推奨事項に含めるかどうか
- `low_utilization_ec2_threshold`: 低使用率とみなすCPU使用率のしきい値（%）
- `unused_ebs_volumes`: 未使用のEBSボリュームを検出するかどうか
- `old_generation_instances`: 旧世代のインスタンスタイプを検出するかどうか
- `reserved_instance_coverage`: リザーブドインスタンスのカバレッジ分析を行うかどうか

### レポート設定のカスタマイズ

レポートの出力形式や含めるセクションを選択できます：

```yaml
report:
  # 出力形式（markdown, html, csv）
  format: "markdown"
  # レポートに含めるセクション
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

- `format`: レポートの出力形式（現在は `markdown` のみサポート、将来的に `html` や `csv` も対応予定）
- `sections`: レポートに含めるセクションの選択（各項目を `true` または `false` に設定）

## ソースコードの拡張

より高度なカスタマイズを行う場合は、ソースコードを直接編集することができます。

### 新しいリソースコレクターの追加

新しいタイプのAWSリソース（例：Lambda関数、ECS、Kinesisなど）の情報を収集するには、以下の手順でコレクターを追加します：

1. `src/collectors/` ディレクトリに新しいPythonファイルを作成します（例：`lambda_collector.py`）
2. 以下のテンプレートを使用して新しいコレクタークラスを実装します：

```python
#!/usr/bin/env python3

import boto3
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class LambdaCollector:
    """AWS Lambda関数情報を収集するクラス"""
    
    def __init__(self, regions='all'):
        """
        初期化
        
        Args:
            regions (str|list): 収集対象のAWSリージョンのリスト、または'all'で全リージョン
        """
        self.regions = regions
        self.session = boto3.Session()
    
    def collect(self):
        """
        Lambda関数情報を収集
        
        Returns:
            list: Lambda関数情報のリスト
        """
        # 対象リージョンリストを取得
        if self.regions == 'all':
            available_regions = self.session.get_available_regions('lambda')
            self.regions = available_regions
        
        logger.info(f"Collecting Lambda function information for regions: {self.regions}")
        
        functions = []
        
        def collect_region_functions(region):
            try:
                lambda_client = self.session.client('lambda', region_name=region)
                response = lambda_client.list_functions()
                region_functions = []
                
                for function in response.get('Functions', []):
                    function_info = {
                        'name': function['FunctionName'],
                        'runtime': function['Runtime'],
                        'memory': function['MemorySize'],
                        'timeout': function['Timeout'],
                        'region': region,
                        'last_modified': function['LastModified'],
                        'description': function.get('Description', ''),
                        'handler': function['Handler'],
                        'size': function['CodeSize']
                    }
                    
                    region_functions.append(function_info)
                
                return region_functions
            except Exception as e:
                logger.error(f"Error collecting Lambda functions in region {region}: {e}")
                return []
        
        # 並列処理で各リージョンの関数情報を収集
        with ThreadPoolExecutor(max_workers=min(10, len(self.regions))) as executor:
            future_to_region = {executor.submit(collect_region_functions, region): region for region in self.regions}
            
            for future in as_completed(future_to_region):
                region = future_to_region[future]
                try:
                    region_functions = future.result()
                    functions.extend(region_functions)
                except Exception as e:
                    logger.error(f"Error processing Lambda functions in region {region}: {e}")
        
        return functions
```

3. `src/main.py` に新しいコレクターを追加します：

```python
# メインスクリプトでのインポート追加
from collectors.lambda_collector import LambdaCollector

# main()関数内での処理追加
# Collect Lambda function data
logger.info(f"Collecting Lambda function information for regions: {regions}")
lambda_collector = LambdaCollector(regions)
resource_data['lambda_functions'] = lambda_collector.collect()
```

4. `src/report_generator.py` ファイルを更新して、新しいリソースタイプの情報をレポートに追加します：

```python
def _generate_lambda_functions(self):
    """Lambda関数詳細セクションを生成"""
    lambda_functions = self.resource_data.get('lambda_functions', [])
    
    if not lambda_functions:
        return "## Lambda関数詳細\n\nLambda関数のデータはありません。"
    
    # Lambda関数の表を作成
    table = (
        "## Lambda関数詳細\n"
        "\n"
        "| 関数名 | ランタイム | メモリ(MB) | タイムアウト(秒) | リージョン | 最終更新日時 | サイズ(バイト) |\n"
        "| --- | --- | ---: | ---: | --- | --- | ---: |\n"
    )
    
    for function in lambda_functions:
        name = function['name']
        runtime = function['runtime']
        memory = function['memory']
        timeout = function['timeout']
        region = function['region']
        last_modified = function['last_modified'].split('T')[0] if function['last_modified'] else 'N/A'
        size = function['size']
        
        table += f"| {name} | {runtime} | {memory} | {timeout} | {region} | {last_modified} | {size} |\n"
    
    return table

# generate()メソッド内でセクションリストに追加
sections = [
    # 既存のセクション
    self._generate_header(),
    self._generate_summary(),
    # ...
    self._generate_lambda_functions(),  # 新しいセクションを追加
    # ...
]
```

5. `config.yml` ファイルも更新して、新しいリソースタイプの設定を追加します：

```yaml
resource_analysis:
  # 既存の設定
  ec2_instances: true
  # ...
  # 新しい設定
  lambda_functions: true
```

### レポート形式のカスタマイズ

レポートのフォーマットをカスタマイズするには、`src/report_generator.py` ファイルの各セクション生成メソッドを編集します。たとえば、EC2インスタンス詳細の表形式を変更する場合：

```python
def _generate_ec2_instances(self):
    """EC2インスタンス詳細セクションを生成（カスタマイズ版）"""
    ec2_instances = self.resource_data.get('ec2_instances', [])
    
    if not ec2_instances:
        return "## EC2インスタンス詳細\n\nEC2インスタンスのデータはありません。"
    
    # カスタマイズした表ヘッダーとフィールド
    table = (
        "## EC2インスタンス詳細\n"
        "\n"
        "| インスタンスID | 名前 | タイプ | 状態 | IP アドレス | VPC ID | タグ |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n"
    )
    
    for instance in ec2_instances:
        instance_id = instance['id']
        name = instance['name'] or 'N/A'
        instance_type = instance['type']
        state = instance['state']
        ip_address = instance.get('public_ip', '') or instance.get('private_ip', 'N/A')
        vpc_id = instance.get('vpc_id', 'N/A')
        
        # タグをフォーマット
        tags = instance.get('tags', [])
        tag_str = ', '.join([f"{tag['Key']}={tag['Value']}" for tag in tags if tag['Key'] != 'Name'])
        
        table += f"| {instance_id} | {name} | {instance_type} | {state} | {ip_address} | {vpc_id} | {tag_str} |\n"
    
    return table
```

### コスト計算ロジックのカスタマイズ

コスト計算やコスト最適化推奨ロジックをカスタマイズするには、`src/collectors/cost_explorer.py` ファイルや `src/report_generator.py` ファイルの関連メソッドを編集します。

例えば、EC2インスタンスの最適化推奨ロジックをカスタマイズするには：

```python
def _generate_optimization_recommendations(self):
    """コスト最適化の推奨事項セクションを生成（カスタマイズ版）"""
    recommendations = []
    
    # EC2インスタンスの最適化推奨事項
    ec2_instances = self.resource_data.get('ec2_instances', [])
    if ec2_instances:
        # 停止中のインスタンスを検出
        stopped_instances = [i for i in ec2_instances if i['state'] == 'stopped']
        if stopped_instances:
            stopped_names = ', '.join([f"{i['id']} ({i['name']})" for i in stopped_instances[:5]])
            if len(stopped_instances) > 5:
                stopped_names += f" 他 {len(stopped_instances) - 5} 件"
            
            recommendations.append(f"- **停止中のEC2インスタンス**: {len(stopped_instances)}個のインスタンスが停止状態です。不要であれば削除を検討してください: {stopped_names}")
        
        # 大型インスタンスタイプの検出（カスタマイズ部分）
        large_instance_prefixes = ['m5.2xlarge', 'm5.4xlarge', 'c5.2xlarge', 'c5.4xlarge', 'r5.2xlarge', 'r5.4xlarge']
        large_instances = [i for i in ec2_instances if any(i['type'].startswith(prefix) for prefix in large_instance_prefixes)]
        if large_instances:
            large_names = ', '.join([f"{i['id']} ({i['type']})" for i in large_instances[:5]])
            if len(large_instances) > 5:
                large_names += f" 他 {len(large_instances) - 5} 件"
            
            recommendations.append(f"- **大型EC2インスタンス**: {len(large_instances)}個の大型インスタンスが使用されています。必要なリソースを見直し、必要に応じてダウンサイジングを検討してください: {large_names}")
    
    # レコメンデーションを結合
    if recommendations:
        return "## コスト最適化の推奨事項\n\n" + "\n\n".join(recommendations)
    else:
        return "## コスト最適化の推奨事項\n\n推奨事項はありません。"
```

## 高度なカスタマイズのヒント

### AWS SDK の追加機能の利用

boto3 (AWS SDK for Python) には様々な機能があります。例えば、コストと使用状況レポート (CUR) やコスト異常検出、コスト最適化推奨事項など、より高度なAWSコスト管理APIを活用できます。

### データの可視化拡張

マークダウン形式のレポートに加えて、データ可視化やインタラクティブなダッシュボードを追加することも可能です：

1. データをJSON形式で出力する機能を追加
2. HTML+JavaScript（例：Chart.js, D3.js）でデータを可視化
3. Dashingなどのダッシュボードフレームワークとの連携

### 通知機能の追加

コスト増加や異常値検出時に自動通知する機能を追加できます：

1. Amazon SNS による通知
2. Slack / Microsoft Teams へのメッセージ送信
3. メール通知

例えば、前回のレポートと比較して大幅なコスト増加を検出した場合に通知する機能を追加できます：

```python
def _check_cost_anomalies(self, threshold_percent=10.0):
    """
    コスト増加を検出して通知する
    
    Args:
        threshold_percent (float): 通知する増加率のしきい値
    """
    comparison = self.cost_data.get('previous_period_comparison', {})
    change_percent = comparison.get('change_percent', 0)
    
    if change_percent > threshold_percent:
        # SNS通知の設定例
        sns = boto3.client('sns')
        topic_arn = 'arn:aws:sns:us-east-1:123456789012:CostAlerts'
        
        message = f"""
        AWS コスト増加アラート
        
        前期間比: {change_percent:.2f}% 増加
        増加額: {comparison.get('change_amount', 0):.2f} {self.cost_data.get('total_cost', {}).get('currency', 'USD')}
        期間: {self.start_date} から {self.end_date}
        
        詳細は最新のコストレポートを確認してください。
        """
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=f'[AWS コストアラート] {change_percent:.2f}% 増加を検出',
            Message=message
        )
```

### データのエクスポート機能

コレクトしたデータを他のシステムやツールで利用できるように、データをエクスポートする機能を追加できます：

1. JSONやCSV形式でのデータエクスポート
2. データベース（RDS、DynamoDB）への保存
3. Amazon Athena や Amazon QuickSight との連携

例えば、コレクトしたデータをCSV形式でエクスポートする機能を追加する場合：

```python
def export_to_csv(self, output_dir):
    """
    収集したデータをCSVファイルとしてエクスポート
    
    Args:
        output_dir (str): 出力ディレクトリ
    """
    import csv
    import os
    from datetime import datetime
    
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # EC2インスタンス情報をCSVとしてエクスポート
    ec2_instances = self.resource_data.get('ec2_instances', [])
    if ec2_instances:
        ec2_file = os.path.join(output_dir, f'ec2_instances_{timestamp}.csv')
        with open(ec2_file, 'w', newline='') as f:
            fieldnames = ['id', 'name', 'type', 'state', 'region', 'launch_time', 'public_ip', 'private_ip']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for instance in ec2_instances:
                writer.writerow({k: instance.get(k, '') for k in fieldnames})
    
    # 同様に他のリソースタイプもCSVとしてエクスポート
    # ...
```

### 外部サービスとの連携

レポートツールを外部サービスと連携させることで、より高度な分析やワークフローを実現できます：

1. FinOps管理ツール（CloudHealth, CloudAbilit）との連携
2. チケット管理システム（Jira, ServiceNow）との連携
3. プロジェクト管理ツール（GitHub Issues, Trello）との連携

例えば、コスト最適化推奨事項に基づいて自動的にJiraチケットを作成する機能を追加できます：

```python
def create_jira_tickets(self):
    """
    コスト最適化推奨事項に基づいてJiraチケットを作成
    """
    from jira import JIRA
    
    # Jira接続設定
    jira = JIRA(
        server='https://your-jira-instance.atlassian.net',
        basic_auth=('your-email@example.com', 'your-api-token')
    )
    
    # EC2インスタンスの最適化推奨事項
    ec2_instances = self.resource_data.get('ec2_instances', [])
    if ec2_instances:
        # 停止中のインスタンスを検出
        stopped_instances = [i for i in ec2_instances if i['state'] == 'stopped']
        if stopped_instances:
            # Jiraチケットの作成
            issue_dict = {
                'project': {'key': 'COST'},
                'summary': f'AWS コスト最適化: {len(stopped_instances)}個の停止中EC2インスタンスを確認',
                'description': f'''
                以下の{len(stopped_instances)}個のEC2インスタンスが停止状態です。不要なインスタンスは削除を検討してください。
                
                {chr(10).join([f"- {i['id']} ({i['name']}) - リージョン: {i['region']} - 停止日時: {i['launch_time']}" for i in stopped_instances])}
                ''',
                'issuetype': {'name': 'Task'},
                'priority': {'name': 'Medium'},
                'labels': ['aws-cost-optimization', 'ec2-instances']
            }
            
            jira.create_issue(fields=issue_dict)
```

これらの高度なカスタマイズやエクステンションを組み合わせることで、AWS環境の複雑さやニーズに合わせた包括的なリソース・コスト管理ソリューションを構築できます。
