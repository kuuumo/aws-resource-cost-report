#!/usr/bin/env python3

import logging
import re

import boto3

from ..formatters.output_formatter import OutputFormatter

logger = logging.getLogger(__name__)


class ResourceIdExtractor:
    """AWS APIからのレスポンスからリソースIDを抽出するユーティリティクラス"""

    # 一般的なリソースIDパターン
    RESOURCE_ID_PATTERNS = [
        r"i-[0-9a-f]{8,17}",  # EC2インスタンス
        r"vol-[0-9a-f]{8,17}",  # EBSボリューム
        r"snap-[0-9a-f]{8,17}",  # EBSスナップショット
        r"sg-[0-9a-f]{8,17}",  # セキュリティグループ
        r"subnet-[0-9a-f]{8,17}",  # サブネット
        r"eni-[0-9a-f]{8,17}",  # ネットワークインターフェース
        r"vpc-[0-9a-f]{8,17}",  # VPC
        r"eipalloc-[0-9a-f]{8,17}",  # Elastic IP
        r"rtb-[0-9a-f]{8,17}",  # ルートテーブル
        r"acl-[0-9a-f]{8,17}",  # ネットワークACL
        r"nat-[0-9a-f]{8,17}",  # NAT Gateway
        r"dopt-[0-9a-f]{8,17}",  # DHCP Options Set
        r"vpn-[0-9a-f]{8,17}",  # VPN接続
        r"vgw-[0-9a-f]{8,17}",  # Virtual Private Gateway
        r"igw-[0-9a-f]{8,17}",  # Internet Gateway
        r"pcx-[0-9a-f]{8,17}",  # VPCピアリング接続
        r"lb-[0-9a-z]{8,17}",  # ロードバランサー
        r"arn:aws:[a-z0-9\-]+:[a-z0-9\-]+:[0-9]+:.+",  # ARN
        r"[a-z]+-[a-z0-9]+-[a-z0-9]{8,10}",  # 各種ID
        r"db-[A-Z0-9]{8,20}",  # RDSインスタンス
        r"cluster-[A-Z0-9]{8,20}",  # RDSクラスター
        r"fs-[0-9a-f]{8,17}",  # EFSファイルシステム
        r"cache-[0-9a-f]{8,17}",  # ElastiCacheクラスター
        r"table/[a-zA-Z0-9_.-]{3,255}",  # DynamoDBテーブル
        r"distribution/[A-Z0-9]{13,14}",  # CloudFront配信
        r"[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}",  # UUIDスタイル
        r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,62}",  # 一般的な名前（バケット名など）
    ]

    @classmethod
    def extract_from_usage_type(cls, usage_type):
        """使用タイプ文字列からリソースIDを抽出"""
        for pattern in cls.RESOURCE_ID_PATTERNS:
            match = re.search(pattern, usage_type)
            if match:
                return match.group(0)
        return None

    @classmethod
    def match_resource_id(cls, usage_type, known_resources):
        """使用タイプからリソースIDを取得し、既知のリソースと照合"""
        resource_id = cls.extract_from_usage_type(usage_type)

        if resource_id:
            # 完全一致
            if resource_id in known_resources:
                return resource_id, known_resources[resource_id]

            # 部分一致（プレフィックスマッチング）
            for known_id in known_resources:
                if known_id in resource_id or resource_id in known_id:
                    return known_id, known_resources[known_id]

        return None, ""


class AWSRegionManager:
    """AWS リージョン管理クラス"""

    @staticmethod
    def get_all_regions():
        """すべてのAWSリージョンを取得"""
        try:
            ec2 = boto3.client("ec2")
            regions = [
                region["RegionName"] for region in ec2.describe_regions()["Regions"]
            ]
            return regions
        except Exception as e:
            logger.warning(f"Failed to get AWS regions: {e}")
            # フォールバック: 主要リージョン
            return [
                "us-east-1",
                "us-east-2",
                "us-west-1",
                "us-west-2",
                "eu-west-1",
                "eu-central-1",
                "ap-northeast-1",
                "ap-southeast-1",
            ]


class AWSCostReport:
    """AWSコストレポート生成のコアクラス"""

    def __init__(
        self,
        start_date,
        end_date,
        output_format="console",
        output_file=None,
        use_all_regions=False,
    ):
        """
        AWS コストレポートの初期化

        Args:
            start_date (str): 開始日 YYYY-MM-DD形式
            end_date (str): 終了日 YYYY-MM-DD形式
            output_format (str): 出力形式 ('console', 'csv', 'html')
            output_file (str): 出力ファイル名（formatがconsole以外の場合に使用）
            use_all_regions (bool): すべてのリージョンを検索するかどうか
        """
        self.start_date = start_date
        self.end_date = end_date
        self.output_format = output_format
        self.output_file = output_file
        self.use_all_regions = use_all_regions
        self.ce_client = boto3.client("ce")

        # フォーマッタの初期化
        self.formatter = OutputFormatter(output_format, output_file)

        # リージョンの設定
        if use_all_regions:
            self.regions = AWSRegionManager.get_all_regions()
        else:
            # 現在のリージョンのみ使用
            session = boto3.session.Session()
            self.regions = [session.region_name]
