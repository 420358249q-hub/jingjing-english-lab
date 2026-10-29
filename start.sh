#!/usr/bin/env bash

# ========================================================
# 静静学习系统 · 一键极简启动脚本
# 专为 Mac / Mac mini (Apple Silicon) 打造
# ========================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "======================================================"
echo "   🚀 正在启动 静静学习系统 · Pro 私教 ..."
echo "======================================================"

# 环境自检与医生模式 (Doctor Mode)
if [ "$1" = "--doctor" ] || [ "$1" = "-d" ]; then
    echo "🩺 正在执行【环境体检与组件完整性自检】..."
    echo "------------------------------------------------------"
    echo "1. 操作系统架构: $(uname -s) $(uname -m)"
    echo "2. 系统 Python 状态: $(command -v python3 2>/dev/null || echo '未检测到')"
    echo "3. 神经语音模型文件:"
    [ -f "models/kokoro-v1.0.onnx" ] && echo "   ✅ Kokoro v1.0 ONNX 模型权重就绪" || echo "   ❌ 缺失 models/kokoro-v1.0.onnx"
    [ -f "models/voices-v1.0.bin" ] && echo "   ✅ 语音特征包 voices-v1.0.bin 就绪" || echo "   ❌ 缺失 models/voices-v1.0.bin"
    echo "4. 课程题库与数据持久化:"
    [ -f "app/courses_database.json" ] && echo "   ✅ 42 门课程大厅题库就绪 (10,328 句真人原声)" || echo "   ❌ 缺失 courses_database.json"
    [ -f "data/jingjing.db" ] && echo "   ✅ SQLite 学习档案与 SM-2 生词库就绪" || echo "   ⚡ SQLite 档案库将在首次启动时自动挂载"
    echo "5. Python 虚拟环境与核心模块:"
    if [ -f "venv/bin/python" ]; then
        ./venv/bin/python -c "import fastapi, uvicorn, kokoro_onnx, soundfile, faster_whisper; print('   ✅ FastAPI / Kokoro ONNX / Faster-Whisper 全部验证通过')" 2>/dev/null || echo "   ⚠️ 依赖包存在缺失，需重新初始化环境"
    else
        echo "   ⚡ 虚拟环境待初始化"
    fi
    echo "------------------------------------------------------"
    echo "🎉 体检完成！如需启动服务，直接执行 ./start.sh 即可。"
    exit 0
fi

# 0. 自动拉取更新（如果是 Git 仓库且网络可用，强制秒级同步最新无冲突代码）
if [ -d ".git" ] && git remote get-url origin >/dev/null 2>&1; then
    echo "🔄 正在检查并同步最新功能 (git sync)..."
    (git fetch origin main && git reset --hard origin/main) >/dev/null 2>&1 && echo "✨ 代码已自动更新至最新版本！" || echo "⚡ 继续使用当前版本（离线或已是最新）"
fi

# 1. 查找最佳 Python 版本 (优先选择 3.11 / 3.12 / 3.10)
PYTHON_BIN=""
for candidate in /opt/homebrew/bin/python3.11 /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.10 /usr/local/bin/python3.11 /usr/local/bin/python3.12 python3.11 python3.12 python3.10 python3; do
    if command -v $candidate &>/dev/null; then
        VER=$($candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
        MAJOR=$(echo $VER | cut -d. -f1)
        MINOR=$(echo $VER | cut -d. -f2)
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 9 ]; then
            PYTHON_BIN=$(command -v $candidate)
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "❌ 未检测到可用的 Python 3 (需要 3.9+)。"
    echo "💡 请在终端执行以下命令安装（任选其一）："
    echo "   1) brew install python@3.11"
    echo "   2) 或访问 https://www.python.org/downloads/macos/ 下载安装"
    read -p "按回车键退出..." dummy
    exit 1
fi

echo "📌 使用系统 Python: $PYTHON_BIN ($($PYTHON_BIN --version))"

# 2. 检查或创建虚拟环境（针对跨机器拷贝 / 路径变更自愈）
VENV_OK=false
if [ -f "venv/bin/python" ] && [ -f "venv/bin/uvicorn" ]; then
    if ./venv/bin/python -c "import uvicorn, fastapi, kokoro_onnx, soundfile" >/dev/null 2>&1; then
        VENV_OK=true
    fi
fi

if [ "$VENV_OK" = false ]; then
    echo "📦 正在初始化运行环境 (跨设备自愈/依赖自检，首次运行约需 1~2 分钟)..."
    rm -rf venv
    $PYTHON_BIN -m venv venv
    ./venv/bin/pip install --upgrade pip -q
    echo "📥 正在安装依赖包 (FastAPI, Kokoro ONNX, SoundFile, faster-whisper)..."
    ./venv/bin/pip install -r requirements.txt
    echo "✅ 环境就绪！"
fi

# 3. 检查模型状态 (若缺失自动下载)
if [ ! -f "models/kokoro-v1.0.onnx" ] || [ ! -f "models/voices-v1.0.bin" ]; then
    echo "📥 未检测到 Kokoro 离线模型，正在自动下载模型权重 (首次运行约需 1~2 分钟)..."
    ./venv/bin/python scripts/download_kokoro.py || echo "⚠️ 自动下载失败，您可以手动将 models 文件夹拷贝到项目中。"
fi

# 4. 检查 Ollama 本地模型服务
echo "🔍 检查本地 Ollama 状态..."
if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "✅ 检测到本地 Ollama 正在运行！"
else
    echo "⚠️  未检测到 Ollama 后台服务。如果需要 AI 实时互动对话，请在 Mac mini 上安装/启动 Ollama。"
    echo "💡 系统内置了智能离线模拟模式，即使没开 Ollama 也能正常体验造句、发音、生词本与跟读！"
fi

# 5. 清理陈旧进程，确保端口可用
HOST="${JJ_HOST:-127.0.0.1}"
PORT="${JJ_PORT:-8000}"
OLD_PID=$(lsof -ti :$PORT 2>/dev/null || true)
if [ -n "$OLD_PID" ]; then
    echo "🧹 释放被占用的端口 $PORT (清理进程: $OLD_PID)..."
    kill -9 $OLD_PID 2>/dev/null || true
    sleep 0.5
fi

# 6. 后台启动 FastAPI 服务
echo "🌐 启动 Web 服务器 (http://${HOST}:${PORT})..."

# 自动在浏览器中打开页面
(sleep 1.5 && open "http://${HOST}:${PORT}") &

mkdir -p data
./venv/bin/uvicorn app.main:app --host "$HOST" --port "$PORT" --reload 2>&1 | tee -a data/server.log
