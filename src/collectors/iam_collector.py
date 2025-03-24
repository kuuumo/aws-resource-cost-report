#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
IAM情報収集モジュール
"""

import logging
from typing import Dict, List, Any
from .base_collector import BaseCollector

# ロギングの設定
logger = logging.getLogger(__name__)

class IAMCollector(BaseCollector):
    """IAM情報を収集するクラス"""
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        IAM情報を収集
        
        Returns:
            Dict: IAM情報
        """
        logger.info("IAM情報の収集を開始します")
        results = {}
        
        try:
            # IAMはグローバルサービス
            iam_client = self.get_client('iam')
            
            # ユーザー情報を取得
            users = self._collect_users(iam_client)
            if users:
                results['IAM_Users'] = users
            
            # グループ情報を取得
            groups = self._collect_groups(iam_client)
            if groups:
                results['IAM_Groups'] = groups
            
            # ロール情報を取得
            roles = self._collect_roles(iam_client)
            if roles:
                results['IAM_Roles'] = roles
            
            # ポリシー情報を取得
            policies = self._collect_policies(iam_client)
            if policies:
                results['IAM_Policies'] = policies
                
            # インスタンスプロファイル情報を取得
            instance_profiles = self._collect_instance_profiles(iam_client)
            if instance_profiles:
                results['IAM_InstanceProfiles'] = instance_profiles
                
        except Exception as e:
            logger.error(f"IAM情報収集中にエラー発生: {str(e)}")
        
        return results
    
    def _collect_users(self, iam_client) -> List[Dict[str, Any]]:
        """IAMユーザー情報を収集"""
        logger.info("IAMユーザー情報を収集しています")
        users = []
        
        try:
            paginator = iam_client.get_paginator('list_users')
            
            for page in paginator.paginate():
                for user in page.get('Users', []):
                    user_name = user.get('UserName', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if user_name:
                            tag_response = iam_client.list_user_tags(
                                UserName=user_name
                            )
                            tags = tag_response.get('Tags', [])
                    except Exception as e:
                        logger.warning(f"IAMユーザー '{user_name}' のタグ取得エラー: {str(e)}")
                    
                    # 所属グループ情報を取得
                    groups = []
                    try:
                        group_response = iam_client.list_groups_for_user(
                            UserName=user_name
                        )
                        groups = [group.get('GroupName', '') for group in group_response.get('Groups', [])]
                    except Exception as e:
                        logger.warning(f"IAMユーザー '{user_name}' のグループ情報取得エラー: {str(e)}")
                    
                    # ユーザー情報を追加
                    users.append({
                        'ResourceId': user.get('UserId', ''),
                        'ResourceName': user_name,
                        'ResourceType': 'User',
                        'Arn': user.get('Arn', ''),
                        'CreateDate': user.get('CreateDate', ''),
                        'PasswordLastUsed': user.get('PasswordLastUsed', ''),
                        'Path': user.get('Path', ''),
                        'Groups': groups,
                        'Tags': tags
                    })
            
            logger.info(f"IAMユーザー: {len(users)}件取得")
        except Exception as e:
            logger.error(f"IAMユーザー情報収集中にエラー発生: {str(e)}")
        
        return users
    
    def _collect_groups(self, iam_client) -> List[Dict[str, Any]]:
        """IAMグループ情報を収集"""
        logger.info("IAMグループ情報を収集しています")
        groups = []
        
        try:
            paginator = iam_client.get_paginator('list_groups')
            
            for page in paginator.paginate():
                for group in page.get('Groups', []):
                    group_name = group.get('GroupName', '名前なし')
                    
                    # アタッチされたポリシー情報を取得
                    attached_policies = []
                    try:
                        policy_response = iam_client.list_attached_group_policies(
                            GroupName=group_name
                        )
                        attached_policies = [policy.get('PolicyName', '') for policy in policy_response.get('AttachedPolicies', [])]
                    except Exception as e:
                        logger.warning(f"IAMグループ '{group_name}' のポリシー情報取得エラー: {str(e)}")
                    
                    # グループ情報を追加
                    groups.append({
                        'ResourceId': group.get('GroupId', ''),
                        'ResourceName': group_name,
                        'ResourceType': 'Group',
                        'Arn': group.get('Arn', ''),
                        'CreateDate': group.get('CreateDate', ''),
                        'Path': group.get('Path', ''),
                        'AttachedPolicies': attached_policies
                    })
            
            logger.info(f"IAMグループ: {len(groups)}件取得")
        except Exception as e:
            logger.error(f"IAMグループ情報収集中にエラー発生: {str(e)}")
        
        return groups
    
    def _collect_roles(self, iam_client) -> List[Dict[str, Any]]:
        """IAMロール情報を収集"""
        logger.info("IAMロール情報を収集しています")
        roles = []
        
        try:
            paginator = iam_client.get_paginator('list_roles')
            
            for page in paginator.paginate():
                for role in page.get('Roles', []):
                    role_name = role.get('RoleName', '名前なし')
                    
                    # タグを取得
                    tags = []
                    try:
                        if role_name:
                            tag_response = iam_client.list_role_tags(
                                RoleName=role_name
                            )
                            tags = tag_response.get('Tags', [])
                    except Exception as e:
                        logger.warning(f"IAMロール '{role_name}' のタグ取得エラー: {str(e)}")
                    
                    # アタッチされたポリシー情報を取得
                    attached_policies = []
                    try:
                        policy_response = iam_client.list_attached_role_policies(
                            RoleName=role_name
                        )
                        attached_policies = [policy.get('PolicyName', '') for policy in policy_response.get('AttachedPolicies', [])]
                    except Exception as e:
                        logger.warning(f"IAMロール '{role_name}' のポリシー情報取得エラー: {str(e)}")
                    
                    # ロール情報を追加
                    roles.append({
                        'ResourceId': role.get('RoleId', ''),
                        'ResourceName': role_name,
                        'ResourceType': 'Role',
                        'Arn': role.get('Arn', ''),
                        'CreateDate': role.get('CreateDate', ''),
                        'Path': role.get('Path', ''),
                        'AssumeRolePolicyDocument': role.get('AssumeRolePolicyDocument', {}),
                        'Description': role.get('Description', ''),
                        'MaxSessionDuration': role.get('MaxSessionDuration', 3600),
                        'AttachedPolicies': attached_policies,
                        'Tags': tags
                    })
            
            logger.info(f"IAMロール: {len(roles)}件取得")
        except Exception as e:
            logger.error(f"IAMロール情報収集中にエラー発生: {str(e)}")
        
        return roles
    
    def _collect_policies(self, iam_client) -> List[Dict[str, Any]]:
        """IAMポリシー情報を収集"""
        logger.info("IAMポリシー情報を収集しています")
        policies = []
        
        try:
            # カスタマー管理ポリシーのみ取得（AWS管理ポリシーは除外）
            paginator = iam_client.get_paginator('list_policies')
            
            for page in paginator.paginate(Scope='Local'):
                for policy in page.get('Policies', []):
                    policy_name = policy.get('PolicyName', '名前なし')
                    
                    # ポリシー情報を追加
                    policies.append({
                        'ResourceId': policy.get('PolicyId', ''),
                        'ResourceName': policy_name,
                        'ResourceType': 'Policy',
                        'Arn': policy.get('Arn', ''),
                        'CreateDate': policy.get('CreateDate', ''),
                        'UpdateDate': policy.get('UpdateDate', ''),
                        'DefaultVersionId': policy.get('DefaultVersionId', ''),
                        'Path': policy.get('Path', ''),
                        'IsAttachable': policy.get('IsAttachable', True),
                        'AttachmentCount': policy.get('AttachmentCount', 0)
                    })
            
            logger.info(f"IAMポリシー（カスタマー管理）: {len(policies)}件取得")
        except Exception as e:
            logger.error(f"IAMポリシー情報収集中にエラー発生: {str(e)}")
        
        return policies
    
    def _collect_instance_profiles(self, iam_client) -> List[Dict[str, Any]]:
        """IAMインスタンスプロファイル情報を収集"""
        logger.info("IAMインスタンスプロファイル情報を収集しています")
        instance_profiles = []
        
        try:
            paginator = iam_client.get_paginator('list_instance_profiles')
            
            for page in paginator.paginate():
                for profile in page.get('InstanceProfiles', []):
                    profile_name = profile.get('InstanceProfileName', '名前なし')
                    
                    # 関連ロール情報を取得
                    roles = []
                    for role in profile.get('Roles', []):
                        roles.append(role.get('RoleName', ''))
                    
                    # インスタンスプロファイル情報を追加
                    instance_profiles.append({
                        'ResourceId': profile.get('InstanceProfileId', ''),
                        'ResourceName': profile_name,
                        'ResourceType': 'InstanceProfile',
                        'Arn': profile.get('Arn', ''),
                        'CreateDate': profile.get('CreateDate', ''),
                        'Path': profile.get('Path', ''),
                        'Roles': roles
                    })
            
            logger.info(f"IAMインスタンスプロファイル: {len(instance_profiles)}件取得")
        except Exception as e:
            logger.error(f"IAMインスタンスプロファイル情報収集中にエラー発生: {str(e)}")
        
        return instance_profiles
