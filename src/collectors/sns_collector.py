#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SNS情報収集モジュール
"""

import logging
from typing import Dict, List, Any
from .base_collector import BaseCollector

# ロギングの設定
logger = logging.getLogger(__name__)

class SNSCollector(BaseCollector):
    """SNS情報を収集するクラス"""
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        SNS情報を収集
        
        Returns:
            Dict: SNS情報
        """
        logger.info("SNS情報の収集を開始します")
        results = {}
        
        try:
            # SNSクライアントを取得
            sns_client = self.get_client('sns')
            
            # トピック情報を取得
            topics = self._collect_topics(sns_client)
            if topics:
                results['SNS_Topics'] = topics
            
            # サブスクリプション情報を取得
            subscriptions = self._collect_subscriptions(sns_client)
            if subscriptions:
                results['SNS_Subscriptions'] = subscriptions
                
        except Exception as e:
            logger.error(f"SNS情報収集中にエラー発生: {str(e)}")
        
        return results
    
    def _collect_topics(self, sns_client) -> List[Dict[str, Any]]:
        """SNSトピック情報を収集"""
        logger.info("SNSトピック情報を収集しています")
        topics = []
        
        try:
            paginator = sns_client.get_paginator('list_topics')
            
            for page in paginator.paginate():
                for topic in page.get('Topics', []):
                    topic_arn = topic.get('TopicArn', '')
                    topic_name = topic_arn.split(':')[-1]  # ARNからトピック名を抽出
                    
                    # トピックの属性を取得
                    try:
                        attr_response = sns_client.get_topic_attributes(
                            TopicArn=topic_arn
                        )
                        attributes = attr_response.get('Attributes', {})
                    except Exception as e:
                        logger.warning(f"SNSトピック '{topic_name}' の属性取得エラー: {str(e)}")
                        attributes = {}
                    
                    # タグを取得
                    tags = []
                    try:
                        tag_response = sns_client.list_tags_for_resource(
                            ResourceArn=topic_arn
                        )
                        # タグ形式を他のリソースと合わせる
                        tags = [{'Key': tag['Key'], 'Value': tag['Value']} 
                               for tag in tag_response.get('Tags', [])]
                    except Exception as e:
                        logger.warning(f"SNSトピック '{topic_name}' のタグ取得エラー: {str(e)}")
                    
                    # トピック情報を追加
                    topics.append({
                        'ResourceId': topic_arn,
                        'ResourceName': topic_name,
                        'ResourceType': 'Topic',
                        'DisplayName': attributes.get('DisplayName', ''),
                        'SubscriptionsConfirmed': int(attributes.get('SubscriptionsConfirmed', 0)),
                        'SubscriptionsPending': int(attributes.get('SubscriptionsPending', 0)),
                        'SubscriptionsDeleted': int(attributes.get('SubscriptionsDeleted', 0)),
                        'DeliveryPolicy': attributes.get('DeliveryPolicy', ''),
                        'EffectiveDeliveryPolicy': attributes.get('EffectiveDeliveryPolicy', ''),
                        'Policy': attributes.get('Policy', ''),
                        'KmsMasterKeyId': attributes.get('KmsMasterKeyId', ''),
                        'FifoTopic': attributes.get('FifoTopic', 'false') == 'true',
                        'ContentBasedDeduplication': attributes.get('ContentBasedDeduplication', 'false') == 'true',
                        'Tags': tags
                    })
            
            logger.info(f"SNSトピック: {len(topics)}件取得")
        except Exception as e:
            logger.error(f"SNSトピック情報収集中にエラー発生: {str(e)}")
        
        return topics
    
    def _collect_subscriptions(self, sns_client) -> List[Dict[str, Any]]:
        """SNSサブスクリプション情報を収集"""
        logger.info("SNSサブスクリプション情報を収集しています")
        subscriptions = []
        
        try:
            paginator = sns_client.get_paginator('list_subscriptions')
            
            for page in paginator.paginate():
                for subscription in page.get('Subscriptions', []):
                    subscription_arn = subscription.get('SubscriptionArn', '')
                    
                    # ARNが保留状態（PendingConfirmation）の場合はスキップ
                    if subscription_arn == 'PendingConfirmation':
                        continue
                    
                    # サブスクリプション名（便宜上、ARNの最後の部分または一意のID）
                    if ':' in subscription_arn:
                        subscription_name = subscription_arn.split(':')[-1]
                    else:
                        subscription_name = subscription_arn
                    
                    # サブスクリプションの属性を取得（確認済みの場合のみ）
                    attributes = {}
                    try:
                        if subscription_arn != 'PendingConfirmation':
                            attr_response = sns_client.get_subscription_attributes(
                                SubscriptionArn=subscription_arn
                            )
                            attributes = attr_response.get('Attributes', {})
                    except Exception as e:
                        logger.warning(f"SNSサブスクリプション '{subscription_name}' の属性取得エラー: {str(e)}")
                    
                    # サブスクリプション情報を追加
                    subscriptions.append({
                        'ResourceId': subscription_arn,
                        'ResourceName': subscription_name,
                        'ResourceType': 'Subscription',
                        'TopicArn': subscription.get('TopicArn', ''),
                        'Protocol': subscription.get('Protocol', ''),
                        'Endpoint': subscription.get('Endpoint', ''),
                        'Owner': subscription.get('Owner', ''),
                        'ConfirmationWasAuthenticated': attributes.get('ConfirmationWasAuthenticated', 'false') == 'true',
                        'DeliveryPolicy': attributes.get('DeliveryPolicy', ''),
                        'EffectiveDeliveryPolicy': attributes.get('EffectiveDeliveryPolicy', ''),
                        'FilterPolicy': attributes.get('FilterPolicy', ''),
                        'RawMessageDelivery': attributes.get('RawMessageDelivery', 'false') == 'true',
                        'RedrivePolicy': attributes.get('RedrivePolicy', ''),
                        'SubscriptionRoleArn': attributes.get('SubscriptionRoleArn', '')
                    })
            
            logger.info(f"SNSサブスクリプション: {len(subscriptions)}件取得")
        except Exception as e:
            logger.error(f"SNSサブスクリプション情報収集中にエラー発生: {str(e)}")
        
        return subscriptions
