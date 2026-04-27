#!/bin/bash
# ZenBlog Python 后端打包脚本（PyInstaller）
# 将 zenblog_backend.py 打包为独立可执行文件
# 输出到 python-dist/ 目录

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================="
echo "  ZenBlog Python 后端打包"
echo "============================================="

# 检查 PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 安装 PyInstaller..."
    pip3 install pyinstaller
fi

# 清理旧构建
echo "🧹 清理旧构建..."
rm -rf build python-dist *.spec

# 打包
echo "🔨 打包 Python 后端..."
pyinstaller --onefile \
    --name zenblog_backend \
    --distpath python-dist \
    --workpath build \
    --add-data "data:data" \
    --add-data "images:images" \
    --add-data "index.html:." \
    --add-data "logo.png:." \
    --hidden-import uvicorn \
    --hidden-import uvicorn.logging \
    --hidden-import uvicorn.loops \
    --hidden-import uvicorn.loops.auto \
    --hidden-import uvicorn.protocols \
    --hidden-import uvicorn.protocols.http \
    --hidden-import uvicorn.protocols.http.auto \
    --hidden-import uvicorn.protocols.websocket \
    --hidden-import uvicorn.protocols.websocket.auto \
    --hidden-import fastapi \
    --hidden-import pydantic \
    --hidden-import starlette \
    --hidden-import starlette.routing \
    --hidden-import starlette.middleware \
    --hidden-import starlette.middleware.cors \
    --hidden-import starlette.staticfiles \
    --hidden-import starlette.responses \
    --hidden-import requests \
    zenblog_backend.py

echo "✅ Python 后端打包完成！"
echo "   输出目录: python-dist/"
echo ""
echo "   可执行文件:"
ls -lh python-dist/
