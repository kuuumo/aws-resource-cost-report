#!/usr/bin/env python3

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3

from ..core.aws_cost_report import AWSRegionManager

logger = logging.getLogger(__name__)


class TagCollector:
    """
    AWSリソースのタグ情報を収集するクラス
    """

    def __init__(self, regions=None):
        """
        初期化

        Args:
            regions (list): 対象リージョンのリスト（Noneの場合は現在のデフォルトリージョン）
        """
        if regions is None:
            session = boto3.session.Session()
            self.regions = [session.region_name]
        else:
            self.regions = regions

    def collect_all_resource_tags(self, service_names, use_all_regions=False):
        """
        すべてのサービスのリソースタグを収集

        Args:
            service_names (set): 対象サービス名のセット
            use_all_regions (bool): すべてのリージョンを検索するかどうか

        Returns:
            dict: リソースIDをキー、タグ値を値とする辞書
        """
        all_tags = {}

        # リージョンの決定
        if use_all_regions:
            regions = AWSRegionManager.get_all_regions()
        else:
            regions = self.regions

        # 利用可能なすべてのサービスを処理
        service_to_process = set(service_names)

        logger.info(
            f"Collecting resource tags for {len(service_to_process)} services "
            f"across {len(regions)} regions"
        )

        # 複数リージョンでの並列処理
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for region in regions:
                for service in service_to_process:
                    futures.append(
                        executor.submit(
                            self.get_resource_tags_for_service, service, region
                        )
                    )

            for future in as_completed(futures):
                try:
                    result = future.result()
                    all_tags.update(result)
                except Exception as e:
                    logger.warning(f"Error getting tags: {e}")

        return all_tags

    def get_resource_tags_for_service(self, service_name, region=None):
        """
        指定したサービスのリソースタグを取得

        Args:
            service_name (str): 対象サービス名
            region (str): AWSリージョン

        Returns:
            dict: リソースIDをキー、タグ値を値とする辞書
        """
        tags = {}

        try:
            # リージョンが指定されていない場合、デフォルトリージョンを使用
            if region is None:
                session = boto3.session.Session()
                region = session.region_name

            # EC2関連リソース（多くのリソースタイプを一度に取得）
            if "EC2" in service_name or "VPC" in service_name or "EBS" in service_name:
                tags.update(self._collect_ec2_tags(region))

            # RDSインスタンス
            if "RDS" in service_name or "Database" in service_name:
                tags.update(self._collect_rds_tags(region))

            # S3バケット
            if "S3" in service_name:
                tags.update(self._collect_s3_tags(region))

            # Lambda関数
            if "Lambda" in service_name:
                tags.update(self._collect_lambda_tags(region))

            # DynamoDB
            if "DynamoDB" in service_name:
                tags.update(self._collect_dynamodb_tags(region))

            # Elastic Load Balancer (ELB, ALB, NLB)
            if "Elastic Load Balancing" in service_name:
                tags.update(self._collect_elb_tags(region))

            # Elastic Container Service (ECS)
            if "ECS" in service_name or "Container" in service_name:
                tags.update(self._collect_ecs_tags(region))

            # ElastiCache
            if "ElastiCache" in service_name:
                tags.update(self._collect_elasticache_tags(region))

            # CloudFront
            if "CloudFront" in service_name:
                tags.update(self._collect_cloudfront_tags())

            # SQS
            if "SQS" in service_name or "Simple Queue Service" in service_name:
                tags.update(self._collect_sqs_tags(region))

            # SNS
            if "SNS" in service_name or "Simple Notification Service" in service_name:
                tags.update(self._collect_sns_tags(region))

            # API Gateway
            if "API Gateway" in service_name:
                tags.update(self._collect_apigateway_tags(region))

        except Exception as e:
            logger.warning(
                f"Failed to get resource tags for service {service_name}: {e}"
            )

        return tags

    def _collect_ec2_tags(self, region):
        """EC2関連リソースのタグを収集"""
        tags = {}

        try:
            ec2 = boto3.client("ec2", region_name=region)

            # タグ付きリソースを取得（Type: インスタンス、ボリューム、スナップショット、セキュリティグループなど）
            paginator = ec2.get_paginator("describe_tags")
            page_iterator = paginator.paginate()

            for page in page_iterator:
                for tag in page["Tags"]:
                    if tag["Key"] == "Name":
                        tags[tag["ResourceId"]] = tag["Value"]
        except Exception as e:
            logger.warning(f"Failed to collect EC2 tags: {e}")

        return tags

    def _collect_rds_tags(self, region):
        """RDSのタグを収集"""
        tags = {}

        try:
            rds = boto3.client("rds", region_name=region)

            # DBインスタンス
            try:
                paginator = rds.get_paginator("describe_db_instances")
                page_iterator = paginator.paginate()

                for page in page_iterator:
                    for db in page["DBInstances"]:
                        db_id = db["DBInstanceIdentifier"]
                        arn = db["DBInstanceArn"]

                        try:
                            tag_list = rds.list_tags_for_resource(ResourceName=arn)
                            for tag in tag_list["TagList"]:
                                if tag["Key"] == "Name":
                                    tags[db_id] = tag["Value"]
                                    break
                        except Exception as e:
                            logger.warning(f"Failed to get tags for RDS {db_id}: {e}")
            except Exception as e:
                logger.warning(f"Failed to list RDS instances: {e}")

            # DBクラスター
            try:
                paginator = rds.get_paginator("describe_db_clusters")
                page_iterator = paginator.paginate()

                for page in page_iterator:
                    for cluster in page["DBClusters"]:
                        cluster_id = cluster["DBClusterIdentifier"]
                        arn = cluster["DBClusterArn"]

                        try:
                            tag_list = rds.list_tags_for_resource(ResourceName=arn)
                            for tag in tag_list["TagList"]:
                                if tag["Key"] == "Name":
                                    tags[cluster_id] = tag["Value"]
                                    break
                        except Exception as e:
                            logger.warning(
                                f"Failed to get tags for RDS cluster {cluster_id}: {e}"
                            )
            except Exception as e:
                logger.warning(f"Failed to list RDS clusters: {e}")
        except Exception as e:
            logger.warning(f"Failed to collect RDS tags: {e}")

        return tags

    def _collect_s3_tags(self, region):
        """S3バケットのタグを収集"""
        tags = {}

        try:
            s3 = boto3.client("s3", region_name=region)

            try:
                buckets = s3.list_buckets()

                for bucket in buckets["Buckets"]:
                    bucket_name = bucket["Name"]

                    try:
                        tag_list = s3.get_bucket_tagging(Bucket=bucket_name)
                        for tag in tag_list["TagSet"]:
                            if tag["Key"] == "Name":
                                tags[bucket_name] = tag["Value"]
                                break
                    except Exception:
                        # タグが設定されていないバケットは無視
                        pass
            except Exception as e:
                logger.warning(f"Failed to list S3 buckets: {e}")
        except Exception as e:
            logger.warning(f"Failed to collect S3 tags: {e}")

        return tags

    def _collect_lambda_tags(self, region):
        """Lambda関数のタグを収集"""
        tags = {}

        try:
            lambda_client = boto3.client("lambda", region_name=region)

            try:
                paginator = lambda_client.get_paginator("list_functions")
                page_iterator = paginator.paginate()

                for page in page_iterator:
                    for function in page["Functions"]:
                        function_name = function["FunctionName"]
                        arn = function["FunctionArn"]

                        try:
                            tag_response = lambda_client.list_tags(Resource=arn)
                            if "Name" in tag_response["Tags"]:
                                tags[function_name] = tag_response["Tags"]["Name"]
                        except Exception as e:
                            logger.warning(
                                f"Failed to get tags for Lambda {function_name}: {e}"
                            )
            except Exception as e:
                logger.warning(f"Failed to list Lambda functions: {e}")
        except Exception as e:
            logger.warning(f"Failed to collect Lambda tags: {e}")

        return tags

    def _collect_dynamodb_tags(self, region):
        """DynamoDBのタグを収集"""
        tags = {}

        try:
            dynamodb = boto3.client("dynamodb", region_name=region)

            try:
                paginator = dynamodb.get_paginator("list_tables")
                page_iterator = paginator.paginate()

                for page in page_iterator:
                    for table_name in page["TableNames"]:
                        try:
                            arn = dynamodb.describe_table(TableName=table_name)[
                                "Table"
                            ]["TableArn"]
                            tag_response = dynamodb.list_tags_of_resource(
                                ResourceArn=arn
                            )

                            for tag in tag_response.get("Tags", []):
                                if tag["Key"] == "Name":
                                    tags[table_name] = tag["Value"]
                                    break
                        except Exception as e:
                            logger.warning(
                                f"Failed to get tags for DynamoDB table {table_name}: {e}"
                            )
            except Exception as e:
                logger.warning(f"Failed to list DynamoDB tables: {e}")
        except Exception as e:
            logger.warning(f"Failed to collect DynamoDB tags: {e}")

        return tags

    def _collect_elb_tags(self, region):
        """ELBのタグを収集"""
        tags = {}

        try:
            # ALB, NLB
            try:
                elb = boto3.client("elbv2", region_name=region)
                paginator = elb.get_paginator("describe_load_balancers")
                page_iterator = paginator.paginate()

                for page in page_iterator:
                    for lb in page["LoadBalancers"]:
                        lb_arn = lb["LoadBalancerArn"]
                        lb_name = lb["LoadBalancerName"]

                        try:
                            tag_response = elb.describe_tags(ResourceArns=[lb_arn])
                            for tag_desc in tag_response["TagDescriptions"]:
                                for tag in tag_desc["Tags"]:
                                    if tag["Key"] == "Name":
                                        tags[lb_name] = tag["Value"]
                                        break
                        except Exception as e:
                            logger.warning(f"Failed to get tags for ELB {lb_name}: {e}")
            except Exception as e:
                logger.warning(f"Failed to list ELBv2 load balancers: {e}")

            # 従来のELB
            try:
                elb_classic = boto3.client("elb", region_name=region)
                paginator = elb_classic.get_paginator("describe_load_balancers")
                page_iterator = paginator.paginate()

                for page in page_iterator:
                    for lb in page["LoadBalancerDescriptions"]:
                        lb_name = lb["LoadBalancerName"]

                        try:
                            tag_response = elb_classic.describe_tags(
                                LoadBalancerNames=[lb_name]
                            )
                            for tag_desc in tag_response["TagDescriptions"]:
                                for tag in tag_desc["Tags"]:
                                    if tag["Key"] == "Name":
                                        tags[lb_name] = tag["Value"]
                                        break
                        except Exception as e:
                            logger.warning(
                                f"Failed to get tags for classic ELB {lb_name}: {e}"
                            )
            except Exception as e:
                logger.warning(f"Failed to list classic ELBs: {e}")
        except Exception as e:
            logger.warning(f"Failed to collect ELB tags: {e}")

        return tags

    def _collect_ecs_tags(self, region):
        """ECSのタグを収集"""
        tags = {}

        try:
            ecs = boto3.client("ecs", region_name=region)

            try:
                # クラスター
                paginator = ecs.get_paginator("list_clusters")
                page_iterator = paginator.paginate()

                cluster_arns = []
                for page in page_iterator:
                    cluster_arns.extend(page["clusterArns"])

                if cluster_arns:
                    clusters = ecs.describe_clusters(
                        clusters=cluster_arns, include=["TAGS"]
                    )
                    for cluster in clusters["clusters"]:
                        cluster_name = cluster["clusterName"]

                        for tag in cluster.get("tags", []):
                            if tag["key"] == "Name":
                                tags[cluster_name] = tag["value"]
                                break
            except Exception as e:
                logger.warning(f"Failed to list ECS clusters: {e}")

            # タスク定義
            try:
                paginator = ecs.get_paginator("list_task_definitions")
                page_iterator = paginator.paginate()

                for page in page_iterator:
                    for task_def_arn in page["taskDefinitionArns"]:
                        task_def_name = task_def_arn.split("/")[-1].split(":")[0]

                        try:
                            task_def = ecs.describe_task_definition(
                                taskDefinition=task_def_arn, include=["TAGS"]
                            )
                            for tag in task_def.get("tags", []):
                                if tag["key"] == "Name":
                                    tags[task_def_name] = tag["value"]
                                    break
                        except Exception as e:
                            logger.warning(
                                f"Failed to get tags for ECS task definition {task_def_name}: {e}"
                            )
            except Exception as e:
                logger.warning(f"Failed to list ECS task definitions: {e}")
        except Exception as e:
            logger.warning(f"Failed to collect ECS tags: {e}")

        return tags

    def _collect_elasticache_tags(self, region):
        """ElastiCacheのタグを収集"""
        tags = {}

        try:
            elasticache = boto3.client("elasticache", region_name=region)

            try:
                # キャッシュクラスター
                paginator = elasticache.get_paginator("describe_cache_clusters")
                page_iterator = paginator.paginate()

                for page in page_iterator:
                    for cluster in page["CacheClusters"]:
                        cluster_id = cluster["CacheClusterId"]
                        account_id = (
                            boto3.client("sts").get_caller_identity().get("Account")
                        )
                        arn = f"arn:aws:elasticache:{region}:{account_id}:cluster:{cluster_id}"

                        try:
                            tag_response = elasticache.list_tags_for_resource(
                                ResourceName=arn
                            )
                            for tag in tag_response["TagList"]:
                                if tag["Key"] == "Name":
                                    tags[cluster_id] = tag["Value"]
                                    break
                        except Exception as e:
                            logger.warning(
                                f"Failed to get tags for ElastiCache cluster {cluster_id}: {e}"
                            )
            except Exception as e:
                logger.warning(f"Failed to list ElastiCache clusters: {e}")
        except Exception as e:
            logger.warning(f"Failed to collect ElastiCache tags: {e}")

        return tags

    def _collect_cloudfront_tags(self):
        """CloudFrontのタグを収集"""
        tags = {}

        try:
            cloudfront = boto3.client("cloudfront")

            try:
                paginator = cloudfront.get_paginator("list_distributions")
                page_iterator = paginator.paginate()

                for page in page_iterator:
                    for dist_summary in page.get("DistributionList", {}).get(
                        "Items", []
                    ):
                        dist_id = dist_summary["Id"]

                        try:
                            tags_response = cloudfront.list_tags_for_resource(
                                Resource=f"arn:aws:cloudfront::{boto3.client('sts').get_caller_identity().get('Account')}:distribution/{dist_id}"
                            )

                            for tag in tags_response.get("Tags", {}).get("Items", []):
                                if tag["Key"] == "Name":
                                    tags[dist_id] = tag["Value"]
                                    break
                        except Exception as e:
                            logger.warning(
                                f"Failed to get tags for CloudFront distribution {dist_id}: {e}"
                            )
            except Exception as e:
                logger.warning(f"Failed to list CloudFront distributions: {e}")
        except Exception as e:
            logger.warning(f"Failed to collect CloudFront tags: {e}")

        return tags

    def _collect_sqs_tags(self, region):
        """SQSのタグを収集"""
        tags = {}

        try:
            sqs = boto3.client("sqs", region_name=region)

            try:
                queues = sqs.list_queues()

                for queue_url in queues.get("QueueUrls", []):
                    queue_name = queue_url.split("/")[-1]

                    try:
                        tag_response = sqs.list_queue_tags(QueueUrl=queue_url)
                        if "Tags" in tag_response and "Name" in tag_response["Tags"]:
                            tags[queue_name] = tag_response["Tags"]["Name"]
                    except Exception as e:
                        logger.warning(
                            f"Failed to get tags for SQS queue {queue_name}: {e}"
                        )
            except Exception as e:
                logger.warning(f"Failed to list SQS queues: {e}")
        except Exception as e:
            logger.warning(f"Failed to collect SQS tags: {e}")

        return tags

    def _collect_sns_tags(self, region):
        """SNSのタグを収集"""
        tags = {}

        try:
            sns = boto3.client("sns", region_name=region)

            try:
                paginator = sns.get_paginator("list_topics")
                page_iterator = paginator.paginate()

                for page in page_iterator:
                    for topic in page["Topics"]:
                        topic_arn = topic["TopicArn"]
                        topic_name = topic_arn.split(":")[-1]

                        try:
                            tag_response = sns.list_tags_for_resource(
                                ResourceArn=topic_arn
                            )
                            name_tag = self._get_resource_tags_from_tag_list(
                                topic_name, topic_name, tag_response
                            )
                            if name_tag:
                                tags[topic_name] = name_tag
                        except Exception as e:
                            logger.warning(
                                f"Failed to get tags for SNS topic {topic_name}: {e}"
                            )
            except Exception as e:
                logger.warning(f"Failed to list SNS topics: {e}")
        except Exception as e:
            logger.warning(f"Failed to collect SNS tags: {e}")

        return tags

    def _get_resource_tags_with_name_key(
        self,
        resource_id,
        resource_name,
        tag_response,
        tags_key="tags",
        default_to_name=False,
    ):
        """
        リソースのタグから「Name」キーの値を取得する共通処理
        タグがキーバリュー形式で格納されている場合に使用

        Args:
            resource_id (str): リソースID
            resource_name (str): リソース名
            tag_response (dict): タグ情報を含むレスポンス
            tags_key (str): タグ情報が格納されているキー名
            default_to_name (bool): Nameタグがない場合にリソース名をデフォルト値として使用するかどうか

        Returns:
            str: Nameタグの値またはNone
        """
        if tags_key in tag_response and "Name" in tag_response[tags_key]:
            return tag_response[tags_key]["Name"]
        elif default_to_name:
            return resource_name
        return None

    def _get_resource_tags_from_tag_list(
        self,
        resource_id,
        resource_name,
        tag_response,
        tags_key="Tags",
        key_field="Key",
        value_field="Value",
        default_to_name=False,
    ):
        """
        リソースのタグリストから「Name」キーの値を取得する共通処理
        タグがリスト形式で格納されている場合に使用

        Args:
            resource_id (str): リソースID
            resource_name (str): リソース名
            tag_response (dict): タグ情報を含むレスポンス
            tags_key (str): タグリストが格納されているキー名
            key_field (str): タグのキーフィールド名
            value_field (str): タグの値フィールド名
            default_to_name (bool): Nameタグがない場合にリソース名をデフォルト値として使用するかどうか

        Returns:
            str: Nameタグの値またはNone
        """
        if tags_key in tag_response:
            for tag in tag_response.get(tags_key, []):
                if tag.get(key_field) == "Name":
                    return tag.get(value_field)

        if default_to_name:
            return resource_name
        return None

    def _collect_apigateway_tags(self, region):
        """API Gatewayのタグを収集"""
        tags = {}

        try:
            apigw = boto3.client("apigateway", region_name=region)

            try:
                apis = apigw.get_rest_apis()

                for api in apis["items"]:
                    api_id = api["id"]
                    api_name = api["name"]

                    try:
                        tag_response = apigw.get_tags(
                            resourceArn=f"arn:aws:apigateway:{region}::/restapis/{api_id}"
                        )
                        name_tag = self._get_resource_tags_with_name_key(
                            api_id, api_name, tag_response, default_to_name=True
                        )
                        if name_tag:
                            tags[api_id] = name_tag
                    except Exception as e:
                        logger.warning(
                            f"Failed to get tags for API Gateway {api_name}: {e}"
                        )
                        # 名前をデフォルトタグとして使用
                        tags[api_id] = api_name
            except Exception as e:
                logger.warning(f"Failed to list API Gateway APIs: {e}")
        except Exception as e:
            logger.warning(f"Failed to collect API Gateway tags: {e}")

        return tags
