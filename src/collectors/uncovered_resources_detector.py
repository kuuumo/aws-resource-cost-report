#!/usr/bin/env python3

import boto3
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class UncoveredResourcesDetector:
    """
    Cost Explorer APIを使用して、課金されているがレポートに含まれていないリソースを検出するクラス
    """
    
    def __init__(self, start_date, end_date, current_resources=None):
        """
        初期化
        
        Args:
            start_date (str): コスト分析の開始日 (YYYY-MM-DD形式)
            end_date (str): コスト分析の終了日 (YYYY-MM-DD形式)
            current_resources (dict): 現在収集対象のリソース情報（任意）
        """
        self.start_date = start_date
        self.end_date = end_date
        self.client = boto3.client('ce')
        self.current_resources = current_resources or {}
        
        # サービス名とリソースタイプのマッピング
        self.service_resource_mapping = {
            'Amazon Elastic Compute Cloud - Compute': 'ec2_instances',
            'Amazon Relational Database Service': 'rds_instances',
            'Amazon ElastiCache': 'elasticache_clusters',
            'Amazon Simple Storage Service': 's3_buckets',
            'Amazon Route 53': 'route53_resources',
            'Amazon DynamoDB': 'dynamodb_tables',
            'AWS Lambda': 'lambda_functions',
            'Amazon API Gateway': 'api_gateways',
            'AWS Step Functions': 'step_functions',
            'Amazon OpenSearch Service': 'opensearch_domains',
            'Amazon Elastic Container Service': 'ecs_clusters',
            'Amazon Elastic Kubernetes Service': 'eks_clusters',
            'AWS Fargate': 'fargate_resources',
            'Amazon SageMaker': 'sagemaker_resources',
            'Amazon CloudFront': 'cloudfront_distributions',
            'Application Load Balancer': 'load_balancers',
            'Network Load Balancer': 'load_balancers',
            'Amazon Elastic File System': 'efs_filesystems',
            'Amazon FSx': 'fsx_filesystems',
            'Amazon Redshift': 'redshift_clusters',
            'Amazon Aurora': 'aurora_clusters',
            'Amazon DocumentDB': 'documentdb_clusters',
            'Amazon Neptune': 'neptune_clusters',
            'Amazon Elasticsearch Service': 'elasticsearch_domains',
            'Amazon Managed Streaming for Apache Kafka': 'msk_clusters',
            'Amazon Kinesis': 'kinesis_streams',
            'Amazon QuickSight': 'quicksight_resources',
            'AWS Glue': 'glue_resources',
            'Amazon Athena': 'athena_resources',
            'Amazon AppFlow': 'appflow_resources',
        }
        
        # カスタム正規表現パターン（サービス名にばらつきがある場合に対応）
        self.service_patterns = {
            'EC2': ['ec2_instances', 'ebs_volumes'],
            'RDS': ['rds_instances'],
            'S3': ['s3_buckets'],
            'ElastiCache': ['elasticache_clusters'],
            'Lambda': ['lambda_functions'],
            'DynamoDB': ['dynamodb_tables'],
            'ECS': ['ecs_clusters'],
            'EKS': ['eks_clusters'],
            'SageMaker': ['sagemaker_resources'],
            'CloudFront': ['cloudfront_distributions'],
            'Load Balancer': ['load_balancers'],
            'EFS': ['efs_filesystems'],
            'FSx': ['fsx_filesystems'],
            'Redshift': ['redshift_clusters'],
            'Aurora': ['aurora_clusters'],
            'Kinesis': ['kinesis_streams'],
        }
    
    def detect(self):
        """
        課金されているが収集対象に含まれていないリソースを検出し、
        可能であれば自動的に収集する
        
        Returns:
            dict: 未カバーリソースの情報と取得したリソースデータ
        """
        try:
            logger.info("Detecting and collecting billed resources...")
            
            # サービス別のコスト内訳を取得
            service_costs = self._get_service_costs()
            
            # リソースタイプ別のコスト内訳を取得
            usage_type_costs = self._get_usage_type_costs()
            
            # 課金されているサービスの一覧を取得
            billed_services = [service['service_name'] for service in service_costs]
            logger.info(f"Found {len(billed_services)} billed services")
            
            # 各サービスのリソース情報を収集
            collected_resources = self._collect_billed_resources(billed_services)
            
            # それでも収集できなかったリソースを検出
            uncovered_resources = self._detect_uncovered_resources(service_costs, usage_type_costs)
            
            # 結果を統合
            result = {
                'billed_services': billed_services,
                'collected_resources': collected_resources,
                'uncovered_resources': uncovered_resources.get('uncovered_resources', []),
                'total_uncovered_cost': uncovered_resources.get('total_uncovered_cost', 0.0),
                'currency': uncovered_resources.get('currency', 'USD')
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting billed resources: {e}", exc_info=True)
            return {
                'billed_services': [],
                'collected_resources': {},
                'uncovered_resources': [],
                'total_uncovered_cost': 0.0,
                'currency': 'USD'
            }
    
    def _get_service_costs(self):
        """
        サービス別のコスト内訳を取得
        
        Returns:
            list: サービス別コスト情報のリスト
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': self.start_date,
                    'End': self.end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            service_costs = []
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service_name = group['Keys'][0]
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    currency = group['Metrics']['UnblendedCost']['Unit']
                    
                    if amount > 0.1:  # 少額のサービスは無視
                        service_costs.append({
                            'service_name': service_name,
                            'amount': amount,
                            'currency': currency
                        })
            
            # コストの降順でソート
            service_costs.sort(key=lambda x: x['amount'], reverse=True)
            
            return service_costs
            
        except Exception as e:
            logger.error(f"Error getting service costs: {e}")
            return []
    
    def _get_usage_type_costs(self):
        """
        使用タイプ別のコスト内訳を取得
        
        Returns:
            list: 使用タイプ別コスト情報のリスト
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': self.start_date,
                    'End': self.end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'USAGE_TYPE'
                    }
                ]
            )
            
            usage_type_costs = []
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    usage_type = group['Keys'][0]
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    currency = group['Metrics']['UnblendedCost']['Unit']
                    
                    if amount > 0.1:  # 少額の使用タイプは無視
                        usage_type_costs.append({
                            'usage_type': usage_type,
                            'amount': amount,
                            'currency': currency
                        })
            
            # コストの降順でソート
            usage_type_costs.sort(key=lambda x: x['amount'], reverse=True)
            
            return usage_type_costs
            
        except Exception as e:
            logger.error(f"Error getting usage type costs: {e}")
            return []
    
    def _detect_uncovered_resources(self, service_costs, usage_type_costs):
        """
        未カバーのサービスや使用タイプを検出
        
        Args:
            service_costs (list): サービス別コスト情報
            usage_type_costs (list): 使用タイプ別コスト情報
            
        Returns:
            dict: 未カバーリソースの情報
        """
        # 現在収集対象のリソースタイプのリスト
        covered_resource_types = set(self.current_resources.keys())
        
        # 未カバーのサービス
        uncovered_services = []
        total_uncovered_cost = 0.0
        currency = 'USD'
        
        for service in service_costs:
            service_name = service['service_name']
            amount = service['amount']
            currency = service['currency']
            
            # サービス名からリソースタイプを推定
            resource_type = self._get_resource_type_from_service(service_name)
            
            # リソースタイプが不明または現在のレポートに含まれていない場合
            if resource_type and not any(rt in covered_resource_types for rt in resource_type):
                uncovered_services.append({
                    'service_name': service_name,
                    'estimated_resource_types': resource_type,
                    'amount': amount,
                    'currency': currency
                })
                total_uncovered_cost += amount
        
        # 未カバーの使用タイプ（サービスベースでは検出できない細かいリソース）
        uncovered_usage_types = []
        
        for usage_type in usage_type_costs:
            usage_type_name = usage_type['usage_type']
            amount = usage_type['amount']
            
            # 使用タイプからリソースタイプを推定
            resource_type = self._get_resource_type_from_usage_type(usage_type_name)
            
            # サービスですでに検出済みのものは除外
            already_detected = any(
                s.get('estimated_resource_types') == resource_type 
                for s in uncovered_services if s.get('estimated_resource_types')
            )
            
            # リソースタイプが推定でき、カバーされておらず、まだ検出されていない場合
            if (resource_type and not any(rt in covered_resource_types for rt in resource_type) 
                    and not already_detected):
                uncovered_usage_types.append({
                    'usage_type': usage_type_name,
                    'estimated_resource_types': resource_type,
                    'amount': amount,
                    'currency': usage_type['currency']
                })
                total_uncovered_cost += amount
        
        # 重複を排除し、コスト順にソート
        all_uncovered = uncovered_services + uncovered_usage_types
        all_uncovered.sort(key=lambda x: x['amount'], reverse=True)
        
        return {
            'uncovered_resources': all_uncovered,
            'total_uncovered_cost': total_uncovered_cost,
            'currency': currency
        }
    
    def _get_resource_type_from_service(self, service_name):
        """
        サービス名からリソースタイプを推定
        
        Args:
            service_name (str): AWSサービス名
            
        Returns:
            list: 推定されるリソースタイプのリスト
        """
        # 完全一致のマッピングをチェック
        if service_name in self.service_resource_mapping:
            return [self.service_resource_mapping[service_name]]
        
        # パターンマッチングを試行
        for pattern, resource_types in self.service_patterns.items():
            if pattern.lower() in service_name.lower():
                return resource_types
        
        # 未知のサービスの場合は空リストを返す
        return []
    
    def _get_resource_type_from_usage_type(self, usage_type):
        """
        使用タイプからリソースタイプを推定
        
        Args:
            usage_type (str): AWS使用タイプ
            
        Returns:
            list: 推定されるリソースタイプのリスト
        """
        usage_type_lower = usage_type.lower()
        
        # 使用タイプに基づくリソースタイプの推定
        if 'box-usage' in usage_type_lower or 'instance' in usage_type_lower:
            return ['ec2_instances']
        elif 'ebs' in usage_type_lower or 'volume' in usage_type_lower:
            return ['ebs_volumes']
        elif 'rds' in usage_type_lower or 'database' in usage_type_lower:
            return ['rds_instances']
        elif 's3' in usage_type_lower or 'bucket' in usage_type_lower:
            return ['s3_buckets']
        elif 'elasticache' in usage_type_lower or 'cache' in usage_type_lower:
            return ['elasticache_clusters']
        elif 'lambda' in usage_type_lower or 'function' in usage_type_lower:
            return ['lambda_functions']
        elif 'dynamodb' in usage_type_lower or 'table' in usage_type_lower:
            return ['dynamodb_tables']
        elif 'elb' in usage_type_lower or 'loadbalancer' in usage_type_lower:
            return ['load_balancers']
        elif 'eks' in usage_type_lower or 'kubernetes' in usage_type_lower:
            return ['eks_clusters']
        elif 'ecs' in usage_type_lower or 'container' in usage_type_lower:
            return ['ecs_clusters']
        elif 'gateway' in usage_type_lower or 'apigw' in usage_type_lower:
            return ['api_gateways']
        elif 'route53' in usage_type_lower or 'dns' in usage_type_lower:
            return ['route53_resources']
        elif 'redshift' in usage_type_lower:
            return ['redshift_clusters']
        elif 'sagemaker' in usage_type_lower:
            return ['sagemaker_resources']
        elif 'sns' in usage_type_lower:
            return ['sns_topics']
        elif 'sqs' in usage_type_lower:
            return ['sqs_queues']
        elif 'kinesis' in usage_type_lower:
            return ['kinesis_streams']
        elif 'glue' in usage_type_lower:
            return ['glue_resources']
        elif 'cloudfront' in usage_type_lower:
            return ['cloudfront_distributions']
        elif 'efs' in usage_type_lower:
            return ['efs_filesystems']
        
        # 未知の使用タイプの場合は空リストを返す
        return []
        
    def _collect_billed_resources(self, billed_services):
        """
        課金されているサービスのリソース情報を動的に収集
        
        Args:
            billed_services (list): 課金されているサービス名のリスト
            
        Returns:
            dict: 収集したリソース情報
        """
        result = {}
        
        # リージョン情報を取得
        session = boto3.Session()
        regions = session.get_available_regions('ec2')
        
        # サービス名からリソースタイプと収集メソッドを推定・実行
        for service_name in billed_services:
            resource_types = self._get_resource_type_from_service(service_name)
            
            if not resource_types:
                logger.warning(f"Unknown resource type for service: {service_name}")
                continue
            
            for resource_type in resource_types:
                # すでに収集済みのリソースタイプはスキップ
                if resource_type in result:
                    continue
                
                # リソースタイプに応じた収集メソッドを呼び出し
                collection_method = self._get_collection_method(resource_type)
                if collection_method:
                    try:
                        logger.info(f"Collecting {resource_type} for service: {service_name}")
                        resources = collection_method(regions)
                        result[resource_type] = resources
                        logger.info(f"Collected {len(resources) if not isinstance(resources, dict) else 'multiple'} {resource_type}")
                    except Exception as e:
                        logger.error(f"Error collecting {resource_type}: {e}")
                else:
                    logger.warning(f"No collection method available for resource type: {resource_type}")
        
        return result
    
    def _get_collection_method(self, resource_type):
        """
        リソースタイプに応じた収集メソッドを返す
        
        Args:
            resource_type (str): リソースタイプ名
            
        Returns:
            function: 収集メソッド
        """
        # リソースタイプと収集メソッドのマッピング
        collection_methods = {
            'ec2_instances': self._collect_ec2_instances,
            'ebs_volumes': self._collect_ebs_volumes,
            'rds_instances': self._collect_rds_instances,
            's3_buckets': self._collect_s3_buckets,
            'elasticache_clusters': self._collect_elasticache_clusters,
            'load_balancers': self._collect_load_balancers,
            'dynamodb_tables': self._collect_dynamodb_tables,
            'lambda_functions': self._collect_lambda_functions,
            'ecs_clusters': self._collect_ecs_clusters,
            'eks_clusters': self._collect_eks_clusters,
            'cloudfront_distributions': self._collect_cloudfront,
            'efs_filesystems': self._collect_efs,
            'api_gateways': self._collect_api_gateway,
            'route53_resources': self._collect_route53,
            'redshift_clusters': self._collect_redshift,
            'sagemaker_resources': self._collect_sagemaker,
            'sns_topics': self._collect_sns,
            'sqs_queues': self._collect_sqs,
            'kinesis_streams': self._collect_kinesis,
            'glue_resources': self._collect_glue
        }
        
        return collection_methods.get(resource_type)
