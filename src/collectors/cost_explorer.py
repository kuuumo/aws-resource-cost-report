#!/usr/bin/env python3

import boto3
import logging
import datetime
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

class CostExplorerCollector:
    """
    AWS Cost Explorer APIを使用してコスト情報を収集するクラス
    """
    
    def __init__(self, start_date, end_date):
        """
        初期化
        
        Args:
            start_date (str): コスト期間の開始日 (YYYY-MM-DD形式)
            end_date (str): コスト期間の終了日 (YYYY-MM-DD形式)
        """
        self.start_date = start_date
        self.end_date = end_date
        self.client = boto3.client('ce')
    
    def collect(self):
        """
        コスト情報を収集
        
        Returns:
            dict: 収集したコスト情報
        """
        try:
            logger.info(f"Collecting cost data from {self.start_date} to {self.end_date}")
            
            # 総コストを取得
            total_cost = self._get_total_cost()
            
            # 前期間比較データを取得
            comparison = self._get_previous_period_comparison()
            
            # サービス別コストを取得
            service_costs = self._get_service_costs()
            
            # リージョン別コストを取得
            region_costs = self._get_region_costs()
            
            # 日次コストを取得
            daily_costs = self._get_daily_costs()
            
            # インスタンスタイプ別コストを取得
            instance_costs = self._get_instance_costs()
            
            return {
                'total_cost': total_cost,
                'previous_period_comparison': comparison,
                'service_costs': service_costs,
                'region_costs': region_costs,
                'daily_costs': daily_costs,
                'instance_costs': instance_costs
            }
            
        except Exception as e:
            logger.error(f"Error collecting cost data: {e}", exc_info=True)
            return {
                'total_cost': {'amount': 0, 'currency': 'USD'},
                'previous_period_comparison': {
                    'change_amount': 0,
                    'change_percent': 0,
                    'previous_period': {'start': '', 'end': ''}
                },
                'service_costs': [],
                'region_costs': [],
                'daily_costs': [],
                'instance_costs': {'ec2': [], 'rds': []}
            }
    
    def _get_total_cost(self):
        """
        期間の総コストを取得
        
        Returns:
            dict: 総コスト情報
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': self.start_date,
                    'End': self.end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            
            total_amount = 0
            currency = 'USD'
            
            for result in response['ResultsByTime']:
                amount = float(result['Total']['UnblendedCost']['Amount'])
                currency = result['Total']['UnblendedCost']['Unit']
                total_amount += amount
            
            return {
                'amount': total_amount,
                'currency': currency
            }
            
        except Exception as e:
            logger.error(f"Error getting total cost: {e}")
            return {'amount': 0, 'currency': 'USD'}
    
    def _get_previous_period_comparison(self):
        """
        前期間との比較データを取得
        
        Returns:
            dict: 前期間比較情報
        """
        try:
            # 現在の期間の日数を計算
            start_date = datetime.datetime.strptime(self.start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(self.end_date, '%Y-%m-%d')
            current_period_days = (end_date - start_date).days
            
            # 前期間の日付を計算
            prev_end_date = start_date - datetime.timedelta(days=1)
            prev_start_date = prev_end_date - datetime.timedelta(days=current_period_days)
            
            # 前期間のコストを取得
            prev_response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': prev_start_date.strftime('%Y-%m-%d'),
                    'End': prev_end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            
            prev_total_amount = 0
            for result in prev_response['ResultsByTime']:
                prev_total_amount += float(result['Total']['UnblendedCost']['Amount'])
            
            # 現在期間のコストを取得
            current_total = self._get_total_cost()['amount']
            
            # 変化量と変化率を計算
            change_amount = current_total - prev_total_amount
            change_percent = (change_amount / prev_total_amount * 100) if prev_total_amount > 0 else 0
            
            return {
                'change_amount': change_amount,
                'change_percent': change_percent,
                'previous_period': {
                    'start': prev_start_date.strftime('%Y-%m-%d'),
                    'end': prev_end_date.strftime('%Y-%m-%d')
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting previous period comparison: {e}")
            return {
                'change_amount': 0,
                'change_percent': 0,
                'previous_period': {'start': '', 'end': ''}
            }
    
    def _get_service_costs(self):
        """
        サービス別のコスト内訳を取得
        
        Returns:
            list: サービス別コスト情報のリスト
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': self.start_date,
                    'End': self.end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            service_costs = []
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    service_name = group['Keys'][0]
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    # すでにリスト内にあるサービスは金額を加算
                    service_entry = next((s for s in service_costs if s['service_name'] == service_name), None)
                    if service_entry:
                        service_entry['amount'] += amount
                    else:
                        service_costs.append({
                            'service_name': service_name,
                            'amount': amount
                        })
            
            # コストの降順でソート
            service_costs.sort(key=lambda x: x['amount'], reverse=True)
            
            return service_costs
            
        except Exception as e:
            logger.error(f"Error getting service costs: {e}")
            return []
    
    def _get_region_costs(self):
        """
        リージョン別のコスト内訳を取得
        
        Returns:
            list: リージョン別コスト情報のリスト
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': self.start_date,
                    'End': self.end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'REGION'
                    }
                ]
            )
            
            region_costs = []
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    region_name = group['Keys'][0]
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    # すでにリスト内にあるリージョンは金額を加算
                    region_entry = next((r for r in region_costs if r['region_name'] == region_name), None)
                    if region_entry:
                        region_entry['amount'] += amount
                    else:
                        region_costs.append({
                            'region_name': region_name,
                            'amount': amount
                        })
            
            # コストの降順でソート
            region_costs.sort(key=lambda x: x['amount'], reverse=True)
            
            return region_costs
            
        except Exception as e:
            logger.error(f"Error getting region costs: {e}")
            return []
    
    def _get_daily_costs(self):
        """
        日次のコスト内訳を取得
        
        Returns:
            list: 日次コスト情報のリスト
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': self.start_date,
                    'End': self.end_date
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            
            daily_costs = []
            
            for result in response['ResultsByTime']:
                date = result['TimePeriod']['Start']
                amount = float(result['Total']['UnblendedCost']['Amount'])
                currency = result['Total']['UnblendedCost']['Unit']
                
                daily_costs.append({
                    'date': date,
                    'amount': amount,
                    'currency': currency
                })
            
            return daily_costs
            
        except Exception as e:
            logger.error(f"Error getting daily costs: {e}")
            return []
    
    def _get_instance_costs(self):
        """
        インスタンスタイプ別のコスト内訳を取得
        
        Returns:
            dict: インスタンスタイプ別コスト情報の辞書
        """
        result = {
            'ec2': self._get_ec2_instance_costs(),
            'rds': self._get_rds_instance_costs(),
        }
        
        return result
    
    def _get_ec2_instance_costs(self):
        """
        EC2インスタンスタイプ別のコスト内訳を取得
        
        Returns:
            list: EC2インスタンスタイプ別コスト情報のリスト
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': self.start_date,
                    'End': self.end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Elastic Compute Cloud - Compute']
                    }
                },
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'INSTANCE_TYPE'
                    }
                ]
            )
            
            instance_costs = []
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    instance_type = group['Keys'][0]
                    if instance_type == 'No instance type':
                        continue
                    
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    # すでにリスト内にあるインスタンスタイプは金額を加算
                    instance_entry = next((i for i in instance_costs if i['instance_type'] == instance_type), None)
                    if instance_entry:
                        instance_entry['amount'] += amount
                    else:
                        instance_costs.append({
                            'instance_type': instance_type,
                            'amount': amount
                        })
            
            # コストの降順でソート
            instance_costs.sort(key=lambda x: x['amount'], reverse=True)
            
            return instance_costs
            
        except Exception as e:
            logger.error(f"Error getting EC2 instance costs: {e}")
            return []
    
    def _get_rds_instance_costs(self):
        """
        RDSインスタンスタイプ別のコスト内訳を取得
        
        Returns:
            list: RDSインスタンスタイプ別コスト情報のリスト
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': self.start_date,
                    'End': self.end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Relational Database Service']
                    }
                },
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'INSTANCE_TYPE'
                    }
                ]
            )
            
            instance_costs = []
            
            for result in response['ResultsByTime']:
                for group in result['Groups']:
                    instance_type = group['Keys'][0]
                    if instance_type == 'No instance type':
                        continue
                    
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    # すでにリスト内にあるインスタンスタイプは金額を加算
                    instance_entry = next((i for i in instance_costs if i['instance_type'] == instance_type), None)
                    if instance_entry:
                        instance_entry['amount'] += amount
                    else:
                        instance_costs.append({
                            'instance_type': instance_type,
                            'amount': amount
                        })
            
            # コストの降順でソート
            instance_costs.sort(key=lambda x: x['amount'], reverse=True)
            
            return instance_costs
            
        except Exception as e:
            logger.error(f"Error getting RDS instance costs: {e}")
            return []
