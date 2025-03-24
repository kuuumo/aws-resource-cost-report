#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lambda関数情報収集モジュール
"""

import logging
from typing import Dict, List, Any
from .base_collector import BaseCollector

# ロギングの設定
logger = logging.getLogger(__name__)

class LambdaCollector(BaseCollector):
    """Lambda関数情報を収集するクラス"""
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Lambda関数情報を収集
        
        Returns:
            Dict: Lambda関数情報
        """
        logger.info("Lambda関数情報の収集を開始します")
        results = {}
        
        try:
            # Lambdaクライアントを取得
            lambda_client = self.get_client('lambda')
            
            # Lambda関数情報を取得
            functions = self._collect_functions(lambda_client)
            if functions:
                results['Lambda_Functions'] = functions
            
            # レイヤー情報を取得
            layers = self._collect_layers(lambda_client)
            if layers:
                results['Lambda_Layers'] = layers
                
            # イベントソースマッピング情報を取得
            event_source_mappings = self._collect_event_source_mappings(lambda_client)
            if event_source_mappings:
                results['Lambda_EventSourceMappings'] = event_source_mappings
                
        except Exception as e:
            logger.error(f"Lambda関数情報収集中にエラー発生: {str(e)}")
        
        return results
    
    def _collect_functions(self, lambda_client) -> List[Dict[str, Any]]:
        """Lambda関数情報を収集"""
        logger.info("Lambda関数情報を収集しています")
        functions = []
        
        try:
            paginator = lambda_client.get_paginator('list_functions')
            for page in paginator.paginate():
                for func in page.get('Functions', []):
                    function_name = func.get('FunctionName', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if 'FunctionArn' in func:
                            tag_response = lambda_client.list_tags(
                                Resource=func['FunctionArn']
                            )
                            # タグ形式を他のリソースと合わせる
                            tags = [{'Key': k, 'Value': v} for k, v in tag_response.get('Tags', {}).items()]
                    except Exception as e:
                        logger.warning(f"Lambda関数 '{function_name}' のタグ取得エラー: {str(e)}")
                    
                    # 関数の設定情報を取得
                    vpc_config = func.get('VpcConfig', {})
                    environment = func.get('Environment', {}).get('Variables', {})
                    
                    # 関数情報を追加
                    functions.append({
                        'ResourceId': func['FunctionArn'],
                        'ResourceName': function_name,
                        'ResourceType': 'Function',
                        'Runtime': func.get('Runtime', 'unknown'),
                        'Role': func.get('Role', ''),
                        'Handler': func.get('Handler', ''),
                        'CodeSize': func.get('CodeSize', 0),
                        'Description': func.get('Description', ''),
                        'Timeout': func.get('Timeout', 0),
                        'MemorySize': func.get('MemorySize', 0),
                        'LastModified': func.get('LastModified', ''),
                        'State': func.get('State', 'unknown'),
                        'PackageType': func.get('PackageType', 'Zip'),
                        'Architectures': func.get('Architectures', ['x86_64']),
                        'VpcEnabled': bool(vpc_config.get('VpcId')),
                        'VpcId': vpc_config.get('VpcId', ''),
                        'SubnetIds': vpc_config.get('SubnetIds', []),
                        'SecurityGroupIds': vpc_config.get('SecurityGroupIds', []),
                        'EnvironmentVariableCount': len(environment),
                        'Tags': tags
                    })
            
            logger.info(f"Lambda関数: {len(functions)}件取得")
        except Exception as e:
            logger.error(f"Lambda関数情報収集中にエラー発生: {str(e)}")
        
        return functions
    
    def _collect_layers(self, lambda_client) -> List[Dict[str, Any]]:
        """Lambdaレイヤー情報を収集"""
        logger.info("Lambdaレイヤー情報を収集しています")
        layers = []
        
        try:
            paginator = lambda_client.get_paginator('list_layers')
            for page in paginator.paginate():
                for layer in page.get('Layers', []):
                    layer_name = layer.get('LayerName', '名前なし')
                    
                    # レイヤーの最新バージョン
                    latest_version = layer.get('LatestMatchingVersion', {})
                    
                    # レイヤー情報を追加
                    layers.append({
                        'ResourceId': layer.get('LayerArn', ''),
                        'ResourceName': layer_name,
                        'ResourceType': 'Layer',
                        'Description': latest_version.get('Description', ''),
                        'LatestVersion': latest_version.get('Version', 0),
                        'CreatedDate': latest_version.get('CreatedDate', ''),
                        'CompatibleRuntimes': latest_version.get('CompatibleRuntimes', []),
                        'CompatibleArchitectures': latest_version.get('CompatibleArchitectures', []),
                        'CodeSize': latest_version.get('CodeSize', 0)
                    })
            
            logger.info(f"Lambdaレイヤー: {len(layers)}件取得")
        except Exception as e:
            logger.error(f"Lambdaレイヤー情報収集中にエラー発生: {str(e)}")
        
        return layers
    
    def _collect_event_source_mappings(self, lambda_client) -> List[Dict[str, Any]]:
        """Lambdaイベントソースマッピング情報を収集"""
        logger.info("Lambdaイベントソースマッピング情報を収集しています")
        mappings = []
        
        try:
            paginator = lambda_client.get_paginator('list_event_source_mappings')
            for page in paginator.paginate():
                for mapping in page.get('EventSourceMappings', []):
                    mapping_id = mapping.get('UUID', '名前なし')
                    function_name = mapping.get('FunctionArn', '').split(':')[-1]
                    
                    # マッピング情報を追加
                    mappings.append({
                        'ResourceId': mapping_id,
                        'ResourceName': f"{function_name}-{mapping_id[:8]}",
                        'ResourceType': 'EventSourceMapping',
                        'EventSourceArn': mapping.get('EventSourceArn', ''),
                        'FunctionArn': mapping.get('FunctionArn', ''),
                        'State': mapping.get('State', ''),
                        'BatchSize': mapping.get('BatchSize', 0),
                        'LastModified': mapping.get('LastModified', ''),
                        'LastProcessingResult': mapping.get('LastProcessingResult', ''),
                        'StateTransitionReason': mapping.get('StateTransitionReason', '')
                    })
            
            logger.info(f"Lambdaイベントソースマッピング: {len(mappings)}件取得")
        except Exception as e:
            logger.error(f"Lambdaイベントソースマッピング情報収集中にエラー発生: {str(e)}")
        
        return mappings
