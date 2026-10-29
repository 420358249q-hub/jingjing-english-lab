#!/usr/bin/env bash
# ========================================================
# 静静学习系统 · Finder 双击启动器 (支持桌面软链接快捷方式)
# ========================================================

# 解析真实脚本所在物理目录
SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

cd "$DIR"
bash ./start.sh
