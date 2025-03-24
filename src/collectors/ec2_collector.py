#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EC2リソース情報収集モジュール
"""

import logging
from typing import Dict, List, Any
from .base_collector import BaseCollector

# ロギングの設定
logger = logging.getLogger(__name__)

class EC2Collector(BaseCollector):
    """EC2リソース情報を収集するクラス"""
    
    def collect(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        EC2リソース情報を収集
        
        Returns:
            Dict: EC2リソース情報
        """
        logger.info("EC2リソース情報の収集を開始します")
        results = {}
        
        try:
            # EC2クライアントを取得
            ec2_client = self.get_client('ec2')
            
            # インスタンス情報を取得
            instances = self._collect_instances(ec2_client)
            if instances:
                results['EC2_Instances'] = instances
            
            # EBSボリューム情報を取得
            volumes = self._collect_volumes(ec2_client)
            if volumes:
                results['EC2_Volumes'] = volumes
            
            # セキュリティグループ情報を取得
            security_groups = self._collect_security_groups(ec2_client)
            if security_groups:
                results['EC2_SecurityGroups'] = security_groups
            
            # ロードバランサー情報を取得
            load_balancers = self._collect_load_balancers()
            if load_balancers:
                results['EC2_LoadBalancers'] = load_balancers
                
            # AMI情報を取得
            images = self._collect_images(ec2_client)
            if images:
                results['EC2_AMIs'] = images
            
            # VPC情報を取得
            vpcs = self._collect_vpcs(ec2_client)
            if vpcs:
                results['EC2_VPCs'] = vpcs
            
            # サブネット情報を取得
            subnets = self._collect_subnets(ec2_client)
            if subnets:
                results['EC2_Subnets'] = subnets
                
            # Elastic IP情報を取得
            eips = self._collect_elastic_ips(ec2_client)
            if eips:
                results['EC2_ElasticIPs'] = eips
                
        except Exception as e:
            logger.error(f"EC2リソース情報収集中にエラー発生: {str(e)}")
        
        return results
    
    def _collect_instances(self, ec2_client) -> List[Dict[str, Any]]:
        """EC2インスタンス情報を収集"""
        logger.info("EC2インスタンス情報を収集しています")
        instances = []
        
        try:
            paginator = ec2_client.get_paginator('describe_instances')
            for page in paginator.paginate():
                for reservation in page.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        instance_name = self.get_resource_name_from_tags(instance.get('Tags', []))
                        
                        instances.append({
                            'ResourceId': instance['InstanceId'],
                            'ResourceName': instance_name,
                            'ResourceType': 'Instance',
                            'State': instance.get('State', {}).get('Name', 'unknown'),
                            'InstanceType': instance.get('InstanceType', 'unknown'),
                            'Platform': instance.get('Platform', 'Linux/UNIX'),
                            'LaunchTime': instance.get('LaunchTime', ''),
                            'AZ': instance.get('Placement', {}).get('AvailabilityZone', ''),
                            'SubnetId': instance.get('SubnetId', ''),
                            'VpcId': instance.get('VpcId', ''),
                            'PrivateIpAddress': instance.get('PrivateIpAddress', ''),
                            'PublicIpAddress': instance.get('PublicIpAddress', ''),
                            'Tags': instance.get('Tags', [])
                        })
            
            logger.info(f"EC2インスタンス: {len(instances)}件取得")
        except Exception as e:
            logger.error(f"EC2インスタンス情報収集中にエラー発生: {str(e)}")
        
        return instances
    
    def _collect_volumes(self, ec2_client) -> List[Dict[str, Any]]:
        """EBSボリューム情報を収集"""
        logger.info("EBSボリューム情報を収集しています")
        volumes = []
        
        try:
            paginator = ec2_client.get_paginator('describe_volumes')
            for page in paginator.paginate():
                for volume in page.get('Volumes', []):
                    volume_name = self.get_resource_name_from_tags(volume.get('Tags', []))
                    
                    # アタッチメント情報
                    attachments = volume.get('Attachments', [])
                    instance_id = attachments[0].get('InstanceId', '') if attachments else ''
                    
                    volumes.append({
                        'ResourceId': volume['VolumeId'],
                        'ResourceName': volume_name,
                        'ResourceType': 'Volume',
                        'State': volume.get('State', ''),
                        'Size': volume.get('Size', 0),
                        'VolumeType': volume.get('VolumeType', ''),
                        'Iops': volume.get('Iops', 0),
                        'Throughput': volume.get('Throughput', 0),
                        'AZ': volume.get('AvailabilityZone', ''),
                        'Encrypted': volume.get('Encrypted', False),
                        'AttachedInstanceId': instance_id,
                        'CreateTime': volume.get('CreateTime', ''),
                        'Tags': volume.get('Tags', [])
                    })
            
            logger.info(f"EBSボリューム: {len(volumes)}件取得")
        except Exception as e:
            logger.error(f"EBSボリューム情報収集中にエラー発生: {str(e)}")
        
        return volumes
    
    def _collect_security_groups(self, ec2_client) -> List[Dict[str, Any]]:
        """セキュリティグループ情報を収集"""
        logger.info("セキュリティグループ情報を収集しています")
        security_groups = []
        
        try:
            paginator = ec2_client.get_paginator('describe_security_groups')
            for page in paginator.paginate():
                for sg in page.get('SecurityGroups', []):
                    sg_name = self.get_resource_name_from_tags(sg.get('Tags', []), sg.get('GroupName', '名前なし'))
                    
                    security_groups.append({
                        'ResourceId': sg['GroupId'],
                        'ResourceName': sg_name,
                        'ResourceType': 'SecurityGroup',
                        'Description': sg.get('Description', ''),
                        'VpcId': sg.get('VpcId', ''),
                        'InboundRuleCount': len(sg.get('IpPermissions', [])),
                        'OutboundRuleCount': len(sg.get('IpPermissionsEgress', [])),
                        'Tags': sg.get('Tags', [])
                    })
            
            logger.info(f"セキュリティグループ: {len(security_groups)}件取得")
        except Exception as e:
            logger.error(f"セキュリティグループ情報収集中にエラー発生: {str(e)}")
        
        return security_groups
    
    def _collect_load_balancers(self) -> List[Dict[str, Any]]:
        """ロードバランサー情報を収集"""
        logger.info("ELB情報を収集しています")
        load_balancers = []
        
        try:
            # ALB, NLB情報を取得
            elbv2_client = self.get_client('elbv2')
            
            paginator = elbv2_client.get_paginator('describe_load_balancers')
            for page in paginator.paginate():
                for lb in page.get('LoadBalancers', []):
                    # ロードバランサーのタグを取得
                    tags = []
                    try:
                        tag_response = elbv2_client.describe_tags(
                            ResourceArns=[lb['LoadBalancerArn']]
                        )
                        for tag_desc in tag_response.get('TagDescriptions', []):
                            if tag_desc['ResourceArn'] == lb['LoadBalancerArn']:
                                tags = tag_desc.get('Tags', [])
                    except Exception as e:
                        logger.warning(f"ロードバランサー '{lb['LoadBalancerName']}' のタグ取得エラー: {str(e)}")
                    
                    lb_name = self.get_resource_name_from_tags(tags, lb.get('LoadBalancerName', '名前なし'))
                    
                    load_balancers.append({
                        'ResourceId': lb['LoadBalancerArn'],
                        'ResourceName': lb_name,
                        'ResourceType': 'LoadBalancer',
                        'DNSName': lb.get('DNSName', ''),
                        'Type': lb.get('Type', ''),
                        'Scheme': lb.get('Scheme', ''),
                        'VpcId': lb.get('VpcId', ''),
                        'State': lb.get('State', {}).get('Code', ''),
                        'AZs': [az['ZoneName'] for az in lb.get('AvailabilityZones', [])],
                        'SecurityGroups': lb.get('SecurityGroups', []),
                        'Tags': tags
                    })
            
            # CLB (Classic Load Balancer) 情報を取得
            try:
                elb_client = self.get_client('elb')
                
                paginator = elb_client.get_paginator('describe_load_balancers')
                for page in paginator.paginate():
                    for lb in page.get('LoadBalancerDescriptions', []):
                        # CLBのタグを取得
                        tags = []
                        try:
                            tag_response = elb_client.describe_tags(
                                LoadBalancerNames=[lb['LoadBalancerName']]
                            )
                            for tag_desc in tag_response.get('TagDescriptions', []):
                                if tag_desc['LoadBalancerName'] == lb['LoadBalancerName']:
                                    tags = tag_desc.get('Tags', [])
                        except Exception as e:
                            logger.warning(f"CLB '{lb['LoadBalancerName']}' のタグ取得エラー: {str(e)}")
                        
                        lb_name = self.get_resource_name_from_tags(tags, lb.get('LoadBalancerName', '名前なし'))
                        
                        load_balancers.append({
                            'ResourceId': lb['LoadBalancerName'],
                            'ResourceName': lb_name,
                            'ResourceType': 'ClassicLoadBalancer',
                            'DNSName': lb.get('DNSName', ''),
                            'Type': 'classic',
                            'Scheme': lb.get('Scheme', ''),
                            'VpcId': lb.get('VPCId', ''),
                            'AZs': lb.get('AvailabilityZones', []),
                            'SecurityGroups': lb.get('SecurityGroups', []),
                            'Tags': tags
                        })
            except Exception as e:
                logger.warning(f"CLB情報収集中にエラー発生: {str(e)}")
                # CLBが存在しない可能性もあるため、エラーでも続行
                
            logger.info(f"ロードバランサー: {len(load_balancers)}件取得")
        except Exception as e:
            logger.error(f"ロードバランサー情報収集中にエラー発生: {str(e)}")
        
        return load_balancers
    
    def _collect_images(self, ec2_client) -> List[Dict[str, Any]]:
        """AMI情報を収集"""
        logger.info("AMI情報を収集しています")
        images = []
        
        try:
            # 所有しているAMIのみを取得
            response = ec2_client.describe_images(Owners=['self'])
            
            for image in response.get('Images', []):
                image_name = self.get_resource_name_from_tags(image.get('Tags', []), image.get('Name', '名前なし'))
                
                images.append({
                    'ResourceId': image['ImageId'],
                    'ResourceName': image_name,
                    'ResourceType': 'AMI',
                    'State': image.get('State', ''),
                    'Architecture': image.get('Architecture', ''),
                    'RootDeviceType': image.get('RootDeviceType', ''),
                    'VirtualizationType': image.get('VirtualizationType', ''),
                    'Public': image.get('Public', False),
                    'CreationDate': image.get('CreationDate', ''),
                    'Tags': image.get('Tags', [])
                })
            
            logger.info(f"AMI: {len(images)}件取得")
        except Exception as e:
            logger.error(f"AMI情報収集中にエラー発生: {str(e)}")
        
        return images
    
    def _collect_vpcs(self, ec2_client) -> List[Dict[str, Any]]:
        """VPC情報を収集"""
        logger.info("VPC情報を収集しています")
        vpcs = []
        
        try:
            paginator = ec2_client.get_paginator('describe_vpcs')
            for page in paginator.paginate():
                for vpc in page.get('Vpcs', []):
                    vpc_name = self.get_resource_name_from_tags(vpc.get('Tags', []))
                    
                    vpcs.append({
                        'ResourceId': vpc['VpcId'],
                        'ResourceName': vpc_name,
                        'ResourceType': 'VPC',
                        'State': vpc.get('State', ''),
                        'CidrBlock': vpc.get('CidrBlock', ''),
                        'IsDefault': vpc.get('IsDefault', False),
                        'Tags': vpc.get('Tags', [])
                    })
            
            logger.info(f"VPC: {len(vpcs)}件取得")
        except Exception as e:
            logger.error(f"VPC情報収集中にエラー発生: {str(e)}")
        
        return vpcs
    
    def _collect_subnets(self, ec2_client) -> List[Dict[str, Any]]:
        """サブネット情報を収集"""
        logger.info("サブネット情報を収集しています")
        subnets = []
        
        try:
            paginator = ec2_client.get_paginator('describe_subnets')
            for page in paginator.paginate():
                for subnet in page.get('Subnets', []):
                    subnet_name = self.get_resource_name_from_tags(subnet.get('Tags', []))
                    
                    subnets.append({
                        'ResourceId': subnet['SubnetId'],
                        'ResourceName': subnet_name,
                        'ResourceType': 'Subnet',
                        'State': subnet.get('State', ''),
                        'VpcId': subnet.get('VpcId', ''),
                        'CidrBlock': subnet.get('CidrBlock', ''),
                        'AvailabilityZone': subnet.get('AvailabilityZone', ''),
                        'AvailableIpAddressCount': subnet.get('AvailableIpAddressCount', 0),
                        'Tags': subnet.get('Tags', [])
                    })
            
            logger.info(f"サブネット: {len(subnets)}件取得")
        except Exception as e:
            logger.error(f"サブネット情報収集中にエラー発生: {str(e)}")
        
        return subnets
    
    def _collect_elastic_ips(self, ec2_client) -> List[Dict[str, Any]]:
        """Elastic IP情報を収集"""
        logger.info("Elastic IP情報を収集しています")
        eips = []
        
        try:
            response = ec2_client.describe_addresses()
            
            for address in response.get('Addresses', []):
                eip_name = self.get_resource_name_from_tags(address.get('Tags', []))
                
                eips.append({
                    'ResourceId': address.get('AllocationId', address.get('PublicIp', '')),
                    'ResourceName': eip_name,
                    'ResourceType': 'ElasticIP',
                    'PublicIp': address.get('PublicIp', ''),
                    'PrivateIpAddress': address.get('PrivateIpAddress', ''),
                    'InstanceId': address.get('InstanceId', ''),
                    'NetworkInterfaceId': address.get('NetworkInterfaceId', ''),
                    'AssociationId': address.get('AssociationId', ''),
                    'Domain': address.get('Domain', ''),
                    'Tags': address.get('Tags', [])
                })
            
            logger.info(f"Elastic IP: {len(eips)}件取得")
        except Exception as e:
            logger.error(f"Elastic IP情報収集中にエラー発生: {str(e)}")
        
        return eips
