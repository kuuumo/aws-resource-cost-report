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
    args = parser.parse_args()
    
    # タイムスタンプ（ファイル名用）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 出力ディレクトリ
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
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
    
    logger.info("処理が完了しました")

if __name__ == "__main__":
    main()
