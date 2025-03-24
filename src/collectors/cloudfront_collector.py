#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudFront情報収集モジュール
"""

import logging
from typing import Dict, List, Any
from .base_collector import BaseCollector

# ロギングの設定
logger = logging.getLogger(__name__)

class CloudFrontCollector(BaseCollector):
    """CloudFront情報を収集するクラス"""
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        CloudFront情報を収集
        
        Returns:
            Dict: CloudFront情報
        """
        logger.info("CloudFront情報の収集を開始します")
        results = {}
        
        try:
            # CloudFrontはグローバルサービスなので、us-east-1リージョンを使用
            cloudfront_client = self.get_client('cloudfront', region='us-east-1')
            
            # ディストリビューション情報を取得
            distributions = self._collect_distributions(cloudfront_client)
            if distributions:
                results['CloudFront_Distributions'] = distributions
                
            # キャッシュポリシー情報を取得
            cache_policies = self._collect_cache_policies(cloudfront_client)
            if cache_policies:
                results['CloudFront_CachePolicies'] = cache_policies
                
            # オリジンリクエストポリシー情報を取得
            origin_request_policies = self._collect_origin_request_policies(cloudfront_client)
            if origin_request_policies:
                results['CloudFront_OriginRequestPolicies'] = origin_request_policies
                
            # 関数情報を取得
            functions = self._collect_functions(cloudfront_client)
            if functions:
                results['CloudFront_Functions'] = functions
                
        except Exception as e:
            logger.error(f"CloudFront情報収集中にエラー発生: {str(e)}")
        
        return results
    
    def _collect_distributions(self, cloudfront_client) -> List[Dict[str, Any]]:
        """CloudFrontディストリビューション情報を収集"""
        logger.info("CloudFrontディストリビューション情報を収集しています")
        distributions = []
        
        try:
            paginator = cloudfront_client.get_paginator('list_distributions')
            
            for page in paginator.paginate():
                dist_list = page.get('DistributionList', {})
                
                for dist_summary in dist_list.get('Items', []):
                    dist_id = dist_summary.get('Id', '')
                    
                    # タグを取得
                    tags = []
                    try:
                        if dist_id:
                            tag_response = cloudfront_client.list_tags_for_resource(
                                Resource=dist_summary.get('ARN', '')
                            )
                            tags = [
                                {'Key': tag['Key'], 'Value': tag['Value']}
                                for tag in tag_response.get('Tags', {}).get('Items', [])
                            ]
                    except Exception as e:
                        logger.warning(f"CloudFrontディストリビューション '{dist_id}' のタグ取得エラー: {str(e)}")
                    
                    # ディストリビューション情報を追加
                    dist_name = dist_summary.get('Comment', '名前なし')
                    distributions.append({
                        'ResourceId': dist_id,
                        'ResourceName': dist_name,
                        'ResourceType': 'Distribution',
                        'ARN': dist_summary.get('ARN', ''),
                        'DomainName': dist_summary.get('DomainName', ''),
                        'Status': dist_summary.get('Status', ''),
                        'Enabled': dist_summary.get('Enabled', False),
                        'PriceClass': dist_summary.get('PriceClass', ''),
                        'LastModifiedTime': dist_summary.get('LastModifiedTime', ''),
                        'Aliases': dist_summary.get('Aliases', {}).get('Items', []),
                        'CustomOrigin': len(dist_summary.get('Origins', {}).get('Items', [])),
                        'DefaultCacheBehavior': bool(dist_summary.get('DefaultCacheBehavior', {})),
                        'CacheBehaviorsCount': len(dist_summary.get('CacheBehaviors', {}).get('Items', [])),
                        'ViewerCertificate': bool(dist_summary.get('ViewerCertificate', {})),
                        'Tags': tags
                    })
            
            logger.info(f"CloudFrontディストリビューション: {len(distributions)}件取得")
        except Exception as e:
            logger.error(f"CloudFrontディストリビューション情報収集中にエラー発生: {str(e)}")
        
        return distributions
    
    def _collect_cache_policies(self, cloudfront_client) -> List[Dict[str, Any]]:
        """CloudFrontキャッシュポリシー情報を収集"""
        logger.info("CloudFrontキャッシュポリシー情報を収集しています")
        cache_policies = []
        
        try:
            # list_cache_policiesはパジネーションに対応していないため、直接呼び出し
            response = cloudfront_client.list_cache_policies()
            
            policies_list = response.get('CachePolicyList', {})
            
            for policy in policies_list.get('Items', []):
                policy_id = policy.get('Id', '')
                policy_name = policy.get('CachePolicy', {}).get('CachePolicyConfig', {}).get('Name', '名前なし')
                
                # ポリシー情報を追加
                cache_policies.append({
                    'ResourceId': policy_id,
                    'ResourceName': policy_name,
                    'ResourceType': 'CachePolicy',
                    'Comment': policy.get('CachePolicy', {}).get('CachePolicyConfig', {}).get('Comment', ''),
                    'MinTTL': policy.get('CachePolicy', {}).get('CachePolicyConfig', {}).get('MinTTL', 0),
                    'MaxTTL': policy.get('CachePolicy', {}).get('CachePolicyConfig', {}).get('MaxTTL', 0),
                    'DefaultTTL': policy.get('CachePolicy', {}).get('CachePolicyConfig', {}).get('DefaultTTL', 0)
                })
            
            logger.info(f"CloudFrontキャッシュポリシー: {len(cache_policies)}件取得")
        except Exception as e:
            logger.error(f"CloudFrontキャッシュポリシー情報収集中にエラー発生: {str(e)}")
        
        return cache_policies
    
    def _collect_origin_request_policies(self, cloudfront_client) -> List[Dict[str, Any]]:
        """CloudFrontオリジンリクエストポリシー情報を収集"""
        logger.info("CloudFrontオリジンリクエストポリシー情報を収集しています")
        origin_request_policies = []
        
        try:
            # list_origin_request_policiesはパジネーションに対応していないため、直接呼び出し
            response = cloudfront_client.list_origin_request_policies()
            
            policies_list = response.get('OriginRequestPolicyList', {})
            
            for policy in policies_list.get('Items', []):
                policy_id = policy.get('Id', '')
                policy_name = policy.get('OriginRequestPolicy', {}).get('OriginRequestPolicyConfig', {}).get('Name', '名前なし')
                
                # ポリシー情報を追加
                origin_request_policies.append({
                    'ResourceId': policy_id,
                    'ResourceName': policy_name,
                    'ResourceType': 'OriginRequestPolicy',
                    'Comment': policy.get('OriginRequestPolicy', {}).get('OriginRequestPolicyConfig', {}).get('Comment', '')
                })
            
            logger.info(f"CloudFrontオリジンリクエストポリシー: {len(origin_request_policies)}件取得")
        except Exception as e:
            logger.error(f"CloudFrontオリジンリクエストポリシー情報収集中にエラー発生: {str(e)}")
        
        return origin_request_policies
    
    def _collect_functions(self, cloudfront_client) -> List[Dict[str, Any]]:
        """CloudFront関数情報を収集"""
        logger.info("CloudFront関数情報を収集しています")
        functions = []
        
        try:
            # list_functionsはパジネーションに対応していないため、直接呼び出し
            response = cloudfront_client.list_functions()
            
            functions_list = response.get('FunctionList', {})
            
            for function_summary in functions_list.get('Items', []):
                function_name = function_summary.get('Name', '名前なし')
                
                # 関数情報を追加
                functions.append({
                    'ResourceId': function_summary.get('FunctionMetadata', {}).get('FunctionARN', ''),
                    'ResourceName': function_name,
                    'ResourceType': 'Function',
                    'Status': function_summary.get('Status', ''),
                    'FunctionConfig': function_summary.get('FunctionConfig', {}).get('Comment', ''),
                    'Runtime': function_summary.get('FunctionConfig', {}).get('Runtime', ''),
                    'CreatedTime': function_summary.get('FunctionMetadata', {}).get('CreatedTime', ''),
                    'LastModifiedTime': function_summary.get('FunctionMetadata', {}).get('LastModifiedTime', ''),
                    'Stage': function_summary.get('FunctionMetadata', {}).get('Stage', '')
                })
            
            logger.info(f"CloudFront関数: {len(functions)}件取得")
        except Exception as e:
            logger.error(f"CloudFront関数情報収集中にエラー発生: {str(e)}")
        
        return functions
