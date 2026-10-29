"""
静静学习系统 · GitHub Issue 自动化遥测与故障反馈服务
自动捕获运行时严重错误，并将系统诊断数据自动推送到开发者 GitHub 仓库 Issue。
"""

import os
import sys
import json
import time
import hashlib
import asyncio
import datetime
import subprocess
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "telemetry_config.json")
LOG_FILE = os.path.join(DATA_DIR, "server.log")

DEFAULT_REPO = "420358249q-hub/jingjing-english-lab"

# 防刷机制：同一个错误哈希在 15 分钟内最多只上报一次
_reported_hashes: Dict[str, float] = {}
DEDUPE_WINDOW_SEC = 900


def get_telemetry_token() -> Optional[str]:
    """获取 GitHub Token（支持环境变量与 data/telemetry_config.json）"""
    # 1. 环境变量优先
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("JJ_TELEMETRY_TOKEN")
    if token:
        return token.strip()

    # 2. 读取配置文件
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("github_token", "").strip() or None
        except Exception:
            pass
    return None


def get_recent_server_logs(max_lines: int = 60) -> str:
    """提取最近的服务器日志"""
    if not os.path.exists(LOG_FILE):
        return "无 server.log 日志记录"
    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            return "".join(lines[-max_lines:])
    except Exception as e:
        return f"读取日志异常: {e}"


def send_github_issue(
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
    repo: str = DEFAULT_REPO
) -> bool:
    """
    提交 GitHub Issue：
    支持直接通过 GitHub REST API 或通过宿主机已登录的 gh 命令行工具。
    """
    labels = labels or ["telemetry"]
    token = get_telemetry_token()

    # 方式 A：如果配置了 Token，直接走官方 REST API (无需本地安装 gh)
    if token:
        api_url = f"https://api.github.com/repos/{repo}/issues"
        payload = json.dumps({
            "title": title,
            "body": body,
            "labels": labels
        }).encode("utf-8")

        req = urllib.request.Request(api_url, data=payload, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", "Jingjing-English-Lab-Telemetry")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if 200 <= resp.status < 300:
                    print(f"✅ [Telemetry] GitHub Issue 自动提交成功: {title}")
                    return True
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(f"⚠️ [Telemetry] GitHub API 请求失败 ({e.code}): {err_body}")
        except Exception as e:
            print(f"⚠️ [Telemetry] 网络上报失败: {e}")

    # 方式 B：通过本机可能存在的 gh CLI 提交
    try:
        label_args = []
        for l in labels:
            label_args.extend(["--label", l])
        cmd = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body] + label_args
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            print(f"✅ [Telemetry] 通过 gh CLI 创建 Issue 成功: {res.stdout.strip()}")
            return True
    except Exception:
        pass

    return False


async def report_telemetry_issue(
    category: str,
    summary: str,
    detail: str = "",
    context: Optional[Dict[str, Any]] = None,
    is_user_feedback: bool = False
) -> bool:
    """
    格式化并异步上报故障报告或用户反馈
    """
    context = context or {}
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 去重检查（用户主动反馈不去重）
    sig = f"{category}:{summary}:{detail}"
    sig_hash = hashlib.md5(sig.encode("utf-8")).hexdigest()
    now_ts = time.time()

    if not is_user_feedback:
        last_time = _reported_hashes.get(sig_hash, 0)
        if now_ts - last_time < DEDUPE_WINDOW_SEC:
            print(f"⏳ [Telemetry] 相似报错短时间内已上报，已自动跳过去重: {summary}")
            return False
        _reported_hashes[sig_hash] = now_ts

    # 提取系统状态
    from app.tts_engine import check_kokoro_status
    kokoro_info = check_kokoro_status()
    server_logs = get_recent_server_logs(60)

    # 组合 Markdown Issue 文本
    issue_type = "🙋‍♀️ 用户主动报障与反馈" if is_user_feedback else "🚨 运行时异常自动告警"
    labels = ["user-feedback"] if is_user_feedback else ["telemetry", "bug"]

    md_body = f"""### {issue_type}

- **发生时间**：`{now_str}`
- **所属模块**：`{category}`
- **问题概要**：{summary}

---

#### 📝 详细描述与上下文
```text
{detail or '无额外异常详情'}
```

<details>
<summary>📋 最近 60 行服务器日志 (Server Logs)</summary>

```text
{server_logs}
```
</details>

<details>
<summary>⚙️ 本地环境与语音引擎诊断 (Environment Diagnostic)</summary>

- **平台**：`{sys.platform}`
- **Python**：`{sys.version.split()[0]}`
- **Kokoro 神经模型**：`{'就绪 (Ready)' if kokoro_info.get('available') else '未就绪 (Offline)'}`
- **模型路径**：`{kokoro_info.get('model_path')}`
- **前端环境**：`{context.get('user_agent', '未知浏览器')}`
- **前端报错缓存**：
```json
{json.dumps(context.get('frontend_logs', []), ensure_ascii=False, indent=2)}
```
</details>

> 💡 *本 Issue 由【静静学习系统 · 自动化遥测模块】实时推送生成。*
"""

    title_prefix = "[User Feedback]" if is_user_feedback else f"[Auto Alert][{category}]"
    title = f"{title_prefix} {summary[:50]}"

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, send_github_issue, title, md_body, labels)
