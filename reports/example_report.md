# AWS リソース・コスト レポート

**期間**: 2025-02-20 から 2025-03-20
**作成日時**: 2025-03-22 09:15:30

## 概要

### 総コスト

**合計**: 5432.10 USD

**前期間 (2025-01-20 ~ 2025-02-19) 比較**: 🔴 256.78 USD (↑ 4.96%)

**最大コストサービス**: Amazon Elastic Compute Cloud - Compute (2345.67 USD)

## サービス別コスト

| サービス | コスト | 全体比 |
| --- | ---: | ---: |
| Amazon Elastic Compute Cloud - Compute | 2345.67 USD | 43.18% |
| Amazon Relational Database Service | 986.43 USD | 18.16% |
| Amazon Simple Storage Service | 654.32 USD | 12.05% |
| Amazon ElastiCache | 432.10 USD | 7.95% |
| Amazon CloudWatch | 321.54 USD | 5.92% |
| AWS Data Transfer | 245.67 USD | 4.52% |
| Amazon Virtual Private Cloud | 213.45 USD | 3.93% |
| Amazon Route 53 | 132.45 USD | 2.44% |
| AWS Lambda | 87.65 USD | 1.61% |
| その他 | 12.82 USD | 0.24% |

## リージョン別コスト

| リージョン | コスト | 全体比 |
| --- | ---: | ---: |
| ap-northeast-1 | 3456.78 USD | 63.64% |
| us-east-1 | 1245.67 USD | 22.93% |
| us-west-2 | 543.21 USD | 10.00% |
| eu-west-1 | 186.44 USD | 3.43% |

## EC2インスタンス詳細

| インスタンスID | 名前 | タイプ | 状態 | リージョン | 起動日時 | 推定月間コスト |
| --- | --- | --- | --- | --- | --- | ---: |
| i-0a1b2c3d4e5f67890 | app-server-1 | m5.xlarge | running | ap-northeast-1 | 2024-10-15 | 145.67 USD |
| i-0b2c3d4e5f6789012 | app-server-2 | m5.xlarge | running | ap-northeast-1 | 2024-10-15 | 145.67 USD |
| i-0c3d4e5f67890a1b2 | db-replica-1 | r5.2xlarge | running | ap-northeast-1 | 2024-11-20 | 256.32 USD |
| i-0d4e5f6789012a3b4 | batch-server | c5.2xlarge | running | ap-northeast-1 | 2024-12-05 | 210.54 USD |
| i-0e5f6789012a3b4c5 | web-server-1 | t3.medium | running | us-east-1 | 2024-09-10 | 32.45 USD |
| i-0f6789012a3b4c5d6 | web-server-2 | t3.medium | running | us-east-1 | 2024-09-10 | 32.45 USD |
| i-067890a1b2c3d4e5f | backup-server | t3.small | stopped | us-east-1 | 2024-08-15 | 0.00 USD |

## RDSインスタンス詳細

| インスタンスID | エンジン | タイプ | 状態 | リージョン | 作成日時 | ストレージ(GB) | マルチAZ | 推定月間コスト |
| --- | --- | --- | --- | --- | --- | ---: | --- | ---: |
| db-main-01 | MySQL 8.0.28 | db.m5.xlarge | available | ap-northeast-1 | 2024-10-20 | 100 | はい | 345.67 USD |
| db-replica-01 | MySQL 8.0.28 | db.m5.large | available | ap-northeast-1 | 2024-11-15 | 100 | いいえ | 123.45 USD |
| db-staging | PostgreSQL 13.7 | db.t3.medium | available | us-east-1 | 2024-09-01 | 50 | いいえ | 76.54 USD |

## S3バケット詳細

| バケット名 | リージョン | 作成日時 | サイズ |
| --- | --- | --- | ---: |
| my-app-logs | ap-northeast-1 | 2024-01-15 | 543.21 GB |
| my-app-assets | ap-northeast-1 | 2024-01-15 | 1.23 TB |
| my-app-backups | us-east-1 | 2024-02-20 | 2.34 TB |
| my-app-configs | us-east-1 | 2024-02-20 | 5.67 MB |

## ElastiCacheクラスター詳細

| クラスターID | エンジン | ノードタイプ | ノード数 | 状態 | リージョン | 作成日時 |
| --- | --- | --- | ---: | --- | --- | --- |
| redis-cluster-1 | Redis 6.2.5 | cache.m5.large | 3 | available | ap-northeast-1 | 2024-10-25 |
| redis-cluster-2 | Redis 6.2.5 | cache.m5.large | 3 | available | us-east-1 | 2024-11-10 |

## ロードバランサー詳細

| 名前 | タイプ | DNSName | スキーム | リージョン | 作成日時 |
| --- | --- | --- | --- | --- | --- |
| app-alb | Application | app-alb-123456789.ap-northeast-1.elb.amazonaws.com | internet-facing | ap-northeast-1 | 2024-10-15 |
| internal-alb | Application | internal-alb-123456789.ap-northeast-1.elb.amazonaws.com | internal | ap-northeast-1 | 2024-10-15 |
| web-alb | Application | web-alb-123456789.us-east-1.elb.amazonaws.com | internet-facing | us-east-1 | 2024-09-10 |

## 日次コストトレンド

| 日付 | コスト |
| --- | ---: |
| 2025-02-20 | 165.43 USD |
| 2025-02-21 | 172.56 USD |
| 2025-02-22 | 154.32 USD |
| 2025-02-23 | 156.78 USD |
| 2025-02-24 | 187.65 USD |
| ... | ... |
| 2025-03-18 | 183.45 USD |
| 2025-03-19 | 179.87 USD |
| 2025-03-20 | 182.23 USD |

## コスト最適化の推奨事項

- **停止中のEC2インスタンス**: 1個のインスタンスが停止状態です。不要であれば削除を検討してください: i-067890a1b2c3d4e5f (backup-server)

- **シングルAZ RDSインスタンス**: 2個のRDSインスタンスがシングルAZ構成です。本番環境では可用性向上のためにマルチAZ構成を検討してください: db-replica-01, db-staging

- **リザーブドインスタンスの活用**: 安定した使用が見込まれるインスタンスに対しては、リザーブドインスタンスの購入を検討してください（最大75%のコスト削減）。

- **自動スケーリングの設定**: 使用パターンに基づいてリソースを自動的にスケールする設定を行うことで、必要なときだけリソースを確保できます。

- **S3のストレージクラスの最適化**: アクセス頻度の低いデータは、Standard-IA, One Zone-IA, Glacierなどの低コストストレージに移行することでコスト削減が可能です。

- **未使用EBSボリュームの削除**: アタッチされていないEBSボリュームを定期的に確認し、不要なものは削除してください。
