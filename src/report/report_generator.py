#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWS リソースレポート生成モジュール
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# ロギングの設定
logger = logging.getLogger(__name__)

class ReportGenerator:
    """AWS リソース情報からレポートを生成するクラス"""
    
    def __init__(self, base_dir: str):
        """
        初期化関数
        
        Args:
            base_dir (str): ベースディレクトリのパス
        """
        self.base_dir = base_dir
        self.processed_dir = os.path.join(base_dir, 'output', 'processed')
        self.reports_dir = os.path.join(self.processed_dir, 'reports')
        self.trends_dir = os.path.join(self.processed_dir, 'trends')
        self.config_dir = os.path.join(base_dir, 'output', 'config')
        
        # 必要なディレクトリを作成
        os.makedirs(self.reports_dir, exist_ok=True)
        
        # 設定ファイルの読み込み
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        config_file = os.path.join(self.config_dir, 'report_config.json')
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # デフォルト設定
            default_config = {
                "report_formats": ["markdown"],
                "show_cost_info": True,
                "include_graphs": True,
                "graph_formats": ["png"],
                "detail_level": "medium"  # low, medium, high
            }
            
            # デフォルト設定を保存
            os.makedirs(self.config_dir, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            return default_config
    
    def generate_summary_report(self, output_format: str = "markdown") -> str:
        """
        サマリーレポートを生成
        
        Args:
            output_format (str): 出力形式 (markdown, html)
            
        Returns:
            str: 生成したレポートファイルのパス
        """
        logger.info(f"サマリーレポートの生成を開始します (形式: {output_format})")
        
        # サマリーデータの読み込み
        summary_file = os.path.join(self.processed_dir, "summary.json")
        if not os.path.exists(summary_file):
            raise FileNotFoundError(f"サマリーファイル {summary_file} が見つかりません")
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # レポートの基本情報
        metadata = summary_data.get("metadata", {})
        resource_summary = summary_data.get("resource_summary", {})
        vpc_resources = summary_data.get("vpc_resources", {})
        
        # マークダウンレポートの生成
        md_content = []
        
        # ヘッダー
        md_content.append("# AWS リソースサマリーレポート")
        md_content.append(f"生成日時: {metadata.get('generated_at')}")
        md_content.append(f"データ取得日: {metadata.get('source_date')}")
        md_content.append(f"合計リソース数: {metadata.get('total_resources')}")
        md_content.append("")
        
        # リソースタイプ別サマリー
        md_content.append("## リソースタイプ別サマリー")
        md_content.append("")
        md_content.append("| リソースタイプ | 件数 |")
        md_content.append("|--------------|------|")
        
        for resource_type, data in resource_summary.items():
            md_content.append(f"| {resource_type} | {data.get('count')} |")
        
        md_content.append("")
        
        # リージョン別リソース分布
        md_content.append("## リージョン別リソース分布")
        md_content.append("")
        region_distribution = {}
        
        for resource_type, data in resource_summary.items():
            for region, count in data.get("region_summary", {}).items():
                if region not in region_distribution:
                    region_distribution[region] = {}
                region_distribution[region][resource_type] = count
        
        # リージョン別テーブルの作成
        if region_distribution:
            resource_types = sorted(list({rt for data in region_distribution.values() for rt in data.keys()}))
            
            # テーブルヘッダー
            header = "| リージョン | " + " | ".join(resource_types) + " | 合計 |"
            md_content.append(header)
            separator = "|" + "|".join(["-" * 10] * (len(resource_types) + 2)) + "|"
            md_content.append(separator)
            
            # データ行
            for region, data in sorted(region_distribution.items()):
                row = f"| {region} |"
                total = 0
                for rt in resource_types:
                    count = data.get(rt, 0)
                    total += count
                    row += f" {count} |"
                row += f" {total} |"
                md_content.append(row)
            
            md_content.append("")
        
        # VPC別リソース分布
        if vpc_resources:
            md_content.append("## VPC別リソース分布")
            md_content.append("")
            
            # VPCに関連するリソースタイプの一覧を取得
            vpc_resource_types = sorted(list({rt for vpc_data in vpc_resources.values() for rt in vpc_data.keys()}))
            
            # テーブルヘッダー
            header = "| VPC ID | " + " | ".join(vpc_resource_types) + " | 合計 |"
            md_content.append(header)
            separator = "|" + "|".join(["-" * 10] * (len(vpc_resource_types) + 2)) + "|"
            md_content.append(separator)
            
            # データ行
            for vpc_id, data in sorted(vpc_resources.items()):
                row = f"| {vpc_id} |"
                total = 0
                for rt in vpc_resource_types:
                    count = data.get(rt, 0)
                    total += count
                    row += f" {count} |"
                row += f" {total} |"
                md_content.append(row)
            
            md_content.append("")
        
        # タグ使用状況
        md_content.append("## タグ使用状況")
        md_content.append("")
        md_content.append("| タグキー | 使用リソース数 |")
        md_content.append("|----------|--------------|")
        
        # 全リソースタイプのタグを集計
        tag_usage = {}
        for resource_type, data in resource_summary.items():
            for tag_key, count in data.get("tags_summary", {}).items():
                tag_usage[tag_key] = tag_usage.get(tag_key, 0) + count
        
        # タグ使用状況をソートして表示
        for tag_key, count in sorted(tag_usage.items(), key=lambda x: x[1], reverse=True):
            md_content.append(f"| {tag_key} | {count} |")
        
        md_content.append("")
        
        # マークダウンファイルの保存
        md_text = "\n".join(md_content)
        output_file = os.path.join(self.reports_dir, f"resource_summary_{metadata.get('source_date')}.md")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_text)
        
        logger.info(f"サマリーレポートを {output_file} に保存しました")
        
        return output_file

    def generate_trend_report(self, output_format: str = "markdown") -> str:
        """
        トレンドレポートを生成
        
        Args:
            output_format (str): 出力形式 (markdown, html)
            
        Returns:
            str: 生成したレポートファイルのパス
        """
        logger.info(f"トレンドレポートの生成を開始します (形式: {output_format})")
        
        # トレンドデータの読み込み
        monthly_cost_file = os.path.join(self.trends_dir, "monthly_cost.json")
        resource_count_file = os.path.join(self.trends_dir, "resource_count.json")
        
        if not os.path.exists(monthly_cost_file) or not os.path.exists(resource_count_file):
            logger.warning("トレンドデータが不足しています")
            if not os.path.exists(monthly_cost_file):
                logger.warning(f"月次コストファイル {monthly_cost_file} が見つかりません")
            if not os.path.exists(resource_count_file):
                logger.warning(f"リソース数ファイル {resource_count_file} が見つかりません")
            return ""
        
        with open(monthly_cost_file, 'r', encoding='utf-8') as f:
            monthly_cost_data = json.load(f)
        
        with open(resource_count_file, 'r', encoding='utf-8') as f:
            resource_count_data = json.load(f)
        
        # マークダウンレポートの生成
        md_content = []
        
        # ヘッダー
        md_content.append("# AWS リソーストレンドレポート")
        md_content.append(f"生成日時: {datetime.now().isoformat()}")
        md_content.append("")
        
        # リソース数のトレンド
        md_content.append("## リソース数のトレンド")
        md_content.append("")
        
        resource_trend = resource_count_data.get("resource_count_trend", [])
        
        if resource_trend:
            md_content.append("| 日付 | 合計リソース数 | " + 
                             " | ".join(sorted(resource_trend[0].get("resource_counts", {}).keys())) + " |")
            md_content.append("|------|--------------|" + 
                             "|".join(["-" * 10] * len(resource_trend[0].get("resource_counts", {}))) + "|")
            
            for entry in resource_trend:
                date = entry.get("date")
                total = entry.get("total_resources", 0)
                counts = entry.get("resource_counts", {})
                
                row = f"| {date} | {total} |"
                for resource_type in sorted(counts.keys()):
                    row += f" {counts.get(resource_type, 0)} |"
                
                md_content.append(row)
            
            md_content.append("")
        
        # コストのトレンド
        md_content.append("## 月次コストのトレンド")
        md_content.append("")
        
        cost_trend = monthly_cost_data.get("monthly_cost_trend", [])
        
        if cost_trend:
            md_content.append("| 日付 | 合計コスト | " + 
                             " | ".join(sorted(cost_trend[0].get("costs", {}).keys())) + " |")
            md_content.append("|------|------------|" + 
                             "|".join(["-" * 10] * len(cost_trend[0].get("costs", {}))) + "|")
            
            for entry in cost_trend:
                date = entry.get("date")
                total = entry.get("total_cost", 0)
                costs = entry.get("costs", {})
                
                row = f"| {date} | ${total:.2f} |"
                for cost_type in sorted(costs.keys()):
                    row += f" ${costs.get(cost_type, 0):.2f} |"
                
                md_content.append(row)
            
            md_content.append("")
        
        # マークダウンファイルの保存
        md_text = "\n".join(md_content)
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.reports_dir, f"resource_trends_{timestamp}.md")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_text)
        
        logger.info(f"トレンドレポートを {output_file} に保存しました")
        
        return output_file
    
    def generate_changes_report(self, change_report_file: str, output_format: str = "markdown") -> str:
        """
        変更レポートを生成
        
        Args:
            change_report_file (str): 変更レポートJSONファイルのパス
            output_format (str): 出力形式 (markdown, html)
            
        Returns:
            str: 生成したレポートファイルのパス
        """
        logger.info(f"変更レポートの生成を開始します (形式: {output_format})")
        
        # 変更レポートデータの読み込み
        if not os.path.exists(change_report_file):
            raise FileNotFoundError(f"変更レポートファイル {change_report_file} が見つかりません")
        
        with open(change_report_file, 'r', encoding='utf-8') as f:
            changes_data = json.load(f)
        
        # レポートの基本情報
        metadata = changes_data.get("metadata", {})
        summary = changes_data.get("summary", {})
        changes = changes_data.get("changes", {})
        cost_changes = changes_data.get("cost_changes", {})
        
        # 日付情報
        start_date = metadata.get("start_date", "Unknown")
        end_date = metadata.get("end_date", "Unknown")
        days_between = metadata.get("days_between", 0)
        
        # マークダウンレポートの生成
        md_content = []
        
        # ヘッダー
        md_content.append(f"# AWS リソース変更レポート ({start_date} から {end_date})")
        md_content.append(f"生成日時: {metadata.get('generated_at', datetime.now().isoformat())}")
        md_content.append(f"期間: {days_between} 日間")
        md_content.append("")
        
        # サマリー
        md_content.append("## 変更サマリー")
        md_content.append("")
        md_content.append(f"* 追加されたリソース: **{summary.get('resources_added', 0)}**")
        md_content.append(f"* 削除されたリソース: **{summary.get('resources_removed', 0)}**")
        md_content.append(f"* 変更されたリソース: **{summary.get('resources_modified', 0)}**")
        
        # コスト影響
        cost_impact = summary.get('cost_impact', 0)
        if cost_impact > 0:
            md_content.append(f"* 推定コスト影響: **増加 ${cost_impact:.2f}/月**")
        else:
            md_content.append(f"* 推定コスト影響: **減少 ${-cost_impact:.2f}/月**")
        md_content.append("")
        
        # リソースタイプ別の変更集計
        resource_type_changes = summary.get("resource_type_changes", {})
        if resource_type_changes:
            md_content.append("## リソースタイプ別の変更")
            md_content.append("")
            md_content.append("| リソースタイプ | 追加 | 削除 | 変更 | 純増減 |")
            md_content.append("|--------------|------|------|------|--------|")
            
            for resource_type, counts in sorted(resource_type_changes.items()):
                added = counts.get("added", 0)
                removed = counts.get("removed", 0)
                modified = counts.get("modified", 0)
                net_change = counts.get("net_change", 0)
                
                # 増減に応じて+/-記号を追加
                net_change_str = f"+{net_change}" if net_change > 0 else str(net_change)
                
                md_content.append(f"| {resource_type} | {added} | {removed} | {modified} | {net_change_str} |")
            
            md_content.append("")
        
        # コスト変動の詳細
        if cost_changes:
            md_content.append("## コスト影響の詳細")
            md_content.append("")
            md_content.append(f"* 追加リソースによるコスト増: **${cost_changes.get('added_cost', 0):.2f}/月**")
            md_content.append(f"* 削除リソースによるコスト減: **${cost_changes.get('removed_cost', 0):.2f}/月**")
            md_content.append(f"* 変更リソースによるコスト影響: **${cost_changes.get('modified_cost', 0):.2f}/月**")
            md_content.append(f"* 合計コスト影響: **${cost_changes.get('total_impact', 0):.2f}/月**")
            md_content.append("")
            
            # サービスタイプ別のコスト内訳
            breakdown = cost_changes.get('breakdown_by_type', {})
            if breakdown:
                md_content.append("### サービスタイプ別のコスト影響")
                md_content.append("")
                md_content.append("| サービス | 追加コスト | 削除コスト | 変更コスト | 合計影響 |")
                md_content.append("|----------|------------|------------|------------|----------|")
                
                for service, impact in sorted(breakdown.items(), key=lambda x: abs(x[1].get('total', 0)), reverse=True):
                    added = impact.get("added", 0)
                    removed = impact.get("removed", 0)
                    modified = impact.get("modified", 0)
                    total = impact.get("total", 0)
                    
                    # 値に$記号とフォーマットを適用
                    md_content.append(f"| {service} | ${added:.2f} | ${removed:.2f} | ${modified:.2f} | ${total:.2f} |")
                
                md_content.append("")
        
        # セキュリティグループの変更
        security_changes = summary.get("security_changes", {})
        if security_changes:
            md_content.append("## セキュリティ関連の変更")
            md_content.append("")
            
            # 追加されたセキュリティグループ
            added_sg = security_changes.get("added", [])
            if added_sg:
                md_content.append("### 追加されたセキュリティグループ")
                md_content.append("")
                md_content.append("| グループID | 名前 | VPC ID | 説明 |")
                md_content.append("|-----------|------|--------|------|")
                
                for sg in added_sg:
                    md_content.append(f"| {sg.get('group_id', '')} | {sg.get('name', '')} | {sg.get('vpc_id', '')} | {sg.get('description', '')} |")
                
                md_content.append("")
            
            # 削除されたセキュリティグループ
            removed_sg = security_changes.get("removed", [])
            if removed_sg:
                md_content.append("### 削除されたセキュリティグループ")
                md_content.append("")
                md_content.append("| グループID | 名前 | VPC ID | 説明 |")
                md_content.append("|-----------|------|--------|------|")
                
                for sg in removed_sg:
                    md_content.append(f"| {sg.get('group_id', '')} | {sg.get('name', '')} | {sg.get('vpc_id', '')} | {sg.get('description', '')} |")
                
                md_content.append("")
            
            # 変更されたセキュリティグループ
            modified_sg = security_changes.get("modified", [])
            if modified_sg:
                md_content.append("### 変更されたセキュリティグループ")
                md_content.append("")
                md_content.append("| グループID/インスタンスID | 変更内容 |")
                md_content.append("|-------------------------|----------|")
                
                for sg in modified_sg:
                    if 'group_id' in sg:
                        id = sg.get('group_id', '')
                        desc = "ルールの変更"
                    else:
                        id = sg.get('instance_id', '')
                        desc = "セキュリティグループの割り当て変更"
                    
                    md_content.append(f"| {id} | {desc} |")
                
                md_content.append("")
        
        # タグの変更サマリー
        tag_changes = summary.get("tag_changes", {})
        if tag_changes:
            md_content.append("## タグの変更サマリー")
            md_content.append("")
            
            # 追加されたタグ
            added_tags = tag_changes.get("added", {})
            if added_tags:
                md_content.append("### 追加されたタグ")
                md_content.append("")
                md_content.append("| タグキー | リソース数 |")
                md_content.append("|----------|------------|")
                
                for tag, count in sorted(added_tags.items(), key=lambda x: x[1], reverse=True):
                    md_content.append(f"| {tag} | {count} |")
                
                md_content.append("")
            
            # 削除されたタグ
            removed_tags = tag_changes.get("removed", {})
            if removed_tags:
                md_content.append("### 削除されたタグ")
                md_content.append("")
                md_content.append("| タグキー | リソース数 |")
                md_content.append("|----------|------------|")
                
                for tag, count in sorted(removed_tags.items(), key=lambda x: x[1], reverse=True):
                    md_content.append(f"| {tag} | {count} |")
                
                md_content.append("")
            
            # 変更されたタグ
            modified_tags = tag_changes.get("modified", {})
            if modified_tags:
                md_content.append("### 変更されたタグ")
                md_content.append("")
                md_content.append("| タグキー | リソース数 |")
                md_content.append("|----------|------------|")
                
                for tag, count in sorted(modified_tags.items(), key=lambda x: x[1], reverse=True):
                    md_content.append(f"| {tag} | {count} |")
                
                md_content.append("")
        
        # 主要な追加リソース
        added = changes.get("added", {})
        if added:
            md_content.append("## 主要な追加リソース")
            md_content.append("")
            
            # リソースタイプごとにソートして表示
            for resource_type, resources in sorted(added.items()):
                if resources:
                    max_display = min(5, len(resources))  # 最大5件まで表示
                    md_content.append(f"### {resource_type} ({len(resources)}件)")
                    md_content.append("")
                    
                    for i, resource in enumerate(resources[:max_display]):
                        resource_id = resource.get("ResourceId", "Unknown")
                        name = resource.get("ResourceName", "")
                        name_str = f" ({name})" if name else ""
                        
                        md_content.append(f"{i+1}. **{resource_id}**{name_str}")
                    
                    if len(resources) > max_display:
                        md_content.append(f"... 他 {len(resources) - max_display} 件")
                    
                    md_content.append("")
        
        # 主要な削除リソース
        removed = changes.get("removed", {})
        if removed:
            md_content.append("## 主要な削除リソース")
            md_content.append("")
            
            # リソースタイプごとにソートして表示
            for resource_type, resources in sorted(removed.items()):
                if resources:
                    max_display = min(5, len(resources))  # 最大5件まで表示
                    md_content.append(f"### {resource_type} ({len(resources)}件)")
                    md_content.append("")
                    
                    for i, resource in enumerate(resources[:max_display]):
                        resource_id = resource.get("ResourceId", "Unknown")
                        name = resource.get("ResourceName", "")
                        name_str = f" ({name})" if name else ""
                        
                        md_content.append(f"{i+1}. **{resource_id}**{name_str}")
                    
                    if len(resources) > max_display:
                        md_content.append(f"... 他 {len(resources) - max_display} 件")
                    
                    md_content.append("")
        
        # マークダウンファイルの保存
        md_text = "\n".join(md_content)
        output_file = os.path.join(self.reports_dir, f"changes_{start_date}_to_{end_date}.md")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_text)
        
        logger.info(f"変更レポートを {output_file} に保存しました")
        
        # HTML形式に変換（オプション）
        if output_format == "html":
            html_file = self._convert_markdown_to_html(output_file)
            return html_file
        
        return output_file
        
    def generate_cost_report(self, output_format: str = "markdown") -> str:
        """
        コストレポートを生成（オプション）
        
        Args:
            output_format (str): 出力形式 (markdown, html)
            
        Returns:
            str: 生成したレポートファイルのパス
        """
        logger.info(f"コストレポートの生成を開始します (形式: {output_format})")
        
        # コストデータの取得（この実装では仮のデータを使用）
        # 実際の実装では、Cost Explorer API からデータを取得するなどが必要
        
        # サンプルコストデータ（実際の実装ではここを適切に変更すること）
        cost_data = {
            "total_monthly_cost": 1250.75,
            "service_costs": {
                "EC2": 450.23,
                "RDS": 320.15,
                "S3": 125.75,
                "Lambda": 55.30,
                "CloudFront": 95.42,
                "Others": 203.90
            },
            "cost_by_tag": {
                "Environment": {
                    "Production": 750.45,
                    "Staging": 320.10,
                    "Development": 180.20
                },
                "Project": {
                    "Main": 820.35,
                    "Secondary": 430.40
                }
            },
            "month": datetime.now().strftime('%Y-%m')
        }
        
        # マークダウンレポートの生成
        md_content = []
        
        # ヘッダー
        md_content.append("# AWS リソースコストレポート")
        md_content.append(f"生成日時: {datetime.now().isoformat()}")
        md_content.append(f"対象月: {cost_data['month']}")
        md_content.append("")
        
        # 月次コスト総額
        md_content.append("## 月次コスト総額")
        md_content.append("")
        md_content.append(f"**合計: ${cost_data['total_monthly_cost']:.2f}**")
        md_content.append("")
        
        # サービス別コスト
        md_content.append("## サービス別コスト")
        md_content.append("")
        md_content.append("| サービス | コスト | 割合 |")
        md_content.append("|----------|--------|------|")
        
        for service, cost in sorted(cost_data['service_costs'].items(), key=lambda x: x[1], reverse=True):
            percentage = (cost / cost_data['total_monthly_cost']) * 100
            md_content.append(f"| {service} | ${cost:.2f} | {percentage:.2f}% |")
        
        md_content.append("")
        
        # タグ別コスト
        md_content.append("## タグ別コスト")
        md_content.append("")
        
        for tag_key, tag_values in cost_data['cost_by_tag'].items():
            md_content.append(f"### タグ: {tag_key}")
            md_content.append("")
            md_content.append("| 値 | コスト | 割合 |")
            md_content.append("|-----|--------|------|")
            
            for value, cost in sorted(tag_values.items(), key=lambda x: x[1], reverse=True):
                percentage = (cost / cost_data['total_monthly_cost']) * 100
                md_content.append(f"| {value} | ${cost:.2f} | {percentage:.2f}% |")
            
            md_content.append("")
        
        # マークダウンファイルの保存
        md_text = "\n".join(md_content)
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.reports_dir, f"cost_report_{cost_data['month']}_{timestamp}.md")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_text)
        
        logger.info(f"コストレポートを {output_file} に保存しました")
        
        return output_file

    def _convert_markdown_to_html(self, markdown_file: str) -> str:
        """
        マークダウンファイルをHTMLに変換
        
        Args:
            markdown_file (str): マークダウンファイルのパス
            
        Returns:
            str: 生成したHTMLファイルのパス
        """
        try:
            import markdown
            from markdown.extensions.tables import TableExtension
        except ImportError:
            logger.error("markdown パッケージがインストールされていません。pip install markdown でインストールしてください。")
            return markdown_file
        
        logger.info(f"マークダウンファイル {markdown_file} をHTMLに変換します")
        
        # マークダウンファイルの読み込み
        with open(markdown_file, 'r', encoding='utf-8') as f:
            md_text = f.read()
        
        # マークダウンをHTMLに変換
        html = markdown.markdown(md_text, extensions=['tables'])
        
        # HTMLテンプレート
        html_template = f"""<\!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AWS リソースレポート</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3 {{
            color: #0066cc;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f2f2f2;
        }}
    </style>
</head>
<body>
    {html}
</body>
</html>
"""
        
        # HTMLファイルの保存
        html_file = os.path.splitext(markdown_file)[0] + ".html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        logger.info(f"HTMLファイルを {html_file} に保存しました")
        
        return html_file

    def _generate_summary_graphs(self, summary_data: Dict[str, Any]) -> List[str]:
        """
        サマリー情報からグラフを生成
        
        Args:
            summary_data (Dict): サマリーデータ
            
        Returns:
            List[str]: 生成したグラフファイルのパスリスト
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # GUIなしでMatplotlibを使用するための設定
        except ImportError:
            logger.error("matplotlib パッケージがインストールされていません。pip install matplotlib でインストールしてください。")
            return []
        
        logger.info("サマリー情報のグラフを生成します")
        
        graph_files = []
        
        # リソースサマリーデータの取得
        resource_summary = summary_data.get("resource_summary", {})
        
        if not resource_summary:
            return graph_files
        
        # グラフ保存用ディレクトリの作成
        graphs_dir = os.path.join(self.reports_dir, 'graphs')
        os.makedirs(graphs_dir, exist_ok=True)
        
        # リソース種類ごとの件数を抽出
        resource_types = []
        resource_counts = []
        
        for resource_type, data in sorted(resource_summary.items(), key=lambda x: x[1].get('count', 0), reverse=True):
            resource_types.append(resource_type)
            resource_counts.append(data.get('count', 0))
        
        # リソース数の円グラフ
        plt.figure(figsize=(10, 6))
        plt.pie(resource_counts, labels=resource_types, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
        plt.title('リソースタイプ別の分布')
        
        pie_chart_file = os.path.join(graphs_dir, f"resource_distribution_pie_{datetime.now().strftime('%Y%m%d')}.png")
        plt.savefig(pie_chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        graph_files.append(pie_chart_file)
        
        # リソース数の棒グラフ（上位10種類）
        if len(resource_types) > 0:
            # 表示するリソースタイプの数を制限
            display_limit = min(10, len(resource_types))
            
            plt.figure(figsize=(12, 6))
            plt.bar(resource_types[:display_limit], resource_counts[:display_limit])
            plt.xlabel('リソースタイプ')
            plt.ylabel('リソース数')
            plt.title('主要リソースタイプの数')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            bar_chart_file = os.path.join(graphs_dir, f"resource_count_bar_{datetime.now().strftime('%Y%m%d')}.png")
            plt.savefig(bar_chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            graph_files.append(bar_chart_file)
        
        return graph_files
    
    def _generate_trend_graphs(self, resource_trend: List[Dict[str, Any]], cost_trend: List[Dict[str, Any]]) -> List[str]:
        """
        トレンドデータからグラフを生成
        
        Args:
            resource_trend (List): リソーストレンドデータ
            cost_trend (List): コストトレンドデータ
            
        Returns:
            List[str]: 生成したグラフファイルのパスリスト
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # GUIなしでMatplotlibを使用するための設定
        except ImportError:
            logger.error("matplotlib パッケージがインストールされていません。pip install matplotlib でインストールしてください。")
            return []
        
        logger.info("トレンドデータのグラフを生成します")
        
        graph_files = []
        
        # グラフ保存用ディレクトリの作成
        graphs_dir = os.path.join(self.reports_dir, 'graphs')
        os.makedirs(graphs_dir, exist_ok=True)
        
        # リソース数トレンドグラフ
        if resource_trend:
            plt.figure(figsize=(12, 6))
            
            # 日付とリソース総数の抽出
            dates = [entry.get("date") for entry in resource_trend]
            total_resources = [entry.get("total_resources", 0) for entry in resource_trend]
            
            # 総リソース数のプロット
            plt.plot(dates, total_resources, marker='o', linestyle='-', linewidth=2, label='総リソース数')
            
            # 主要リソースタイプのプロット
            resource_types = {}
            for entry in resource_trend:
                for resource_type, count in entry.get("resource_counts", {}).items():
                    if resource_type not in resource_types:
                        resource_types[resource_type] = []
                    resource_types[resource_type].append(count)
            
            # 上位5種類のリソースタイプを選択
            top_resources = sorted(resource_types.items(), key=lambda x: sum(x[1]), reverse=True)[:5]
            
            # 各リソースタイプのプロット
            for resource_type, counts in top_resources:
                plt.plot(dates, counts, marker='.', linestyle='--', label=resource_type)
            
            plt.xlabel('日付')
            plt.ylabel('リソース数')
            plt.title('リソース数の推移')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend()
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            resource_trend_file = os.path.join(graphs_dir, f"resource_trend_{datetime.now().strftime('%Y%m%d')}.png")
            plt.savefig(resource_trend_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            graph_files.append(resource_trend_file)
        
        # コストトレンドグラフ
        if cost_trend:
            plt.figure(figsize=(12, 6))
            
            # 日付とコスト合計の抽出
            dates = [entry.get("date") for entry in cost_trend]
            total_costs = [entry.get("total_cost", 0) for entry in cost_trend]
            
            # コスト合計のプロット
            plt.plot(dates, total_costs, marker='o', linestyle='-', linewidth=2, color='red', label='総コスト')
            
            # サービス別コスト
            service_costs = {}
            for entry in cost_trend:
                for service, cost in entry.get("costs", {}).items():
                    if service not in service_costs:
                        service_costs[service] = []
                    service_costs[service].append(cost)
            
            # 上位5種類のサービスを選択
            top_services = sorted(service_costs.items(), key=lambda x: sum(x[1]), reverse=True)[:5]
            
            # 各サービスのプロット
            for service, costs in top_services:
                plt.plot(dates, costs, marker='.', linestyle='--', label=service)
            
            plt.xlabel('日付')
            plt.ylabel('コスト ($)')
            plt.title('月次コストの推移')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend()
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            cost_trend_file = os.path.join(graphs_dir, f"cost_trend_{datetime.now().strftime('%Y%m%d')}.png")
            plt.savefig(cost_trend_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            graph_files.append(cost_trend_file)
        
        return graph_files
    
    def _generate_cost_graphs(self, cost_data: Dict[str, Any]) -> List[str]:
        """
        コストデータからグラフを生成
        
        Args:
            cost_data (Dict): コストデータ
            
        Returns:
            List[str]: 生成したグラフファイルのパスリスト
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # GUIなしでMatplotlibを使用するための設定
        except ImportError:
            logger.error("matplotlib パッケージがインストールされていません。pip install matplotlib でインストールしてください。")
            return []
        
        logger.info("コストデータのグラフを生成します")
        
        graph_files = []
        
        # グラフ保存用ディレクトリの作成
        graphs_dir = os.path.join(self.reports_dir, 'graphs')
        os.makedirs(graphs_dir, exist_ok=True)
        
        # サービス別コストの円グラフ
        service_costs = cost_data.get("service_costs", {})
        if service_costs:
            plt.figure(figsize=(10, 6))
            
            # サービス名とコストを抽出
            services = []
            costs = []
            
            for service, cost in sorted(service_costs.items(), key=lambda x: x[1], reverse=True):
                services.append(service)
                costs.append(cost)
            
            plt.pie(costs, labels=services, autopct='%1.1f%%', startangle=90)
            plt.axis('equal')
            plt.title('サービス別コスト分布')
            
            service_pie_file = os.path.join(graphs_dir, f"service_cost_pie_{cost_data.get('month', datetime.now().strftime('%Y-%m'))}.png")
            plt.savefig(service_pie_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            graph_files.append(service_pie_file)
        
        # タグ別コストの棒グラフ
        cost_by_tag = cost_data.get("cost_by_tag", {})
        for tag_key, tag_values in cost_by_tag.items():
            if tag_values:
                plt.figure(figsize=(10, 6))
                
                # タグ値とコストを抽出
                values = []
                values_costs = []
                
                for value, cost in sorted(tag_values.items(), key=lambda x: x[1], reverse=True):
                    values.append(value)
                    values_costs.append(cost)
                
                plt.bar(values, values_costs)
                plt.xlabel(f'タグ: {tag_key}')
                plt.ylabel('コスト ($)')
                plt.title(f'タグ "{tag_key}" 別コスト分布')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                
                tag_bar_file = os.path.join(graphs_dir, f"tag_cost_bar_{tag_key}_{cost_data.get('month', datetime.now().strftime('%Y-%m'))}.png")
                plt.savefig(tag_bar_file, dpi=300, bbox_inches='tight')
                plt.close()
                
                graph_files.append(tag_bar_file)
        
        return graph_files

# 既存の generate_summary_report メソッドにグラフ生成部分を追加するためのコード（既存メソッドの修正）
# 実際には既存のクラスに以下の機能を追加する必要があるが、ファイル更新の問題を回避するためにここに記載

# 以下のコードは generate_summary_report の修正版です
"""
        # マークダウンファイルの保存
        md_text = "\n".join(md_content)
        output_file = os.path.join(self.reports_dir, f"resource_summary_{metadata.get('source_date')}.md")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_text)
        
        logger.info(f"サマリーレポートを {output_file} に保存しました")
        
        # グラフの生成（オプション）
        if self.config.get("include_graphs", True):
            graph_files = self._generate_summary_graphs(summary_data)
            logger.info(f"{len(graph_files)} 個のグラフを生成しました")
            
            # HTML形式の場合、HTMLファイルにグラフへのリンクを追加
            if output_format == "html":
                html_file = self._convert_markdown_to_html(output_file)
                return html_file
        
        return output_file
"""

# 以下のコードは generate_trend_report の修正版です
"""
        # マークダウンファイルの保存
        md_text = "\n".join(md_content)
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.reports_dir, f"resource_trends_{timestamp}.md")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_text)
        
        logger.info(f"トレンドレポートを {output_file} に保存しました")
        
        # グラフの生成（オプション）
        if self.config.get("include_graphs", True):
            graph_files = self._generate_trend_graphs(resource_trend, cost_trend)
            logger.info(f"{len(graph_files)} 個のグラフを生成しました")
            
            # HTML形式の場合、HTMLファイルにグラフへのリンクを追加
            if output_format == "html":
                html_file = self._convert_markdown_to_html(output_file)
                return html_file
        
        return output_file
"""

# 以下のコードは generate_cost_report の修正版です
"""
        # マークダウンファイルの保存
        md_text = "\n".join(md_content)
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.reports_dir, f"cost_report_{cost_data['month']}_{timestamp}.md")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_text)
        
        logger.info(f"コストレポートを {output_file} に保存しました")
        
        # グラフの生成（オプション）
        if self.config.get("include_graphs", True):
            graph_files = self._generate_cost_graphs(cost_data)
            logger.info(f"{len(graph_files)} 個のグラフを生成しました")
            
            # HTML形式の場合、HTMLファイルにグラフへのリンクを追加
            if output_format == "html":
                html_file = self._convert_markdown_to_html(output_file)
                return html_file
        
        return output_file
"""
