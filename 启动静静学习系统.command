#!/usr/bin/env bash
# ========================================================
# 静静学习系统 · Finder 双击启动器
# ========================================================

SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

cd "$DIR"

# 执行启动脚本
bash ./start.sh
RET=$?

# 如果异常退出，保持终端窗口打开，避免闪退看不清报错
if [ $RET -ne 0 ]; then
  echo ""
  echo "======================================================"
  echo "❌ 启动异常中断 (错误码: $RET)"
  echo "💡 终端窗口已保持打开，请将上述报错截图发给开发者排查。"
  echo "======================================================"
  echo "按回车键关闭此窗口..."
  read dummy
fi
