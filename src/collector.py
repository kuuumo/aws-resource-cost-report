#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWS リソース情報収集モジュール
"""

import logging
import boto3
import botocore
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor

# サービス別コレクターをインポート
from collectors.ec2_collector import EC2Collector
from collectors.s3_collector import S3Collector
from collectors.rds_collector import RDSCollector
from collectors.lambda_collector import LambdaCollector
from collectors.dynamodb_collector import DynamoDBCollector
from collectors.cloudfront_collector import CloudFrontCollector
from collectors.route53_collector import Route53Collector
from collectors.iam_collector import IAMCollector
from collectors.cloudwatch_collector import CloudWatchCollector
from collectors.elasticache_collector import ElastiCacheCollector
from collectors.sns_collector import SNSCollector
from collectors.sqs_collector import SQSCollector

# ロギングの設定
logger = logging.getLogger(__name__)

class AWSResourceCollector:
    """AWS全サービスからリソース情報を収集するクラス"""

    def __init__(self, profile_name: Optional[str] = None, region_name: Optional[str] = None):
        """
        初期化関数
        
        Args:
            profile_name (str, optional): 使用するAWSプロファイル名
            region_name (str, optional): 対象AWSリージョン
        """
        self.session = boto3.Session(profile_name=profile_name, region_name=region_name)
        self.profile_name = profile_name
        self.region_name = region_name or self.session.region_name
        
        # 利用可能なリージョンのリストを取得
        self.available_regions = self._get_available_regions()
        logger.info(f"使用リージョン: {self.region_name}, 利用可能リージョン数: {len(self.available_regions)}")

    def _get_available_regions(self) -> List[str]:
        """
        EC2サービスで利用可能なリージョンのリストを取得
        
        Returns:
            List[str]: 利用可能なリージョンのリスト
        """
        try:
            ec2_client = self.session.client('ec2', region_name=self.region_name)
            regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
            return regions
        except Exception as e:
            logger.warning(f"利用可能なリージョンの取得に失敗しました: {str(e)}")
            # デフォルトの主要リージョンを返す
            return [
                'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
                'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3',
                'ap-south-1', 'ap-southeast-1', 'ap-southeast-2',
                'ca-central-1', 'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3'
            ]

    def collect_all_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        全AWSサービスのリソース情報を収集
        
        Returns:
            Dict: 全リソース情報
        """
        logger.info("全AWSリソース情報の収集を開始します")
        all_resources = {}
        
        # サービス別コレクターのリスト
        collectors = [
            EC2Collector(self.session, self.region_name),
            S3Collector(self.session, self.region_name),
            RDSCollector(self.session, self.region_name),
            LambdaCollector(self.session, self.region_name),
            DynamoDBCollector(self.session, self.region_name),
            CloudFrontCollector(self.session, self.region_name),
            Route53Collector(self.session, self.region_name),
            IAMCollector(self.session, self.region_name),
            CloudWatchCollector(self.session, self.region_name),
            ElastiCacheCollector(self.session, self.region_name),
            SNSCollector(self.session, self.region_name),
            SQSCollector(self.session, self.region_name)
        ]
        
        # 各コレクターからリソース情報を収集
        for collector in collectors:
            try:
                logger.info(f"{collector.__class__.__name__} からのリソース収集を開始します")
                resources = collector.collect()
                all_resources.update(resources)
                resource_count = sum(len(items) for items in resources.values())
                logger.info(f"{collector.__class__.__name__} から {resource_count} 件のリソース情報を収集しました")
            except Exception as e:
                logger.error(f"{collector.__class__.__name__} の実行中にエラー発生: {str(e)}")
        
        # 収集したリソース数のログ出力
        total_resources = sum(len(resources) for resources in all_resources.values())
        logger.info(f"合計 {len(all_resources)} 種類, {total_resources} 件のリソース情報を収集しました")
        
        return all_resources
