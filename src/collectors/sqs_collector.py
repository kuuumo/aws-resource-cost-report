#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQS情報収集モジュール
"""

import logging
from typing import Dict, List, Any
from .base_collector import BaseCollector

# ロギングの設定
logger = logging.getLogger(__name__)

class SQSCollector(BaseCollector):
    """SQS情報を収集するクラス"""
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        SQS情報を収集
        
        Returns:
            Dict: SQS情報
        """
        logger.info("SQS情報の収集を開始します")
        results = {}
        
        try:
            # SQSクライアントを取得
            sqs_client = self.get_client('sqs')
            
            # キュー情報を取得
            queues = self._collect_queues(sqs_client)
            if queues:
                results['SQS_Queues'] = queues
                
        except Exception as e:
            logger.error(f"SQS情報収集中にエラー発生: {str(e)}")
        
        return results
    
    def _collect_queues(self, sqs_client) -> List[Dict[str, Any]]:
        """SQSキュー情報を収集"""
        logger.info("SQSキュー情報を収集しています")
        queues = []
        
        try:
            paginator = sqs_client.get_paginator('list_queues')
            
            # 標準キューとFIFOキューの両方を取得するために、PrefixなしとFIFO用のPrefixを使用
            for prefix in ['', '.fifo']:
                try:
                    for page in paginator.paginate(QueueNamePrefix=prefix):
                        for queue_url in page.get('QueueUrls', []):
                            queue_name = queue_url.split('/')[-1]  # URLからキュー名を抽出
                            
                            # キューの属性を取得
                            try:
                                attr_response = sqs_client.get_queue_attributes(
                                    QueueUrl=queue_url,
                                    AttributeNames=['All']
                                )
                                attributes = attr_response.get('Attributes', {})
                            except Exception as e:
                                logger.warning(f"SQSキュー '{queue_name}' の属性取得エラー: {str(e)}")
                                attributes = {}
                            
                            # タグを取得
                            tags = []
                            try:
                                tag_response = sqs_client.list_queue_tags(
                                    QueueUrl=queue_url
                                )
                                # タグ形式を他のリソースと合わせる
                                tags = [{'Key': k, 'Value': v} 
                                      for k, v in tag_response.get('Tags', {}).items()]
                            except Exception as e:
                                logger.warning(f"SQSキュー '{queue_name}' のタグ取得エラー: {str(e)}")
                            
                            # キュー情報を追加
                            queue_arn = attributes.get('QueueArn', '')
                            queues.append({
                                'ResourceId': queue_arn,
                                'ResourceName': queue_name,
                                'ResourceType': 'Queue',
                                'QueueUrl': queue_url,
                                'FifoQueue': queue_name.endswith('.fifo'),
                                'VisibilityTimeout': int(attributes.get('VisibilityTimeout', 30)),
                                'MaximumMessageSize': int(attributes.get('MaximumMessageSize', 262144)),
                                'MessageRetentionPeriod': int(attributes.get('MessageRetentionPeriod', 345600)),
                                'DelaySeconds': int(attributes.get('DelaySeconds', 0)),
                                'ReceiveMessageWaitTimeSeconds': int(attributes.get('ReceiveMessageWaitTimeSeconds', 0)),
                                'ApproximateNumberOfMessages': int(attributes.get('ApproximateNumberOfMessages', 0)),
                                'ApproximateNumberOfMessagesNotVisible': int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0)),
                                'ApproximateNumberOfMessagesDelayed': int(attributes.get('ApproximateNumberOfMessagesDelayed', 0)),
                                'ContentBasedDeduplication': attributes.get('ContentBasedDeduplication', 'false') == 'true',
                                'KmsMasterKeyId': attributes.get('KmsMasterKeyId', ''),
                                'KmsDataKeyReusePeriodSeconds': int(attributes.get('KmsDataKeyReusePeriodSeconds', 300)),
                                'SqsManagedSseEnabled': attributes.get('SqsManagedSseEnabled', 'false') == 'true',
                                'CreatedTimestamp': attributes.get('CreatedTimestamp', ''),
                                'LastModifiedTimestamp': attributes.get('LastModifiedTimestamp', ''),
                                'RedrivePolicy': attributes.get('RedrivePolicy', ''),
                                'DeadLetterTargetArn': self._extract_dlq_arn(attributes.get('RedrivePolicy', '')),
                                'Tags': tags
                            })
                except Exception as e:
                    logger.warning(f"SQSキュー（プレフィックス '{prefix}'）の一覧取得エラー: {str(e)}")
            
            logger.info(f"SQSキュー: {len(queues)}件取得")
        except Exception as e:
            logger.error(f"SQSキュー情報収集中にエラー発生: {str(e)}")
        
        return queues
    
    def _extract_dlq_arn(self, redrive_policy: str) -> str:
        """
        リドライブポリシーからデッドレターキューのARNを抽出
        
        Args:
            redrive_policy (str): リドライブポリシーのJSON文字列
            
        Returns:
            str: デッドレターキューのARN（存在しない場合は空文字）
        """
        import json
        
        if not redrive_policy:
            return ''
        
        try:
            policy = json.loads(redrive_policy)
            return policy.get('deadLetterTargetArn', '')
        except Exception:
            return ''
