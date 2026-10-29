#!/usr/bin/env bash
# ========================================================
# 静静学习系统 · 一键打包脚本（专供发送到 Mac mini）
# ========================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
PARENT_DIR="$( dirname "$DIR" )"
BASE_NAME="$( basename "$DIR" )"

cd "$PARENT_DIR"
TARGET_ZIP="${PARENT_DIR}/jingjing-english-lab-macmini.zip"

echo "======================================================"
echo "📦 正在打包静静学习系统..."
echo "======================================================"
echo "包含内容: 核心服务、Kokoro v1.0离线模型、本地前端资源、学习数据库"
echo "排除内容: venv虚拟环境(避免跨机路径冲突)、__pycache__、.git"

zip -r "$TARGET_ZIP" "$BASE_NAME" \
    -x "*/venv/*" \
    -x "*/.git/*" \
    -x "*/**/__pycache__/*" \
    -x "*/.DS_Store" \
    -x "*/**/.DS_Store"

echo "======================================================"
echo "🎉 打包完成！"
echo "📦 文件路径: $TARGET_ZIP"
echo "👉 通过隔空投送 (AirDrop) 或 U 盘发送到 Mac mini，解压后双击【启动静静学习系统.command】即可！"
echo "======================================================"
