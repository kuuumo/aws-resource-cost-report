#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
S3リソース情報収集モジュール
"""

import logging
from typing import Dict, List, Any
from .base_collector import BaseCollector

# ロギングの設定
logger = logging.getLogger(__name__)

class S3Collector(BaseCollector):
    """S3リソース情報を収集するクラス"""
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        S3リソース情報を収集
        
        Returns:
            Dict: S3リソース情報
        """
        logger.info("S3リソース情報の収集を開始します")
        results = {}
        
        try:
            # S3クライアントを取得
            s3_client = self.get_client('s3')
            
            # バケット情報を取得
            buckets = self._collect_buckets(s3_client)
            if buckets:
                results['S3_Buckets'] = buckets
                
        except Exception as e:
            logger.error(f"S3リソース情報収集中にエラー発生: {str(e)}")
        
        return results
    
    def _collect_buckets(self, s3_client) -> List[Dict[str, Any]]:
        """S3バケット情報を収集"""
        logger.info("S3バケット情報を収集しています")
        buckets = []
        
        try:
            response = s3_client.list_buckets()
            
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                
                # バケット情報の初期化
                bucket_info = {
                    'ResourceId': bucket_name,
                    'ResourceName': bucket_name,
                    'ResourceType': 'Bucket',
                    'CreationDate': bucket.get('CreationDate', ''),
                    'Region': 'unknown',
                    'Versioning': 'Disabled',
                    'WebsiteEnabled': False,
                    'Tags': []
                }
                
                # リージョン情報を取得
                try:
                    location = s3_client.get_bucket_location(Bucket=bucket_name)
                    region = location.get('LocationConstraint')
                    # None または '' の場合は 'us-east-1'
                    bucket_info['Region'] = region if region else 'us-east-1'
                except Exception as e:
                    logger.warning(f"バケット '{bucket_name}' のリージョン取得エラー: {str(e)}")
                
                # バージョニング状態を取得
                try:
                    versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
                    if versioning.get('Status') == 'Enabled':
                        bucket_info['Versioning'] = 'Enabled'
                    elif versioning.get('Status') == 'Suspended':
                        bucket_info['Versioning'] = 'Suspended'
                except Exception as e:
                    logger.warning(f"バケット '{bucket_name}' のバージョニング状態取得エラー: {str(e)}")
                
                # ウェブサイト設定を確認
                try:
                    s3_client.get_bucket_website(Bucket=bucket_name)
                    bucket_info['WebsiteEnabled'] = True
                except Exception as e:
                    # ウェブサイト設定がない場合は例外が発生するが問題ない
                    pass
                
                # タグ情報を取得
                try:
                    tags = s3_client.get_bucket_tagging(Bucket=bucket_name)
                    bucket_info['Tags'] = tags.get('TagSet', [])
                except Exception as e:
                    # タグがない場合は例外が発生するが問題ない
                    pass
                
                # 暗号化設定を確認
                try:
                    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
                    rules = encryption.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
                    if rules:
                        bucket_info['Encryption'] = 'Enabled'
                        # 暗号化タイプを取得
                        encryption_types = []
                        for rule in rules:
                            if 'ApplyServerSideEncryptionByDefault' in rule:
                                encryption_types.append(
                                    rule['ApplyServerSideEncryptionByDefault'].get('SSEAlgorithm', 'unknown')
                                )
                        bucket_info['EncryptionType'] = ', '.join(encryption_types)
                    else:
                        bucket_info['Encryption'] = 'Disabled'
                except Exception as e:
                    # 暗号化設定がない場合は例外が発生するが問題ない
                    bucket_info['Encryption'] = 'Disabled'
                
                # バケットサイズとオブジェクト数の取得（CloudWatchメトリクスからの取得は避ける）
                bucket_info['BucketSize'] = 'Unknown'
                bucket_info['ObjectCount'] = 'Unknown'
                
                buckets.append(bucket_info)
            
            logger.info(f"S3バケット: {len(buckets)}件取得")
        except Exception as e:
            logger.error(f"S3バケット情報収集中にエラー発生: {str(e)}")
        
        return buckets
