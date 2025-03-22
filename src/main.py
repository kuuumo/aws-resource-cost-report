#!/usr/bin/env python3

import os
import sys
import argparse
import logging
import datetime
import yaml
from pathlib import Path

from collectors.cost_explorer import CostExplorerCollector
from collectors.resource_explorer import ResourceExplorerCollector
from collectors.uncovered_resources_detector import UncoveredResourcesDetector
from report_generator import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='AWS Resource Cost Report Generator')
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date for cost analysis (YYYY-MM-DD)',
        default=(datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for cost analysis (YYYY-MM-DD)',
        default=datetime.datetime.now().strftime('%Y-%m-%d')
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
        help='Detect uncovered resources with significant costs',
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
        
        # リソースデータを収集
        logger.info(f"Collecting resource information for regions: {regions}")
        resource_collector = ResourceExplorerCollector(regions)
        resource_data = resource_collector.collect()
        
        # 未カバーリソースを検出（オプション）
        uncovered_resources_data = {}
        if args.detect_uncovered:
            logger.info("Detecting uncovered resources with significant costs")
            detector = UncoveredResourcesDetector(args.start_date, args.end_date, resource_data)
            uncovered_resources_data = detector.detect()
            logger.info(f"Found {len(uncovered_resources_data.get('uncovered_resources', []))} uncovered resources")
            
            # 未カバーリソースのデータを追加
            resource_data['uncovered_resources'] = uncovered_resources_data
        
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
