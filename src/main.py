#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWS リソース棚卸しメインスクリプト
"""

import os
import logging
import argparse
from datetime import datetime
import sys
from pathlib import Path

# プロジェクトルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.collector import AWSResourceCollector
from src.exporters import CSVExporter, JSONExporter
from src.processor.data_processor import DataProcessor
from src.report.report_generator import ReportGenerator

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """メイン実行関数"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='AWS リソース棚卸しツール')
    parser.add_argument('--profile', help='使用するAWS CLIプロファイル名')
    parser.add_argument('--region', help='対象リージョン (デフォルト: デフォルトプロファイルのリージョン)')
    parser.add_argument('--format', choices=['csv', 'json', 'both'], default='both',
                       help='出力形式 (csv, json, both、デフォルト: both)')
    parser.add_argument('--report', choices=['summary', 'trend', 'cost', 'all', 'none'], default='all',
                       help='生成するレポートの種類 (summary, trend, cost, all, none、デフォルト: all)')
    parser.add_argument('--report-format', choices=['markdown', 'html', 'both'], default='both',
                       help='レポート形式 (markdown, html, both、デフォルト: both)')
    parser.add_argument('--no-collect', action='store_true', 
                       help='リソース収集をスキップしてレポート生成のみを行う')
    parser.add_argument('--compare', action='store_true',
                       help='直近の2回分のデータを比較して変更レポートを生成する')
    args = parser.parse_args()
    
    # タイムスタンプ（ファイル名用）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 出力ディレクトリのベースパス
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, 'output')
    
    # レポートファイルのリスト
    report_files = []
    
    # データプロセッサの初期化
    processor = DataProcessor(base_dir=base_dir)
    
    # レポートジェネレータの初期化
    report_generator = ReportGenerator(base_dir=base_dir)
    
    # レポート形式の決定
    formats = []
    if args.report_format == 'both':
        formats = ['markdown', 'html']
    else:
        formats = [args.report_format]
    
    # リソース収集とデータ処理
    if not args.no_collect:
        # リソースコレクターの初期化
        collector = AWSResourceCollector(profile_name=args.profile, region_name=args.region)
        
        # リソース情報を収集
        resources = collector.collect_all_resources()
        
        # 結果の出力
        if args.format in ['csv', 'both']:
            exporter = CSVExporter(output_dir=output_dir, timestamp=timestamp)
            csv_files = exporter.export(resources)
            logger.info(f"CSVファイルを出力しました: {', '.join(csv_files)}")
        
        if args.format in ['json', 'both']:
            exporter = JSONExporter(output_dir=output_dir, timestamp=timestamp)
            json_file = exporter.export(resources)
            logger.info(f"JSONファイルを出力しました: {json_file}")
        
        # 生データの保存
        date_dir = processor.save_raw_data(resources)
        logger.info(f"生データを {date_dir} に保存しました")
        
        # サマリー情報の生成
        summary_file = processor.generate_summary()
        logger.info(f"サマリー情報を {summary_file} に生成しました")
        
        # トレンドデータの生成
        trend_files = processor.generate_trend_data()
        logger.info(f"トレンドデータを生成しました: {trend_files}")
        
        # 変更レポートの生成（直近2回分）
        if args.compare:
            latest_date = processor.get_latest_raw_data_date()
            previous_date = processor.get_previous_raw_data_date(latest_date)
            if previous_date:
                change_report_file = processor.generate_change_report(previous_date, latest_date)
                logger.info(f"変更レポートファイルを {change_report_file} に生成しました")
                
                # 変更レポートの生成
                for fmt in formats:
                    changes_report = report_generator.generate_changes_report(change_report_file, output_format=fmt)
                    report_files.append(changes_report)
                    logger.info(f"変更レポートを {changes_report} に生成しました")
            else:
                logger.warning("比較対象の前回データが見つかりません。変更レポートは生成されませんでした。")
    else:
        logger.info("リソース収集をスキップしました")
    
    # レポート生成
    if args.report != 'none':
        # サマリーレポート
        if args.report in ['summary', 'all']:
            for fmt in formats:
                summary_report = report_generator.generate_summary_report(output_format=fmt)
                report_files.append(summary_report)
                logger.info(f"サマリーレポートを {summary_report} に生成しました")
        
        # トレンドレポート
        if args.report in ['trend', 'all']:
            for fmt in formats:
                trend_report = report_generator.generate_trend_report(output_format=fmt)
                if trend_report:  # 空文字列でなければリストに追加
                    report_files.append(trend_report)
                    logger.info(f"トレンドレポートを {trend_report} に生成しました")
        
        # コストレポート
        if args.report in ['cost', 'all']:
            for fmt in formats:
                cost_report = report_generator.generate_cost_report(output_format=fmt)
                report_files.append(cost_report)
                logger.info(f"コストレポートを {cost_report} に生成しました")
        
        logger.info(f"合計 {len(report_files)} 個のレポートを生成しました")
    
    logger.info("処理が完了しました")

if __name__ == "__main__":
    main()
