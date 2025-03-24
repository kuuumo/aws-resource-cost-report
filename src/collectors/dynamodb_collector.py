#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DynamoDB情報収集モジュール
"""

import logging
from typing import Dict, List, Any
from .base_collector import BaseCollector

# ロギングの設定
logger = logging.getLogger(__name__)

class DynamoDBCollector(BaseCollector):
    """DynamoDB情報を収集するクラス"""
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        DynamoDB情報を収集
        
        Returns:
            Dict: DynamoDB情報
        """
        logger.info("DynamoDB情報の収集を開始します")
        results = {}
        
        try:
            # DynamoDBクライアントを取得
            dynamodb_client = self.get_client('dynamodb')
            
            # テーブル情報を取得
            tables = self._collect_tables(dynamodb_client)
            if tables:
                results['DynamoDB_Tables'] = tables
                
            # グローバルテーブル情報を取得
            global_tables = self._collect_global_tables(dynamodb_client)
            if global_tables:
                results['DynamoDB_GlobalTables'] = global_tables
                
            # バックアップ情報を取得
            backups = self._collect_backups(dynamodb_client)
            if backups:
                results['DynamoDB_Backups'] = backups
                
        except Exception as e:
            logger.error(f"DynamoDB情報収集中にエラー発生: {str(e)}")
        
        return results
    
    def _collect_tables(self, dynamodb_client) -> List[Dict[str, Any]]:
        """DynamoDBテーブル情報を収集"""
        logger.info("DynamoDBテーブル情報を収集しています")
        tables = []
        
        try:
            # テーブル一覧を取得
            paginator = dynamodb_client.get_paginator('list_tables')
            all_table_names = []
            
            for page in paginator.paginate():
                all_table_names.extend(page.get('TableNames', []))
            
            # 各テーブルの詳細情報を取得
            for table_name in all_table_names:
                try:
                    # テーブル詳細情報
                    table_info = dynamodb_client.describe_table(TableName=table_name)
                    table = table_info.get('Table', {})
                    
                    # テーブルARN
                    table_arn = table.get('TableArn', '')
                    
                    # タグを取得
                    tags = []
                    try:
                        if table_arn:
                            tag_response = dynamodb_client.list_tags_of_resource(
                                ResourceArn=table_arn
                            )
                            tags = [{'Key': tag['Key'], 'Value': tag['Value']} 
                                   for tag in tag_response.get('Tags', [])]
                    except Exception as e:
                        logger.warning(f"DynamoDBテーブル '{table_name}' のタグ取得エラー: {str(e)}")
                    
                    # プロビジョニングされたキャパシティ
                    provisioned_throughput = table.get('ProvisionedThroughput', {})
                    read_capacity = provisioned_throughput.get('ReadCapacityUnits', 0)
                    write_capacity = provisioned_throughput.get('WriteCapacityUnits', 0)
                    
                    # オンデマンドか判定
                    billing_mode = 'PROVISIONED'
                    billing_mode_summary = table.get('BillingModeSummary', {})
                    if billing_mode_summary:
                        billing_mode = billing_mode_summary.get('BillingMode', 'PROVISIONED')
                    
                    # テーブル情報を追加
                    tables.append({
                        'ResourceId': table_arn,
                        'ResourceName': table_name,
                        'ResourceType': 'Table',
                        'Status': table.get('TableStatus', 'unknown'),
                        'CreationDateTime': table.get('CreationDateTime', ''),
                        'ItemCount': table.get('ItemCount', 0),
                        'TableSizeBytes': table.get('TableSizeBytes', 0),
                        'BillingMode': billing_mode,
                        'ReadCapacityUnits': read_capacity,
                        'WriteCapacityUnits': write_capacity,
                        'KeySchema': table.get('KeySchema', []),
                        'GlobalSecondaryIndexes': len(table.get('GlobalSecondaryIndexes', [])),
                        'LocalSecondaryIndexes': len(table.get('LocalSecondaryIndexes', [])),
                        'StreamEnabled': table.get('StreamSpecification', {}).get('StreamEnabled', False),
                        'Tags': tags
                    })
                    
                except Exception as e:
                    logger.warning(f"DynamoDBテーブル '{table_name}' の詳細情報取得エラー: {str(e)}")
            
            logger.info(f"DynamoDBテーブル: {len(tables)}件取得")
        except Exception as e:
            logger.error(f"DynamoDBテーブル情報収集中にエラー発生: {str(e)}")
        
        return tables
    
    def _collect_global_tables(self, dynamodb_client) -> List[Dict[str, Any]]:
        """DynamoDBグローバルテーブル情報を収集"""
        logger.info("DynamoDBグローバルテーブル情報を収集しています")
        global_tables = []
        
        try:
            # グローバルテーブル一覧を取得
            response = dynamodb_client.list_global_tables()
            
            for global_table in response.get('GlobalTables', []):
                global_table_name = global_table.get('GlobalTableName', '名前なし')
                replicas = global_table.get('ReplicationGroup', [])
                
                # グローバルテーブル情報を追加
                global_tables.append({
                    'ResourceId': global_table_name,
                    'ResourceName': global_table_name,
                    'ResourceType': 'GlobalTable',
                    'Regions': [replica.get('RegionName', '') for replica in replicas],
                    'ReplicaCount': len(replicas)
                })
            
            logger.info(f"DynamoDBグローバルテーブル: {len(global_tables)}件取得")
        except Exception as e:
            # グローバルテーブル機能が有効でない場合もあるため、警告として処理
            logger.warning(f"DynamoDBグローバルテーブル情報収集中にエラー発生: {str(e)}")
        
        return global_tables
    
    def _collect_backups(self, dynamodb_client) -> List[Dict[str, Any]]:
        """DynamoDBバックアップ情報を収集"""
        logger.info("DynamoDBバックアップ情報を収集しています")
        backups = []
        
        try:
            paginator = dynamodb_client.get_paginator('list_backups')
            
            for page in paginator.paginate():
                for backup in page.get('BackupSummaries', []):
                    backup_name = backup.get('BackupName', '名前なし')
                    table_name = backup.get('TableName', '')
                    
                    # バックアップ情報を追加
                    backups.append({
                        'ResourceId': backup.get('BackupArn', ''),
                        'ResourceName': backup_name,
                        'ResourceType': 'Backup',
                        'TableName': table_name,
                        'BackupStatus': backup.get('BackupStatus', ''),
                        'BackupType': backup.get('BackupType', ''),
                        'BackupCreationDateTime': backup.get('BackupCreationDateTime', ''),
                        'BackupSizeBytes': backup.get('BackupSizeBytes', 0)
                    })
            
            logger.info(f"DynamoDBバックアップ: {len(backups)}件取得")
        except Exception as e:
            logger.error(f"DynamoDBバックアップ情報収集中にエラー発生: {str(e)}")
        
        return backups
