# AWS リソースコスト報告ツール 開発者ガイド

このガイドでは、AWS リソースコスト報告ツールの開発環境のセットアップ方法、コーディング規約、およびプロジェクトへの貢献方法について説明します。

## 開発環境のセットアップ

### 前提条件

- Python 3.8以上
- Git
- AWS CLI（テスト用）
- pip または pipenv（パッケージ管理用）

### 環境構築手順

1. リポジトリをクローン：

```bash
git clone https://github.com/your-organization/aws-resource-cost-report.git
cd aws-resource-cost-report
```

2. 開発用依存関係をインストール：

```bash
pip install -r requirements-dev.txt
```

3. pre-commit フックをセットアップ（オプション）：

```bash
pre-commit install
```

### 開発用ブランチの作成

```bash
# 開発用ブランチを作成
git checkout -b feature/your-feature-name

# 開発終了後にプッシュ
git push -u origin feature/your-feature-name
```

## プロジェクト構造

```
aws-resource-cost-report/
├── src/                            # ソースコード
│   ├── collectors/                 # リソース収集モジュール
│   │   ├── __init__.py
│   │   ├── base_collector.py       # 基底コレクタークラス
│   │   ├── ec2_collector.py        # EC2リソース収集クラス
│   │   └── ...                     # その他サービス用コレクター
│   ├── processor/                  # データ処理モジュール
│   │   └── data_processor.py       # データ処理クラス
│   ├── report/                     # レポート生成モジュール
│   │   └── report_generator.py     # レポート生成クラス
│   ├── utils/                      # ユーティリティモジュール
│   │   ├── __init__.py
│   │   └── error_utils.py          # エラー処理ユーティリティ
│   ├── collector.py                # コレクター統合モジュール
│   ├── exporters.py                # エクスポートモジュール
│   └── main.py                     # メインスクリプト
├── output/                         # 出力ディレクトリ
├── tests/                          # テストコード
│   ├── unit/                       # ユニットテスト
│   ├── integration/                # 統合テスト
│   └── test_data/                  # テスト用データ
├── docs/                           # ドキュメント
├── requirements.txt                # 実行時依存関係
├── requirements-dev.txt            # 開発用依存関係
├── pyproject.toml                  # プロジェクト設定
├── Taskfile.yml                    # タスク定義
└── README.md                       # プロジェクト説明
```

## コンポーネント設計

### 1. コレクター（Collectors）

各AWSサービス用のコレクターはすべて `BaseCollector` クラスを継承します。

```python
from src.collectors.base_collector import BaseCollector

class EC2Collector(BaseCollector):
    """EC2リソースを収集するコレクタークラス"""
    
    def collect(self):
        """EC2リソース情報を収集して返す"""
        ec2_client = self.get_client('ec2')
        instances = []
        
        # インスタンス情報の収集ロジック
        ...
        
        return {"EC2_Instances": instances}
```

新しいコレクターを追加する際のポイント：

1. `BaseCollector` クラスを継承する
2. `collect()` メソッドをオーバーライドし、収集したリソース情報を辞書で返す
3. 適切なエラー処理と再試行ロジックを実装する
4. 大量のリソースがある場合のページング処理を実装する

### 2. データプロセッサ（DataProcessor）

`DataProcessor` クラスはコレクターから取得したデータを処理し、サマリー情報や変更レポートを生成します。

```python
# DataProcessorクラスの基本的な使い方
processor = DataProcessor(base_dir="/path/to/base/dir")

# 生データの保存
date_dir = processor.save_raw_data(resources)

# サマリー情報の生成
summary_file = processor.generate_summary()

# トレンドデータの生成
trend_files = processor.generate_trend_data()

# 変更レポートの生成
change_report = processor.generate_change_report("2025-02-01", "2025-03-01")
```

新しい機能を追加する際のポイント：

1. 既存のメソッドとの整合性を考慮する
2. ファイル名やパスの命名規則を維持する
3. 日付ベースでのバージョン管理を意識する
4. 適切なJSONスキーマを定義する

### 3. レポートジェネレータ（ReportGenerator）

`ReportGenerator` クラスは処理されたデータからマークダウンやHTML形式のレポートを生成します。

```python
# ReportGeneratorクラスの基本的な使い方
generator = ReportGenerator(base_dir="/path/to/base/dir")

# サマリーレポートの生成
summary_report = generator.generate_summary_report(output_format="markdown")

# トレンドレポートの生成
trend_report = generator.generate_trend_report(output_format="html")

# 変更レポートの生成
changes_report = generator.generate_changes_report(change_report_file, output_format="both")
```

レポートテンプレートを修正する際のポイント：

1. マークダウン形式を優先し、HTMLへの変換はライブラリに任せる
2. レポート形式の一貫性を保つ
3. 設定ファイルによってカスタマイズ可能にする
4. グラフ生成機能と連携する

## コーディング規約

### PythonスタイルガイドとBest Practices

このプロジェクトは [PEP 8](https://peps.python.org/pep-0008/) に準拠しています。以下の主要なルールを遵守してください：

1. **インデント**: 4スペースを使用
2. **行の長さ**: 最大100文字（例外的に120文字まで）
3. **命名規則**:
   - クラス名: `CamelCase`
   - 関数・メソッド名: `snake_case`
   - 定数: `UPPER_CASE`
   - プライベートメソッド/変数: `_leading_underscore`
4. **ドキュメンテーション**:
   - すべてのパブリックメソッド/クラスにはDocstringを記述（Google形式）
   - 複雑なロジックには適切なコメントを追加
5. **インポート**:
   - 標準ライブラリ、サードパーティライブラリ、プロジェクト内モジュールの順に記述
   - `from xxx import *` は避ける

### リント・フォーマット

コードの品質と一貫性を確保するため、次のツールを使用します：

```bash
# コードのリント
flake8 src/

# コードのフォーマット
black src/

# 型チェック
mypy src/
```

## テスト

### テストフレームワーク

このプロジェクトでは [pytest](https://docs.pytest.org/) を使用してテストを実行します。

```bash
# すべてのテストを実行
pytest

# 特定のテストを実行
pytest tests/unit/test_data_processor.py

# カバレッジレポートを生成
pytest --cov=src tests/
```

### モックとフィクスチャ

AWS APIのモック化には `unittest.mock` と `pytest-mock` を使用します。

```python
def test_ec2_collector(mocker):
    # boto3クライアントのモック
    mock_client = mocker.Mock()
    mock_client.describe_instances.return_value = {
        'Reservations': [
            {
                'Instances': [
                    {
                        'InstanceId': 'i-12345abcde',
                        # ...その他のパラメータ
                    }
                ]
            }
        ]
    }
    
    # モックのセッションを作成
    mock_session = mocker.Mock()
    mock_session.client.return_value = mock_client
    
    # EC2コレクターをインスタンス化
    collector = EC2Collector(mock_session)
    result = collector.collect()
    
    # アサーション
    assert 'EC2_Instances' in result
    assert len(result['EC2_Instances']) == 1
    assert result['EC2_Instances'][0]['ResourceId'] == 'i-12345abcde'
```

## 新機能の追加方法

### 1. 新しいAWSサービスのサポート追加

1. `src/collectors/` ディレクトリに新しいコレクタークラスを作成：

```python
# src/collectors/new_service_collector.py
from src.collectors.base_collector import BaseCollector

class NewServiceCollector(BaseCollector):
    """新しいAWSサービス用のコレクタークラス"""
    
    def collect(self):
        """リソース情報を収集して返す"""
        client = self.get_client('service_name')
        resources = []
        
        # APIを呼び出してリソース情報を収集
        response = self.aws_api_call(client.list_resources)
        
        for item in response.get('Items', []):
            resource = {
                'ResourceId': item['Id'],
                'ResourceName': self.get_resource_name_from_tags(item.get('Tags', [])),
                'ResourceType': 'NewService_Resources',
                # ... その他の属性
            }
            resources.append(resource)
        
        return {"NewService_Resources": resources}
```

2. コレクターリストに新しいコレクターを追加（`src/collector.py`）：

```python
from src.collectors.new_service_collector import NewServiceCollector

# コレクターリストに追加
COLLECTORS = [
    # ... 既存のコレクター
    NewServiceCollector
]
```

3. テストケースを追加：

```python
# tests/unit/collectors/test_new_service_collector.py
import unittest
from unittest.mock import Mock
from src.collectors.new_service_collector import NewServiceCollector

class TestNewServiceCollector(unittest.TestCase):
    # ... テストメソッド
```

### 2. レポート機能の拡張

1. 新しいレポートタイプを追加（`src/report/report_generator.py`）：

```python
def generate_new_report(self, output_format="markdown"):
    """新しいレポートを生成する"""
    # レポート生成ロジック
    # ...
    
    return output_file
```

2. コマンドラインインターフェースに新しいオプションを追加（`src/main.py`）：

```python
parser.add_argument('--new-report', action='store_true',
                   help='新しいレポートを生成する')
```

3. テストケースを追加：

```python
# tests/unit/report/test_report_generator.py
def test_generate_new_report(self):
    # テストコード
```

## デバッグ方法

### ロギング

このプロジェクトでは、Pythonの標準的なロギングモジュールを使用しています。

```python
import logging

# ロガーの取得
logger = logging.getLogger(__name__)

# ログレベルに応じたメッセージ
logger.debug("デバッグ情報")
logger.info("情報メッセージ")
logger.warning("警告メッセージ")
logger.error("エラーメッセージ")
logger.critical("致命的なエラー")
```

ログレベルを変更するには：

```bash
# デバッグレベルでツールを実行
PYTHONPATH=. LOG_LEVEL=DEBUG python src/main.py
```

### パフォーマンスプロファイリング

大規模環境でのパフォーマンス問題を特定するには、プロファイリングツールを使用します：

```bash
# cProfileによるプロファイリング
python -m cProfile -o profile.stats src/main.py

# 結果の分析
python -m pstats profile.stats
```

## リリースプロセス

### バージョニング

このプロジェクトは [セマンティック バージョニング](https://semver.org/) に従います：

- **メジャーバージョン**: 後方互換性のない変更
- **マイナーバージョン**: 後方互換性のある機能追加
- **パッチバージョン**: バグ修正や小さな改善

### リリースチェックリスト

新バージョンをリリースする前に、以下を確認してください：

1. すべてのテストが成功している（`pytest`）
2. コードカバレッジが目標を達成している（`pytest --cov=src tests/`）
3. リント・型チェックに問題がない（`flake8`, `mypy`）
4. ドキュメントが更新されている（README, ユーザーガイド）
5. リリースノートが作成されている
6. バージョン番号が更新されている

### 継続的インテグレーション（CI）

以下のタスクが自動化されています：

```yaml
# .gitlab-ci.yml または .github/workflows/*.yml の例
stages:
  - test
  - lint
  - build
  - docs

test-job:
  stage: test
  script:
    - pip install -r requirements-dev.txt
    - pytest tests/
```

## 貢献方法

### イシューとプルリクエスト

1. 新機能の提案やバグ報告は、まずイシューを作成する
2. 修正・機能追加は、新しいブランチで開発する
3. コードを変更したら、テストを追加し、既存のテストも実行する
4. 変更内容をプルリクエストとして提出する
5. コードレビューを受け、必要に応じて修正する
6. すべての自動テストが通過したら、マージされる

### コードレビュープロセス

コードレビューでは、以下の観点からチェックされます：

1. 実装が要件を満たしているか
2. コーディング規約に従っているか
3. テストが適切に書かれているか
4. パフォーマンスに問題がないか
5. セキュリティリスクがないか
6. ドキュメントが更新されているか

### ドキュメント更新の方針

新機能やバグ修正を行った場合は、関連するドキュメントも更新してください：

1. クラス・メソッドの追加/変更 → API リファレンスを更新
2. 使用方法の変更 → ユーザーガイドを更新
3. アーキテクチャの変更 → 設計ドキュメントを更新
4. 新バージョンのリリース → リリースノートを作成

## トラブルシューティング

### 開発中によくある問題

#### インポートエラー

**症状**: `ModuleNotFoundError: No module named 'src'`

**解決策**:
```bash
# PYTHONPATHを設定してルートディレクトリを追加
export PYTHONPATH=.
```

#### AWS一時的なエラー

**症状**: テスト中に `ThrottlingException` などのエラーが発生

**解決策**:
```python
# src/utils/error_utils.py の RETRY_EXCEPTIONS に例外を追加
# モックを使用してテストする
```

#### リソースクリーンアップ漏れ

**症状**: テストでファイルやディレクトリが残存する

**解決策**:
```python
# テストクラスの tearDown メソッドで確実にクリーンアップを行う
def tearDown(self):
    # 一時ファイル・ディレクトリの削除
    if os.path.exists(self.test_dir):
        shutil.rmtree(self.test_dir)
```

## パフォーマンス最適化

### 大規模環境での考慮事項

1. **適切なページング処理**:
   - 大量のリソースがある環境ではページング処理が重要
   - `MaxResults` パラメータを適切に設定
   - `NextToken` を適切に処理

2. **並列処理の活用**:
   - リージョンごとに並列処理
   - サービスごとに並列処理
   - `concurrent.futures` を使用

3. **メモリ使用量の最適化**:
   - 不要なデータをメモリに保持しない
   - ジェネレータパターンを活用
   - 大きなデータセットはストリーム処理

### 実装例：並列処理

```python
import concurrent.futures

def collect_resources_in_parallel(collectors, max_workers=10):
    """複数のコレクターを並列実行"""
    all_resources = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_collector = {
            executor.submit(collector.collect): collector_name
            for collector_name, collector in collectors.items()
        }
        
        for future in concurrent.futures.as_completed(future_to_collector):
            collector_name = future_to_collector[future]
            try:
                resources = future.result()
                all_resources.update(resources)
            except Exception as e:
                logger.error(f"{collector_name} の実行中にエラーが発生しました: {e}")
    
    return all_resources
```

## セキュリティのベストプラクティス

### 安全な実装のポイント

1. **AWS認証情報の管理**:
   - 認証情報をコードにハードコーディングしない
   - AWS CLI のプロファイル機能を利用
   - IAM ロールを使用

2. **最小権限の原則**:
   - 必要最小限の権限だけを付与
   - 読み取り専用権限を基本とする

3. **機密データの扱い**:
   - 機密データは適切に暗号化
   - 出力ファイルからの機密情報の除外

4. **エラーメッセージ**:
   - 詳細なエラーメッセージを本番環境で公開しない
   - ログレベルを適切に設定

## ドキュメント作成ガイドライン

### ドキュメントの種類と書き方

1. **API リファレンス**:
   - すべてのパブリックメソッド・クラスにDocstringを記述
   - パラメータ、戻り値、例外を明記
   - サンプルコードを追加

2. **ユーザーガイド**:
   - 一般ユーザー向けの使い方の説明
   - スクリーンショットや具体的な例を含める
   - トラブルシューティングセクションを設ける

3. **開発者ガイド**:
   - 開発環境のセットアップ方法
   - アーキテクチャの説明
   - 拡張方法や貢献の手順

4. **リリースノート**:
   - 新機能の説明
   - バグ修正の内容
   - 非互換性のある変更点
   - アップグレード手順

## 更新履歴

| 日付 | バージョン | 説明 | 作成者 |
|------|------------|------|--------|
| 2025-03-27 | 1.0 | 初期バージョン | - |
