#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWS リソースコレクター基底クラス
"""

import logging
import boto3
import botocore
import time
from typing import Dict, List, Any, Optional, Callable
from botocore.exceptions import ClientError

# ロギングの設定
logger = logging.getLogger(__name__)

class BaseCollector:
    """AWS リソースコレクターの基底クラス"""
    
    def __init__(self, session, region_name=None):
        """
        初期化関数
        
        Args:
            session (boto3.Session): AWS セッション
            region_name (str, optional): 対象リージョン
        """
        self.session = session
        self.region_name = region_name or session.region_name
        self.client_cache = {}
    
    def get_client(self, service_name: str, region: Optional[str] = None) -> Any:
        """
        指定したサービスのboto3クライアントを取得（キャッシュ付き）
        
        Args:
            service_name (str): AWSサービス名
            region (str, optional): リージョン（指定なしの場合、デフォルトリージョン）
            
        Returns:
            Any: boto3クライアントオブジェクト
        """
        region = region or self.region_name
        cache_key = f"{service_name}_{region}"
        
        if cache_key not in self.client_cache:
            # 再試行設定を強化
            retry_config = botocore.config.Config(
                retries={'max_attempts': 5, 'mode': 'adaptive'},
                connect_timeout=10,
                read_timeout=15
            )
            
            self.client_cache[cache_key] = self.session.client(
                service_name, 
                region_name=region,
                config=retry_config
            )
        
        return self.client_cache[cache_key]
    
    def get_resource_name_from_tags(self, tags, default='名前なし'):
        """
        タグリストから Name タグの値を取得
        
        Args:
            tags (List): タグのリスト
            default (str): タグがない場合のデフォルト値
            
        Returns:
            str: リソース名
        """
        if not tags:
            return default
            
        for tag in tags:
            if tag.get('Key') == 'Name':
                return tag.get('Value') or default
                
        return default
    
    def aws_api_call(self, client_method: Callable, **kwargs) -> Dict:
        """
        AWS APIを安全に呼び出す（再試行ロジック付き）
        
        Args:
            client_method (Callable): 呼び出すAWS APIメソッド
            **kwargs: APIメソッドに渡す引数
            
        Returns:
            Dict: API呼び出しの結果
            
        Raises:
            ClientError: API呼び出し失敗時
        """
        # 再試行の実装
        max_attempts = 3
        initial_delay = 1.0
        backoff_factor = 2.0
        
        for attempt in range(1, max_attempts + 1):
            try:
                return client_method(**kwargs)
            except (
                botocore.exceptions.ConnectionClosedError,
                botocore.exceptions.EndpointConnectionError, 
                botocore.exceptions.ConnectTimeoutError,
                botocore.exceptions.ReadTimeoutError
            ) as e:
                if attempt < max_attempts:
                    delay = initial_delay * (backoff_factor ** (attempt - 1))
                    logger.warning(f"ネットワークエラー発生: {type(e).__name__}, {attempt}回目の試行, {delay:.2f}秒後に再試行します: {str(e)}")
                    time.sleep(delay)
                    continue
                raise
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                retry_errors = [
                    'RequestLimitExceeded', 'Throttling', 'ThrottlingException', 
                    'RequestThrottledException', 'TooManyRequestsException',
                    'ProvisionedThroughputExceededException', 'TransactionInProgressException',
                    'RequestTimeout', 'ServiceUnavailable', 'InternalServiceError'
                ]
                
                if error_code in retry_errors and attempt < max_attempts:
                    delay = initial_delay * (backoff_factor ** (attempt - 1))
                    logger.warning(f"APIエラー発生: {error_code}, {attempt}回目の試行, {delay:.2f}秒後に再試行します: {str(e)}")
                    time.sleep(delay)
                    continue
                raise
        
        # 予防的な戻り値（通常はここに到達しない）
        return {}
    
    def safe_get_tags(self, resource_id: str, resource_name: str, service_client: Any, 
                     tag_method_name: str, **tag_method_args) -> List[Dict[str, str]]:
        """
        リソースからタグを安全に取得する
        
        Args:
            resource_id (str): リソースID
            resource_name (str): リソース名
            service_client (Any): AWSサービスクライアント
            tag_method_name (str): タグ取得メソッド名
            **tag_method_args: タグ取得メソッドに渡す引数
            
        Returns:
            List[Dict[str, str]]: タグリスト、取得に失敗した場合は空リスト
        """
        try:
            tag_method = getattr(service_client, tag_method_name)
            tag_response = self.aws_api_call(tag_method, **tag_method_args)
            
            # タグのレスポンス形式はサービスによって異なるため、一般的な形式に変換
            if 'Tags' in tag_response:
                return tag_response['Tags']
            elif 'TagList' in tag_response:
                return tag_response['TagList']
            elif 'tags' in tag_response:
                return [{'Key': k, 'Value': v} for k, v in tag_response['tags'].items()]
            elif 'ResourceTagSet' in tag_response and 'Tags' in tag_response['ResourceTagSet']:
                return tag_response['ResourceTagSet']['Tags']
            else:
                return []
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['AccessDenied', 'UnauthorizedOperation', 'InvalidParameterValue', 'ResourceNotFoundException']:
                logger.warning(f"リソース '{resource_name}' (ID: {resource_id}) のタグ取得エラー（権限不足）: {str(e)}")
            else:
                logger.warning(f"リソース '{resource_name}' (ID: {resource_id}) のタグ取得エラー: {str(e)}")
        except Exception as e:
            logger.warning(f"リソース '{resource_name}' (ID: {resource_id}) のタグ取得中に未知のエラー発生: {str(e)}")
            
        return []
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        リソース情報を収集（サブクラスで実装）
        
        Returns:
            Dict: リソース情報
        """
        raise NotImplementedError("サブクラスで実装する必要があります")
