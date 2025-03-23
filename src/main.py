#!/usr/bin/env python3

import os
import sys
import argparse
import logging
import datetime
import yaml
from pathlib import Path

from collectors.cost_explorer import CostExplorerCollector
from collectors.uncovered_resources_detector import UncoveredResourcesDetector
from report_generator import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_last_month_first_day():
    """先月の初日を取得"""
    today = datetime.date.today()
    # 今月の1日
    first_day_of_this_month = today.replace(day=1)
    # 今月の1日から1日引くと先月の末日
    last_day_of_last_month = first_day_of_this_month - datetime.timedelta(days=1)
    # 先月の末日の年月を使って先月の初日を計算
    first_day_of_last_month = last_day_of_last_month.replace(day=1)
    return first_day_of_last_month.strftime('%Y-%m-%d')

def get_last_month_last_day():
    """先月の末日を取得"""
    today = datetime.date.today()
    # 今月の1日
    first_day_of_this_month = today.replace(day=1)
    # 今月の1日から1日引くと先月の末日
    last_day_of_last_month = first_day_of_this_month - datetime.timedelta(days=1)
    return last_day_of_last_month.strftime('%Y-%m-%d')

def parse_args():
    parser = argparse.ArgumentParser(description='AWS Resource Cost Report Generator')
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date for cost analysis (YYYY-MM-DD)',
        default=get_last_month_first_day()
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for cost analysis (YYYY-MM-DD)',
        default=get_last_month_last_day()
    )
    parser.add_argument(
        '--regions',
        type=str,
        help='Comma-separated list of AWS regions to analyze',
        default='all'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Directory to save the generated report',
        default='reports'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file',
        default='config.yml'
    )
    parser.add_argument(
        '--detect-uncovered',
        action='store_true',
        help='自動的にすべての課金リソースを検出・収集する',
        default=True
    )
    return parser.parse_args()

def load_config(config_path):
    """設定ファイルを読み込む"""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.warning(f"Failed to load config file: {e}. Using default settings.")
        return {
            'regions': {'include': 'all', 'exclude': ''},
            'cost_analysis': {'ec2_instance_types': True, 'rds_instance_types': True},
            'resource_analysis': {'ec2_instances': True, 'rds_instances': True, 's3_buckets': True},
            'optimization': {'stopped_ec2_instances': True},
            'report': {'format': 'markdown', 'sections': {'summary': True}}
        }

def get_regions_from_config(config, cli_regions):
    """CLI引数と設定ファイルからリージョンリストを取得"""
    if cli_regions != 'all':
        regions = cli_regions.split(',')
    else:
        regions = config.get('regions', {}).get('include', 'all')
        if regions != 'all' and isinstance(regions, str):
            regions = regions.split(',')
    
    # 除外リージョンを処理
    exclude_regions = config.get('regions', {}).get('exclude', '')
    if regions != 'all' and exclude_regions:
        exclude_list = exclude_regions.split(',') if isinstance(exclude_regions, str) else exclude_regions
        regions = [r for r in regions if r not in exclude_list]
    
    return regions

def main():
    args = parse_args()
    
    # 設定ファイルを読み込む
    config = load_config(args.config)
    
    # リージョンを設定
    regions = get_regions_from_config(config, args.regions)
    
    # 出力ディレクトリを作成
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # レポートのファイル名に使用するタイムスタンプを生成
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"aws_resource_cost_report_{timestamp}.md"
    report_path = output_dir / report_filename
    
    try:
        # コストデータを収集
        logger.info(f"Collecting cost data from {args.start_date} to {args.end_date}")
        cost_collector = CostExplorerCollector(args.start_date, args.end_date)
        cost_data = cost_collector.collect()

        # リソースデータ用の空の辞書を初期化
        resource_data = {}

        # AWS課金リソースを検出・収集
        if args.detect_uncovered:
            logger.info("Detecting and collecting billed AWS resources automatically")
            detector = UncoveredResourcesDetector(args.start_date, args.end_date, resource_data)
            uncovered_resources_data = detector.detect()
            logger.info(f"Found {len(uncovered_resources_data.get('billed_services', []))} billed services")
            
            # 収集されたリソースデータをマージ
            collected_resources = uncovered_resources_data.get('collected_resources', {})
            for resource_type, resources in collected_resources.items():
                resource_data[resource_type] = resources
                count = len(resources) if isinstance(resources, list) else 'multiple'
                logger.info(f"Added {count} {resource_type} resources")
            
            # 未カバーリソースのデータを追加
            resource_data['uncovered_resources'] = uncovered_resources_data.get('uncovered_resources', [])
            logger.info(f"Found {len(resource_data['uncovered_resources'])} uncovered resources")
        
        # レポートを生成
        logger.info(f"Generating report to {report_path}")
        report_generator = ReportGenerator(cost_data, resource_data, args.start_date, args.end_date, config)
        report_generator.generate(report_path)
        
        # インデックスファイルを作成または更新
        index_path = output_dir / "index.md"
        if not index_path.exists():
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write("# AWS リソース・コスト レポート一覧\n\n")
                f.write("このページには生成されたAWSリソース・コストレポートの一覧が表示されます。\n\n")
                f.write("| 日付 | レポート |\n")
                f.write("| ---- | ------ |\n")
        
        # 新しいレポートをインデックスに追加
        with open(index_path, 'a', encoding='utf-8') as f:
            report_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"| {report_date} | [{report_filename}](./{report_filename}) |\n")
        
        logger.info(f"Report generated successfully: {report_path}")
        return 0
    
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())