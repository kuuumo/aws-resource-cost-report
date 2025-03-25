#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
エラーハンドリングユーティリティモジュール
"""

import logging
import time
import random
from functools import wraps
from typing import Callable, Any, Dict, Type, List, Union, Optional
from botocore.exceptions import ClientError, ConnectionClosedError, EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError

# ロギングの設定
logger = logging.getLogger(__name__)

# 再試行対象のエラー
RETRY_EXCEPTIONS = (
    ConnectionClosedError,
    EndpointConnectionError,
    ConnectTimeoutError,
    ReadTimeoutError,
    'RequestLimitExceeded',
    'Throttling',
    'ThrottlingException',
    'RequestThrottledException',
    'TooManyRequestsException',
    'ProvisionedThroughputExceededException',
    'TransactionInProgressException',
    'RequestTimeout',
    'ServiceUnavailable',
    'InternalServiceError'
)

def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_exceptions: Optional[Union[Type[Exception], List[Type[Exception]], List[str]]] = None
) -> Callable:
    """
    AWSのAPI呼び出しを再試行するデコレータ
    
    Args:
        max_attempts (int): 最大試行回数（デフォルト: 3）
        initial_delay (float): 初期待機時間（秒）（デフォルト: 1.0）
        backoff_factor (float): バックオフ係数（デフォルト: 2.0）
        jitter (bool): ジッターを追加するかどうか（デフォルト: True）
        retry_exceptions (Optional[Union[Type[Exception], List[Type[Exception]], List[str]]]): 
            再試行する例外クラスまたはエラーコードのリスト
            
    Returns:
        Callable: デコレータ関数
    """
    if retry_exceptions is None:
        retry_exceptions = RETRY_EXCEPTIONS
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    
                    # エラーコードが再試行対象か確認
                    if isinstance(retry_exceptions, (list, tuple)) and error_code in retry_exceptions:
                        last_exception = e
                        if attempt < max_attempts:
                            delay = calculate_delay(attempt, initial_delay, backoff_factor, jitter)
                            logger.warning(f"APIエラー発生: {error_code}, {attempt}回目の試行, {delay:.2f}秒後に再試行します: {str(e)}")
                            time.sleep(delay)
                            continue
                    raise
                except Exception as e:
                    # 一般的な例外が再試行対象かどうか確認
                    if isinstance(e, retry_exceptions) or type(e) in retry_exceptions:
                        last_exception = e
                        if attempt < max_attempts:
                            delay = calculate_delay(attempt, initial_delay, backoff_factor, jitter)
                            logger.warning(f"例外発生: {type(e).__name__}, {attempt}回目の試行, {delay:.2f}秒後に再試行します: {str(e)}")
                            time.sleep(delay)
                            continue
                    raise
            
            # 全ての試行が失敗した場合
            if last_exception:
                logger.error(f"全ての再試行が失敗しました（{max_attempts}回）: {str(last_exception)}")
                raise last_exception
            
            # 予防的な戻り値（通常はここに到達しない）
            return None
        
        return wrapper
    
    return decorator

def calculate_delay(attempt: int, initial_delay: float, backoff_factor: float, jitter: bool) -> float:
    """
    指数バックオフとジッターに基づいて待機時間を計算
    
    Args:
        attempt (int): 現在の試行回数
        initial_delay (float): 初期待機時間（秒）
        backoff_factor (float): バックオフ係数
        jitter (bool): ジッターを追加するかどうか
        
    Returns:
        float: 計算された待機時間（秒）
    """
    delay = initial_delay * (backoff_factor ** (attempt - 1))
    
    if jitter:
        # 0.5 ~ 1.5の間のランダム係数を適用
        jitter_factor = random.uniform(0.5, 1.5)
        delay *= jitter_factor
    
    return delay

def safe_get(
    dictionary: Dict, 
    key_path: str, 
    default: Any = None, 
    separator: str = '.'
) -> Any:
    """
    ネストされた辞書から安全に値を取得する
    
    Args:
        dictionary (Dict): 対象の辞書
        key_path (str): キーパス（例: 'a.b.c'）
        default (Any): キーパスが見つからない場合のデフォルト値
        separator (str): キーパスの区切り文字（デフォルト: '.'）
        
    Returns:
        Any: 取得した値またはデフォルト値
    """
    keys = key_path.split(separator)
    result = dictionary
    
    for key in keys:
        try:
            if isinstance(result, dict):
                result = result.get(key, default)
            elif isinstance(result, (list, tuple)) and key.isdigit():
                index = int(key)
                if 0 <= index < len(result):
                    result = result[index]
                else:
                    return default
            else:
                return default
        except (KeyError, IndexError, TypeError):
            return default
    
    return result
