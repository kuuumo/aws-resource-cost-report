#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWS リソースコレクター基底クラス
"""

import logging
import boto3
import botocore
from typing import Dict, List, Any, Optional, Callable

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
            self.client_cache[cache_key] = self.session.client(
                service_name, 
                region_name=region,
                config=botocore.config.Config(retries={'max_attempts': 3})
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
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        リソース情報を収集（サブクラスで実装）
        
        Returns:
            Dict: リソース情報
        """
        raise NotImplementedError("サブクラスで実装する必要があります")
