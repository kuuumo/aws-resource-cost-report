#!/usr/bin/env python3

import os
import logging
import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    AWS のリソースとコスト情報からレポートを生成するクラス
    """
    
    def __init__(self, cost_data, resource_data, start_date, end_date):
        """
        初期化
        
        Args:
            cost_data (dict): Cost Explorer から取得したコストデータ
            resource_data (dict): Resource Explorer から取得したリソースデータ
            start_date (str): 期間の開始日 (YYYY-MM-DD形式)
            end_date (str): 期間の終了日 (YYYY-MM-DD形式)
        """
        self.cost_data = cost_data
        self.resource_data = resource_data
        self.start_date = start_date
        self.end_date = end_date
    
    def generate(self, output_file):
        """
        マークダウン形式でレポートを生成
        
        Args:
            output_file (str or Path): 出力ファイルパス
        
        Returns:
            bool: 成功した場合は True
        """
        try:
            # レポートの各セクションを生成
            sections = [
                self._generate_header(),
                self._generate_summary(),
                self._generate_service_costs(),
                self._generate_region_costs(),
                self._generate_ec2_instances(),
                self._generate_rds_instances(),
                self._generate_other_resources(),
                self._generate_daily_trends(),
                self._generate_optimization_recommendations()
            ]
            
            # セクションを結合してレポートを作成
            report_content = '\n\n'.join(sections)
            
            # ファイルに書き込み
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Report successfully generated: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            return False
    
    def _generate_header(self):
        """レポートのヘッダーを生成"""
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return (
            f"# AWS リソース・コスト レポート\n"
            f"\n"
            f"**期間**: {self.start_date} から {self.end_date}\n"
            f"**作成日時**: {current_time}\n"
        )
    
    def _generate_summary(self):
        """コスト概要セクションを生成"""
        total_cost = self.cost_data.get('total_cost', {})
        comparison = self.cost_data.get('previous_period_comparison', {})
        
        amount = total_cost.get('amount', 0)
        currency = total_cost.get('currency', 'USD')
        
        change_amount = comparison.get('change_amount', 0)
        change_percent = comparison.get('change_percent', 0)
        prev_start = comparison.get('previous_period', {}).get('start', '')
        prev_end = comparison.get('previous_period', {}).get('end', '')
        
        # 最も高いサービスを特定
        service_costs = self.cost_data.get('service_costs', [])
        top_service = service_costs[0] if service_costs else {'service_name': '不明', 'amount': 0}
        
        # 変化の表記用の矢印とスタイル
        if change_percent > 0:
            change_arrow = "↑"
            change_style = "🔴"
        elif change_percent < 0:
            change_arrow = "↓"
            change_style = "🟢"
        else:
            change_arrow = "→"
            change_style = "⚪"
        
        return (
            f"## 概要\n"
            f"\n"
            f"### 総コスト\n"
            f"\n"
            f"**合計**: {amount:.2f} {currency}\n"
            f"\n"
            f"**前期間 ({prev_start} ~ {prev_end}) 比較**: {change_style} {change_amount:.2f} {currency} ({change_arrow} {change_percent:.2f}%)\n"
            f"\n"
            f"**最大コストサービス**: {top_service['service_name']} ({top_service['amount']:.2f} {currency})\n"
        )
    
    def _generate_service_costs(self):
        """サービス別コストセクションを生成"""
        service_costs = self.cost_data.get('service_costs', [])
        
        if not service_costs:
            return "## サービス別コスト\n\nサービス別コストデータはありません。"
        
        # サービス別コストの表を作成
        table = (
            "## サービス別コスト\n"
            "\n"
            "| サービス | コスト | 全体比 |\n"
            "| --- | ---: | ---: |\n"
        )
        
        total_amount = self.cost_data.get('total_cost', {}).get('amount', 0)
        currency = self.cost_data.get('total_cost', {}).get('currency', 'USD')
        
        for service in service_costs:
            name = service['service_name']
            amount = service['amount']
            percent = (amount / total_amount * 100) if total_amount > 0 else 0
            
            table += f"| {name} | {amount:.2f} {currency} | {percent:.2f}% |\n"
        
        return table
    
    def _generate_region_costs(self):
        """リージョン別コストセクションを生成"""
        region_costs = self.cost_data.get('region_costs', [])
        
        if not region_costs:
            return "## リージョン別コスト\n\nリージョン別コストデータはありません。"
        
        # リージョン別コストの表を作成
        table = (
            "## リージョン別コスト\n"
            "\n"
            "| リージョン | コスト | 全体比 |\n"
            "| --- | ---: | ---: |\n"
        )
        
        total_amount = self.cost_data.get('total_cost', {}).get('amount', 0)
        currency = self.cost_data.get('total_cost', {}).get('currency', 'USD')
        
        for region in region_costs:
            name = region['region_name']
            amount = region['amount']
            percent = (amount / total_amount * 100) if total_amount > 0 else 0
            
            table += f"| {name} | {amount:.2f} {currency} | {percent:.2f}% |\n"
        
        return table
    
    def _generate_ec2_instances(self):
        """EC2インスタンス詳細セクションを生成"""
        ec2_instances = self.resource_data.get('ec2_instances', [])
        ec2_costs = self.cost_data.get('instance_costs', {}).get('ec2', [])
        
        if not ec2_instances:
            return "## EC2インスタンス詳細\n\nEC2インスタンスのデータはありません。"
        
        # インスタンスタイプごとのコスト辞書を作成
        cost_by_type = {}
        for cost in ec2_costs:
            cost_by_type[cost['instance_type']] = cost['amount']
        
        # EC2インスタンスの表を作成
        table = (
            "## EC2インスタンス詳細\n"
            "\n"
            "| インスタンスID | 名前 | タイプ | 状態 | リージョン | 起動日時 | 推定月間コスト |\n"
            "| --- | --- | --- | --- | --- | --- | ---: |\n"
        )
        
        currency = self.cost_data.get('total_cost', {}).get('currency', 'USD')
        
        for instance in ec2_instances:
            instance_id = instance['id']
            name = instance['name'] or 'N/A'
            instance_type = instance['type']
            state = instance['state']
            region = instance['region']
            launch_time = instance['launch_time'].split('T')[0] if instance['launch_time'] else 'N/A'
            
            # インスタンスタイプのコストデータがある場合は表示
            estimated_cost = cost_by_type.get(instance_type, 'N/A')
            if estimated_cost != 'N/A':
                estimated_cost = f"{estimated_cost:.2f} {currency}"
            
            table += f"| {instance_id} | {name} | {instance_type} | {state} | {region} | {launch_time} | {estimated_cost} |\n"
        
        return table
    
    def _generate_rds_instances(self):
        """RDSインスタンス詳細セクションを生成"""
        rds_instances = self.resource_data.get('rds_instances', [])
        rds_costs = self.cost_data.get('instance_costs', {}).get('rds', [])
        
        if not rds_instances:
            return "## RDSインスタンス詳細\n\nRDSインスタンスのデータはありません。"
        
        # インスタンスタイプごとのコスト辞書を作成
        cost_by_type = {}
        for cost in rds_costs:
            cost_by_type[cost['instance_type']] = cost['amount']
        
        # RDSインスタンスの表を作成
        table = (
            "## RDSインスタンス詳細\n"
            "\n"
            "| インスタンスID | エンジン | タイプ | 状態 | リージョン | 作成日時 | ストレージ(GB) | マルチAZ | 推定月間コスト |\n"
            "| --- | --- | --- | --- | --- | --- | ---: | --- | ---: |\n"
        )
        
        currency = self.cost_data.get('total_cost', {}).get('currency', 'USD')
        
        for instance in rds_instances:
            instance_id = instance['id']
            engine = f"{instance['engine']} {instance['version']}"
            instance_class = instance['class']
            status = instance['status']
            region = instance['region']
            create_time = instance['create_time'].split('T')[0] if instance['create_time'] else 'N/A'
            storage = instance['storage']
            multi_az = "はい" if instance['multi_az'] else "いいえ"
            
            # インスタンスタイプのコストデータがある場合は表示
            estimated_cost = cost_by_type.get(instance_class, 'N/A')
            if estimated_cost != 'N/A':
                estimated_cost = f"{estimated_cost:.2f} {currency}"
            
            table += f"| {instance_id} | {engine} | {instance_class} | {status} | {region} | {create_time} | {storage} | {multi_az} | {estimated_cost} |\n"
        
        return table
    
    def _generate_other_resources(self):
        """その他のリソース詳細セクションを生成"""
        sections = []
        
        # S3バケット
        s3_buckets = self.resource_data.get('s3_buckets', [])
        if s3_buckets:
            s3_table = (
                "## S3バケット詳細\n"
                "\n"
                "| バケット名 | リージョン | 作成日時 | サイズ |\n"
                "| --- | --- | --- | ---: |\n"
            )
            
            for bucket in s3_buckets:
                name = bucket['name']
                region = bucket['region']
                creation_date = bucket['creation_date'].split('T')[0]
                
                # サイズを適切な単位に変換
                size_bytes = bucket['size_bytes']
                if size_bytes >= 1024 ** 4:
                    size_str = f"{size_bytes / (1024 ** 4):.2f} TB"
                elif size_bytes >= 1024 ** 3:
                    size_str = f"{size_bytes / (1024 ** 3):.2f} GB"
                elif size_bytes >= 1024 ** 2:
                    size_str = f"{size_bytes / (1024 ** 2):.2f} MB"
                elif size_bytes >= 1024:
                    size_str = f"{size_bytes / 1024:.2f} KB"
                else:
                    size_str = f"{size_bytes} Bytes"
                
                s3_table += f"| {name} | {region} | {creation_date} | {size_str} |\n"
            
            sections.append(s3_table)
        
        # ElastiCacheクラスター
        elasticache_clusters = self.resource_data.get('elasticache_clusters', [])
        if elasticache_clusters:
            ec_table = (
                "## ElastiCacheクラスター詳細\n"
                "\n"
                "| クラスターID | エンジン | ノードタイプ | ノード数 | 状態 | リージョン | 作成日時 |\n"
                "| --- | --- | --- | ---: | --- | --- | --- |\n"
            )
            
            for cluster in elasticache_clusters:
                cluster_id = cluster['id']
                engine = f"{cluster['engine']} {cluster['version']}"
                node_type = cluster['node_type']
                num_nodes = cluster['num_nodes']
                status = cluster['status']
                region = cluster['region']
                create_time = cluster['create_time'].split('T')[0] if cluster['create_time'] else 'N/A'
                
                ec_table += f"| {cluster_id} | {engine} | {node_type} | {num_nodes} | {status} | {region} | {create_time} |\n"
            
            sections.append(ec_table)
        
        # ロードバランサー
        lb_data = self.resource_data.get('load_balancers', {})
        classic_lbs = lb_data.get('classic', [])
        application_lbs = lb_data.get('application', [])
        network_lbs = lb_data.get('network', [])
        
        if classic_lbs or application_lbs or network_lbs:
            lb_table = (
                "## ロードバランサー詳細\n"
                "\n"
                "| 名前 | タイプ | DNSName | スキーム | リージョン | 作成日時 |\n"
                "| --- | --- | --- | --- | --- | --- |\n"
            )
            
            # Classicロードバランサー
            for lb in classic_lbs:
                name = lb['name']
                lb_type = "Classic"
                dns_name = lb['dns_name']
                scheme = lb['scheme']
                region = lb['region']
                created_time = lb['created_time'].split('T')[0]
                
                lb_table += f"| {name} | {lb_type} | {dns_name} | {scheme} | {region} | {created_time} |\n"
            
            # Application Load Balancer
            for lb in application_lbs:
                name = lb['name']
                lb_type = "Application"
                dns_name = lb['dns_name']
                scheme = lb['scheme']
                region = lb['region']
                created_time = lb['created_time'].split('T')[0]
                
                lb_table += f"| {name} | {lb_type} | {dns_name} | {scheme} | {region} | {created_time} |\n"
            
            # Network Load Balancer
            for lb in network_lbs:
                name = lb['name']
                lb_type = "Network"
                dns_name = lb['dns_name']
                scheme = lb['scheme']
                region = lb['region']
                created_time = lb['created_time'].split('T')[0]
                
                lb_table += f"| {name} | {lb_type} | {dns_name} | {scheme} | {region} | {created_time} |\n"
            
            sections.append(lb_table)
        
        # セクションを結合
        if sections:
            return '\n\n'.join(sections)
        else:
            return "## その他のリソース詳細\n\nその他のリソースデータはありません。"
    
    def _generate_daily_trends(self):
        """日次コストトレンドセクションを生成"""
        daily_costs = self.cost_data.get('daily_costs', [])
        
        if not daily_costs:
            return "## 日次コストトレンド\n\n日次コストデータはありません。"
        
        # 日次コストのテーブルを作成
        table = (
            "## 日次コストトレンド\n"
            "\n"
            "| 日付 | コスト |\n"
            "| --- | ---: |\n"
        )
        
        currency = self.cost_data.get('total_cost', {}).get('currency', 'USD')
        
        for day in daily_costs:
            date = day['date']
            amount = day['amount']
            
            table += f"| {date} | {amount:.2f} {currency} |\n"
        
        return table
    
    def _generate_optimization_recommendations(self):
        """コスト最適化の推奨事項セクションを生成"""
        recommendations = []
        
        # EC2インスタンスの最適化推奨事項
        ec2_instances = self.resource_data.get('ec2_instances', [])
        if ec2_instances:
            # 停止中のインスタンスを検出
            stopped_instances = [i for i in ec2_instances if i['state'] == 'stopped']
            if stopped_instances:
                stopped_names = ', '.join([f"{i['id']} ({i['name']})" for i in stopped_instances[:5]])
                if len(stopped_instances) > 5:
                    stopped_names += f" 他 {len(stopped_instances) - 5} 件"
                
                recommendations.append(f"- **停止中のEC2インスタンス**: {len(stopped_instances)}個のインスタンスが停止状態です。不要であれば削除を検討してください: {stopped_names}")
            
            # 古いインスタンスタイプを検出
            old_gen_prefixes = ['t1.', 'm1.', 'm2.', 'c1.', 'c3.', 'r3.', 'i2.', 'hs1.', 'g2.', 'cr1.']
            old_instances = [i for i in ec2_instances if any(i['type'].startswith(prefix) for prefix in old_gen_prefixes)]
            if old_instances:
                old_names = ', '.join([f"{i['id']} ({i['type']})" for i in old_instances[:5]])
                if len(old_instances) > 5:
                    old_names += f" 他 {len(old_instances) - 5} 件"
                
                recommendations.append(f"- **旧世代のEC2インスタンスタイプ**: {len(old_instances)}個のインスタンスが旧世代のインスタンスタイプを使用しています。新しい世代へのアップグレードでコスト削減や性能向上が見込めます: {old_names}")
        
        # RDSインスタンスの最適化推奨事項
        rds_instances = self.resource_data.get('rds_instances', [])
        if rds_instances:
            # マルチAZ構成でないインスタンスを検出（本番環境では可用性向上のためマルチAZが推奨）
            non_multi_az = [i for i in rds_instances if not i['multi_az']]
            if non_multi_az:
                non_multi_az_names = ', '.join([i['id'] for i in non_multi_az[:5]])
                if len(non_multi_az) > 5:
                    non_multi_az_names += f" 他 {len(non_multi_az) - 5} 件"
                
                recommendations.append(f"- **シングルAZ RDSインスタンス**: {len(non_multi_az)}個のRDSインスタンスがシングルAZ構成です。本番環境では可用性向上のためにマルチAZ構成を検討してください: {non_multi_az_names}")
        
        # その他の一般的な推奨事項
        recommendations.extend([
            "- **リザーブドインスタンスの活用**: 安定した使用が見込まれるインスタンスに対しては、リザーブドインスタンスの購入を検討してください（最大75%のコスト削減）。",
            "- **自動スケーリングの設定**: 使用パターンに基づいてリソースを自動的にスケールする設定を行うことで、必要なときだけリソースを確保できます。",
            "- **S3のストレージクラスの最適化**: アクセス頻度の低いデータは、Standard-IA, One Zone-IA, Glacierなどの低コストストレージに移行することでコスト削減が可能です。",
            "- **未使用EBSボリュームの削除**: アタッチされていないEBSボリュームを定期的に確認し、不要なものは削除してください。"
        ])
        
        # レコメンデーションを結合
        if recommendations:
            return "## コスト最適化の推奨事項\n\n" + "\n\n".join(recommendations)
        else:
            return "## コスト最適化の推奨事項\n\n推奨事項はありません。"
