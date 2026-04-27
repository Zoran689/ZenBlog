#!/bin/bash
# ZenBlog 启动脚本 v5.0
# 仅启动 FastAPI 后端

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

echo "🚀 启动 ZenBlog v5.0..."

# =============================================
# 启动 FastAPI 后端（端口 8877）
# =============================================
echo "📡 启动后端服务 (端口 8877)..."
cd "$SCRIPT_DIR"
nohup python3 zenblog_backend.py > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$LOG_DIR/backend.pid"
echo "✅ 后端已启动 (PID: $BACKEND_PID)"
sleep 2

echo ""
echo "============================================="
echo "✅ ZenBlog 启动完成！"
echo ""
echo "   ZenBlog:      http://localhost:8877/"
echo "============================================="
echo ""
echo "日志文件: $LOG_DIR/backend.log"
echo "停止服务: ./stop.sh"
