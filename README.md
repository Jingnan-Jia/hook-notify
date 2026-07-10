# 🔔 hook-notify — AI 终端通知助手

当 Claude Code、Codex、CodeBuddy 等 AI 终端需要你确认时，**立刻推送通知到你的微信**。

你再也不用盯着终端发呆，也不用担心离开座位后回来发现 AI 一直在等你授权。

## 🚀 安装

### 一行命令（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/xxx/hook-notify/main/install.sh | bash
```

### 或本地安装

```bash
git clone https://github.com/xxx/hook-notify.git
cd hook-notify
bash install.sh
```

## 📋 安装过程只需 2 步

```
安装脚本运行
  │
  ├─ 1. 终端弹出二维码 → 微信扫码关注公众号
  │
  ├─ 2. 确认你的微信昵称 → 自动获取 UID
  │
  └─ 3. 自动检测并配置 AI 终端的 Hook
        │
        └─ 收到测试通知 🎉
```

全程无需打开网页、无需注册账号、无需手动填写任何配置。

## 🛠 支持哪些 AI 终端？

| 终端 | 自动配置 Hook | 手动配置 |
|------|:--:|:--:|
| **Claude Code** | ✅ | — |
| OpenAI Codex CLI | — | 待适配 |
| CodeBuddy | — | 待适配 |
| Windsurf | — | 待适配 |
| Cursor | — | 待适配 |

## 📖 使用

安装完成后：

```bash
# 发送默认通知
notify.py

# 发送自定义消息
notify.py "构建已完成，请检查"

# 测试通知
notify.py --test

# 查看当前状态
notify.py --status

# 重新配置
notify.py --setup
```

安装后，Claude Code 每次完成任务停下来等你时，你的微信会自动收到通知。

## 🔧 手动配置其他 AI 终端

如果某个终端不支持自动配置，你可以手动在它的 Hook 设置中添加：

```bash
python3 ~/.hook-notify/notify.py "终端名称 需要你的确认"
```

### Codex CLI

在 `~/.codex/config.yaml` 中添加 hook（如有 Hook 功能）。

### CodeBuddy / Windsurf

请查看对应文档的 Hook 配置章节。

## 🏗 工作原理

```
AI 终端完成任务 / 需要确认
        │
        ▼
Hook 触发 (Stop 事件)
        │
        ▼
notify.py 调用 WxPusher API
        │
        ▼
WxPusher 公众号推送
        │
        ▼
你的微信收到通知 📱
```

## 🔒 隐私

- 你的 AppToken 和 UID 只存储在本地 `~/.hook-notify/config.json` 中
- 通知通过 WxPusher 的加密通道推送
- 开源代码，所有逻辑可审查

## 🤝 贡献

欢迎 PR！特别需要：
- 为更多 AI 终端适配自动 Hook 配置
- 支持更多推送渠道（Bark、Telegram、钉钉、飞书等）

## 📄 许可

MIT License

---

Made with ❤️ for AI terminal users who want their freedom back.
