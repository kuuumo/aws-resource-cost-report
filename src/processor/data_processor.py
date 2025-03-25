#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWS リソースデータ処理モジュール
"""

import os
import json
import logging
import shutil
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

import pandas as pd

# ロギングの設定
logger = logging.getLogger(__name__)

class DataProcessor:
    """AWS リソースデータを処理するクラス"""
    
    def __init__(self, base_dir: str):
        """
        初期化関数
        
        Args:
            base_dir (str): ベースディレクトリのパス
        """
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, 'output', 'raw')
        self.processed_dir = os.path.join(base_dir, 'output', 'processed')
        self.trends_dir = os.path.join(self.processed_dir, 'trends')
        self.reports_dir = os.path.join(self.processed_dir, 'reports')
        self.config_dir = os.path.join(base_dir, 'output', 'config')
        
        # 必要なディレクトリを作成
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.trends_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
    
    def save_raw_data(self, resources: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        生データを日付ごとのディレクトリに保存
        
        Args:
            resources (Dict): リソース情報
            
        Returns:
            str: 保存した日付ディレクトリのパス
        """
        # 現在日時のフォーマットを生成
        date_str = datetime.now().strftime('%Y-%m-%d')
        date_dir = os.path.join(self.raw_dir, date_str)
        
        # 日付ディレクトリがすでに存在していれば削除して再作成
        if os.path.exists(date_dir):
            logger.warning(f"日付ディレクトリ {date_dir} はすでに存在します。内容を削除して再作成します。")
            shutil.rmtree(date_dir)
        
        # 日付ディレクトリを作成
        os.makedirs(date_dir, exist_ok=True)
        
        # リソースタイプごとにJSONファイルとして保存
        for resource_type, resource_list in resources.items():
            resource_file = os.path.join(date_dir, f"{resource_type.lower()}.json")
            
            with open(resource_file, 'w', encoding='utf-8') as f:
                json.dump(resource_list, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"{resource_type} データを {resource_file} に保存しました ({len(resource_list)} 件)")
        
        # すべてのリソースの統合ファイルを作成
        all_resources_file = os.path.join(date_dir, "all_resources.json")
        
        # リソースカウント情報を追加
        output_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "resource_counts": {
                    resource_type: len(resource_list)
                    for resource_type, resource_list in resources.items()
                },
                "total_resources": sum(len(resource_list) for resource_list in resources.values())
            },
            "resources": resources
        }
        
        with open(all_resources_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"全リソースデータを {all_resources_file} に統合しました")
        return date_dir
    
    def generate_summary(self, date_str: Optional[str] = None) -> str:
        """
        指定日付のデータからサマリー情報を生成
        
        Args:
            date_str (str, optional): 処理対象の日付 (YYYY-MM-DD形式)。未指定時は最新のデータを使用
            
        Returns:
            str: 生成したサマリーファイルのパス
        """
        # 対象の日付ディレクトリを決定
        if date_str:
            date_dir = os.path.join(self.raw_dir, date_str)
            if not os.path.exists(date_dir):
                raise ValueError(f"指定された日付 {date_str} のデータが存在しません")
        else:
            date_str = self.get_latest_raw_data_date()
            if not date_str:
                raise ValueError("処理対象のデータがありません")
            date_dir = os.path.join(self.raw_dir, date_str)
        
        logger.info(f"{date_str} のデータからサマリー情報を生成します")
        
        # 全リソースデータの読み込み
        all_resources_file = os.path.join(date_dir, "all_resources.json")
        if not os.path.exists(all_resources_file):
            raise FileNotFoundError(f"全リソースデータファイル {all_resources_file} が見つかりません")
        
        with open(all_resources_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        
        # サマリー情報を構築
        resources = all_data.get("resources", {})
        metadata = all_data.get("metadata", {})
        
        # リソースタイプ別の集計
        resource_summary = {}
        for resource_type, resource_list in resources.items():
            # タグベースの集計
            tags_summary = self._summarize_tags(resource_list)
            
            # リージョン別の集計（適用可能な場合）
            region_summary = self._summarize_by_field(resource_list, 'AZ', 
                                                     transform_func=lambda az: az.split('-')[0] if az else 'unknown')
            
            resource_summary[resource_type] = {
                "count": len(resource_list),
                "tags_summary": tags_summary,
                "region_summary": region_summary
            }
        
        # VPCごとのリソース数を集計
        vpc_resources = self._summarize_vpc_resources(resources)
        
        # 最終的なサマリーデータの構築
        summary_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source_date": date_str,
                "total_resources": metadata.get("total_resources", 0)
            },
            "resource_summary": resource_summary,
            "vpc_resources": vpc_resources
        }
        
        # サマリーファイルに保存
        summary_file = os.path.join(self.processed_dir, "summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"サマリー情報を {summary_file} に保存しました")
        return summary_file
    
    def generate_trend_data(self) -> Dict[str, str]:
        """
        トレンドデータを生成
        
        Returns:
            Dict[str, str]: 生成したトレンドファイルのパスマップ
        """
        logger.info("トレンドデータの生成を開始します")
        
        # 日付ディレクトリの一覧を取得（日付でソート）
        date_dirs = sorted([d for d in os.listdir(self.raw_dir) 
                           if os.path.isdir(os.path.join(self.raw_dir, d)) and 
                           self._is_valid_date_format(d)])
        
        if not date_dirs:
            logger.warning("トレンドデータの生成に必要なデータがありません")
            return {}
        
        # 月次コストトレンドの生成
        monthly_cost_file = os.path.join(self.trends_dir, "monthly_cost.json")
        monthly_cost_data = self._generate_monthly_cost_trend(date_dirs)
        
        with open(monthly_cost_file, 'w', encoding='utf-8') as f:
            json.dump(monthly_cost_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"月次コストトレンドを {monthly_cost_file} に保存しました")
        
        # リソース数トレンドの生成
        resource_count_file = os.path.join(self.trends_dir, "resource_count.json")
        resource_count_data = self._generate_resource_count_trend(date_dirs)
        
        with open(resource_count_file, 'w', encoding='utf-8') as f:
            json.dump(resource_count_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"リソース数トレンドを {resource_count_file} に保存しました")
        
        # 結果のパスマップを返す
        return {
            "monthly_cost": monthly_cost_file,
            "resource_count": resource_count_file
        }
    
    def generate_change_report(self, start_date: str, end_date: str) -> str:
        """
        2つの日付間のリソース変更を検出してレポートを生成
        
        Args:
            start_date (str): 開始日（YYYY-MM-DD形式）
            end_date (str): 終了日（YYYY-MM-DD形式）
            
        Returns:
            str: 生成したレポートファイルのパス
        """
        logger.info(f"{start_date} から {end_date} までの変更レポートを生成します")
        
        # 両日付のデータが存在するか確認
        start_dir = os.path.join(self.raw_dir, start_date)
        end_dir = os.path.join(self.raw_dir, end_date)
        
        if not os.path.exists(start_dir):
            raise ValueError(f"開始日 {start_date} のデータが存在しません")
        if not os.path.exists(end_dir):
            raise ValueError(f"終了日 {end_date} のデータが存在しません")
        
        # 両日付の全リソースデータを読み込み
        start_file = os.path.join(start_dir, "all_resources.json")
        end_file = os.path.join(end_dir, "all_resources.json")
        
        with open(start_file, 'r', encoding='utf-8') as f:
            start_data = json.load(f)
        
        with open(end_file, 'r', encoding='utf-8') as f:
            end_data = json.load(f)
        
        # 変更の検出
        changes = self._detect_changes(start_data, end_data)
        
        # コスト変動の計算
        cost_changes = self._calculate_cost_changes(changes)
        
        # リソースタイプごとの集計
        summary_by_type = self._summarize_changes_by_type(changes)
        
        # タグ変更の集計
        tag_changes = self._summarize_tag_changes(changes)
        
        # セキュリティグループ変更の集計
        security_group_changes = self._extract_security_group_changes(changes)
        
        # 変更レポートの構築
        report = {
            "metadata": {
                "start_date": start_date,
                "end_date": end_date,
                "generated_at": datetime.now().isoformat(),
                "days_between": self._calculate_days_between(start_date, end_date)
            },
            "summary": {
                "resources_added": sum(len(v) for v in changes["added"].values()),
                "resources_removed": sum(len(v) for v in changes["removed"].values()),
                "resources_modified": sum(len(v) for v in changes["modified"].values()),
                "cost_impact": cost_changes["total_impact"],
                "resource_type_changes": summary_by_type,
                "tag_changes": tag_changes,
                "security_changes": security_group_changes
            },
            "changes": changes,
            "cost_changes": cost_changes
        }
        
        # レポートファイルに保存
        report_file = os.path.join(self.reports_dir, f"changes_{start_date}_to_{end_date}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"変更レポートを {report_file} に保存しました")
        return report_file
    
    def get_latest_raw_data_date(self) -> Optional[str]:
        """
        最新の生データの日付を取得
        
        Returns:
            str: 最新の日付 (YYYY-MM-DD形式)、データがなければNone
        """
        date_dirs = [d for d in os.listdir(self.raw_dir) 
                    if os.path.isdir(os.path.join(self.raw_dir, d)) and 
                    self._is_valid_date_format(d)]
        
        if not date_dirs:
            return None
        
        # 日付でソートして最新を返す
        return sorted(date_dirs)[-1]
    
    def get_previous_raw_data_date(self, current_date: str) -> Optional[str]:
        """
        指定された日付の前の日付を取得
        
        Args:
            current_date (str): 現在の日付 (YYYY-MM-DD形式)
            
        Returns:
            str: 前の日付、なければNone
        """
        date_dirs = [d for d in os.listdir(self.raw_dir) 
                    if os.path.isdir(os.path.join(self.raw_dir, d)) and 
                    self._is_valid_date_format(d) and d < current_date]
        
        if not date_dirs:
            return None
        
        # 日付でソートして最新を返す
        return sorted(date_dirs)[-1]
    
    def _is_valid_date_format(self, date_str: str) -> bool:
        """日付文字列がYYYY-MM-DD形式かどうか検証"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def _summarize_tags(self, resources: List[Dict[str, Any]]) -> Dict[str, int]:
        """リソースのタグ使用状況を集計"""
        tag_counts = {}
        
        for resource in resources:
            tags = resource.get('Tags', [])
            if not tags:
                continue
            
            for tag in tags:
                key = tag.get('Key', '')
                if not key:
                    continue
                
                tag_counts[key] = tag_counts.get(key, 0) + 1
        
        return tag_counts
    
    def _summarize_by_field(self, resources: List[Dict[str, Any]], field: str, 
                          transform_func=None) -> Dict[str, int]:
        """指定フィールドの値ごとにリソースを集計"""
        field_counts = {}
        
        for resource in resources:
            value = resource.get(field, '')
            if not value:
                continue
            
            # 変換関数があれば適用
            if transform_func:
                value = transform_func(value)
            
            field_counts[value] = field_counts.get(value, 0) + 1
        
        return field_counts
    
    def _summarize_vpc_resources(self, resources: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, int]]:
        """VPCごとのリソース数を集計"""
        vpc_resources = {}
        
        # VPC IDを持つリソースタイプのリスト
        vpc_related_resources = [
            'EC2_Instances', 'EC2_Subnets', 'EC2_SecurityGroups', 
            'EC2_LoadBalancers', 'RDS_Instances'
        ]
        
        # VPCごとにリソース数を集計
        for resource_type in vpc_related_resources:
            if resource_type not in resources:
                continue
            
            for resource in resources[resource_type]:
                vpc_id = resource.get('VpcId', '')
                if not vpc_id:
                    continue
                
                if vpc_id not in vpc_resources:
                    vpc_resources[vpc_id] = {}
                
                vpc_resources[vpc_id][resource_type] = vpc_resources[vpc_id].get(resource_type, 0) + 1
        
        return vpc_resources
    
    def _generate_monthly_cost_trend(self, date_dirs: List[str]) -> Dict[str, Any]:
        """月次コストトレンドの生成"""
        # 月次コスト情報をシミュレート（実際のデータがないため）
        # 実際の実装では、Cost Explorer API からデータを取得するなどが必要
        
        monthly_data = []
        for date_str in date_dirs:
            # シミュレーション用のコストデータ（実際はこれらのデータを算出/取得する）
            ec2_cost = 100  # 仮のEC2コスト
            s3_cost = 50    # 仮のS3コスト
            rds_cost = 75   # 仮のRDSコスト
            other_cost = 30 # その他コスト
            
            monthly_data.append({
                "date": date_str,
                "costs": {
                    "EC2": ec2_cost,
                    "S3": s3_cost,
                    "RDS": rds_cost,
                    "Other": other_cost
                },
                "total_cost": ec2_cost + s3_cost + rds_cost + other_cost
            })
        
        return {
            "monthly_cost_trend": monthly_data,
            "updated_at": datetime.now().isoformat()
        }
    
    def _generate_resource_count_trend(self, date_dirs: List[str]) -> Dict[str, Any]:
        """リソース数トレンドの生成"""
        trend_data = []
        
        for date_str in date_dirs:
            date_dir = os.path.join(self.raw_dir, date_str)
            all_resources_file = os.path.join(date_dir, "all_resources.json")
            
            if not os.path.exists(all_resources_file):
                logger.warning(f"{date_str} の全リソースデータファイルが見つかりません")
                continue
            
            with open(all_resources_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            
            metadata = all_data.get("metadata", {})
            resources = all_data.get("resources", {})
            
            # リソースタイプごとの集計
            resource_counts = {}
            for resource_type, resource_list in resources.items():
                resource_counts[resource_type] = len(resource_list)
            
            trend_data.append({
                "date": date_str,
                "resource_counts": resource_counts,
                "total_resources": metadata.get("total_resources", 0)
            })
        
        return {
            "resource_count_trend": trend_data,
            "updated_at": datetime.now().isoformat()
        }
    
    def _detect_changes(self, start_data: Dict[str, Any], end_data: Dict[str, Any]) -> Dict[str, Any]:
        """2つの時点間のリソース変更を検出"""
        changes = {
            "added": {},
            "removed": {},
            "modified": {}
        }
        
        start_resources = start_data.get("resources", {})
        end_resources = end_data.get("resources", {})
        
        # 全リソースタイプの集合を取得
        all_resource_types = set(start_resources.keys()) | set(end_resources.keys())
        
        for resource_type in all_resource_types:
            start_list = start_resources.get(resource_type, [])
            end_list = end_resources.get(resource_type, [])
            
            # リソースIDをキーにしたマップを作成
            start_map = {res.get('ResourceId'): res for res in start_list if res.get('ResourceId')}
            end_map = {res.get('ResourceId'): res for res in end_list if res.get('ResourceId')}
            
            # 追加されたリソースを検出
            added_ids = set(end_map.keys()) - set(start_map.keys())
            if added_ids:
                changes["added"][resource_type] = [end_map[id] for id in added_ids]
            
            # 削除されたリソースを検出
            removed_ids = set(start_map.keys()) - set(end_map.keys())
            if removed_ids:
                changes["removed"][resource_type] = [start_map[id] for id in removed_ids]
            
            # 変更されたリソースを検出
            common_ids = set(start_map.keys()) & set(end_map.keys())
            modified = []
            
            for id in common_ids:
                start_res = start_map[id]
                end_res = end_map[id]
                
                # 変更の検出（単純な比較では不十分な場合がある）
                # タグや重要なフィールドに焦点を当てた比較が必要
                if self._is_resource_modified(start_res, end_res):
                    modified.append({
                        "resource_id": id,
                        "before": start_res,
                        "after": end_res,
                        "changes": self._get_resource_changes(start_res, end_res)
                    })
            
            if modified:
                changes["modified"][resource_type] = modified
        
        return changes
    
    def _is_resource_modified(self, start_res: Dict[str, Any], end_res: Dict[str, Any]) -> bool:
        """リソースが変更されたかどうかを判断"""
        # 比較から除外するフィールド
        exclude_fields = {'Tags'}
        
        # タグ以外のフィールドで変更があるか確認
        for key in set(start_res.keys()) | set(end_res.keys()):
            if key in exclude_fields:
                continue
            
            if key not in start_res or key not in end_res:
                return True
            
            if start_res[key] != end_res[key]:
                return True
        
        # タグの変更を確認
        start_tags = {tag.get('Key'): tag.get('Value') for tag in start_res.get('Tags', [])}
        end_tags = {tag.get('Key'): tag.get('Value') for tag in end_res.get('Tags', [])}
        
        return start_tags != end_tags
    
    def _get_resource_changes(self, start_res: Dict[str, Any], end_res: Dict[str, Any]) -> Dict[str, Dict]:
        """リソースの変更内容を取得"""
        changes = {}
        
        # フィールドの変更を検出
        all_keys = set(start_res.keys()) | set(end_res.keys())
        for key in all_keys:
            if key == 'Tags':
                continue  # タグは別途処理
            
            if key not in start_res:
                changes[key] = {"added": end_res[key]}
            elif key not in end_res:
                changes[key] = {"removed": start_res[key]}
            elif start_res[key] != end_res[key]:
                changes[key] = {"from": start_res[key], "to": end_res[key]}
        
        # タグの変更を検出
        start_tags = {tag.get('Key'): tag.get('Value') for tag in start_res.get('Tags', [])}
        end_tags = {tag.get('Key'): tag.get('Value') for tag in end_res.get('Tags', [])}
        
        tag_changes = {}
        
        # 追加されたタグ
        added_tags = {k: v for k, v in end_tags.items() if k not in start_tags}
        if added_tags:
            tag_changes["added"] = added_tags
        
        # 削除されたタグ
        removed_tags = {k: v for k, v in start_tags.items() if k not in end_tags}
        if removed_tags:
            tag_changes["removed"] = removed_tags
        
        # 変更されたタグ
        modified_tags = {k: {"from": start_tags[k], "to": end_tags[k]} 
                        for k in set(start_tags.keys()) & set(end_tags.keys()) 
                        if start_tags[k] != end_tags[k]}
        if modified_tags:
            tag_changes["modified"] = modified_tags
        
        if tag_changes:
            changes["Tags"] = tag_changes
        
        return changes
        
    def _calculate_cost_changes(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """コスト変動を計算する"""
        # 注意: 実際の実装では、コストはAWS Cost ExplorerやS3やEC2などのサービス料金から算出される
        # ここでは仮の計算ロジックを実装
        
        # サービスごとのコスト係数（実際はAPIを呼び出して取得するなど）
        cost_factors = {
            'EC2_Instances': 100,
            'RDS_Instances': 200,
            'S3_Buckets': 5,
            'Lambda_Functions': 0.5,
            'CloudFront_Distributions': 30,
            'default': 10  # その他のリソースタイプ
        }
        
        # 追加されたリソースのコスト合計
        added_cost = 0
        for resource_type, resources in changes.get('added', {}).items():
            cost_factor = cost_factors.get(resource_type, cost_factors['default'])
            added_cost += len(resources) * cost_factor
        
        # 削除されたリソースのコスト合計
        removed_cost = 0
        for resource_type, resources in changes.get('removed', {}).items():
            cost_factor = cost_factors.get(resource_type, cost_factors['default'])
            removed_cost += len(resources) * cost_factor
        
        # 変更されたリソースのコスト影響
        modified_cost = 0
        for resource_type, resources in changes.get('modified', {}).items():
            # 変更によるコスト影響の計算（例: インスタンスタイプの変更など）
            # 実際はもっと複雑なロジックになる
            impact_factor = 0.1  # 変更による影響係数（10%と仮定）
            cost_factor = cost_factors.get(resource_type, cost_factors['default'])
            modified_cost += len(resources) * cost_factor * impact_factor
        
        # コスト変動のサマリー
        result = {
            'added_cost': added_cost,
            'removed_cost': removed_cost,
            'modified_cost': modified_cost,
            'total_impact': added_cost - removed_cost + modified_cost,
            'breakdown_by_type': {}
        }
        
        # サービスタイプ別の内訳
        for change_type, type_resources in changes.items():
            if change_type not in ['added', 'removed', 'modified']:
                continue
                
            for resource_type, resources in type_resources.items():
                if resource_type not in result['breakdown_by_type']:
                    result['breakdown_by_type'][resource_type] = {
                        'added': 0,
                        'removed': 0,
                        'modified': 0,
                        'total': 0
                    }
                
                cost_factor = cost_factors.get(resource_type, cost_factors['default'])
                if change_type == 'added':
                    impact = len(resources) * cost_factor
                elif change_type == 'removed':
                    impact = -len(resources) * cost_factor
                else:  # modified
                    impact = len(resources) * cost_factor * impact_factor
                
                result['breakdown_by_type'][resource_type][change_type] = impact
                result['breakdown_by_type'][resource_type]['total'] += impact
        
        return result
    
    def _summarize_changes_by_type(self, changes: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """リソースタイプごとの変更を集計"""
        summary = {}
        
        for change_type in ['added', 'removed', 'modified']:
            change_data = changes.get(change_type, {})
            
            for resource_type, resources in change_data.items():
                if resource_type not in summary:
                    summary[resource_type] = {
                        'added': 0,
                        'removed': 0,
                        'modified': 0,
                        'net_change': 0
                    }
                
                count = len(resources)
                summary[resource_type][change_type] = count
                
                # ネット変化を計算
                if change_type == 'added':
                    summary[resource_type]['net_change'] += count
                elif change_type == 'removed':
                    summary[resource_type]['net_change'] -= count
        
        return summary
    
    def _summarize_tag_changes(self, changes: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """タグの変更を集計"""
        tag_summary = {
            'added': {},
            'removed': {},
            'modified': {}
        }
        
        # 変更されたリソースのタグ変更を集計
        for resource_type, resources in changes.get('modified', {}).items():
            for resource in resources:
                change_details = resource.get('changes', {})
                tag_changes = change_details.get('Tags', {})
                
                # 追加されたタグ
                for tag_key, tag_value in tag_changes.get('added', {}).items():
                    if tag_key not in tag_summary['added']:
                        tag_summary['added'][tag_key] = 0
                    tag_summary['added'][tag_key] += 1
                
                # 削除されたタグ
                for tag_key, tag_value in tag_changes.get('removed', {}).items():
                    if tag_key not in tag_summary['removed']:
                        tag_summary['removed'][tag_key] = 0
                    tag_summary['removed'][tag_key] += 1
                
                # 変更されたタグ
                for tag_key, tag_value in tag_changes.get('modified', {}).items():
                    if tag_key not in tag_summary['modified']:
                        tag_summary['modified'][tag_key] = 0
                    tag_summary['modified'][tag_key] += 1
        
        # 追加されたリソースのタグを集計
        for resource_type, resources in changes.get('added', {}).items():
            for resource in resources:
                tags = resource.get('Tags', [])
                for tag in tags:
                    tag_key = tag.get('Key')
                    if not tag_key:
                        continue
                        
                    if tag_key not in tag_summary['added']:
                        tag_summary['added'][tag_key] = 0
                    tag_summary['added'][tag_key] += 1
        
        # 削除されたリソースのタグを集計
        for resource_type, resources in changes.get('removed', {}).items():
            for resource in resources:
                tags = resource.get('Tags', [])
                for tag in tags:
                    tag_key = tag.get('Key')
                    if not tag_key:
                        continue
                        
                    if tag_key not in tag_summary['removed']:
                        tag_summary['removed'][tag_key] = 0
                    tag_summary['removed'][tag_key] += 1
        
        return tag_summary
    
    def _extract_security_group_changes(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティグループの変更を抽出"""
        security_changes = {
            'added': [],
            'removed': [],
            'modified': []
        }
        
        # 追加されたセキュリティグループ
        if 'EC2_SecurityGroups' in changes.get('added', {}):
            for sg in changes['added']['EC2_SecurityGroups']:
                security_changes['added'].append({
                    'group_id': sg.get('GroupId', ''),
                    'name': sg.get('GroupName', ''),
                    'description': sg.get('Description', ''),
                    'vpc_id': sg.get('VpcId', '')
                })
        
        # 削除されたセキュリティグループ
        if 'EC2_SecurityGroups' in changes.get('removed', {}):
            for sg in changes['removed']['EC2_SecurityGroups']:
                security_changes['removed'].append({
                    'group_id': sg.get('GroupId', ''),
                    'name': sg.get('GroupName', ''),
                    'description': sg.get('Description', ''),
                    'vpc_id': sg.get('VpcId', '')
                })
        
        # 変更されたセキュリティグループ
        if 'EC2_SecurityGroups' in changes.get('modified', {}):
            for sg in changes['modified']['EC2_SecurityGroups']:
                sg_changes = sg.get('changes', {})
                security_changes['modified'].append({
                    'group_id': sg.get('resource_id', ''),
                    'name': sg.get('before', {}).get('GroupName', ''),
                    'vpc_id': sg.get('before', {}).get('VpcId', ''),
                    'changes': sg_changes
                })
        
        # インスタンスのセキュリティグループ変更を抽出
        if 'EC2_Instances' in changes.get('modified', {}):
            for instance in changes['modified']['EC2_Instances']:
                sg_changes = instance.get('changes', {}).get('SecurityGroups')
                if sg_changes:
                    security_changes['modified'].append({
                        'instance_id': instance.get('resource_id', ''),
                        'security_group_changes': sg_changes
                    })
        
        return security_changes
    
    def _calculate_days_between(self, start_date: str, end_date: str) -> int:
        """2つの日付間の日数を計算"""
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        delta = end - start
        return delta.days
