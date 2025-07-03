# 使用するPythonのベースイメージを指定
# Pythonのバージョンに合わせて変更してください (例: python:3.9-slim-buster)
FROM python:3.9-slim-buster

# システムのパッケージリストを更新し、ビルドに必要なツールをインストール
# これにより、PythonパッケージのC拡張などが正しくコンパイルされるようになります
# && rm -rf /var/lib/apt/lists/* は、インストール後にキャッシュを削除してイメージサイズを小さく保つためのものです。
RUN apt-get update && apt-get install -y build-essential \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリをコンテナ内に設定
WORKDIR /app

# ホストのrequirements.txtをコンテナの/appにコピー
COPY requirements.txt .

# Pythonの依存関係をインストール
# --no-cache-dir: キャッシュを保存しない（コンテナイメージを小さくするため）
# -r: requirements.txtからインストール
RUN pip install --no-cache-dir -r requirements.txt

# ホストの全てのアプリケーションコードをコンテナの/appにコピー
COPY . .

# Flaskアプリケーションがリッスンするポートを指定
EXPOSE 5000

# アプリケーションを実行するコマンド
# FLASK_APP環境変数を設定し、Flask開発サーバーを起動
ENV FLASK_APP=app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
# --host=0.0.0.0 は、コンテナ外からアクセスできるようにするために必要です
