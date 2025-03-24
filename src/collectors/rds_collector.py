#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RDSリソース情報収集モジュール
"""

import logging
from typing import Dict, List, Any
from .base_collector import BaseCollector

# ロギングの設定
logger = logging.getLogger(__name__)

class RDSCollector(BaseCollector):
    """RDSリソース情報を収集するクラス"""
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        RDSリソース情報を収集
        
        Returns:
            Dict: RDSリソース情報
        """
        logger.info("RDSリソース情報の収集を開始します")
        results = {}
        
        try:
            # RDSクライアントを取得
            rds_client = self.get_client('rds')
            
            # DBインスタンス情報を取得
            db_instances = self._collect_db_instances(rds_client)
            if db_instances:
                results['RDS_Instances'] = db_instances
            
            # DBクラスター情報を取得
            db_clusters = self._collect_db_clusters(rds_client)
            if db_clusters:
                results['RDS_Clusters'] = db_clusters
                
            # スナップショット情報を取得
            snapshots = self._collect_snapshots(rds_client)
            if snapshots:
                results['RDS_Snapshots'] = snapshots
                
            # パラメータグループ情報を取得
            parameter_groups = self._collect_parameter_groups(rds_client)
            if parameter_groups:
                results['RDS_ParameterGroups'] = parameter_groups
                
            # オプショングループ情報を取得
            option_groups = self._collect_option_groups(rds_client)
            if option_groups:
                results['RDS_OptionGroups'] = option_groups
                
            # サブネットグループ情報を取得
            subnet_groups = self._collect_subnet_groups(rds_client)
            if subnet_groups:
                results['RDS_SubnetGroups'] = subnet_groups
                
        except Exception as e:
            logger.error(f"RDSリソース情報収集中にエラー発生: {str(e)}")
        
        return results
    
    def _collect_db_instances(self, rds_client) -> List[Dict[str, Any]]:
        """RDS DBインスタンス情報を収集"""
        logger.info("RDS DBインスタンス情報を収集しています")
        db_instances = []
        
        try:
            paginator = rds_client.get_paginator('describe_db_instances')
            for page in paginator.paginate():
                for db in page.get('DBInstances', []):
                    db_name = db.get('DBInstanceIdentifier', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if 'DBInstanceArn' in db:
                            tag_response = rds_client.list_tags_for_resource(
                                ResourceName=db['DBInstanceArn']
                            )
                            tags = tag_response.get('TagList', [])
                    except Exception as e:
                        logger.warning(f"RDSインスタンス '{db_name}' のタグ取得エラー: {str(e)}")
                    
                    # 複数AZ配置かどうか
                    multi_az = db.get('MultiAZ', False)
                    
                    # ストレージタイプと割り当て容量
                    storage_type = db.get('StorageType', 'unknown')
                    allocated_storage = db.get('AllocatedStorage', 0)
                    
                    # 暗号化状態
                    encrypted = db.get('StorageEncrypted', False)
                    
                    # インスタンス情報を追加
                    db_instances.append({
                        'ResourceId': db_name,
                        'ResourceName': db_name,
                        'ResourceType': 'DBInstance',
                        'Engine': db.get('Engine', 'unknown'),
                        'EngineVersion': db.get('EngineVersion', 'unknown'),
                        'Status': db.get('DBInstanceStatus', 'unknown'),
                        'InstanceClass': db.get('DBInstanceClass', 'unknown'),
                        'StorageType': storage_type,
                        'AllocatedStorage': allocated_storage,
                        'MultiAZ': multi_az,
                        'Encrypted': encrypted,
                        'PubliclyAccessible': db.get('PubliclyAccessible', False),
                        'VpcId': db.get('DBSubnetGroup', {}).get('VpcId', ''),
                        'Endpoint': db.get('Endpoint', {}).get('Address', ''),
                        'Port': db.get('Endpoint', {}).get('Port', 0),
                        'AvailabilityZone': db.get('AvailabilityZone', ''),
                        'BackupRetentionPeriod': db.get('BackupRetentionPeriod', 0),
                        'InstanceCreateTime': db.get('InstanceCreateTime', ''),
                        'Tags': tags
                    })
            
            logger.info(f"RDS DBインスタンス: {len(db_instances)}件取得")
        except Exception as e:
            logger.error(f"RDS DBインスタンス情報収集中にエラー発生: {str(e)}")
        
        return db_instances
    
    def _collect_db_clusters(self, rds_client) -> List[Dict[str, Any]]:
        """RDS DBクラスター情報を収集"""
        logger.info("RDS DBクラスター情報を収集しています")
        db_clusters = []
        
        try:
            paginator = rds_client.get_paginator('describe_db_clusters')
            for page in paginator.paginate():
                for cluster in page.get('DBClusters', []):
                    cluster_id = cluster.get('DBClusterIdentifier', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if 'DBClusterArn' in cluster:
                            tag_response = rds_client.list_tags_for_resource(
                                ResourceName=cluster['DBClusterArn']
                            )
                            tags = tag_response.get('TagList', [])
                    except Exception as e:
                        logger.warning(f"RDSクラスター '{cluster_id}' のタグ取得エラー: {str(e)}")
                    
                    # クラスターエンドポイントを取得
                    endpoint = cluster.get('Endpoint', '')
                    reader_endpoint = cluster.get('ReaderEndpoint', '')
                    
                    # クラスター情報を追加
                    db_clusters.append({
                        'ResourceId': cluster_id,
                        'ResourceName': cluster_id,
                        'ResourceType': 'DBCluster',
                        'Engine': cluster.get('Engine', 'unknown'),
                        'EngineVersion': cluster.get('EngineVersion', 'unknown'),
                        'Status': cluster.get('Status', 'unknown'),
                        'DatabaseName': cluster.get('DatabaseName', ''),
                        'AvailabilityZones': cluster.get('AvailabilityZones', []),
                        'MultiAZ': len(cluster.get('AvailabilityZones', [])) > 1,
                        'Endpoint': endpoint,
                        'ReaderEndpoint': reader_endpoint,
                        'Port': cluster.get('Port', 0),
                        'Engine': cluster.get('Engine', ''),
                        'EngineMode': cluster.get('EngineMode', ''),
                        'DBClusterMembers': len(cluster.get('DBClusterMembers', [])),
                        'AllocatedStorage': cluster.get('AllocatedStorage', 0),
                        'BackupRetentionPeriod': cluster.get('BackupRetentionPeriod', 0),
                        'ClusterCreateTime': cluster.get('ClusterCreateTime', ''),
                        'StorageEncrypted': cluster.get('StorageEncrypted', False),
                        'Tags': tags
                    })
            
            logger.info(f"RDS DBクラスター: {len(db_clusters)}件取得")
        except Exception as e:
            logger.error(f"RDS DBクラスター情報収集中にエラー発生: {str(e)}")
        
        return db_clusters
    
    def _collect_snapshots(self, rds_client) -> List[Dict[str, Any]]:
        """RDSスナップショット情報を収集"""
        logger.info("RDSスナップショット情報を収集しています")
        snapshots = []
        
        try:
            # DBインスタンススナップショットを取得
            paginator = rds_client.get_paginator('describe_db_snapshots')
            for page in paginator.paginate():
                for snapshot in page.get('DBSnapshots', []):
                    snapshot_id = snapshot.get('DBSnapshotIdentifier', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if 'DBSnapshotArn' in snapshot:
                            tag_response = rds_client.list_tags_for_resource(
                                ResourceName=snapshot['DBSnapshotArn']
                            )
                            tags = tag_response.get('TagList', [])
                    except Exception as e:
                        logger.warning(f"RDSスナップショット '{snapshot_id}' のタグ取得エラー: {str(e)}")
                    
                    # スナップショット情報を追加
                    snapshots.append({
                        'ResourceId': snapshot_id,
                        'ResourceName': snapshot_id,
                        'ResourceType': 'DBSnapshot',
                        'SnapshotType': snapshot.get('SnapshotType', ''),
                        'Status': snapshot.get('Status', ''),
                        'Engine': snapshot.get('Engine', ''),
                        'EngineVersion': snapshot.get('EngineVersion', ''),
                        'DBInstanceIdentifier': snapshot.get('DBInstanceIdentifier', ''),
                        'AllocatedStorage': snapshot.get('AllocatedStorage', 0),
                        'SnapshotCreateTime': snapshot.get('SnapshotCreateTime', ''),
                        'Encrypted': snapshot.get('Encrypted', False),
                        'Tags': tags
                    })
            
            # DBクラスタースナップショットを取得
            try:
                paginator = rds_client.get_paginator('describe_db_cluster_snapshots')
                for page in paginator.paginate():
                    for snapshot in page.get('DBClusterSnapshots', []):
                        snapshot_id = snapshot.get('DBClusterSnapshotIdentifier', '名前なし')
                        
                        # タグを取得
                        tags = []
                        try:
                            if 'DBClusterSnapshotArn' in snapshot:
                                tag_response = rds_client.list_tags_for_resource(
                                    ResourceName=snapshot['DBClusterSnapshotArn']
                                )
                                tags = tag_response.get('TagList', [])
                        except Exception as e:
                            logger.warning(f"RDSクラスタースナップショット '{snapshot_id}' のタグ取得エラー: {str(e)}")
                        
                        # スナップショット情報を追加
                        snapshots.append({
                            'ResourceId': snapshot_id,
                            'ResourceName': snapshot_id,
                            'ResourceType': 'DBClusterSnapshot',
                            'SnapshotType': snapshot.get('SnapshotType', ''),
                            'Status': snapshot.get('Status', ''),
                            'Engine': snapshot.get('Engine', ''),
                            'EngineVersion': snapshot.get('EngineVersion', ''),
                            'DBClusterIdentifier': snapshot.get('DBClusterIdentifier', ''),
                            'AllocatedStorage': snapshot.get('AllocatedStorage', 0),
                            'SnapshotCreateTime': snapshot.get('SnapshotCreateTime', ''),
                            'Encrypted': snapshot.get('StorageEncrypted', False),
                            'Tags': tags
                        })
            except Exception as e:
                logger.warning(f"RDSクラスタースナップショット情報収集中にエラー発生: {str(e)}")
                # クラスタースナップショットがない場合もあるため、エラーでも続行
            
            logger.info(f"RDSスナップショット: {len(snapshots)}件取得")
        except Exception as e:
            logger.error(f"RDSスナップショット情報収集中にエラー発生: {str(e)}")
        
        return snapshots
    
    def _collect_parameter_groups(self, rds_client) -> List[Dict[str, Any]]:
        """RDSパラメータグループ情報を収集"""
        logger.info("RDSパラメータグループ情報を収集しています")
        parameter_groups = []
        
        try:
            paginator = rds_client.get_paginator('describe_db_parameter_groups')
            for page in paginator.paginate():
                for param_group in page.get('DBParameterGroups', []):
                    group_name = param_group.get('DBParameterGroupName', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if 'DBParameterGroupArn' in param_group:
                            tag_response = rds_client.list_tags_for_resource(
                                ResourceName=param_group['DBParameterGroupArn']
                            )
                            tags = tag_response.get('TagList', [])
                    except Exception as e:
                        logger.warning(f"RDSパラメータグループ '{group_name}' のタグ取得エラー: {str(e)}")
                    
                    # パラメータグループ情報を追加
                    parameter_groups.append({
                        'ResourceId': group_name,
                        'ResourceName': group_name,
                        'ResourceType': 'DBParameterGroup',
                        'Description': param_group.get('Description', ''),
                        'Family': param_group.get('DBParameterGroupFamily', ''),
                        'Tags': tags
                    })
            
            # クラスターパラメータグループを取得
            try:
                paginator = rds_client.get_paginator('describe_db_cluster_parameter_groups')
                for page in paginator.paginate():
                    for param_group in page.get('DBClusterParameterGroups', []):
                        group_name = param_group.get('DBClusterParameterGroupName', '名前なし')
                        
                        # タグを取得
                        tags = []
                        try:
                            if 'DBClusterParameterGroupArn' in param_group:
                                tag_response = rds_client.list_tags_for_resource(
                                    ResourceName=param_group['DBClusterParameterGroupArn']
                                )
                                tags = tag_response.get('TagList', [])
                        except Exception as e:
                            logger.warning(f"RDSクラスターパラメータグループ '{group_name}' のタグ取得エラー: {str(e)}")
                        
                        # パラメータグループ情報を追加
                        parameter_groups.append({
                            'ResourceId': group_name,
                            'ResourceName': group_name,
                            'ResourceType': 'DBClusterParameterGroup',
                            'Description': param_group.get('Description', ''),
                            'Family': param_group.get('DBParameterGroupFamily', ''),
                            'Tags': tags
                        })
            except Exception as e:
                logger.warning(f"RDSクラスターパラメータグループ情報収集中にエラー発生: {str(e)}")
                # クラスターパラメータグループがない場合もあるため、エラーでも続行
            
            logger.info(f"RDSパラメータグループ: {len(parameter_groups)}件取得")
        except Exception as e:
            logger.error(f"RDSパラメータグループ情報収集中にエラー発生: {str(e)}")
        
        return parameter_groups
    
    def _collect_option_groups(self, rds_client) -> List[Dict[str, Any]]:
        """RDSオプショングループ情報を収集"""
        logger.info("RDSオプショングループ情報を収集しています")
        option_groups = []
        
        try:
            paginator = rds_client.get_paginator('describe_option_groups')
            for page in paginator.paginate():
                for option_group in page.get('OptionGroupsList', []):
                    group_name = option_group.get('OptionGroupName', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if 'OptionGroupArn' in option_group:
                            tag_response = rds_client.list_tags_for_resource(
                                ResourceName=option_group['OptionGroupArn']
                            )
                            tags = tag_response.get('TagList', [])
                    except Exception as e:
                        logger.warning(f"RDSオプショングループ '{group_name}' のタグ取得エラー: {str(e)}")
                    
                    # オプショングループ情報を追加
                    option_groups.append({
                        'ResourceId': group_name,
                        'ResourceName': group_name,
                        'ResourceType': 'OptionGroup',
                        'Description': option_group.get('OptionGroupDescription', ''),
                        'Engine': option_group.get('EngineName', ''),
                        'MajorEngineVersion': option_group.get('MajorEngineVersion', ''),
                        'OptionCount': len(option_group.get('Options', [])),
                        'Tags': tags
                    })
            
            logger.info(f"RDSオプショングループ: {len(option_groups)}件取得")
        except Exception as e:
            logger.error(f"RDSオプショングループ情報収集中にエラー発生: {str(e)}")
        
        return option_groups
    
    def _collect_subnet_groups(self, rds_client) -> List[Dict[str, Any]]:
        """RDSサブネットグループ情報を収集"""
        logger.info("RDSサブネットグループ情報を収集しています")
        subnet_groups = []
        
        try:
            paginator = rds_client.get_paginator('describe_db_subnet_groups')
            for page in paginator.paginate():
                for subnet_group in page.get('DBSubnetGroups', []):
                    group_name = subnet_group.get('DBSubnetGroupName', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if 'DBSubnetGroupArn' in subnet_group:
                            tag_response = rds_client.list_tags_for_resource(
                                ResourceName=subnet_group['DBSubnetGroupArn']
                            )
                            tags = tag_response.get('TagList', [])
                    except Exception as e:
                        logger.warning(f"RDSサブネットグループ '{group_name}' のタグ取得エラー: {str(e)}")
                    
                    # サブネットグループ情報を追加
                    subnet_groups.append({
                        'ResourceId': group_name,
                        'ResourceName': group_name,
                        'ResourceType': 'DBSubnetGroup',
                        'Description': subnet_group.get('DBSubnetGroupDescription', ''),
                        'VpcId': subnet_group.get('VpcId', ''),
                        'Status': subnet_group.get('SubnetGroupStatus', ''),
                        'SubnetCount': len(subnet_group.get('Subnets', [])),
                        'Tags': tags
                    })
            
            logger.info(f"RDSサブネットグループ: {len(subnet_groups)}件取得")
        except Exception as e:
            logger.error(f"RDSサブネットグループ情報収集中にエラー発生: {str(e)}")
        
        return subnet_groups
