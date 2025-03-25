#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ReportGeneratorクラスのユニットテスト
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

from src.report.report_generator import ReportGenerator

class TestReportGenerator(unittest.TestCase):
    """ReportGeneratorクラスのユニットテスト"""

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
        
        # テスト用のReportGeneratorインスタンス
        self.generator = ReportGenerator(base_dir=self.base_dir)
        
        # テストデータのコピー
        self._copy_test_data()
        
        # サンプルのサマリーデータを作成
        self._create_sample_summary()
        
        # サンプルのトレンドデータを作成
        self._create_sample_trends()
        
        # サンプルの変更レポートを作成
        self._create_sample_change_report()

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

    def _create_sample_summary(self):
        """サンプルのサマリーデータを作成"""
        summary_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source_date": "2025-03-01",
                "total_resources": 5
            },
            "resource_summary": {
                "EC2_Instances": {
                    "count": 3,
                    "tags_summary": {
                        "Name": 3,
                        "Environment": 3,
                        "Project": 3,
                        "UpdatedTag": 1
                    },
                    "region_summary": {
                        "ap-northeast-1": 3
                    }
                },
                "S3_Buckets": {
                    "count": 2,
                    "tags_summary": {
                        "Name": 2,
                        "Environment": 2,
                        "Department": 2,
                        "CostCenter": 1
                    },
                    "region_summary": {
                        "ap-northeast-1": 2
                    }
                }
            },
            "vpc_resources": {
                "vpc-11223344": {
                    "EC2_Instances": 3
                }
            }
        }
        
        summary_file = os.path.join(self.base_dir, 'output', 'processed', 'summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

    def _create_sample_trends(self):
        """サンプルのトレンドデータを作成"""
        # 月次コストトレンド
        monthly_cost_data = {
            "monthly_cost_trend": [
                {
                    "date": "2025-02-01",
                    "costs": {
                        "EC2": 100,
                        "S3": 50,
                        "RDS": 75,
                        "Other": 30
                    },
                    "total_cost": 255
                },
                {
                    "date": "2025-03-01",
                    "costs": {
                        "EC2": 120,
                        "S3": 55,
                        "RDS": 75,
                        "Other": 35
                    },
                    "total_cost": 285
                }
            ],
            "updated_at": datetime.now().isoformat()
        }
        
        monthly_cost_file = os.path.join(self.base_dir, 'output', 'processed', 'trends', 'monthly_cost.json')
        with open(monthly_cost_file, 'w', encoding='utf-8') as f:
            json.dump(monthly_cost_data, f, indent=2, ensure_ascii=False)
        
        # リソース数トレンド
        resource_count_data = {
            "resource_count_trend": [
                {
                    "date": "2025-02-01",
                    "resource_counts": {
                        "EC2_Instances": 2,
                        "S3_Buckets": 2
                    },
                    "total_resources": 4
                },
                {
                    "date": "2025-03-01",
                    "resource_counts": {
                        "EC2_Instances": 3,
                        "S3_Buckets": 2
                    },
                    "total_resources": 5
                }
            ],
            "updated_at": datetime.now().isoformat()
        }
        
        resource_count_file = os.path.join(self.base_dir, 'output', 'processed', 'trends', 'resource_count.json')
        with open(resource_count_file, 'w', encoding='utf-8') as f:
            json.dump(resource_count_data, f, indent=2, ensure_ascii=False)

    def _create_sample_change_report(self):
        """サンプルの変更レポートを作成"""
        change_report_data = {
            "metadata": {
                "start_date": "2025-02-01",
                "end_date": "2025-03-01",
                "generated_at": datetime.now().isoformat(),
                "days_between": 28
            },
            "summary": {
                "resources_added": 2,
                "resources_removed": 1,
                "resources_modified": 2,
                "cost_impact": 30.0,
                "resource_type_changes": {
                    "EC2_Instances": {
                        "added": 1,
                        "removed": 0,
                        "modified": 1,
                        "net_change": 1
                    },
                    "S3_Buckets": {
                        "added": 1,
                        "removed": 1,
                        "modified": 1,
                        "net_change": 0
                    }
                },
                "tag_changes": {
                    "added": {
                        "UpdatedTag": 1,
                        "CostCenter": 1
                    },
                    "removed": {},
                    "modified": {}
                },
                "security_changes": {
                    "added": [],
                    "removed": [],
                    "modified": []
                }
            },
            "changes": {
                "added": {
                    "EC2_Instances": [
                        {
                            "ResourceId": "i-112233445566ccdd",
                            "ResourceName": "AppServer01"
                        }
                    ],
                    "S3_Buckets": [
                        {
                            "ResourceId": "example-backups-bucket",
                            "ResourceName": "example-backups-bucket"
                        }
                    ]
                },
                "removed": {
                    "S3_Buckets": [
                        {
                            "ResourceId": "example-logs-bucket",
                            "ResourceName": "example-logs-bucket"
                        }
                    ]
                },
                "modified": {
                    "EC2_Instances": [
                        {
                            "resource_id": "i-aabbccddee112233",
                            "before": {
                                "InstanceType": "t3.xlarge"
                            },
                            "after": {
                                "InstanceType": "t3.2xlarge"
                            },
                            "changes": {
                                "InstanceType": {
                                    "from": "t3.xlarge",
                                    "to": "t3.2xlarge"
                                }
                            }
                        }
                    ],
                    "S3_Buckets": [
                        {
                            "resource_id": "example-assets-bucket",
                            "changes": {
                                "Tags": {
                                    "added": {
                                        "CostCenter": "MK123"
                                    }
                                }
                            }
                        }
                    ]
                }
            },
            "cost_changes": {
                "added_cost": 50.0,
                "removed_cost": 30.0,
                "modified_cost": 10.0,
                "total_impact": 30.0,
                "breakdown_by_type": {
                    "EC2_Instances": {
                        "added": 20.0,
                        "removed": 0.0,
                        "modified": 10.0,
                        "total": 30.0
                    },
                    "S3_Buckets": {
                        "added": 30.0,
                        "removed": -30.0,
                        "modified": 0.0,
                        "total": 0.0
                    }
                }
            }
        }
        
        change_report_file = os.path.join(
            self.base_dir, 'output', 'processed', 'reports', 
            f"changes_2025-02-01_to_2025-03-01.json"
        )
        with open(change_report_file, 'w', encoding='utf-8') as f:
            json.dump(change_report_data, f, indent=2, ensure_ascii=False)

    def test_generate_summary_report(self):
        """generate_summary_report メソッドのテスト"""
        # マークダウン形式でレポート生成
        report_file = self.generator.generate_summary_report(output_format="markdown")
        
        # ファイルが作成されたか確認
        self.assertTrue(os.path.exists(report_file))
        self.assertTrue(report_file.endswith('.md'))
        
        # 内容の検証
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('# AWS リソースサマリーレポート', content)
            self.assertIn('## リソースタイプ別サマリー', content)
            self.assertIn('EC2_Instances', content)
            self.assertIn('S3_Buckets', content)

    def test_generate_trend_report(self):
        """generate_trend_report メソッドのテスト"""
        # マークダウン形式でレポート生成
        report_file = self.generator.generate_trend_report(output_format="markdown")
        
        # ファイルが作成されたか確認
        self.assertTrue(os.path.exists(report_file))
        self.assertTrue(report_file.endswith('.md'))
        
        # 内容の検証
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('# AWS リソーストレンドレポート', content)
            self.assertIn('## リソース数のトレンド', content)
            self.assertIn('## 月次コストのトレンド', content)
            self.assertIn('2025-02-01', content)
            self.assertIn('2025-03-01', content)

    def test_generate_changes_report(self):
        """generate_changes_report メソッドのテスト"""
        # 変更レポートファイルのパス
        change_report_file = os.path.join(
            self.base_dir, 'output', 'processed', 'reports', 
            f"changes_2025-02-01_to_2025-03-01.json"
        )
        
        # マークダウン形式でレポート生成
        report_file = self.generator.generate_changes_report(change_report_file, output_format="markdown")
        
        # ファイルが作成されたか確認
        self.assertTrue(os.path.exists(report_file))
        self.assertTrue(report_file.endswith('.md'))
        
        # 内容の検証
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('# AWS リソース変更レポート', content)
            self.assertIn('追加されたリソース: **2**', content)
            self.assertIn('削除されたリソース: **1**', content)
            self.assertIn('変更されたリソース: **2**', content)

    def test_generate_cost_report(self):
        """generate_cost_report メソッドのテスト"""
        # マークダウン形式でレポート生成
        with patch('src.report.report_generator.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 3, 15)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            report_file = self.generator.generate_cost_report(output_format="markdown")
        
        # ファイルが作成されたか確認
        self.assertTrue(os.path.exists(report_file))
        self.assertTrue(report_file.endswith('.md'))
        
        # 内容の検証
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('# AWS リソースコストレポート', content)
            self.assertIn('## 月次コスト総額', content)
            self.assertIn('## サービス別コスト', content)
            self.assertIn('## タグ別コスト', content)

if __name__ == '__main__':
    unittest.main()
