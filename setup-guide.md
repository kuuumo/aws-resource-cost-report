# AWS リソース・コスト レポート セットアップガイド

このガイドでは、AWS リソース・コスト レポートツールの詳細なセットアップ手順を説明します。

## 前提条件のインストール

### 1. asdfのインストール (Pythonバージョン管理)

[asdf](https://asdf-vm.com/)は複数のランタイムバージョンを管理するためのツールです。

macOSの場合:
```bash
# Homebrewを使用
brew install asdf

# シェル設定ファイルに以下を追加（bashの場合）
echo -e "\n. $(brew --prefix asdf)/libexec/asdf.sh" >> ~/.bashrc
source ~/.bashrc

# zshの場合
echo -e "\n. $(brew --prefix asdf)/libexec/asdf.sh" >> ~/.zshrc
source ~/.zshrc
```

Linuxの場合:
```bash
git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.12.0
echo -e "\n. $HOME/.asdf/asdf.sh" >> ~/.bashrc
echo -e "\n. $HOME/.asdf/completions/asdf.bash" >> ~/.bashrc
source ~/.bashrc
```

### 2. asdf Pythonプラグインのインストール

```bash
asdf plugin add python
```

### 3. Task CLIのインストール

[Task](https://taskfile.dev/)はMakefileの代替として使用されるタスクランナーです。

macOSの場合:
```bash
brew install go-task/tap/go-task
```

Linuxの場合:
```bash
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b ~/.local/bin
```

## プロジェクトのセットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-username/aws-resource-cost-report.git
cd aws-resource-cost-report
```

### 2. asdfでPythonをインストール

プロジェクトディレクトリ内で以下のコマンドを実行します：

```bash
# .tool-versionsファイルに基づいてPythonをインストール
asdf install
```

エラーが発生する場合は、手動でPythonバージョンを指定できます：

```bash
asdf local python 3.11.7
asdf install
```

### 3. 環境のセットアップ

```bash
# task setupを実行して仮想環境を作成し、依存パッケージをインストール
task setup
```

このコマンドは以下の処理を行います：
- Pythonの仮想環境（.venv）を作成
- 必要なパッケージをインストール

## プロジェクトの実行

### 実行（AWS認証情報が必要）

```bash
task run
```

## よくある問題と解決方法

### asdfが「command not found」エラーになる場合

シェルの設定ファイルに正しくasdfのパスが設定されているか確認してください：

```bash
# bashの場合
echo -e "\n. $(brew --prefix asdf)/libexec/asdf.sh" >> ~/.bashrc
source ~/.bashrc

# zshの場合
echo -e "\n. $(brew --prefix asdf)/libexec/asdf.sh" >> ~/.zshrc
source ~/.zshrc
```

### Pythonのインストールに失敗する場合

依存パッケージをインストールしてから再試行してください：

macOSの場合:
```bash
brew install openssl readline sqlite3 xz zlib tcl-tk
```

Linuxの場合:
```bash
sudo apt-get update
sudo apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
xz-utils tk-dev libffi-dev liblzma-dev python-openssl
```

### 仮想環境の作成に失敗する場合

古い仮想環境を削除して再試行してください：

```bash
rm -rf .venv
task setup
```

### AWS認証情報の設定

ローカルでAWSリソースにアクセスするには、認証情報を設定する必要があります：

```bash
aws configure
```

AWSアクセスキーID、シークレットアクセスキー、デフォルトリージョン名、出力形式（通常はjson）を入力します。
