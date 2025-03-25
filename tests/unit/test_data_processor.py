#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DataProcessorクラスのユニットテスト
"""

import os
import unittest
import json
import shutil
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

# プロジェクトルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.processor.data_processor import DataProcessor

class TestDataProcessor(unittest.TestCase):
    """DataProcessorクラスのユニットテスト"""

    def setUp(self):
        """テスト前の準備"""
        # テスト用のディレクトリパス
        self.test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data')
        self.base_dir = tempfile.mkdtemp()
        
        # テストディレクトリの準備
        os.makedirs(os.path.join(self.base_dir, 'output', 'raw'), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, 'output', 'processed'), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, 'output', 'processed', 'trends'), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, 'output', 'processed', 'reports'), exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, 'output', 'config'), exist_ok=True)
        
        # テスト用のDataProcessorインスタンス
        self.processor = DataProcessor(base_dir=self.base_dir)
        
        # テストデータのコピー
        self._copy_test_data()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.base_dir)

    def _copy_test_data(self):
        """テストデータをテスト環境にコピー"""
        # 2025-02-01のデータをコピー
        src_dir = os.path.join(self.test_dir, 'raw', '2025-02-01')
        dst_dir = os.path.join(self.base_dir, 'output', 'raw', '2025-02-01')
        os.makedirs(dst_dir, exist_ok=True)
        
        for filename in os.listdir(src_dir):
            src_file = os.path.join(src_dir, filename)
            dst_file = os.path.join(dst_dir, filename)
            shutil.copy2(src_file, dst_file)
        
        # 2025-03-01のデータをコピー
        src_dir = os.path.join(self.test_dir, 'raw', '2025-03-01')
        dst_dir = os.path.join(self.base_dir, 'output', 'raw', '2025-03-01')
        os.makedirs(dst_dir, exist_ok=True)
        
        for filename in os.listdir(src_dir):
            src_file = os.path.join(src_dir, filename)
            dst_file = os.path.join(dst_dir, filename)
            shutil.copy2(src_file, dst_file)
            
        # 設定ファイルのコピー
        src_config = os.path.join(self.test_dir, 'config')
        dst_config = os.path.join(self.base_dir, 'output', 'config')
        
        for filename in os.listdir(src_config):
            src_file = os.path.join(src_config, filename)
            dst_file = os.path.join(dst_config, filename)
            shutil.copy2(src_file, dst_file)

    def test_save_raw_data(self):
        """save_raw_data メソッドのテスト"""
        resources = {
            "EC2_Instances": [
                {
                    "ResourceId": "i-test123",
                    "ResourceName": "TestServer",
                    "ResourceType": "EC2_Instances",
                    "AZ": "ap-northeast-1a",
                    "VpcId": "vpc-test",
                    "Tags": [{"Key": "Name", "Value": "TestServer"}],
                    "InstanceType": "t3.micro",
                    "State": "running"
                }
            ]
        }
        
        # 現在日付で保存
        with patch('src.processor.data_processor.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 3, 15)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            date_dir = self.processor.save_raw_data(resources)
            
            # 正しいディレクトリが作成されたか確認
            self.assertTrue(os.path.exists(date_dir))
            self.assertEqual(os.path.basename(date_dir), '2025-03-15')
            
            # EC2データファイルが作成されたか確認
            ec2_file = os.path.join(date_dir, 'ec2_instances.json')
            self.assertTrue(os.path.exists(ec2_file))
            
            # 統合ファイルが作成されたか確認
            all_resources_file = os.path.join(date_dir, 'all_resources.json')
            self.assertTrue(os.path.exists(all_resources_file))
            
            # 内容の検証
            with open(all_resources_file, 'r') as f:
                data = json.load(f)
                self.assertEqual(data['metadata']['total_resources'], 1)
                self.assertEqual(len(data['resources']['EC2_Instances']), 1)

    def test_generate_summary(self):
        """generate_summary メソッドのテスト"""
        # 日付指定でサマリー生成
        summary_file = self.processor.generate_summary('2025-02-01')
        
        # ファイルが作成されたか確認
        self.assertTrue(os.path.exists(summary_file))
        
        # 内容の検証
        with open(summary_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(data['metadata']['source_date'], '2025-02-01')
            self.assertEqual(data['metadata']['total_resources'], 4)
            self.assertEqual(len(data['resource_summary']), 2)  # EC2とS3

    def test_generate_trend_data(self):
        """generate_trend_data メソッドのテスト"""
        trend_files = self.processor.generate_trend_data()
        
        # ファイルが作成されたか確認
        self.assertTrue('monthly_cost' in trend_files)
        self.assertTrue('resource_count' in trend_files)
        self.assertTrue(os.path.exists(trend_files['monthly_cost']))
        self.assertTrue(os.path.exists(trend_files['resource_count']))
        
        # リソースカウントトレンドの検証
        with open(trend_files['resource_count'], 'r') as f:
            data = json.load(f)
            trend_data = data['resource_count_trend']
            self.assertEqual(len(trend_data), 2)  # 2つの日付データ
            
            # 日付の順序確認
            self.assertEqual(trend_data[0]['date'], '2025-02-01')
            self.assertEqual(trend_data[1]['date'], '2025-03-01')
            
            # 総リソース数の確認
            self.assertEqual(trend_data[0]['total_resources'], 4)
            self.assertEqual(trend_data[1]['total_resources'], 5)

    def test_generate_change_report(self):
        """generate_change_report メソッドのテスト"""
        report_file = self.processor.generate_change_report('2025-02-01', '2025-03-01')
        
        # ファイルが作成されたか確認
        self.assertTrue(os.path.exists(report_file))
        
        # 内容の検証
        with open(report_file, 'r') as f:
            data = json.load(f)
            
            # メタデータの確認
            self.assertEqual(data['metadata']['start_date'], '2025-02-01')
            self.assertEqual(data['metadata']['end_date'], '2025-03-01')
            self.assertEqual(data['metadata']['days_between'], 28)
            
            # サマリーの確認
            summary = data['summary']
            self.assertEqual(summary['resources_added'], 2)  # 新しいEC2とS3
            self.assertEqual(summary['resources_removed'], 1)  # 削除されたS3
            self.assertEqual(summary['resources_modified'], 2)  # 変更されたEC2とS3

if __name__ == '__main__':
    unittest.main()
