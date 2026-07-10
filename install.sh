#!/usr/bin/env bash
#
# hook-notify 一键安装脚本
#
# 用法:
#   curl -fsSL https://raw.githubusercontent.com/Jingnan-Jia/hook-notify/main/install.sh | bash
#
#  或本地安装:
#   bash install.sh
#

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

INSTALL_DIR="$HOME/.hook-notify"
REPO_URL="${HOOK_NOTIFY_REPO:-https://github.com/Jingnan-Jia/hook-notify.git}"
BRANCH="${HOOK_NOTIFY_BRANCH:-main}"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║       🔔  AI 终端通知助手  一键安装           ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# --------------------------------------------------
# 检查 Python
# --------------------------------------------------
echo -e "  [1/4] 检查运行环境..."

if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo -e "${RED}  ✗ 未找到 Python，请先安装 Python 3.8+${NC}"
    echo "    macOS:  brew install python3"
    echo "    Ubuntu: sudo apt install python3"
    echo "    Arch:   sudo pacman -S python"
    exit 1
fi

PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "  ${GREEN}✓${NC} Python $PY_VERSION"

# --------------------------------------------------
# 安装文件
# --------------------------------------------------
echo ""
echo -e "  [2/4] 安装 hook-notify..."

# 判断是通过 curl 管道还是本地运行
if [ -f "./notify.py" ] && [ -f "./install.sh" ]; then
    # 本地安装模式
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    echo "  本地安装模式: $SCRIPT_DIR"
    mkdir -p "$INSTALL_DIR"
    cp "$SCRIPT_DIR/notify.py" "$INSTALL_DIR/notify.py"
    cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/requirements.txt" 2>/dev/null || true
else
    # 远程安装模式
    echo "  远程安装模式"
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo "  目录已存在，更新..."
        cd "$INSTALL_DIR"
        git pull origin "$BRANCH" --ff-only 2>/dev/null || true
    else
        rm -rf "$INSTALL_DIR"
        if command -v git &> /dev/null; then
            echo "  通过 git clone 下载..."
            git clone --depth 1 -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
        else
            echo "  通过 curl 下载..."
            mkdir -p "$INSTALL_DIR"
            curl -fsSL "https://raw.githubusercontent.com/Jingnan-Jia/hook-notify/$BRANCH/notify.py" -o "$INSTALL_DIR/notify.py"
            curl -fsSL "https://raw.githubusercontent.com/Jingnan-Jia/hook-notify/$BRANCH/requirements.txt" -o "$INSTALL_DIR/requirements.txt"
        fi
    fi
fi

echo -e "  ${GREEN}✓${NC} 文件已安装到 $INSTALL_DIR"

# --------------------------------------------------
# 安装依赖
# --------------------------------------------------
echo ""
echo -e "  [3/4] 安装 Python 依赖..."

cd "$INSTALL_DIR"
$PYTHON -m pip install requests qrcode --quiet 2>&1 | tail -1

echo -e "  ${GREEN}✓${NC} 依赖安装完成"

# --------------------------------------------------
# 创建通知快捷命令
# --------------------------------------------------
echo ""
echo -e "  [4/4] 创建快捷命令..."

SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_RC="$HOME/.bash_profile"
fi

ALIAS_LINE="alias hook-notify='python3 $INSTALL_DIR/notify.py'"

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "hook-notify" "$SHELL_RC" 2>/dev/null; then
        echo "$ALIAS_LINE" >> "$SHELL_RC"
        echo -e "  ${GREEN}✓${NC} 快捷命令已添加到 $SHELL_RC"
        echo "    使用: hook-notify 或 hook-notify '消息内容'"
    else
        echo "  快捷命令已存在，跳过"
    fi
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          安装完成！即将启动配置向导...        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# --------------------------------------------------
# 启动安装向导
# --------------------------------------------------
# 预写默认 AppToken，减少交互步骤
$PYTHON -c "
import json
from pathlib import Path
config_file = Path.home() / '.hook-notify' / 'config.json'
config = {}
if config_file.exists():
    try:
        with open(config_file) as f:
            config = json.load(f)
    except: pass
if not config.get('appToken'):
    config['appToken'] = 'AT_mx4gZJ9t47IibakBWuCQ5qoNyfn0eJXo'
config_file.parent.mkdir(parents=True, exist_ok=True)
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
"

exec $PYTHON "$INSTALL_DIR/notify.py" --setup < /dev/tty
