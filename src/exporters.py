#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWS リソース情報のエクスポートモジュール
"""

import os
import json
import csv
import logging
from typing import Dict, List, Any, Optional

# ロギングの設定
logger = logging.getLogger(__name__)

class BaseExporter:
    """エクスポーターの基底クラス"""
    
    def __init__(self, output_dir: str, timestamp: str):
        """
        初期化関数
        
        Args:
            output_dir (str): 出力ディレクトリパス
            timestamp (str): タイムスタンプ文字列
        """
        self.output_dir = output_dir
        self.timestamp = timestamp
    
    def export(self, resources: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        リソース情報をエクスポート（サブクラスで実装）
        
        Args:
            resources (Dict): リソース情報
            
        Returns:
            str: 出力ファイルパス
        """
        raise NotImplementedError("サブクラスで実装する必要があります")

class CSVExporter(BaseExporter):
    """リソース情報をCSVファイルにエクスポートするクラス"""
    
    def export(self, resources: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """
        リソース情報をCSVファイルにエクスポート
        
        Args:
            resources (Dict): リソース情報
            
        Returns:
            List[str]: 出力ファイル名のリスト
        """
        logger.info("CSVファイルへのエクスポートを開始します")
        
        csv_files = []
        
        # サービスごとにCSVファイルを作成
        for resource_type, resource_list in resources.items():
            if not resource_list:
                continue
                
            # ヘッダー行の準備（共通フィールド + リソース固有フィールド）
            common_fields = ["ResourceId", "ResourceName", "ResourceType"]
            resource_fields = set()
            
            # リソース固有のフィールドを収集
            for resource in resource_list:
                for key in resource.keys():
                    if key not in common_fields and not isinstance(resource[key], (dict, list)):
                        resource_fields.add(key)
            
            # フィールドをソートして順序を一定に
            headers = common_fields + sorted(list(resource_fields))
            
            # CSVファイルのパス
            csv_file = os.path.join(self.output_dir, f"{resource_type}_{self.timestamp}.csv")
            csv_files.append(csv_file)
            
            # CSVファイルに書き込み
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
                writer.writeheader()
                
                for resource in resource_list:
                    # 複雑な構造をシンプルな文字列に変換
                    row = {}
                    for key, value in resource.items():
                        if isinstance(value, (dict, list)):
                            # 複雑な型は文字列表現に変換
                            row[key] = str(value)
                        else:
                            row[key] = value
                    
                    writer.writerow(row)
        
        logger.info(f"{len(csv_files)}個のCSVファイルを作成しました")
        return csv_files

class JSONExporter(BaseExporter):
    """リソース情報をJSONファイルにエクスポートするクラス"""
    
    def export(self, resources: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        リソース情報をJSONファイルにエクスポート
        
        Args:
            resources (Dict): リソース情報
            
        Returns:
            str: 出力ファイルパス
        """
        logger.info("JSONファイルへのエクスポートを開始します")
        
        # JSONファイルのパス
        json_file = os.path.join(self.output_dir, f"aws_resources_{self.timestamp}.json")
        
        # リソースカウント情報を追加
        output_data = {
            "metadata": {
                "timestamp": self.timestamp,
                "resource_counts": {
                    resource_type: len(resource_list)
                    for resource_type, resource_list in resources.items()
                },
                "total_resources": sum(len(resource_list) for resource_list in resources.values())
            },
            "resources": resources
        }
        
        # JSONファイルに書き込み
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"JSONファイル {json_file} を作成しました")
        return json_file
