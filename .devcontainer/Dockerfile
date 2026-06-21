FROM mcr.microsoft.com/devcontainers/javascript-node:latest

# pnpm を最新版でインストール
RUN npm install -g pnpm@latest

# uv をインストール
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
