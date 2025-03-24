#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ElastiCache情報収集モジュール
"""

import logging
from typing import Dict, List, Any
from .base_collector import BaseCollector

# ロギングの設定
logger = logging.getLogger(__name__)

class ElastiCacheCollector(BaseCollector):
    """ElastiCache情報を収集するクラス"""
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        ElastiCache情報を収集
        
        Returns:
            Dict: ElastiCache情報
        """
        logger.info("ElastiCache情報の収集を開始します")
        results = {}
        
        try:
            # ElastiCacheクライアントを取得
            elasticache_client = self.get_client('elasticache')
            
            # キャッシュクラスター情報を取得
            clusters = self._collect_clusters(elasticache_client)
            if clusters:
                results['ElastiCache_Clusters'] = clusters
            
            # レプリケーショングループ情報を取得
            replication_groups = self._collect_replication_groups(elasticache_client)
            if replication_groups:
                results['ElastiCache_ReplicationGroups'] = replication_groups
            
            # パラメータグループ情報を取得
            parameter_groups = self._collect_parameter_groups(elasticache_client)
            if parameter_groups:
                results['ElastiCache_ParameterGroups'] = parameter_groups
            
            # サブネットグループ情報を取得
            subnet_groups = self._collect_subnet_groups(elasticache_client)
            if subnet_groups:
                results['ElastiCache_SubnetGroups'] = subnet_groups
            
            # スナップショット情報を取得
            snapshots = self._collect_snapshots(elasticache_client)
            if snapshots:
                results['ElastiCache_Snapshots'] = snapshots
                
        except Exception as e:
            logger.error(f"ElastiCache情報収集中にエラー発生: {str(e)}")
        
        return results
    
    def _collect_clusters(self, elasticache_client) -> List[Dict[str, Any]]:
        """ElastiCacheクラスター情報を収集"""
        logger.info("ElastiCacheクラスター情報を収集しています")
        clusters = []
        
        try:
            paginator = elasticache_client.get_paginator('describe_cache_clusters')
            
            for page in paginator.paginate():
                for cluster in page.get('CacheClusters', []):
                    cluster_id = cluster.get('CacheClusterId', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if 'ARN' in cluster:
                            tag_response = elasticache_client.list_tags_for_resource(
                                ResourceName=cluster['ARN']
                            )
                            tags = tag_response.get('TagList', [])
                    except Exception as e:
                        logger.warning(f"ElastiCacheクラスター '{cluster_id}' のタグ取得エラー: {str(e)}")
                    
                    # クラスター情報を追加
                    clusters.append({
                        'ResourceId': cluster.get('ARN', ''),
                        'ResourceName': cluster_id,
                        'ResourceType': 'CacheCluster',
                        'Engine': cluster.get('Engine', ''),
                        'EngineVersion': cluster.get('EngineVersion', ''),
                        'CacheNodeType': cluster.get('CacheNodeType', ''),
                        'CacheClusterStatus': cluster.get('CacheClusterStatus', ''),
                        'NumCacheNodes': cluster.get('NumCacheNodes', 0),
                        'PreferredAvailabilityZone': cluster.get('PreferredAvailabilityZone', ''),
                        'CacheSubnetGroupName': cluster.get('CacheSubnetGroupName', ''),
                        'CacheParameterGroupName': cluster.get('CacheParameterGroup', {}).get('CacheParameterGroupName', ''),
                        'ReplicationGroupId': cluster.get('ReplicationGroupId', ''),
                        'AutoMinorVersionUpgrade': cluster.get('AutoMinorVersionUpgrade', False),
                        'SnapshotRetentionLimit': cluster.get('SnapshotRetentionLimit', 0),
                        'SnapshotWindow': cluster.get('SnapshotWindow', ''),
                        'PreferredMaintenanceWindow': cluster.get('PreferredMaintenanceWindow', ''),
                        'SecurityGroups': [sg.get('SecurityGroupId', '') for sg in cluster.get('SecurityGroups', [])],
                        'Tags': tags
                    })
            
            logger.info(f"ElastiCacheクラスター: {len(clusters)}件取得")
        except Exception as e:
            logger.error(f"ElastiCacheクラスター情報収集中にエラー発生: {str(e)}")
        
        return clusters
    
    def _collect_replication_groups(self, elasticache_client) -> List[Dict[str, Any]]:
        """ElastiCacheレプリケーショングループ情報を収集"""
        logger.info("ElastiCacheレプリケーショングループ情報を収集しています")
        replication_groups = []
        
        try:
            paginator = elasticache_client.get_paginator('describe_replication_groups')
            
            for page in paginator.paginate():
                for group in page.get('ReplicationGroups', []):
                    group_id = group.get('ReplicationGroupId', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if 'ARN' in group:
                            tag_response = elasticache_client.list_tags_for_resource(
                                ResourceName=group['ARN']
                            )
                            tags = tag_response.get('TagList', [])
                    except Exception as e:
                        logger.warning(f"ElastiCacheレプリケーショングループ '{group_id}' のタグ取得エラー: {str(e)}")
                    
                    # レプリケーショングループ情報を追加
                    replication_groups.append({
                        'ResourceId': group.get('ARN', ''),
                        'ResourceName': group_id,
                        'ResourceType': 'ReplicationGroup',
                        'Description': group.get('Description', ''),
                        'Status': group.get('Status', ''),
                        'MultiAZ': group.get('MultiAZ', ''),
                        'AutomaticFailover': group.get('AutomaticFailover', ''),
                        'MemberClusters': group.get('MemberClusters', []),
                        'NodeGroups': len(group.get('NodeGroups', [])),
                        'SnapshotRetentionLimit': group.get('SnapshotRetentionLimit', 0),
                        'SnapshotWindow': group.get('SnapshotWindow', ''),
                        'ClusterEnabled': group.get('ClusterEnabled', False),
                        'CacheNodeType': group.get('CacheNodeType', ''),
                        'AuthTokenEnabled': group.get('AuthTokenEnabled', False),
                        'TransitEncryptionEnabled': group.get('TransitEncryptionEnabled', False),
                        'AtRestEncryptionEnabled': group.get('AtRestEncryptionEnabled', False),
                        'KmsKeyId': group.get('KmsKeyId', ''),
                        'Tags': tags
                    })
            
            logger.info(f"ElastiCacheレプリケーショングループ: {len(replication_groups)}件取得")
        except Exception as e:
            logger.error(f"ElastiCacheレプリケーショングループ情報収集中にエラー発生: {str(e)}")
        
        return replication_groups
    
    def _collect_parameter_groups(self, elasticache_client) -> List[Dict[str, Any]]:
        """ElastiCacheパラメータグループ情報を収集"""
        logger.info("ElastiCacheパラメータグループ情報を収集しています")
        parameter_groups = []
        
        try:
            paginator = elasticache_client.get_paginator('describe_cache_parameter_groups')
            
            for page in paginator.paginate():
                for group in page.get('CacheParameterGroups', []):
                    group_name = group.get('CacheParameterGroupName', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if 'ARN' in group:
                            tag_response = elasticache_client.list_tags_for_resource(
                                ResourceName=group['ARN']
                            )
                            tags = tag_response.get('TagList', [])
                    except Exception as e:
                        logger.warning(f"ElastiCacheパラメータグループ '{group_name}' のタグ取得エラー: {str(e)}")
                    
                    # パラメータグループ情報を追加
                    parameter_groups.append({
                        'ResourceId': group.get('ARN', ''),
                        'ResourceName': group_name,
                        'ResourceType': 'ParameterGroup',
                        'Family': group.get('CacheParameterGroupFamily', ''),
                        'Description': group.get('Description', ''),
                        'IsGlobal': group.get('IsGlobal', False),
                        'Tags': tags
                    })
            
            logger.info(f"ElastiCacheパラメータグループ: {len(parameter_groups)}件取得")
        except Exception as e:
            logger.error(f"ElastiCacheパラメータグループ情報収集中にエラー発生: {str(e)}")
        
        return parameter_groups
    
    def _collect_subnet_groups(self, elasticache_client) -> List[Dict[str, Any]]:
        """ElastiCacheサブネットグループ情報を収集"""
        logger.info("ElastiCacheサブネットグループ情報を収集しています")
        subnet_groups = []
        
        try:
            paginator = elasticache_client.get_paginator('describe_cache_subnet_groups')
            
            for page in paginator.paginate():
                for group in page.get('CacheSubnetGroups', []):
                    group_name = group.get('CacheSubnetGroupName', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if 'ARN' in group:
                            tag_response = elasticache_client.list_tags_for_resource(
                                ResourceName=group['ARN']
                            )
                            tags = tag_response.get('TagList', [])
                    except Exception as e:
                        logger.warning(f"ElastiCacheサブネットグループ '{group_name}' のタグ取得エラー: {str(e)}")
                    
                    # サブネットグループ情報を追加
                    subnet_groups.append({
                        'ResourceId': group.get('ARN', ''),
                        'ResourceName': group_name,
                        'ResourceType': 'SubnetGroup',
                        'Description': group.get('Description', ''),
                        'VpcId': group.get('VpcId', ''),
                        'SubnetIds': [subnet.get('SubnetIdentifier', '') for subnet in group.get('Subnets', [])],
                        'Tags': tags
                    })
            
            logger.info(f"ElastiCacheサブネットグループ: {len(subnet_groups)}件取得")
        except Exception as e:
            logger.error(f"ElastiCacheサブネットグループ情報収集中にエラー発生: {str(e)}")
        
        return subnet_groups
    
    def _collect_snapshots(self, elasticache_client) -> List[Dict[str, Any]]:
        """ElastiCacheスナップショット情報を収集"""
        logger.info("ElastiCacheスナップショット情報を収集しています")
        snapshots = []
        
        try:
            paginator = elasticache_client.get_paginator('describe_snapshots')
            
            for page in paginator.paginate():
                for snapshot in page.get('Snapshots', []):
                    snapshot_name = snapshot.get('SnapshotName', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if 'ARN' in snapshot:
                            tag_response = elasticache_client.list_tags_for_resource(
                                ResourceName=snapshot['ARN']
                            )
                            tags = tag_response.get('TagList', [])
                    except Exception as e:
                        logger.warning(f"ElastiCacheスナップショット '{snapshot_name}' のタグ取得エラー: {str(e)}")
                    
                    # スナップショット情報を追加
                    snapshots.append({
                        'ResourceId': snapshot.get('ARN', ''),
                        'ResourceName': snapshot_name,
                        'ResourceType': 'Snapshot',
                        'CacheClusterId': snapshot.get('CacheClusterId', ''),
                        'ReplicationGroupId': snapshot.get('ReplicationGroupId', ''),
                        'SnapshotStatus': snapshot.get('SnapshotStatus', ''),
                        'SnapshotSource': snapshot.get('SnapshotSource', ''),
                        'CacheNodeType': snapshot.get('CacheNodeType', ''),
                        'Engine': snapshot.get('Engine', ''),
                        'EngineVersion': snapshot.get('EngineVersion', ''),
                        'NumCacheNodes': snapshot.get('NumCacheNodes', 0),
                        'PreferredAvailabilityZone': snapshot.get('PreferredAvailabilityZone', ''),
                        'CacheParameterGroupName': snapshot.get('CacheParameterGroupName', ''),
                        'VpcId': snapshot.get('VpcId', ''),
                        'AutoMinorVersionUpgrade': snapshot.get('AutoMinorVersionUpgrade', False),
                        'SnapshotRetentionLimit': snapshot.get('SnapshotRetentionLimit', 0),
                        'SnapshotWindow': snapshot.get('SnapshotWindow', ''),
                        'NodeSnapshots': len(snapshot.get('NodeSnapshots', [])),
                        'Tags': tags
                    })
            
            logger.info(f"ElastiCacheスナップショット: {len(snapshots)}件取得")
        except Exception as e:
            logger.error(f"ElastiCacheスナップショット情報収集中にエラー発生: {str(e)}")
        
        return snapshots
