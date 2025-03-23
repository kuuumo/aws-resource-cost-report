#!/usr/bin/env python3

import argparse
import logging
from datetime import datetime, timedelta

from .collectors import CostExplorerCollector, TagCollector
from .core import AWSCostReport, DataProcessor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(description="AWS Cost Report Generator")

    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of past days to analyze (default: 30)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="aws_cost_report.csv",
        help="Output file name (default: aws_cost_report.csv)",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["csv", "html", "console"],
        default="console",
        help="Output format (csv, html, or console)",
    )

    parser.add_argument(
        "--all-regions",
        action="store_true",
        help="Collect resources from all regions (slower but more comprehensive)",
    )

    return parser.parse_args()


def get_date_range(days):
    """日付範囲を計算"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    return start_date.isoformat(), end_date.isoformat()


def main():
    """メイン関数"""
    args = parse_args()

    # 日付範囲を計算
    start_date, end_date = get_date_range(args.days)
    logger.info(f"Analyzing costs from {start_date} to {end_date}")

    try:
        # コストデータを収集
        logger.info("Collecting cost data from AWS Cost Explorer...")
        cost_collector = CostExplorerCollector(start_date, end_date)
        cost_response = cost_collector.get_cost_and_usage()

        # サービス名を取得
        service_names = cost_collector.get_service_names(cost_response)
        logger.info(f"Found {len(service_names)} services with costs")

        # タグ情報を収集
        logger.info("Collecting resource tags...")
        tag_collector = TagCollector()
        resource_tags = tag_collector.collect_all_resource_tags(
            service_names, args.all_regions
        )
        logger.info(f"Collected tags for {len(resource_tags)} resources")

        # コストデータを処理
        logger.info("Processing cost data...")
        processor = DataProcessor(cost_response, resource_tags)
        cost_df = processor.process_cost_data()

        # サービスとリソースの集計
        service_summary = processor.generate_service_summary(cost_df)
        resource_summary = processor.generate_resource_summary(cost_df)

        # レポート生成
        logger.info(f"Generating {args.format} report...")
        cost_report = AWSCostReport(
            start_date,
            end_date,
            output_format=args.format,
            output_file=args.output,
            use_all_regions=args.all_regions,
        )

        # 通貨単位を取得（すべて同じ通貨と仮定）
        currency = cost_df["Currency"].iloc[0] if not cost_df.empty else "USD"

        # データに応じた出力
        if args.format == "console":
            # コンソールに直接出力
            cost_report.formatter.format_service_summary(service_summary, currency)
            cost_report.formatter.format_resource_summary(resource_summary, currency)
        elif args.format == "html":
            # HTML形式でレポートを生成
            service_html = cost_report.formatter.format_service_summary(
                service_summary, currency
            )
            resource_html = cost_report.formatter.format_resource_summary(
                resource_summary, currency
            )
            html_content = cost_report.formatter.generate_html_report(
                service_html, resource_html, start_date, end_date
            )
            cost_report.formatter.save_report(html_content)
        elif args.format == "csv":
            # CSV形式で保存
            cost_report.formatter.format_service_summary(service_summary, currency)
            cost_report.formatter.format_resource_summary(resource_summary, currency)

        logger.info("Report generation completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return 1
