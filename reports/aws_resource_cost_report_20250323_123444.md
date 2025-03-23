# AWS リソース・コスト レポート

**期間**: 2025-02-01 から 2025-02-28
**作成日時**: 2025-03-23 12:34:49


## 概要

### 総コスト

**合計**: 1258.57 USD

**前期間 (2025-01-04 ~ 2025-01-31) 比較**: 🔴 24.92 USD (↑ 2.02%)

**最大コストサービス**: Amazon Relational Database Service (339.76 USD)


## サービス別コスト

| サービス | コスト | 全体比 |
| --- | ---: | ---: |
| Amazon Relational Database Service | 339.76 USD | 27.00% |
| Amazon Elastic Compute Cloud - Compute | 311.84 USD | 24.78% |
| EC2 - Other | 234.92 USD | 18.67% |
| Amazon Elastic Container Service | 134.78 USD | 10.71% |
| Tax | 118.35 USD | 9.40% |
| Amazon Virtual Private Cloud | 53.98 USD | 4.29% |
| AWS WAF | 23.44 USD | 1.86% |
| Amazon Elastic Load Balancing | 18.00 USD | 1.43% |
| Amazon EC2 Container Registry (ECR) | 13.52 USD | 1.07% |
| AmazonCloudWatch | 7.99 USD | 0.64% |
| Amazon Elastic File System | 0.73 USD | 0.06% |
| AWS Backup | 0.39 USD | 0.03% |
| AWS Cost Explorer | 0.38 USD | 0.03% |
| Amazon Simple Storage Service | 0.33 USD | 0.03% |
| Amazon DocumentDB (with MongoDB compatibility) | 0.15 USD | 0.01% |
| Amazon CloudFront | 0.00 USD | 0.00% |
| AWS Secrets Manager | 0.00 USD | 0.00% |
| Amazon ElastiCache | 0.00 USD | 0.00% |
| AWS Key Management Service | 0.00 USD | 0.00% |
| AWS Lambda | 0.00 USD | 0.00% |
| AWS Systems Manager | 0.00 USD | 0.00% |
| Amazon Simple Notification Service | 0.00 USD | 0.00% |
| Amazon Simple Queue Service | 0.00 USD | 0.00% |
| CloudWatch Events | 0.00 USD | 0.00% |


## リージョン別コスト

| リージョン | コスト | 全体比 |
| --- | ---: | ---: |
| ap-northeast-1 | 1124.41 USD | 89.34% |
| NoRegion | 118.35 USD | 9.40% |
| global | 15.43 USD | 1.23% |
| us-east-1 | 0.38 USD | 0.03% |
| us-east-2 | 0.00 USD | 0.00% |
| eu-central-1 | 0.00 USD | 0.00% |
| ap-southeast-2 | 0.00 USD | 0.00% |
| ap-southeast-1 | 0.00 USD | 0.00% |
| us-west-1 | 0.00 USD | 0.00% |
| us-west-2 | 0.00 USD | 0.00% |
| eu-west-1 | 0.00 USD | 0.00% |
| eu-west-2 | 0.00 USD | 0.00% |
| ap-northeast-2 | 0.00 USD | 0.00% |
| ca-central-1 | 0.00 USD | 0.00% |
| me-south-1 | 0.00 USD | 0.00% |
| sa-east-1 | 0.00 USD | 0.00% |


## EC2インスタンス詳細

EC2インスタンスのデータはありません。

## RDSインスタンス詳細

RDSインスタンスのデータはありません。

## その他のリソース詳細

その他のリソースデータはありません。

## 日次コストトレンド

| 日付 | コスト |
| --- | ---: |
| 2025-02-01 | 160.19 USD |
| 2025-02-02 | 41.61 USD |
| 2025-02-03 | 41.50 USD |
| 2025-02-04 | 41.68 USD |
| 2025-02-05 | 41.63 USD |
| 2025-02-06 | 41.60 USD |
| 2025-02-07 | 42.24 USD |
| 2025-02-08 | 41.32 USD |
| 2025-02-09 | 42.55 USD |
| 2025-02-10 | 42.08 USD |
| 2025-02-11 | 42.42 USD |
| 2025-02-12 | 42.44 USD |
| 2025-02-13 | 42.42 USD |
| 2025-02-14 | 42.35 USD |
| 2025-02-15 | 42.16 USD |
| 2025-02-16 | 43.55 USD |
| 2025-02-17 | 42.55 USD |
| 2025-02-18 | 42.73 USD |
| 2025-02-19 | 42.88 USD |
| 2025-02-20 | 42.76 USD |
| 2025-02-21 | 42.13 USD |
| 2025-02-22 | 41.56 USD |
| 2025-02-23 | 41.78 USD |
| 2025-02-24 | 42.01 USD |
| 2025-02-25 | 43.22 USD |
| 2025-02-26 | 42.32 USD |
| 2025-02-27 | 42.89 USD |


## コスト最適化の推奨事項

- **リザーブドインスタンスの活用**: 安定した使用が見込まれるインスタンスに対しては、リザーブドインスタンスの購入を検討してください（最大75%のコスト削減）。

- **自動スケーリングの設定**: 使用パターンに基づいてリソースを自動的にスケールする設定を行うことで、必要なときだけリソースを確保できます。

- **S3のストレージクラスの最適化**: アクセス頻度の低いデータは、Standard-IA, One Zone-IA, Glacierなどの低コストストレージに移行することでコスト削減が可能です。

- **未使用EBSボリュームの削除**: アタッチされていないEBSボリュームを定期的に確認し、不要なものは削除してください。