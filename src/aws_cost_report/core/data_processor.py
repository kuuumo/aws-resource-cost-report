#!/usr/bin/env python3

import logging

import pandas as pd

from ..core.aws_cost_report import ResourceIdExtractor

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    コストデータとリソースタグの処理を行うクラス
    """

    def __init__(self, cost_response, resource_tags):
        """
        初期化

        Args:
            cost_response (dict): Cost Explorerのレスポンス
            resource_tags (dict): リソースIDをキー、タグ値を値とする辞書
        """
        self.cost_response = cost_response
        self.resource_tags = resource_tags

    def process_cost_data(self):
        """
        コストデータを処理してDataFrameに変換

        Returns:
            DataFrame: 処理したコストデータ
        """
        data = []

        for result in self.cost_response["ResultsByTime"]:
            for group in result["Groups"]:
                service = group["Keys"][0]
                usage_type = group["Keys"][1]

                # リソースIDとタグを取得
                resource_id, name_tag = ResourceIdExtractor.match_resource_id(
                    usage_type, self.resource_tags
                )

                cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                currency = group["Metrics"]["UnblendedCost"]["Unit"]

                data.append(
                    {
                        "Service": service,
                        "Usage Type": usage_type,
                        "Resource ID": resource_id if resource_id else "",
                        "Name Tag": name_tag,
                        "Cost": cost,
                        "Currency": currency,
                        "Time Period": f"{result['TimePeriod']['Start']} to {result['TimePeriod']['End']}",
                    }
                )

        return pd.DataFrame(data)

    def generate_service_summary(self, df):
        """
        サービス別の集計データを生成

        Args:
            df (DataFrame): コストデータのDataFrame

        Returns:
            DataFrame: サービス別集計データ
        """
        service_summary = (
            df.groupby("Service")["Cost"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        return service_summary

    def generate_resource_summary(self, df):
        """
        リソース別の集計データを生成

        Args:
            df (DataFrame): コストデータのDataFrame

        Returns:
            DataFrame: リソース別集計データ
        """
        resource_summary = (
            df.groupby(["Service", "Usage Type", "Resource ID", "Name Tag"])["Cost"]
            .sum()
            .reset_index()
            .sort_values("Cost", ascending=False)
        )
        return resource_summary
