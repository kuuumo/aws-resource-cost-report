#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Route 53情報収集モジュール
"""

import logging
from typing import Dict, List, Any
from .base_collector import BaseCollector

# ロギングの設定
logger = logging.getLogger(__name__)

class Route53Collector(BaseCollector):
    """Route 53情報を収集するクラス"""
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Route 53情報を収集
        
        Returns:
            Dict: Route 53情報
        """
        logger.info("Route 53情報の収集を開始します")
        results = {}
        
        try:
            # Route 53はグローバルサービス
            route53_client = self.get_client('route53')
            
            # ホストゾーン情報を取得
            hosted_zones = self._collect_hosted_zones(route53_client)
            if hosted_zones:
                results['Route53_HostedZones'] = hosted_zones
            
            # ヘルスチェック情報を取得
            health_checks = self._collect_health_checks(route53_client)
            if health_checks:
                results['Route53_HealthChecks'] = health_checks
            
            # ドメイン情報を取得（Route 53 Domains）
            try:
                domains = self._collect_domains()
                if domains:
                    results['Route53_Domains'] = domains
            except Exception as e:
                # Route 53 Domainsが使用できないリージョンでは例外が発生するため、警告のみで続行
                logger.warning(f"Route 53ドメイン情報収集中にエラー発生: {str(e)}")
                
            # トラフィックポリシー情報を取得
            traffic_policies = self._collect_traffic_policies(route53_client)
            if traffic_policies:
                results['Route53_TrafficPolicies'] = traffic_policies
            
        except Exception as e:
            logger.error(f"Route 53情報収集中にエラー発生: {str(e)}")
        
        return results
    
    def _collect_hosted_zones(self, route53_client) -> List[Dict[str, Any]]:
        """Route 53ホストゾーン情報を収集"""
        logger.info("Route 53ホストゾーン情報を収集しています")
        hosted_zones = []
        
        try:
            paginator = route53_client.get_paginator('list_hosted_zones')
            
            for page in paginator.paginate():
                for zone in page.get('HostedZones', []):
                    zone_id = zone.get('Id', '').split('/')[-1]  # /hostedzone/Z1234 から Z1234 部分を抽出
                    zone_name = zone.get('Name', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if zone_id:
                            tag_response = route53_client.list_tags_for_resource(
                                ResourceType='hostedzone',
                                ResourceId=zone_id
                            )
                            tags = tag_response.get('ResourceTagSet', {}).get('Tags', [])
                    except Exception as e:
                        logger.warning(f"Route 53ホストゾーン '{zone_name}' のタグ取得エラー: {str(e)}")
                    
                    # ホストゾーン情報を追加
                    hosted_zones.append({
                        'ResourceId': zone_id,
                        'ResourceName': zone_name,
                        'ResourceType': 'HostedZone',
                        'RecordSetCount': zone.get('ResourceRecordSetCount', 0),
                        'PrivateZone': zone.get('Config', {}).get('PrivateZone', False),
                        'Comment': zone.get('Config', {}).get('Comment', ''),
                        'Tags': tags
                    })
                    
                    # リソースレコードセットの数を取得（オプション、時間がかかる可能性あり）
                    # record_sets = self._collect_resource_record_sets(route53_client, zone.get('Id', ''))
                    # hosted_zones[-1]['RecordSets'] = record_sets
            
            logger.info(f"Route 53ホストゾーン: {len(hosted_zones)}件取得")
        except Exception as e:
            logger.error(f"Route 53ホストゾーン情報収集中にエラー発生: {str(e)}")
        
        return hosted_zones
    
    def _collect_health_checks(self, route53_client) -> List[Dict[str, Any]]:
        """Route 53ヘルスチェック情報を収集"""
        logger.info("Route 53ヘルスチェック情報を収集しています")
        health_checks = []
        
        try:
            paginator = route53_client.get_paginator('list_health_checks')
            
            for page in paginator.paginate():
                for health_check in page.get('HealthChecks', []):
                    health_check_id = health_check.get('Id', '')
                    
                    # タグを取得
                    tags = []
                    try:
                        if health_check_id:
                            tag_response = route53_client.list_tags_for_resource(
                                ResourceType='healthcheck',
                                ResourceId=health_check_id
                            )
                            tags = tag_response.get('ResourceTagSet', {}).get('Tags', [])
                    except Exception as e:
                        logger.warning(f"Route 53ヘルスチェック '{health_check_id}' のタグ取得エラー: {str(e)}")
                    
                    # ヘルスチェック設定
                    config = health_check.get('HealthCheckConfig', {})
                    
                    # ヘルスチェックのタイプを決定
                    health_check_type = 'unknown'
                    if 'IPAddress' in config and 'Port' in config:
                        if config.get('Type') == 'HTTP' or config.get('Type') == 'HTTPS':
                            health_check_type = f"{config.get('Type')}_{config.get('Port')}"
                        else:
                            health_check_type = f"TCP_{config.get('Port')}"
                    elif 'FullyQualifiedDomainName' in config:
                        health_check_type = f"DNS_{config.get('Type')}"
                    
                    # ヘルスチェック名を取得（タグから）
                    health_check_name = health_check_id
                    for tag in tags:
                        if tag.get('Key') == 'Name':
                            health_check_name = tag.get('Value')
                            break
                    
                    # ヘルスチェック情報を追加
                    health_checks.append({
                        'ResourceId': health_check_id,
                        'ResourceName': health_check_name,
                        'ResourceType': 'HealthCheck',
                        'Type': health_check_type,
                        'IPAddress': config.get('IPAddress', ''),
                        'Port': config.get('Port', 0),
                        'FullyQualifiedDomainName': config.get('FullyQualifiedDomainName', ''),
                        'RequestInterval': config.get('RequestInterval', 0),
                        'FailureThreshold': config.get('FailureThreshold', 0),
                        'MeasureLatency': config.get('MeasureLatency', False),
                        'Disabled': config.get('Disabled', False),
                        'HealthThreshold': config.get('HealthThreshold', 0),
                        'Tags': tags
                    })
            
            logger.info(f"Route 53ヘルスチェック: {len(health_checks)}件取得")
        except Exception as e:
            logger.error(f"Route 53ヘルスチェック情報収集中にエラー発生: {str(e)}")
        
        return health_checks
    
    def _collect_domains(self) -> List[Dict[str, Any]]:
        """Route 53ドメイン情報を収集"""
        logger.info("Route 53ドメイン情報を収集しています")
        domains = []
        
        try:
            # Route 53 Domainsは特定のリージョン（us-east-1）でのみ利用可能
            route53domains_client = self.get_client('route53domains', region='us-east-1')
            
            paginator = route53domains_client.get_paginator('list_domains')
            
            for page in paginator.paginate():
                for domain in page.get('Domains', []):
                    domain_name = domain.get('DomainName', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if domain_name:
                            tag_response = route53domains_client.list_tags_for_domain(
                                DomainName=domain_name
                            )
                            tags = tag_response.get('TagList', [])
                    except Exception as e:
                        logger.warning(f"Route 53ドメイン '{domain_name}' のタグ取得エラー: {str(e)}")
                    
                    # ドメイン情報を追加
                    domains.append({
                        'ResourceId': domain_name,
                        'ResourceName': domain_name,
                        'ResourceType': 'Domain',
                        'AutoRenew': domain.get('AutoRenew', False),
                        'TransferLock': domain.get('TransferLock', False),
                        'Expiry': domain.get('Expiry', ''),
                        'Tags': tags
                    })
            
            logger.info(f"Route 53ドメイン: {len(domains)}件取得")
        except Exception as e:
            logger.error(f"Route 53ドメイン情報収集中にエラー発生: {str(e)}")
            # Route 53 Domainsが使用できないリージョンでは例外が発生する可能性あり
            raise
        
        return domains
    
    def _collect_traffic_policies(self, route53_client) -> List[Dict[str, Any]]:
        """Route 53トラフィックポリシー情報を収集"""
        logger.info("Route 53トラフィックポリシー情報を収集しています")
        traffic_policies = []
        
        try:
            # パジネーション処理の修正：すべてのトラフィックポリシーを取得する
            # list_traffic_policiesはマーカーベースのパジネーションをサポート
            response = route53_client.list_traffic_policies()
            
            # 最初のページのアイテムを処理
            for policy_summary in response.get('TrafficPolicySummaries', []):
                self._process_traffic_policy(policy_summary, traffic_policies)
            
            # 追加ページがあれば取得
            while response.get('IsTruncated', False):
                traffic_policy_id_marker = response.get('TrafficPolicyIdMarker', '')
                
                if traffic_policy_id_marker:
                    response = route53_client.list_traffic_policies(
                        TrafficPolicyIdMarker=traffic_policy_id_marker
                    )
                    
                    for policy_summary in response.get('TrafficPolicySummaries', []):
                        self._process_traffic_policy(policy_summary, traffic_policies)
                else:
                    # マーカーがない場合は中断
                    break
            
            logger.info(f"Route 53トラフィックポリシー: {len(traffic_policies)}件取得")
        except Exception as e:
            # トラフィックポリシー機能が有効でない場合もあるため、警告として処理
            logger.warning(f"Route 53トラフィックポリシー情報収集中にエラー発生: {str(e)}")
        
        return traffic_policies
    
    def _process_traffic_policy(self, policy_summary, traffic_policies):
        """トラフィックポリシーの情報を処理して追加"""
        policy_id = policy_summary.get('Id', '')
        policy_name = policy_summary.get('Name', '名前なし')
        
        # トラフィックポリシー情報を追加
        traffic_policies.append({
            'ResourceId': policy_id,
            'ResourceName': policy_name,
            'ResourceType': 'TrafficPolicy',
            'LatestVersion': policy_summary.get('LatestVersion', 0),
            'TrafficPolicyCount': policy_summary.get('TrafficPolicyCount', 0),
            'Type': policy_summary.get('Type', ''),
            'Comment': policy_summary.get('Comment', '')
        })
    
    def _collect_resource_record_sets(self, route53_client, hosted_zone_id) -> int:
        """Route 53リソースレコードセット数を収集"""
        record_sets_count = 0
        
        try:
            paginator = route53_client.get_paginator('list_resource_record_sets')
            
            for page in paginator.paginate(HostedZoneId=hosted_zone_id):
                record_sets_count += len(page.get('ResourceRecordSets', []))
        except Exception as e:
            logger.warning(f"Route 53リソースレコードセット情報収集中にエラー発生: {str(e)}")
        
        return record_sets_count
