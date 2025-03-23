#!/usr/bin/env python3

import logging

import boto3

logger = logging.getLogger(__name__)


class CostExplorerCollector:
    """AWS Cost Explorer APIを使用してコスト情報を収集するクラス"""

    def __init__(self, start_date, end_date):
        """
        初期化

        Args:
            start_date (str): コスト期間の開始日 (YYYY-MM-DD形式)
            end_date (str): コスト期間の終了日 (YYYY-MM-DD形式)
        """
        self.start_date = start_date
        self.end_date = end_date
        self.client = boto3.client("ce")

    def get_cost_and_usage(self):
        """
        Cost ExplorerからサービスとUSAGE_TYPEでグループ化されたコストデータを取得

        Returns:
            dict: Cost Explorerのレスポンス
        """
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={"Start": self.start_date, "End": self.end_date},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[
                    {"Type": "DIMENSION", "Key": "SERVICE"},
                    {"Type": "DIMENSION", "Key": "USAGE_TYPE"},
                ],
            )
            return response
        except Exception as e:
            logger.error(f"Failed to get cost data: {e}")
            raise RuntimeError(f"Failed to get cost data from AWS Cost Explorer: {e}")

    def get_service_names(self, response):
        """
        レスポンスからサービス名を抽出

        Args:
            response (dict): Cost Explorerレスポンス

        Returns:
            set: サービス名のセット
        """
        service_names = set()
        for result in response["ResultsByTime"]:
            for group in result["Groups"]:
                service_names.add(group["Keys"][0])
        return service_names
