#!/usr/bin/env python3
"""
hook-notify: AI 终端通知助手
当 AI 终端需要你的确认时，通过 WxPusher 推送通知到你的微信。

用法:
  python3 notify.py                    发送默认通知
  python3 notify.py "自定义消息"        发送自定义通知
  python3 notify.py --setup            重新运行安装向导
  python3 notify.py --test             发送测试通知
  python3 notify.py --status           查看当前配置状态

首次运行会自动进入安装向导。
"""

import json
import os
import sys
import subprocess
import time
import re
from pathlib import Path

try:
    import requests
except ImportError:
    print("正在安装依赖 requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# ============================================================
# 配置
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "config.json"

WXPUSHER_SEND_URL = "https://wxpusher.zjiecode.com/api/send/message"
WXPUSHER_USERS_URL = "https://wxpusher.zjiecode.com/api/fun/wxuser/v2"

# 共享 AppToken（开源版默认使用此 Token，用户也可替换为自己的）
DEFAULT_APP_TOKEN = "AT_mx4gZJ9t47IibakBWuCQ5qoNyfn0eJXo"
DEFAULT_APP_ID = 131553

# WxPusher 公众号订阅链接
WXPUSHER_SUBSCRIBE_URL = f"https://wxpusher.zjiecode.com/wxuser/?type=1&id={DEFAULT_APP_ID}#/follow"

# AI 终端检测规则
KNOWN_TERMINALS = {
    "claude-code": {
        "name": "Claude Code",
        "check_paths": ["~/.claude"],
        "check_commands": ["claude"],
        "hook_config": "claude_code",
    },
    "codex": {
        "name": "OpenAI Codex CLI",
        "check_paths": ["~/.codex"],
        "check_commands": ["codex"],
        "hook_config": None,  # 暂不支持自动配置
    },
    "codebuddy": {
        "name": "CodeBuddy",
        "check_paths": ["~/.codebuddy"],
        "check_commands": ["codebuddy"],
        "hook_config": None,
    },
    "windsurf": {
        "name": "Windsurf",
        "check_paths": ["~/.windsurf"],
        "check_commands": ["windsurf"],
        "hook_config": None,
    },
    "cursor": {
        "name": "Cursor",
        "check_paths": [],
        "check_commands": ["cursor"],
        "hook_config": None,
    },
}

# ============================================================
# 工具函数
# ============================================================

def load_config():
    """加载配置文件。"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_config(config):
    """保存配置文件。"""
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def print_banner():
    """打印欢迎横幅。"""
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║       🔔  AI 终端通知助手  hook-notify        ║")
    print("║   当 AI 等你确认时，微信立刻通知你             ║")
    print("╚══════════════════════════════════════════════╝")
    print()


def print_box(text, char="="):
    """打印带边框的文字。"""
    print(char * 60)
    print(f"  {text}")
    print(char * 60)


def expand_path(path_str):
    """展开 ~ 路径。"""
    return os.path.expanduser(path_str)


def run_command(cmd):
    """静默运行命令，返回是否成功。"""
    try:
        subprocess.run(cmd, shell=True, capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


# ============================================================
# WxPusher API
# ============================================================

def query_users(app_token):
    """查询已关注应用的用户列表。"""
    try:
        resp = requests.get(WXPUSHER_USERS_URL, params={
            "appToken": app_token,
            "page": 1,
            "pageSize": 50,
        }, timeout=10)
        data = resp.json()
        if data.get("code") == 1000:
            records = data.get("data", {}).get("records", [])
            return records
        else:
            print(f"  ⚠ 查询用户失败: code={data.get('code')} msg={data.get('msg')}")
            return []
    except requests.RequestException as e:
        print(f"  ⚠ 网络请求失败: {e}")
        return []


def send_message(app_token, uids, content, content_type=1, summary=None):
    """发送消息到指定用户。"""
    payload = {
        "appToken": app_token,
        "content": content,
        "contentType": content_type,
        "uids": uids,
    }
    if summary:
        payload["summary"] = summary

    try:
        resp = requests.post(
            WXPUSHER_SEND_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        data = resp.json()
        if data.get("code") == 1000:
            return True, "发送成功"
        else:
            return False, data.get("msg", "未知错误")
    except requests.RequestException as e:
        return False, str(e)


# ============================================================
# QR 码显示
# ============================================================

def show_qrcode_terminal(url):
    """在终端中显示 ASCII QR 码。"""
    try:
        import qrcode
        qr = qrcode.QRCode(border=2, box_size=1)
        qr.add_data(url)
        qr.make(fit=True)
        print()
        print("  ╔══════════════════════════════════════╗")
        print("  ║  📱 请用微信扫描以下二维码关注公众号  ║")
        print("  ╚══════════════════════════════════════╝")
        print()
        qr.print_ascii(invert=True)
        print()
        print("  (如果二维码显示异常，请用浏览器打开下方链接)")
        return True
    except ImportError:
        return False


def show_qrcode_url(url):
    """显示链接并用系统默认浏览器打开。"""
    print()
    print("  ┌─────────────────────────────────────────────┐")
    print("  │  请用微信扫描二维码，或打开以下链接扫码：       │")
    print("  │                                             │")
    print(f"  │  {url} │")
    print("  └─────────────────────────────────────────────┘")
    print()

    # 尝试用浏览器打开链接
    try:
        import webbrowser
        webbrowser.open(url)
        print("  ✓ 已自动在浏览器中打开二维码页面")
    except Exception:
        pass


# ============================================================
# AI 终端检测
# ============================================================

def detect_terminals():
    """检测系统中安装了哪些 AI 终端。"""
    detected = []
    home = os.path.expanduser("~")

    for key, info in KNOWN_TERMINALS.items():
        found = False

        # 检查目录
        for path_pattern in info.get("check_paths", []):
            path = expand_path(path_pattern)
            if os.path.exists(path):
                found = True
                break

        # 检查命令
        if not found:
            for cmd in info.get("check_commands", []):
                if run_command(f"which {cmd} 2>/dev/null"):
                    found = True
                    break

        if found:
            detected.append((key, info))

    return detected


# ============================================================
# Hook 配置生成
# ============================================================

def configure_claude_code(script_path):
    """为 Claude Code 配置 Stop hook。"""
    settings_path = os.path.expanduser("~/.claude/settings.json")
    existing = {}

    # 读取已有配置
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {}

    # 构建 hook 命令
    hook_cmd = f"python3 {script_path} 'Claude Code 已停止，需要你的确认'"

    # 构建 hook 条目
    hook_entry = {
        "type": "command",
        "command": hook_cmd,
        "async": True,
    }

    # 合并到现有配置
    if "hooks" not in existing:
        existing["hooks"] = {}
    if "Stop" not in existing["hooks"]:
        existing["hooks"]["Stop"] = []

    # 检查是否已存在相同 hook
    stop_hooks = existing["hooks"]["Stop"]
    hook_group_exists = False
    for group in stop_hooks:
        if "hooks" in group:
            for h in group["hooks"]:
                if h.get("command") == hook_cmd:
                    print(f"  ✓ Claude Code hook 已配置，跳过")
                    return True

    # 添加新 hook
    stop_hooks.append({
        "hooks": [hook_entry]
    })
    existing["hooks"]["Stop"] = stop_hooks

    # 写入配置
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Claude Code hook 已配置 → {settings_path}")
    return True


TERMINAL_HOOK_CONFIGURATORS = {
    "claude_code": configure_claude_code,
}


def configure_terminal_hooks(terminals, script_path):
    """为检测到的 AI 终端配置 hook。"""
    print_box("配置 AI 终端 Hook", char="-")
    print()

    configured = 0
    for key, info in terminals:
        hook_config = info.get("hook_config")
        if hook_config and hook_config in TERMINAL_HOOK_CONFIGURATORS:
            print(f"  [{info['name']}]")
            configurator = TERMINAL_HOOK_CONFIGURATORS[hook_config]
            if configurator(script_path):
                configured += 1
            print()
        else:
            print(f"  [{info['name']}] 自动配置暂不支持，请手动配置 Hook")
            print(f"  参考: https://github.com/xxx/hook-notify#手动配置")
            print()

    return configured


# ============================================================
# 安装向导
# ============================================================

def setup_wizard():
    """交互式安装向导。"""
    config = load_config()

    print_banner()
    print("  首次安装引导")
    print()
    print("  整个过程只需 2 步：")
    print("  1. 微信扫码关注公众号")
    print("  2. 确认你的用户身份")
    print()
    print("─" * 60)
    print()

    # 步骤 1: 配置 AppToken
    app_token = config.get("appToken", "")
    if not app_token:
        app_token = DEFAULT_APP_TOKEN
        config["appToken"] = app_token
    print("  [1/4] AppToken: ✓ 已配置")

    # 步骤 2: 显示 QR 码
    print()
    print("  [2/4] 关注公众号")
    print()

    subscribe_url = WXPUSHER_SUBSCRIBE_URL

    # 尝试显示终端 QR 码
    qr_shown = show_qrcode_terminal(subscribe_url)

    if not qr_shown:
        # 降级为显示链接
        show_qrcode_url(subscribe_url)
    else:
        print()
        print(f"  或用浏览器打开: {subscribe_url}")

    print()
    print("  ⚠ 请用微信扫描上方二维码，关注 WxPusher 公众号")
    print()

    # 步骤 3: 获取 UID
    print("  [3/4] 获取你的用户 UID")
    print()

    uid = config.get("uid", "")
    if uid:
        print(f"  当前 UID: {uid}")
        try:
            keep = input("  保持不变? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            keep = "y"
        if keep in ("n", "no"):
            uid = ""

    if not uid:
        retry_count = 0
        while retry_count < 10:
            try:
                input(f"  扫码关注后，按 Enter 继续... (第 {retry_count + 1} 次尝试)")
            except (EOFError, KeyboardInterrupt):
                print("\n  输入已取消。")
                break
            print()
            print("  正在查询用户列表...")

            users = query_users(app_token)

            if users:
                # 按关注时间倒序排列，最新的在前面
                users.sort(key=lambda u: u.get("createTime", 0), reverse=True)

                print()
                print(f"  找到 {len(users)} 个已关注用户：")
                print()
                for i, u in enumerate(users):
                    nickname = u.get('nickName', '') or '(未设置昵称)'
                    uid_short = u.get('uid', '')[:20] + '...'
                    ts = u.get('createTime', 0)
                    if ts:
                        from datetime import datetime
                        t = datetime.fromtimestamp(ts / 1000).strftime('%Y-%m-%d %H:%M')
                    else:
                        t = '未知'
                    marker = ' ← 最新' if i == 0 else ''
                    print(f"  [{i + 1}] {nickname}{marker}")
                    print(f"      UID: {u.get('uid')}")
                    print(f"      关注时间: {t}")
                    print()

                if len(users) == 1:
                    nickname = users[0].get('nickName', '') or '该用户'
                    print(f"  只有一个用户，自动选择: {nickname}")
                    uid = users[0]["uid"]
                    break
                else:
                    print(f"  如果你刚扫描关注，通常选择第 1 个（最新）。")
                    try:
                        choice = input(f"  请选择你的用户 [1-{len(users)}，默认 1]: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        choice = "1"
                    if not choice:
                        choice = "1"
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(users):
                            uid = users[idx]["uid"]
                            break
                        else:
                            print(f"  无效选择，请输入 1-{len(users)}。")
                    except ValueError:
                        print(f"  无效输入，请输入数字 1-{len(users)}。")
            else:
                print()
                print("  还没有找到用户。请确保：")
                print("  1. 已用微信扫描上方二维码")
                print("  2. 已关注 WxPusher 公众号")
                print("  3. 公众号显示\"订阅成功\"")
                print()
                try:
                    retry = input("  重新查询? [Y/n]: ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    retry = "y"
                if retry in ("n", "no"):
                    break
                retry_count += 1

    if not uid:
        print()
        print("  ⚠ 未能获取 UID。你可以：")
        print("  1. 重新运行 python3 notify.py --setup")
        print(f"  2. 手动编辑 config.json 填入你的 UID")
        return False

    config["uid"] = uid
    save_config(config)
    print(f"  ✓ UID 已保存: {uid}")
    print()

    # 步骤 4: 检测 AI 终端并配置 Hook
    print("  [4/4] 检测 AI 终端并配置 Hook")
    print()
    print("  正在扫描系统中已安装的 AI 终端...")
    print()

    terminals = detect_terminals()

    if terminals:
        print(f"  检测到 {len(terminals)} 个 AI 终端：")
        for key, info in terminals:
            print(f"    - {info['name']}")
        print()
        configure_terminal_hooks(terminals, str(SCRIPT_DIR / "notify.py"))
    else:
        print("  未检测到已安装的 AI 终端。")
        print()
        print("  支持自动配置的终端：Claude Code")
        print("  其他终端请参考 README 手动配置 Hook")
        print()

    # 保存最终配置
    config["version"] = 1
    config["configured_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    save_config(config)

    # 发送测试通知
    print()
    print_box("发送测试通知")
    print()
    ok, msg = send_message(config["appToken"], [config["uid"]],
                           "🎉 hook-notify 安装成功！当 AI 终端需要你确认时，你将收到此通知。",
                           summary="hook-notify 安装成功")
    if ok:
        print("  ✓ 测试通知已发送，请检查微信！")
    else:
        print(f"  ⚠ 测试通知发送失败: {msg}")

    # 完成
    print()
    print_box("安装完成！")
    print()
    print("  使用方式：")
    print()
    print("    python3 notify.py              # 发送默认通知")
    print("    python3 notify.py '自定义消息'   # 发送自定义通知")
    print("    python3 notify.py --test       # 发送测试通知")
    print("    python3 notify.py --status     # 查看状态")
    print("    python3 notify.py --setup      # 重新配置")
    print()
    print("  Claude Code 的 Hook 已自动配置。")
    print("  现在 Claude Code 每次停下来等你时，你的微信都会收到通知。")
    print()

    return True


# ============================================================
# 查看状态
# ============================================================

def show_status():
    """显示当前配置状态。"""
    config = load_config()

    print_banner()
    print_box("当前状态")

    if not config:
        print()
        print("  尚未配置。运行 python3 notify.py --setup 开始安装。")
        return

    print(f"  AppToken: {config.get('appToken', '未设置')[:20]}...")
    uid = config.get("uid", "")
    if isinstance(uid, list):
        print(f"  UID: {uid}")
    else:
        print(f"  UID: {uid}")
    print(f"  配置时间: {config.get('configured_at', '未知')}")
    print()

    # 检测终端
    terminals = detect_terminals()
    if terminals:
        print("  已安装的 AI 终端:")
        for key, info in terminals:
            print(f"    ✓ {info['name']}")
    else:
        print("  未检测到 AI 终端")

    # 检查 hook 配置
    print()
    settings_path = os.path.expanduser("~/.claude/settings.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r") as f:
                settings = json.load(f)
            if "hooks" in settings and "Stop" in settings["hooks"]:
                print("  Claude Code Stop Hook: ✓ 已配置")
            else:
                print("  Claude Code Stop Hook: ✗ 未配置")
        except (json.JSONDecodeError, IOError):
            print("  Claude Code Stop Hook: ✗ 配置文件读取失败")
    else:
        print("  Claude Code Stop Hook: ✗ 未配置")

    print()


# ============================================================
# 主入口
# ============================================================

def main():
    # 解析参数
    is_setup = "--setup" in sys.argv
    is_test = "--test" in sys.argv
    is_status = "--status" in sys.argv
    is_help = "--help" in sys.argv or "-h" in sys.argv

    if is_help:
        print(__doc__)
        return

    if is_status:
        show_status()
        return

    if is_setup:
        print("  配置已重置，重新开始安装向导。")

    if not CONFIG_FILE.exists() or is_setup:
        setup_wizard()
        return

    config = load_config()

    # 兼容旧格式: uids (list) → uid (str)
    if "uid" not in config and "uids" in config:
        uids = config["uids"]
        config["uid"] = uids[0] if isinstance(uids, list) else uids
        save_config(config)

    uid = config.get("uid", "")
    app_token = config.get("appToken", "")
    uids = [uid] if isinstance(uid, str) else uid

    if is_test:
        print_banner()
        print_box("发送测试通知")
        ok, msg = send_message(app_token, uids,
                               "🧪 hook-notify 测试通知 — 链路正常！",
                               summary="测试通知")
        if ok:
            print("  ✓ 测试通知已发送，请检查微信！")
        else:
            print(f"  ⚠ 发送失败: {msg}")
        return

    # 默认：发送通知
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    message = args[0] if args else "AI 终端需要你的确认"
    summary = message[:50]

    ok, msg = send_message(app_token, uids, message, summary=summary)
    if not ok:
        print(f"发送通知失败: {msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
