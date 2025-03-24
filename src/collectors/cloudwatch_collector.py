#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CloudWatch情報収集モジュール
"""

import logging
from typing import Dict, List, Any
from .base_collector import BaseCollector

# ロギングの設定
logger = logging.getLogger(__name__)

class CloudWatchCollector(BaseCollector):
    """CloudWatch情報を収集するクラス"""
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        CloudWatch情報を収集
        
        Returns:
            Dict: CloudWatch情報
        """
        logger.info("CloudWatch情報の収集を開始します")
        results = {}
        
        try:
            # CloudWatchクライアントを取得
            cloudwatch_client = self.get_client('cloudwatch')
            
            # アラーム情報を取得
            alarms = self._collect_alarms(cloudwatch_client)
            if alarms:
                results['CloudWatch_Alarms'] = alarms
            
            # ダッシュボード情報を取得
            dashboards = self._collect_dashboards(cloudwatch_client)
            if dashboards:
                results['CloudWatch_Dashboards'] = dashboards
            
            # CloudWatch Logsクライアントを取得
            logs_client = self.get_client('logs')
            
            # ロググループ情報を取得
            log_groups = self._collect_log_groups(logs_client)
            if log_groups:
                results['CloudWatch_LogGroups'] = log_groups
            
            # CloudWatch Eventsクライアントを取得（EventBridgeと同じAPI）
            events_client = self.get_client('events')
            
            # ルール情報を取得
            rules = self._collect_rules(events_client)
            if rules:
                results['CloudWatch_Rules'] = rules
            
        except Exception as e:
            logger.error(f"CloudWatch情報収集中にエラー発生: {str(e)}")
        
        return results
    
    def _collect_alarms(self, cloudwatch_client) -> List[Dict[str, Any]]:
        """CloudWatchアラーム情報を収集"""
        logger.info("CloudWatchアラーム情報を収集しています")
        alarms = []
        
        try:
            paginator = cloudwatch_client.get_paginator('describe_alarms')
            
            for page in paginator.paginate():
                # メトリクスアラーム
                for alarm in page.get('MetricAlarms', []):
                    alarm_name = alarm.get('AlarmName', '名前なし')
                    
                    # タグの取得はスキップして空のタグリストを使用
                    # CloudWatchアラームのタグ取得には権限の問題がある可能性があるため
                    tags = []
                    
                    # 以下のコードはコメントアウト（将来的に必要になった場合のために残しておく）
                    """
                    try:
                        if 'AlarmArn' in alarm:
                            tag_response = cloudwatch_client.list_tags_for_resource(
                                ResourceARN=alarm['AlarmArn']
                            )
                            tags = tag_response.get('Tags', [])
                    except Exception as e:
                        logger.warning(f"CloudWatchアラーム '{alarm_name}' のタグ取得エラー: {str(e)}")
                    """
                    
                    # アラーム情報を追加
                    alarms.append({
                        'ResourceId': alarm.get('AlarmArn', ''),
                        'ResourceName': alarm_name,
                        'ResourceType': 'MetricAlarm',
                        'AlarmDescription': alarm.get('AlarmDescription', ''),
                        'Namespace': alarm.get('Namespace', ''),
                        'MetricName': alarm.get('MetricName', ''),
                        'Statistic': alarm.get('Statistic', ''),
                        'Period': alarm.get('Period', 0),
                        'EvaluationPeriods': alarm.get('EvaluationPeriods', 0),
                        'Threshold': alarm.get('Threshold', 0),
                        'ComparisonOperator': alarm.get('ComparisonOperator', ''),
                        'AlarmActions': alarm.get('AlarmActions', []),
                        'OKActions': alarm.get('OKActions', []),
                        'InsufficientDataActions': alarm.get('InsufficientDataActions', []),
                        'StateValue': alarm.get('StateValue', ''),
                        'StateUpdatedTimestamp': alarm.get('StateUpdatedTimestamp', ''),
                        'Tags': tags
                    })
                
                # 複合アラーム
                for alarm in page.get('CompositeAlarms', []):
                    alarm_name = alarm.get('AlarmName', '名前なし')
                    
                    # タグの取得はスキップして空のタグリストを使用
                    # CloudWatch複合アラームのタグ取得には権限の問題がある可能性があるため
                    tags = []
                    
                    # 以下のコードはコメントアウト（将来的に必要になった場合のために残しておく）
                    """
                    try:
                        if 'AlarmArn' in alarm:
                            tag_response = cloudwatch_client.list_tags_for_resource(
                                ResourceARN=alarm['AlarmArn']
                            )
                            tags = tag_response.get('Tags', [])
                    except Exception as e:
                        logger.warning(f"CloudWatch複合アラーム '{alarm_name}' のタグ取得エラー: {str(e)}")
                    """
                    
                    # 複合アラーム情報を追加
                    alarms.append({
                        'ResourceId': alarm.get('AlarmArn', ''),
                        'ResourceName': alarm_name,
                        'ResourceType': 'CompositeAlarm',
                        'AlarmDescription': alarm.get('AlarmDescription', ''),
                        'AlarmRule': alarm.get('AlarmRule', ''),
                        'AlarmActions': alarm.get('AlarmActions', []),
                        'OKActions': alarm.get('OKActions', []),
                        'InsufficientDataActions': alarm.get('InsufficientDataActions', []),
                        'StateValue': alarm.get('StateValue', ''),
                        'StateUpdatedTimestamp': alarm.get('StateUpdatedTimestamp', ''),
                        'Tags': tags
                    })
            
            logger.info(f"CloudWatchアラーム: {len(alarms)}件取得")
        except Exception as e:
            logger.error(f"CloudWatchアラーム情報収集中にエラー発生: {str(e)}")
        
        return alarms
    
    def _collect_dashboards(self, cloudwatch_client) -> List[Dict[str, Any]]:
        """CloudWatchダッシュボード情報を収集"""
        logger.info("CloudWatchダッシュボード情報を収集しています")
        dashboards = []
        
        try:
            paginator = cloudwatch_client.get_paginator('list_dashboards')
            
            for page in paginator.paginate():
                for entry in page.get('DashboardEntries', []):
                    dashboard_name = entry.get('DashboardName', '名前なし')
                    
                    # ダッシュボード情報を追加
                    dashboards.append({
                        'ResourceId': entry.get('DashboardArn', ''),
                        'ResourceName': dashboard_name,
                        'ResourceType': 'Dashboard',
                        'LastModified': entry.get('LastModified', ''),
                        'Size': entry.get('Size', 0)
                    })
            
            logger.info(f"CloudWatchダッシュボード: {len(dashboards)}件取得")
        except Exception as e:
            logger.error(f"CloudWatchダッシュボード情報収集中にエラー発生: {str(e)}")
        
        return dashboards
    
    def _collect_log_groups(self, logs_client) -> List[Dict[str, Any]]:
        """CloudWatch Logsロググループ情報を収集"""
        logger.info("CloudWatch Logsロググループ情報を収集しています")
        log_groups = []
        
        try:
            paginator = logs_client.get_paginator('describe_log_groups')
            
            for page in paginator.paginate():
                for group in page.get('logGroups', []):
                    group_name = group.get('logGroupName', '名前なし')
                    
                    # タグの取得はスキップして空のタグリストを使用
                    # CloudWatch Logsロググループのタグ取得には権限の問題がある可能性があるため
                    tags = []
                    
                    # 以下のコードはコメントアウト（将来的に必要になった場合のために残しておく）
                    """
                    try:
                        # ARNを手動で構築する
                        # APIからARNが返されない場合があるため、自分で構築する
                        if 'arn' in group:
                            log_group_arn = group['arn']
                        else:
                            # AWS アカウントIDとリージョンを取得
                            sts_client = self.get_client('sts')
                            account_id = sts_client.get_caller_identity()['Account']
                            region = logs_client.meta.region_name
                            
                            # ARNを構築
                            log_group_name = group.get('logGroupName', '')
                            # CloudWatch Logs ARN形式: arn:aws:logs:region:account-id:log-group:log-group-name:*
                            log_group_arn = f'arn:aws:logs:{region}:{account_id}:log-group:{log_group_name}:*'
                            
                        tag_response = logs_client.list_tags_for_resource(
                            resourceArn=log_group_arn
                        )
                        # タグ形式を他のリソースと合わせる
                        tags = [{'Key': k, 'Value': v} for k, v in tag_response.get('tags', {}).items()]
                    except Exception as e:
                        logger.warning(f"CloudWatch Logsロググループ '{group_name}' のタグ取得エラー: {str(e)}")
                    """
                    
                    # ロググループ情報を追加
                    log_groups.append({
                        'ResourceId': group.get('arn', ''),
                        'ResourceName': group_name,
                        'ResourceType': 'LogGroup',
                        'CreationTime': group.get('creationTime', 0),
                        'RetentionInDays': group.get('retentionInDays', 0),
                        'MetricFilterCount': group.get('metricFilterCount', 0),
                        'StoredBytes': group.get('storedBytes', 0),
                        'KmsKeyId': group.get('kmsKeyId', ''),
                        'Tags': tags
                    })
            
            logger.info(f"CloudWatch Logsロググループ: {len(log_groups)}件取得")
        except Exception as e:
            logger.error(f"CloudWatch Logsロググループ情報収集中にエラー発生: {str(e)}")
        
        return log_groups
    
    def _collect_rules(self, events_client) -> List[Dict[str, Any]]:
        """CloudWatch Eventsルール情報を収集"""
        logger.info("CloudWatch Eventsルール情報を収集しています")
        rules = []
        
        try:
            paginator = events_client.get_paginator('list_rules')
            
            for page in paginator.paginate():
                for rule in page.get('Rules', []):
                    rule_name = rule.get('Name', '名前なし')
                    
                    # タグの取得はスキップして空のタグリストを使用
                    # CloudWatch Eventsルールのタグ取得には権限の問題がある可能性があるため
                    tags = []
                    
                    # 以下のコードはコメントアウト（将来的に必要になった場合のために残しておく）
                    """
                    try:
                        if 'Arn' in rule:
                            tag_response = events_client.list_tags_for_resource(
                                ResourceARN=rule['Arn']
                            )
                            tags = tag_response.get('Tags', [])
                    except Exception as e:
                        logger.warning(f"CloudWatch Eventsルール '{rule_name}' のタグ取得エラー: {str(e)}")
                    """
                    
                    # ルールのターゲット情報を取得
                    targets = []
                    try:
                        target_response = events_client.list_targets_by_rule(
                            Rule=rule_name
                        )
                        targets = [target.get('Id', '') for target in target_response.get('Targets', [])]
                    except Exception as e:
                        logger.warning(f"CloudWatch Eventsルール '{rule_name}' のターゲット情報取得エラー: {str(e)}")
                    
                    # ルール情報を追加
                    rules.append({
                        'ResourceId': rule.get('Arn', ''),
                        'ResourceName': rule_name,
                        'ResourceType': 'EventRule',
                        'Description': rule.get('Description', ''),
                        'ScheduleExpression': rule.get('ScheduleExpression', ''),
                        'EventPattern': rule.get('EventPattern', ''),
                        'State': rule.get('State', ''),
                        'ManagedBy': rule.get('ManagedBy', ''),
                        'Targets': targets,
                        'Tags': tags
                    })
            
            logger.info(f"CloudWatch Eventsルール: {len(rules)}件取得")
        except Exception as e:
            logger.error(f"CloudWatch Eventsルール情報収集中にエラー発生: {str(e)}")
        
        return rules
