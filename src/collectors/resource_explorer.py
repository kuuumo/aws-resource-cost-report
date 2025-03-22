#!/usr/bin/env python3

import boto3
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

logger = logging.getLogger(__name__)

class ResourceExplorerCollector:
    """AWS リソース情報を収集するクラス"""
    
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
        各種AWSリソース情報を収集
        
        Returns:
            dict: 収集したリソース情報
        """
        # 対象リージョンリストを取得
        if self.regions == 'all':
            available_regions = self.session.get_available_regions('ec2')
            self.regions = available_regions
        
        logger.info(f"Collecting resource information for regions: {self.regions}")
        
        result = {}
        
        # EC2インスタンス情報を収集
        result['ec2_instances'] = self._collect_ec2_instances()
        
        # RDSインスタンス情報を収集
        result['rds_instances'] = self._collect_rds_instances()
        
        # S3バケット情報を収集
        result['s3_buckets'] = self._collect_s3_buckets()
        
        # ElastiCacheクラスター情報を収集
        result['elasticache_clusters'] = self._collect_elasticache_clusters()
        
        # ELBロードバランサー情報を収集
        result['load_balancers'] = self._collect_load_balancers()
        
        return result
    
    def _collect_ec2_instances(self):
        """
        EC2インスタンス情報を収集
        
        Returns:
            list: EC2インスタンス情報のリスト
        """
        instances = []
        
        def collect_region_instances(region):
            try:
                ec2 = self.session.client('ec2', region_name=region)
                response = ec2.describe_instances()
                region_instances = []
                
                for reservation in response['Reservations']:
                    for instance in reservation['Instances']:
                        # インスタンス名タグを抽出
                        name = ''
                        if 'Tags' in instance:
                            for tag in instance['Tags']:
                                if tag['Key'] == 'Name':
                                    name = tag['Value']
                                    break
                        
                        # インスタンス情報を収集
                        instance_info = {
                            'id': instance['InstanceId'],
                            'name': name,
                            'type': instance['InstanceType'],
                            'state': instance['State']['Name'],
                            'az': instance['Placement']['AvailabilityZone'],
                            'region': region,
                            'launch_time': instance['LaunchTime'].isoformat() if 'LaunchTime' in instance else '',
                            'public_ip': instance.get('PublicIpAddress', ''),
                            'private_ip': instance.get('PrivateIpAddress', ''),
                            'platform': instance.get('Platform', 'Linux/UNIX'),
                            'vpc_id': instance.get('VpcId', ''),
                            'tags': instance.get('Tags', [])
                        }
                        
                        region_instances.append(instance_info)
                
                return region_instances
            except Exception as e:
                logger.error(f"Error collecting EC2 instances in region {region}: {e}")
                return []
        
        # 並列処理で各リージョンのインスタンス情報を収集
        with ThreadPoolExecutor(max_workers=min(10, len(self.regions))) as executor:
            future_to_region = {executor.submit(collect_region_instances, region): region for region in self.regions}
            
            for future in as_completed(future_to_region):
                region = future_to_region[future]
                try:
                    region_instances = future.result()
                    instances.extend(region_instances)
                except Exception as e:
                    logger.error(f"Error processing EC2 instances in region {region}: {e}")
        
        return instances
    
    def _collect_rds_instances(self):
        """
        RDSインスタンス情報を収集
        
        Returns:
            list: RDSインスタンス情報のリスト
        """
        instances = []
        
        def collect_region_instances(region):
            try:
                rds = self.session.client('rds', region_name=region)
                response = rds.describe_db_instances()
                region_instances = []
                
                for instance in response['DBInstances']:
                    # インスタンス情報を収集
                    instance_info = {
                        'id': instance['DBInstanceIdentifier'],
                        'engine': instance['Engine'],
                        'version': instance['EngineVersion'],
                        'class': instance['DBInstanceClass'],
                        'status': instance['DBInstanceStatus'],
                        'region': region,
                        'storage': instance['AllocatedStorage'],
                        'endpoint': instance.get('Endpoint', {}).get('Address', ''),
                        'multi_az': instance['MultiAZ'],
                        'create_time': instance['InstanceCreateTime'].isoformat() if 'InstanceCreateTime' in instance else '',
                        'vpc_id': instance.get('DBSubnetGroup', {}).get('VpcId', '')
                    }
                    
                    region_instances.append(instance_info)
                
                return region_instances
            except Exception as e:
                logger.error(f"Error collecting RDS instances in region {region}: {e}")
                return []
        
        # 並列処理で各リージョンのインスタンス情報を収集
        with ThreadPoolExecutor(max_workers=min(10, len(self.regions))) as executor:
            future_to_region = {executor.submit(collect_region_instances, region): region for region in self.regions}
            
            for future in as_completed(future_to_region):
                region = future_to_region[future]
                try:
                    region_instances = future.result()
                    instances.extend(region_instances)
                except Exception as e:
                    logger.error(f"Error processing RDS instances in region {region}: {e}")
        
        return instances
    
    def _collect_s3_buckets(self):
        """
        S3バケット情報を収集
        
        Returns:
            list: S3バケット情報のリスト
        """
        try:
            # S3はグローバルサービスなのでリージョン指定なし
            s3 = self.session.client('s3')
            response = s3.list_buckets()
            
            buckets = []
            
            for bucket in response['Buckets']:
                # バケットのリージョンを取得
                try:
                    location = s3.get_bucket_location(Bucket=bucket['Name'])
                    region = location['LocationConstraint']
                    if region is None:
                        region = 'us-east-1'  # None の場合は us-east-1
                except Exception as e:
                    logger.warning(f"Error getting bucket location for {bucket['Name']}: {e}")
                    region = 'unknown'
                
                # バケットのサイズを取得 (CloudWatch Metrics から)
                try:
                    cloudwatch = self.session.client('cloudwatch', region_name=region)
                    size_response = cloudwatch.get_metric_statistics(
                        Namespace='AWS/S3',
                        MetricName='BucketSizeBytes',
                        Dimensions=[
                            {'Name': 'BucketName', 'Value': bucket['Name']},
                            {'Name': 'StorageType', 'Value': 'StandardStorage'}
                        ],
                        StartTime=bucket['CreationDate'] - datetime.timedelta(days=1),
                        EndTime=datetime.datetime.utcnow(),
                        Period=86400,  # 1日
                        Statistics=['Average']
                    )
                    
                    if size_response['Datapoints']:
                        size_bytes = size_response['Datapoints'][0]['Average']
                    else:
                        size_bytes = 0
                except Exception as e:
                    logger.warning(f"Error getting bucket size for {bucket['Name']}: {e}")
                    size_bytes = 0
                
                bucket_info = {
                    'name': bucket['Name'],
                    'creation_date': bucket['CreationDate'].isoformat(),
                    'region': region,
                    'size_bytes': size_bytes
                }
                
                buckets.append(bucket_info)
            
            return buckets
            
        except Exception as e:
            logger.error(f"Error collecting S3 buckets: {e}")
            return []
    
    def _collect_elasticache_clusters(self):
        """
        ElastiCache クラスター情報を収集
        
        Returns:
            list: ElastiCache クラスター情報のリスト
        """
        clusters = []
        
        def collect_region_clusters(region):
            try:
                elasticache = self.session.client('elasticache', region_name=region)
                response = elasticache.describe_cache_clusters()
                region_clusters = []
                
                for cluster in response['CacheClusters']:
                    cluster_info = {
                        'id': cluster['CacheClusterId'],
                        'engine': cluster['Engine'],
                        'version': cluster['EngineVersion'],
                        'node_type': cluster['CacheNodeType'],
                        'num_nodes': cluster['NumCacheNodes'],
                        'status': cluster['CacheClusterStatus'],
                        'region': region,
                        'create_time': cluster['CacheClusterCreateTime'].isoformat() if 'CacheClusterCreateTime' in cluster else '',
                        'vpc_id': cluster.get('CacheSubnetGroupName', '')
                    }
                    
                    region_clusters.append(cluster_info)
                
                return region_clusters
            except Exception as e:
                logger.error(f"Error collecting ElastiCache clusters in region {region}: {e}")
                return []
        
        # 並列処理で各リージョンのクラスター情報を収集
        with ThreadPoolExecutor(max_workers=min(10, len(self.regions))) as executor:
            future_to_region = {executor.submit(collect_region_clusters, region): region for region in self.regions}
            
            for future in as_completed(future_to_region):
                region = future_to_region[future]
                try:
                    region_clusters = future.result()
                    clusters.extend(region_clusters)
                except Exception as e:
                    logger.error(f"Error processing ElastiCache clusters in region {region}: {e}")
        
        return clusters
    
    def _collect_load_balancers(self):
        """
        ELB (ロードバランサー) 情報を収集
        
        Returns:
            dict: ELB 情報の辞書 (Classic, ALB, NLB)
        """
        load_balancers = {
            'classic': [],
            'application': [],
            'network': []
        }
        
        def collect_region_lbs(region):
            try:
                # Classic Load Balancer
                elb = self.session.client('elb', region_name=region)
                classic_response = elb.describe_load_balancers()
                
                classic_lbs = []
                for lb in classic_response['LoadBalancerDescriptions']:
                    lb_info = {
                        'name': lb['LoadBalancerName'],
                        'dns_name': lb['DNSName'],
                        'created_time': lb['CreatedTime'].isoformat(),
                        'scheme': lb.get('Scheme', 'internet-facing'),
                        'vpc_id': lb.get('VPCId', ''),
                        'region': region
                    }
                    classic_lbs.append(lb_info)
                
                # Application & Network Load Balancer
                elbv2 = self.session.client('elbv2', region_name=region)
                elbv2_response = elbv2.describe_load_balancers()
                
                application_lbs = []
                network_lbs = []
                
                for lb in elbv2_response['LoadBalancers']:
                    lb_info = {
                        'name': lb['LoadBalancerName'],
                        'arn': lb['LoadBalancerArn'],
                        'dns_name': lb['DNSName'],
                        'created_time': lb['CreatedTime'].isoformat(),
                        'scheme': lb.get('Scheme', 'internet-facing'),
                        'vpc_id': lb.get('VpcId', ''),
                        'region': region
                    }
                    
                    if lb['Type'] == 'application':
                        application_lbs.append(lb_info)
                    elif lb['Type'] == 'network':
                        network_lbs.append(lb_info)
                
                return {
                    'classic': classic_lbs,
                    'application': application_lbs,
                    'network': network_lbs
                }
            except Exception as e:
                logger.error(f"Error collecting Load Balancers in region {region}: {e}")
                return {'classic': [], 'application': [], 'network': []}
        
        # 並列処理で各リージョンのロードバランサー情報を収集
        with ThreadPoolExecutor(max_workers=min(10, len(self.regions))) as executor:
            future_to_region = {executor.submit(collect_region_lbs, region): region for region in self.regions}
            
            for future in as_completed(future_to_region):
                region = future_to_region[future]
                try:
                    region_lbs = future.result()
                    load_balancers['classic'].extend(region_lbs['classic'])
                    load_balancers['application'].extend(region_lbs['application'])
                    load_balancers['network'].extend(region_lbs['network'])
                except Exception as e:
                    logger.error(f"Error processing Load Balancers in region {region}: {e}")
        
        return load_balancers
