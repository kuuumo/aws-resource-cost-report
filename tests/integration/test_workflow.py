#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWSリソースコスト報告ツールの統合テスト
"""

import os
import unittest
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

# プロジェクトルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.processor.data_processor import DataProcessor
from src.report.report_generator import ReportGenerator

class TestWorkflow(unittest.TestCase):
    """AWSリソースコスト報告ツールの統合テスト"""

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
        
        # テストデータのコピー
        self._copy_test_data()

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.base_dir)

    def _copy_test_data(self):
        """テストデータをテスト環境にコピー"""
        # 設定ファイルのコピー
        src_config = os.path.join(self.test_dir, 'config')
        dst_config = os.path.join(self.base_dir, 'output', 'config')
        
        for filename in os.listdir(src_config):
            src_file = os.path.join(src_config, filename)
            dst_file = os.path.join(dst_config, filename)
            shutil.copy2(src_file, dst_file)

    def test_end_to_end_workflow(self):
        """エンドツーエンドのワークフローテスト"""
        # 1. テスト用のリソースデータを作成
        resources = {
            "EC2_Instances": [
                {
                    "ResourceId": "i-001122334455aabb",
                    "ResourceName": "WebServer01",
                    "ResourceType": "EC2_Instances",
                    "AZ": "ap-northeast-1a",
                    "VpcId": "vpc-11223344",
                    "Tags": [
                        {"Key": "Name", "Value": "WebServer01"},
                        {"Key": "Environment", "Value": "Production"},
                        {"Key": "Project", "Value": "MainApp"}
                    ],
                    "InstanceType": "t3.large",
                    "State": "running"
                },
                {
                    "ResourceId": "i-aabbccddee112233",
                    "ResourceName": "DBServer01",
                    "ResourceType": "EC2_Instances",
                    "AZ": "ap-northeast-1b",
                    "VpcId": "vpc-11223344",
                    "Tags": [
                        {"Key": "Name", "Value": "DBServer01"},
                        {"Key": "Environment", "Value": "Production"},
                        {"Key": "Project", "Value": "MainApp"}
                    ],
                    "InstanceType": "t3.xlarge",
                    "State": "running"
                }
            ],
            "S3_Buckets": [
                {
                    "ResourceId": "example-assets-bucket",
                    "ResourceName": "example-assets-bucket",
                    "ResourceType": "S3_Buckets",
                    "AZ": "ap-northeast-1",
                    "Tags": [
                        {"Key": "Name", "Value": "AssetsBucket"},
                        {"Key": "Environment", "Value": "Production"},
                        {"Key": "Department", "Value": "Marketing"}
                    ],
                    "CreationDate": "2024-01-15T09:00:00Z"
                }
            ]
        }
        
        # モックの日付を設定
        with patch('src.processor.data_processor.datetime') as mock_datetime:
            mock_datetime.now.return_value = MagicMock(
                isoformat=lambda: '2025-03-15T12:00:00+09:00',
                strftime=lambda fmt: '2025-03-15' if fmt == '%Y-%m-%d' else mock_datetime.now().isoformat()
            )
            mock_datetime.side_effect = lambda *args, **kw: __import__('datetime').datetime(*args, **kw)
            
            # 2. DataProcessorインスタンスを作成
            processor = DataProcessor(base_dir=self.base_dir)
            
            # 3. 生データを保存
            date_dir = processor.save_raw_data(resources)
            self.assertTrue(os.path.exists(date_dir))
            self.assertEqual(os.path.basename(date_dir), '2025-03-15')
            
            # 4. サマリー情報を生成
            summary_file = processor.generate_summary()
            self.assertTrue(os.path.exists(summary_file))
            
            # サマリー内容の確認
            with open(summary_file, 'r') as f:
                summary_data = json.load(f)
                self.assertEqual(summary_data['metadata']['source_date'], '2025-03-15')
                self.assertEqual(summary_data['metadata']['total_resources'], 3)
            
            # 5. トレンドデータを生成
            trend_files = processor.generate_trend_data()
            self.assertTrue('resource_count' in trend_files)
            self.assertTrue(os.path.exists(trend_files['resource_count']))
            
            # 5日後のデータを作成（変更を含む）
            changed_resources = {
                "EC2_Instances": [
                    {
                        "ResourceId": "i-001122334455aabb",
                        "ResourceName": "WebServer01",
                        "ResourceType": "EC2_Instances",
                        "AZ": "ap-northeast-1a",
                        "VpcId": "vpc-11223344",
                        "Tags": [
                            {"Key": "Name", "Value": "WebServer01"},
                            {"Key": "Environment", "Value": "Production"},
                            {"Key": "Project", "Value": "MainApp"},
                            {"Key": "UpdatedTag", "Value": "NewValue"}
                        ],
                        "InstanceType": "t3.large",
                        "State": "running"
                    },
                    {
                        "ResourceId": "i-aabbccddee112233",
                        "ResourceName": "DBServer01",
                        "ResourceType": "EC2_Instances",
                        "AZ": "ap-northeast-1b",
                        "VpcId": "vpc-11223344",
                        "Tags": [
                            {"Key": "Name", "Value": "DBServer01"},
                            {"Key": "Environment", "Value": "Production"},
                            {"Key": "Project", "Value": "MainApp"}
                        ],
                        "InstanceType": "t3.2xlarge",  # インスタンスタイプ変更
                        "State": "running"
                    },
                    {
                        "ResourceId": "i-112233445566ccdd",  # 新規追加
                        "ResourceName": "AppServer01",
                        "ResourceType": "EC2_Instances",
                        "AZ": "ap-northeast-1c",
                        "VpcId": "vpc-11223344",
                        "Tags": [
                            {"Key": "Name", "Value": "AppServer01"},
                            {"Key": "Environment", "Value": "Production"},
                            {"Key": "Project", "Value": "SecondaryApp"}
                        ],
                        "InstanceType": "t3.medium",
                        "State": "running"
                    }
                ],
                "S3_Buckets": [
                    {
                        "ResourceId": "example-assets-bucket",
                        "ResourceName": "example-assets-bucket",
                        "ResourceType": "S3_Buckets",
                        "AZ": "ap-northeast-1",
                        "Tags": [
                            {"Key": "Name", "Value": "AssetsBucket"},
                            {"Key": "Environment", "Value": "Production"},
                            {"Key": "Department", "Value": "Marketing"},
                            {"Key": "CostCenter", "Value": "MK123"}  # タグ追加
                        ],
                        "CreationDate": "2024-01-15T09:00:00Z"
                    }
                ]
            }
            
            # 5日後のデータを保存
            with patch('src.processor.data_processor.datetime') as mock_datetime2:
                mock_datetime2.now.return_value = MagicMock(
                    isoformat=lambda: '2025-03-20T12:00:00+09:00',
                    strftime=lambda fmt: '2025-03-20' if fmt == '%Y-%m-%d' else mock_datetime2.now().isoformat()
                )
                mock_datetime2.side_effect = lambda *args, **kw: __import__('datetime').datetime(*args, **kw)
                
                date_dir2 = processor.save_raw_data(changed_resources)
                self.assertTrue(os.path.exists(date_dir2))
                self.assertEqual(os.path.basename(date_dir2), '2025-03-20')
                
                # サマリー情報を更新
                summary_file2 = processor.generate_summary()
                self.assertTrue(os.path.exists(summary_file2))
                
                # トレンドデータを更新
                trend_files2 = processor.generate_trend_data()
                self.assertTrue('resource_count' in trend_files2)
                self.assertTrue(os.path.exists(trend_files2['resource_count']))
                
                # 変更レポートを生成
                change_report_file = processor.generate_change_report('2025-03-15', '2025-03-20')
                self.assertTrue(os.path.exists(change_report_file))
                
                # 変更レポートの内容確認
                with open(change_report_file, 'r') as f:
                    change_data = json.load(f)
                    self.assertEqual(change_data['metadata']['start_date'], '2025-03-15')
                    self.assertEqual(change_data['metadata']['end_date'], '2025-03-20')
                    self.assertEqual(change_data['summary']['resources_added'], 1)  # 追加されたEC2
                    self.assertEqual(change_data['summary']['resources_removed'], 0)
                    self.assertEqual(change_data['summary']['resources_modified'], 2)  # 変更されたEC2とS3
        
        # 6. ReportGeneratorインスタンスを作成
        report_generator = ReportGenerator(base_dir=self.base_dir)
        
        # 7. 各種レポートを生成
        with patch('src.report.report_generator.datetime') as mock_datetime3:
            mock_datetime3.now.return_value = MagicMock(
                isoformat=lambda: '2025-03-20T12:00:00+09:00',
                strftime=lambda fmt: '2025-03-20'
            )
            
            # サマリーレポート
            summary_report = report_generator.generate_summary_report(output_format="markdown")
            self.assertTrue(os.path.exists(summary_report))
            
            # トレンドレポート
            trend_report = report_generator.generate_trend_report(output_format="markdown")
            self.assertTrue(os.path.exists(trend_report))
            
            # 変更レポート
            changes_report = report_generator.generate_changes_report(change_report_file, output_format="markdown")
            self.assertTrue(os.path.exists(changes_report))
            
            # コストレポート
            cost_report = report_generator.generate_cost_report(output_format="markdown")
            self.assertTrue(os.path.exists(cost_report))

if __name__ == '__main__':
    unittest.main()
