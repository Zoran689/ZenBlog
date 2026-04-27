#!/bin/bash
# ZenBlog 停止脚本 v5.0

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"

echo "🛑 停止 ZenBlog..."

# 停止后端
PID_FILE="$LOG_DIR/backend.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID" && echo "✅ 后端已停止 (PID: $PID)" || echo "⚠️  停止失败"
    else
        echo "⏭️  后端未运行"
    fi
    rm -f "$PID_FILE"
else
    # 兜底：按端口杀
    lsof -t -i :8877 | xargs kill -9 2>/dev/null && echo "✅ 已清理端口 8877"
fi

echo "✅ 全部服务已停止"
