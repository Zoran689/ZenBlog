#!/bin/bash
# ZenBlog 同步 MySQL → JSON → GitHub Pages 一键脚本
# 用法: ./sync_and_push.sh "提交说明"

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

COMMIT_MSG="${1:-"chore: sync data to JSON for GitHub Pages"}"

echo "========================================="
echo "  ZenBlog 同步并推送 GitHub Pages"
echo "========================================="
echo ""

# 1. 同步 MySQL → JSON
echo "📥 步骤1: 从 MySQL 同步到 JSON..."
python3 sync_to_json.py
echo ""

# 2. 检查是否有数据变更
if git diff --quiet data/; then
    echo "⏭️  数据无变更，跳过提交"
else
    # 3. 提交
    echo "📦 步骤2: 提交数据变更..."
    git add data/
    git commit -m "$COMMIT_MSG"
    echo ""

    # 4. 推送
    echo "🚀 步骤3: 推送到 GitHub..."
    git push origin main
    echo ""

    # 5. 触发 GitHub Pages 部署
    echo "🌐 步骤4: 触发 GitHub Pages 部署..."
    gh workflow run "Deploy to GitHub Pages" --ref main 2>/dev/null || \
        echo "⚠️  无法触发 workflow，请手动在 GitHub Actions 页面触发"
    echo ""

    echo "✅ 全部完成！"
    echo "   GitHub Pages: https://Zoran689.github.io/ZenBlog/"
    echo "   部署状态:   https://github.com/Zoran689/ZenBlog/actions"
else
    echo "✅ 完成（无变更）"
fi
