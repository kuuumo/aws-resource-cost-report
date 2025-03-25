#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWS リソースコレクターパッケージ
"""

from typing import Dict, List, Any, Optional, TypedDict, Union

# リソースの標準データ構造の定義
class ResourceData(TypedDict, total=False):
    # 必須フィールド
    ResourceId: str  # リソース識別子
    ResourceName: Optional[str]  # リソース名（ある場合）
    ResourceType: str  # リソースタイプ
    Service: str  # AWSサービス名
    Region: str  # リージョン（グローバルリソースの場合は "global"）
    
    # オプションフィールド
    ARN: Optional[str]  # ARN
    CreationDate: Optional[str]  # 作成日時
    LastModified: Optional[str]  # 最終更新日時
    Size: Optional[Union[int, float]]  # サイズ（適用可能な場合）
    Status: Optional[str]  # ステータス
    VpcId: Optional[str]  # VPC ID（適用可能な場合）
    AZ: Optional[str]  # アベイラビリティゾーン（適用可能な場合）
    Tags: Optional[List[Dict[str, str]]]  # タグリスト
    
    # コスト関連情報
    EstimatedMonthlyCost: Optional[float]  # 推定月額コスト
    PricingModel: Optional[str]  # 料金モデル（On-Demand, Reserved, etc.）
    
    # その他の属性（サービス固有の属性はここに追加）
    Attributes: Optional[Dict[str, Any]]
