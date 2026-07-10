#!/usr/bin/env python3
"""
hook-notify 桌面应用
双击打开，逐步引导你完成 AI 终端通知配置。
"""

import json
import os
import sys
import time
import threading
import tkinter as tk
from tkinter import font as tkfont
from pathlib import Path
from datetime import datetime
from io import BytesIO

import requests
import qrcode
from PIL import Image, ImageTk

# ============================================================
# 配置常量
# ============================================================

APP_NAME = "Hook Notify"
APP_DIR = Path.home() / ".hook-notify"
CONFIG_FILE = APP_DIR / "config.json"

DEFAULT_APP_TOKEN = "AT_mx4gZJ9t47IibakBWuCQ5qoNyfn0eJXo"
DEFAULT_APP_ID = 131553

WXPUSHER_SUBSCRIBE_URL = f"https://wxpusher.zjiecode.com/wxuser/?type=1&id={DEFAULT_APP_ID}#/follow"
WXPUSHER_USERS_URL = "https://wxpusher.zjiecode.com/api/fun/wxuser/v2"
WXPUSHER_SEND_URL = "https://wxpusher.zjiecode.com/api/send/message"

# 颜色主题
COLOR_BG = "#1e1e2e"
COLOR_CARD = "#2a2a3e"
COLOR_ACCENT = "#7c3aed"
COLOR_ACCENT_HOVER = "#8b5cf6"
COLOR_TEXT = "#e2e8f0"
COLOR_TEXT_MUTED = "#94a3b8"
COLOR_SUCCESS = "#22c55e"
COLOR_WARNING = "#f59e0b"
COLOR_ERROR = "#ef4444"
COLOR_BORDER = "#3f3f5c"

# ============================================================
# 工具函数
# ============================================================

# notify.py 的核心内容，部署到 ~/.hook-notify/ 供 Hook 调用
NOTIFY_SCRIPT = r'''#!/usr/bin/env python3
"""hook-notify: 发送通知到微信。供 AI 终端 Hook 调用。"""
import json, os, sys, requests

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
WXPUSHER_SEND_URL = "https://wxpusher.zjiecode.com/api/send/message"

def send():
    if not os.path.exists(CONFIG_FILE):
        print("未配置，请先运行 hook-notify 应用")
        sys.exit(1)
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    msg = sys.argv[1] if len(sys.argv) > 1 else "AI 终端需要你的确认"
    payload = {
        "appToken": cfg.get("appToken", ""),
        "content": msg,
        "contentType": 1,
        "uids": [cfg.get("uid", "")],
        "summary": msg[:50],
    }
    try:
        resp = requests.post(WXPUSHER_SEND_URL, json=payload,
                             headers={"Content-Type": "application/json"}, timeout=10)
        if resp.json().get("code") == 1000:
            print("通知已发送")
        else:
            print(f"发送失败: {resp.json().get('msg')}")
    except Exception as e:
        print(f"发送失败: {e}")

if __name__ == "__main__":
    send()
'''


def deploy_notify_script():
    """将 notify.py 部署到 ~/.hook-notify/。"""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    script_path = APP_DIR / "notify.py"
    if not script_path.exists():
        with open(script_path, "w") as f:
            f.write(NOTIFY_SCRIPT.strip())
        os.chmod(script_path, 0o755)
    return script_path


def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(cfg):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def detect_terminals():
    """检测系统中已安装的 AI 终端。"""
    import subprocess
    known = {
        "Claude Code": {"paths": ["~/.claude"], "cmds": ["claude"]},
        "OpenAI Codex CLI": {"paths": ["~/.codex"], "cmds": ["codex"]},
        "CodeBuddy": {"paths": ["~/.codebuddy"], "cmds": ["codebuddy"]},
        "Windsurf": {"paths": ["~/.windsurf"], "cmds": ["windsurf"]},
        "Cursor": {"paths": [], "cmds": ["cursor"]},
        "GitHub Copilot": {"paths": [], "cmds": ["gh"]},
    }
    detected = []
    home = os.path.expanduser("~")
    for name, info in known.items():
        found = False
        for p in info["paths"]:
            if os.path.exists(os.path.expanduser(p)):
                found = True
                break
        if not found:
            for cmd in info["cmds"]:
                try:
                    subprocess.run(["which", cmd], capture_output=True, check=True)
                    found = True
                    break
                except Exception:
                    pass
        if found:
            detected.append(name)
    return detected


def configure_claude_code_hook():
    """配置 Claude Code 的 Stop hook。"""
    settings_path = os.path.expanduser("~/.claude/settings.json")
    existing = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path) as f:
                existing = json.load(f)
        except Exception:
            pass

    script_path = APP_DIR / "notify.py"
    hook_cmd = f"python3 {script_path} 'Claude Code 已停止，需要你的确认'"
    hook_entry = {"type": "command", "command": hook_cmd, "async": True}

    existing.setdefault("hooks", {}).setdefault("Stop", [])
    for group in existing["hooks"]["Stop"]:
        for h in group.get("hooks", []):
            if h.get("command") == hook_cmd:
                return True  # already configured

    existing["hooks"]["Stop"].append({"hooks": [hook_entry]})
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    return True


def send_test_notification(app_token, uid):
    """发送测试通知。"""
    try:
        resp = requests.post(WXPUSHER_SEND_URL, json={
            "appToken": app_token,
            "content": "\U0001f389 hook-notify \u914d\u7f6e\u6210\u529f\uff01\u5f53 AI \u7ec8\u7aef\u9700\u8981\u4f60\u786e\u8ba4\u65f6\uff0c\u4f60\u5c06\u6536\u5230\u6b64\u901a\u77e5\u3002",
            "contentType": 1,
            "uids": [uid],
            "summary": "hook-notify \u914d\u7f6e\u6210\u529f",
        }, headers={"Content-Type": "application/json"}, timeout=10)
        return resp.json().get("code") == 1000
    except Exception:
        return False


# ============================================================
# GUI 组件
# ============================================================

class RoundedFrame(tk.Frame):
    """圆角卡片容器。"""
    def __init__(self, parent, **kwargs):
        bg = kwargs.pop("bg", COLOR_CARD)
        super().__init__(parent, bg=bg, **kwargs)


class StepButton(tk.Button):
    """风格化的按钮。"""
    def __init__(self, parent, text, command, primary=True, **kwargs):
        if primary:
            bg = COLOR_ACCENT
            fg = "white"
        else:
            bg = COLOR_BORDER
            fg = COLOR_TEXT
        super().__init__(
            parent, text=text, command=command,
            bg=bg, fg=fg, activebackground=COLOR_ACCENT_HOVER,
            activeforeground="white",
            font=("Helvetica", 13),
            relief="flat", bd=0, padx=24, pady=10,
            cursor="hand2",
            **kwargs
        )


# ============================================================
# 主应用
# ============================================================

class HookNotifyApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("540x640")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        # 居中窗口
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"+{x}+{y}")

        # 状态
        self.current_frame = None
        self.config = load_config()
        self.app_token = self.config.get("appToken", DEFAULT_APP_TOKEN)
        self.uid = self.config.get("uid", "")
        self.qr_image = None

        # 生成 QR 码图片（提前生成）
        self._generate_qr()

        # 显示首页
        self.show_welcome()

    def _generate_qr(self):
        """预生成 QR 码 PIL Image。"""
        qr = qrcode.QRCode(border=2, box_size=8)
        qr.add_data(WXPUSHER_SUBSCRIBE_URL)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        # 缩放
        img = img.resize((260, 260), Image.NEAREST)
        self.qr_image = ImageTk.PhotoImage(img)

    def _clear(self):
        """清除当前页面。"""
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = tk.Frame(self.root, bg=COLOR_BG)
        self.current_frame.pack(fill="both", expand=True)

    def _title_label(self, text):
        """创建标题。"""
        return tk.Label(
            self.current_frame, text=text,
            font=("Helvetica", 22, "bold"),
            bg=COLOR_BG, fg=COLOR_TEXT
        )

    def _subtitle_label(self, text):
        """创建副标题。"""
        return tk.Label(
            self.current_frame, text=text,
            font=("Helvetica", 13),
            bg=COLOR_BG, fg=COLOR_TEXT_MUTED
        )

    def _card_frame(self, **kwargs):
        """创建卡片容器。"""
        return tk.Frame(self.current_frame, bg=COLOR_CARD, **kwargs)

    # ============================================================
    # Step 1: 欢迎页
    # ============================================================

    def show_welcome(self):
        self._clear()

        # 顶部图标
        tk.Label(
            self.current_frame, text="\U0001f514",
            font=("Helvetica", 48),
            bg=COLOR_BG, fg=COLOR_TEXT
        ).pack(pady=(80, 16))

        self._title_label("AI \u7ec8\u7aef\u901a\u77e5\u52a9\u624b").pack(pady=(0, 8))
        self._subtitle_label(
            "\u5f53 AI \u7ec8\u7aef\u9700\u8981\u4f60\u786e\u8ba4\u65f6\uff0c\u7acb\u523b\u63a8\u9001\u901a\u77e5\u5230\u4f60\u7684\u5fae\u4fe1"
        ).pack(pady=(0, 4))

        self._subtitle_label(
            "\u518d\u4e5f\u4e0d\u7528\u76ef\u7740\u7ec8\u7aef\u53d1\u5446\u4e86"
        ).pack(pady=(0, 40))

        # 卡片：安装步骤预览
        card = self._card_frame()
        card.pack(padx=40, pady=(0, 30), fill="x")
        card.configure(padx=20, pady=20)

        steps_text = [
            ("\u2705", "\u5fae\u4fe1\u626b\u7801\u5173\u6ce8\u516c\u4f17\u53f7"),
            ("\u2705", "\u81ea\u52a8\u8bc6\u522b\u4f60\u7684\u8eab\u4efd"),
            ("\u2705", "\u68c0\u6d4b\u5e76\u914d\u7f6e AI \u7ec8\u7aef Hook"),
            ("\u2705", "\u5b8c\u6210\uff01\u5f00\u59cb\u4f7f\u7528"),
        ]

        for icon, desc in steps_text:
            row = tk.Frame(card, bg=COLOR_CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=icon, font=("Helvetica", 14), bg=COLOR_CARD, fg=COLOR_SUCCESS).pack(side="left")
            tk.Label(row, text=desc, font=("Helvetica", 13), bg=COLOR_CARD, fg=COLOR_TEXT).pack(side="left", padx=(8, 0))

        # 开始按钮
        StepButton(
            self.current_frame, text="\u5f00\u59cb\u914d\u7f6e",
            command=self.show_qrcode, primary=True
        ).pack(pady=(10, 0))

    # ============================================================
    # Step 2: 扫码关注
    # ============================================================

    def show_qrcode(self):
        self._clear()

        # 步骤指示器
        self._step_indicator(1)

        self._title_label("\U0001f4f1 \u5fae\u4fe1\u626b\u7801\u5173\u6ce8").pack(pady=(30, 8))
        self._subtitle_label("\u8bf7\u7528\u5fae\u4fe1\u626b\u63cf\u4e0b\u65b9\u4e8c\u7ef4\u7801").pack(pady=(0, 4))
        self._subtitle_label("\u5173\u6ce8 WxPusher \u516c\u4f17\u53f7\u540e\u70b9\u51fb\u4e0b\u65b9\u6309\u94ae").pack(pady=(0, 20))

        # QR 码卡片
        card = self._card_frame()
        card.pack(padx=40, pady=(0, 20))
        card.configure(padx=20, pady=20)

        qr_label = tk.Label(card, image=self.qr_image, bg=COLOR_CARD)
        qr_label.pack()

        tk.Label(
            card, text="\u5fae\u4fe1\u626b\u7801 \u2192 \u5173\u6ce8\u516c\u4f17\u53f7 \u2192 \u8ba2\u9605\u6210\u529f",
            font=("Helvetica", 11), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED
        ).pack(pady=(12, 0))

        # 按钮
        btn_frame = tk.Frame(self.current_frame, bg=COLOR_BG)
        btn_frame.pack(pady=(0, 20))

        StepButton(
            btn_frame, text="\u2714 \u6211\u5df2\u626b\u7801\u5173\u6ce8\uff0c\u7ee7\u7eed",
            command=self.show_user_select, primary=True
        ).pack()

        # 状态提示
        self._status_label = tk.Label(
            self.current_frame, text="",
            font=("Helvetica", 11), bg=COLOR_BG, fg=COLOR_TEXT_MUTED
        )
        self._status_label.pack()

    # ============================================================
    # Step 3: 选择用户
    # ============================================================

    def show_user_select(self):
        self._update_status("\u6b63\u5728\u67e5\u8be2\u7528\u6237\u5217\u8868...")

        def _query():
            try:
                resp = requests.get(WXPUSHER_USERS_URL, params={
                    "appToken": self.app_token,
                    "page": 1, "pageSize": 50,
                }, timeout=10)
                data = resp.json()
                if data.get("code") == 1000:
                    users = data.get("data", {}).get("records", [])
                    users.sort(key=lambda u: u.get("createTime", 0), reverse=True)
                    self.root.after(0, lambda: self._show_user_select_ui(users))
                else:
                    self.root.after(0, lambda: self._show_error(
                        f"\u67e5\u8be2\u5931\u8d25: {data.get('msg')}"
                    ))
            except Exception as e:
                self.root.after(0, lambda: self._show_error(f"\u7f51\u7edc\u9519\u8bef: {e}"))

        threading.Thread(target=_query, daemon=True).start()

    def _show_user_select_ui(self, users):
        self._clear()
        self._step_indicator(2)

        if not users:
            self._title_label("\u26a0\ufe0f \u672a\u627e\u5230\u7528\u6237").pack(pady=(40, 8))
            self._subtitle_label("\u8bf7\u786e\u4fdd\u5df2\u7528\u5fae\u4fe1\u626b\u7801\u5173\u6ce8\u516c\u4f17\u53f7").pack(pady=(0, 20))

            btn_frame = tk.Frame(self.current_frame, bg=COLOR_BG)
            btn_frame.pack(pady=(10, 0))
            StepButton(btn_frame, text="\u2190 \u8fd4\u56de\u91cd\u65b0\u626b\u7801", command=self.show_qrcode, primary=False).pack(side="left", padx=5)
            StepButton(btn_frame, text="\U0001f504 \u91cd\u65b0\u67e5\u8be2", command=self.show_user_select, primary=True).pack(side="left", padx=5)
            return

        if len(users) == 1:
            self._title_label("\u2705 \u627e\u5230\u4f60\u4e86\uff01").pack(pady=(40, 8))
            nickname = users[0].get("nickName") or "\u7528\u6237"
            self._subtitle_label(f"\u5fae\u4fe1\u6635\u79f0: {nickname}").pack(pady=(0, 20))

            # 小字显示 UID
            card = self._card_frame()
            card.pack(padx=60, pady=(0, 20))
            card.configure(padx=16, pady=12)
            tk.Label(card, text=f"UID: {users[0]['uid']}", font=("Helvetica", 11),
                     bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack()

            self.selected_uid = users[0]["uid"]

            btn_frame = tk.Frame(self.current_frame, bg=COLOR_BG)
            btn_frame.pack(pady=(10, 0))
            StepButton(btn_frame, text="\u2714 \u8fd9\u662f\u6211\uff0c\u7ee7\u7eed", command=self.show_terminals, primary=True).pack()
        else:
            self._title_label("\U0001f465 \u9009\u62e9\u4f60\u7684\u8d26\u53f7").pack(pady=(30, 8))
            self._subtitle_label(f"\u627e\u5230 {len(users)} \u4e2a\u5df2\u5173\u6ce8\u7528\u6237\uff0c\u8bf7\u9009\u62e9\u4f60\u81ea\u5df1").pack(pady=(0, 16))

            self._user_buttons = []
            self.selected_uid = tk.StringVar()

            list_frame = tk.Frame(self.current_frame, bg=COLOR_BG)
            list_frame.pack(padx=40, fill="x")

            for i, u in enumerate(users):
                nickname = u.get("nickName") or "\u672a\u8bbe\u7f6e\u6635\u79f0"
                ts = u.get("createTime", 0)
                if ts:
                    t = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M")
                else:
                    t = ""
                marker = " \u2190 \u6700\u65b0" if i == 0 else ""

                card = self._card_frame()
                card.pack(fill="x", pady=3)
                card.configure(padx=16, pady=12)

                # Radio button + 用户信息
                rb = tk.Radiobutton(
                    card, text=f"{nickname}{marker}",
                    variable=self.selected_uid, value=u["uid"],
                    font=("Helvetica", 13),
                    bg=COLOR_CARD, fg=COLOR_TEXT,
                    activebackground=COLOR_CARD, activeforeground=COLOR_TEXT,
                    selectcolor=COLOR_CARD,
                    indicatoron=True
                )
                rb.pack(anchor="w")
                if i == 0:
                    rb.select()

                tk.Label(
                    card, text=f"UID: {u['uid']}  |  \u5173\u6ce8\u65f6\u95f4: {t}",
                    font=("Helvetica", 10), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED
                ).pack(anchor="w", padx=(24, 0))

            btn_frame = tk.Frame(self.current_frame, bg=COLOR_BG)
            btn_frame.pack(pady=(16, 0))
            StepButton(btn_frame, text="\u2714 \u786e\u8ba4\u9009\u62e9\uff0c\u7ee7\u7eed", command=self._confirm_user, primary=True).pack()

    def _confirm_user(self):
        uid = self.selected_uid
        if isinstance(uid, tk.StringVar):
            uid = uid.get()
        if uid:
            self.uid = uid
            self.show_terminals()

    # ============================================================
    # Step 4: 检测终端并配置 Hook
    # ============================================================

    def show_terminals(self):
        self._clear()
        self._step_indicator(3)

        self._title_label("\U0001f50d \u68c0\u6d4b AI \u7ec8\u7aef").pack(pady=(30, 8))
        self._subtitle_label("\u6b63\u5728\u626b\u63cf\u4f60\u7684\u7535\u8111...").pack(pady=(0, 20))

        # 加载动画
        self._progress_label = tk.Label(
            self.current_frame, text="\u23f3",
            font=("Helvetica", 36), bg=COLOR_BG, fg=COLOR_TEXT
        )
        self._progress_label.pack(pady=(20, 20))

        # 后台检测
        def _detect():
            time.sleep(0.5)  # 给点动画时间
            terminals = detect_terminals()
            self.root.after(0, lambda: self._show_terminal_results(terminals))

        threading.Thread(target=_detect, daemon=True).start()

    def _show_terminal_results(self, terminals):
        self._clear()
        self._step_indicator(3)

        self._title_label("\U0001f500 \u914d\u7f6e AI \u7ec8\u7aef Hook").pack(pady=(30, 8))

        if terminals:
            self._subtitle_label(f"\u68c0\u6d4b\u5230 {len(terminals)} \u4e2a AI \u7ec8\u7aef").pack(pady=(0, 16))
        else:
            self._subtitle_label("\u672a\u68c0\u6d4b\u5230 AI \u7ec8\u7aef").pack(pady=(0, 16))

        card = self._card_frame()
        card.pack(padx=40, pady=(0, 20), fill="x")
        card.configure(padx=20, pady=16)

        # 部署 notify.py 到 ~/.hook-notify/ 供 Hook 调用
        deploy_notify_script()

        config_results = []
        for name in terminals:
            row = tk.Frame(card, bg=COLOR_CARD)
            row.pack(fill="x", pady=4)

            if name == "Claude Code":
                try:
                    configure_claude_code_hook()
                    status = "\u2705 \u5df2\u914d\u7f6e"
                    color = COLOR_SUCCESS
                except Exception:
                    status = "\u26a0\ufe0f \u914d\u7f6e\u5931\u8d25"
                    color = COLOR_WARNING
            else:
                status = "\U0001f6e0 \u8bf7\u624b\u52a8\u914d\u7f6e"
                color = COLOR_TEXT_MUTED

            tk.Label(row, text=name, font=("Helvetica", 13), bg=COLOR_CARD, fg=COLOR_TEXT).pack(side="left")
            tk.Label(row, text=status, font=("Helvetica", 12), bg=COLOR_CARD, fg=color).pack(side="right")

        if not terminals:
            tk.Label(
                card, text="\u652f\u6301\u81ea\u52a8\u914d\u7f6e\uff1aClaude Code\n\u5176\u4ed6\u7ec8\u7aef\u8bf7\u53c2\u8003 README \u624b\u52a8\u914d\u7f6e",
                font=("Helvetica", 12), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED, justify="left"
            ).pack(pady=(8, 4))

        # 保存配置
        self.config["appToken"] = self.app_token
        self.config["uid"] = self.uid
        self.config["version"] = 1
        self.config["configured_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        save_config(self.config)

        # 按钮
        btn_frame = tk.Frame(self.current_frame, bg=COLOR_BG)
        btn_frame.pack(pady=(10, 0))
        StepButton(btn_frame, text="\u2714 \u5b8c\u6210\u914d\u7f6e", command=self.show_done, primary=True).pack()

    # ============================================================
    # Step 5: 完成
    # ============================================================

    def show_done(self):
        self._clear()
        self._step_indicator(4)

        self._title_label("\U0001f389 \u914d\u7f6e\u5b8c\u6210\uff01").pack(pady=(40, 8))
        self._subtitle_label("\u6b63\u5728\u53d1\u9001\u6d4b\u8bd5\u901a\u77e5...").pack(pady=(0, 20))

        self._done_status = tk.Label(
            self.current_frame, text="\u23f3",
            font=("Helvetica", 36), bg=COLOR_BG, fg=COLOR_TEXT
        )
        self._done_status.pack(pady=(10, 20))

        # 后台发送测试通知
        def _send_test():
            ok = send_test_notification(self.app_token, self.uid)
            self.root.after(0, lambda: self._show_done_result(ok))

        threading.Thread(target=_send_test, daemon=True).start()

    def _show_done_result(self, success):
        self._done_status.configure(
            text="\u2705 \u6d4b\u8bd5\u901a\u77e5\u5df2\u53d1\u9001\uff0c\u8bf7\u68c0\u67e5\u5fae\u4fe1\uff01" if success
            else "\u26a0\ufe0f \u6d4b\u8bd5\u901a\u77e5\u53d1\u9001\u5931\u8d25\uff0c\u8bf7\u68c0\u67e5\u7f51\u7edc"
        )

        card = self._card_frame()
        card.pack(padx=40, pady=(10, 20), fill="x")
        card.configure(padx=20, pady=16)

        tips = [
            "\u2714 \u6bcf\u6b21 Claude Code \u505c\u4e0b\u6765\u7b49\u4f60\u65f6\uff0c\u5fae\u4fe1\u4f1a\u6536\u5230\u901a\u77e5",
            "\u2714 \u4f60\u53ef\u4ee5\u653e\u5fc3\u79bb\u5f00\u684c\u9762\uff0c\u4e0d\u7528\u76ef\u7740\u5c4f\u5e55",
            "\u2714 \u5176\u4ed6\u4eba\u4e5f\u53ef\u4ee5\u626b\u7801\u52a0\u5165\uff0c\u5171\u4eab\u901a\u77e5",
        ]
        for tip in tips:
            tk.Label(card, text=tip, font=("Helvetica", 12), bg=COLOR_CARD, fg=COLOR_TEXT).pack(anchor="w", pady=2)

        StepButton(
            self.current_frame, text="\u5173\u95ed\u7a97\u53e3",
            command=self.root.destroy, primary=True
        ).pack(pady=(10, 0))

    # ============================================================
    # 错误页
    # ============================================================

    def _show_error(self, msg):
        self._clear()
        self._title_label("\u274c \u51fa\u9519\u4e86").pack(pady=(40, 8))
        self._subtitle_label(msg).pack(pady=(0, 20))

        btn_frame = tk.Frame(self.current_frame, bg=COLOR_BG)
        btn_frame.pack(pady=(10, 0))
        StepButton(btn_frame, text="\u2190 \u8fd4\u56de", command=self.show_qrcode, primary=False).pack(side="left", padx=5)
        StepButton(btn_frame, text="\U0001f504 \u91cd\u8bd5", command=self.show_user_select, primary=True).pack(side="left", padx=5)

    # ============================================================
    # 辅助方法
    # ============================================================

    def _step_indicator(self, step):
        """显示步骤进度指示器。"""
        frame = tk.Frame(self.current_frame, bg=COLOR_BG)
        frame.pack(pady=(16, 0))
        steps = ["\u626b\u7801", "\u8eab\u4efd", "\u914d\u7f6e", "\u5b8c\u6210"]
        for i, s in enumerate(steps):
            if i + 1 < step:
                dot = "\u25c9"
                color = COLOR_SUCCESS
            elif i + 1 == step:
                dot = "\u25ce"
                color = COLOR_ACCENT
            else:
                dot = "\u25cb"
                color = COLOR_TEXT_MUTED
            tk.Label(frame, text=dot, font=("Helvetica", 11), bg=COLOR_BG, fg=color).pack(side="left", padx=4)
            tk.Label(frame, text=s, font=("Helvetica", 10), bg=COLOR_BG, fg=color).pack(side="left", padx=(1, 12))

    def _update_status(self, text):
        """更新状态标签。"""
        try:
            self._status_label.configure(text=text)
        except Exception:
            pass

    def run(self):
        self.root.mainloop()


# ============================================================
# 入口
# ============================================================

def main():
    app = HookNotifyApp()
    app.run()


if __name__ == "__main__":
    main()
