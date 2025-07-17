# ベースイメージとしてPython 3.9の軽量版を使用
FROM python:3.9-alpine

# 作業ディレクトリをコンテナ内に設定
WORKDIR /app

# ホストのrequirements.txtをコンテナの/appにコピー
COPY requirements.txt .

# 必要なPythonパッケージをインストール
RUN pip install -r requirements.txt

# ホストのアプリケーションコードをコンテナの/appにコピー
COPY . .

# Flaskアプリケーションがリッスンするポートを公開
EXPOSE 5000

# コンテナ起動時に実行されるデフォルトコマンド (docker-compose.ymlで上書きされるが、単体起動時用)
CMD ["flask", "run", "--host=0.0.0.0"]