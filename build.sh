#!/usr/bin/env bash
#
# 构建 hook-notify 桌面应用
#   macOS: 生成 .app
#   Windows: 生成 .exe (需要交叉编译或在 Windows 上运行)
#

set -e

echo ""
echo "🔨 构建 hook-notify 桌面应用..."
echo ""

# 安装打包依赖
pip3 install pyinstaller Pillow requests qrcode --quiet

# 清理旧构建
rm -rf build dist *.spec

# 检测平台
OS=$(uname -s)
APP_NAME="Hook Notify"

if [ "$OS" = "Darwin" ]; then
    echo "  构建 macOS .app ..."
    pyinstaller \
        --windowed \
        --onefile \
        --name "$APP_NAME" \
        --add-data "notify.py:." \
        --icon "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericApplicationIcon.icns" \
        hook_notify_app.py

    echo ""
    echo "✅ 构建完成！"
    echo "  应用位置: dist/$APP_NAME.app"
    echo "  双击 dist/$APP_NAME.app 即可运行"

elif [ "$OS" = "MINGW64_NT" ] || [ "$OS" = "MSYS_NT" ] || [[ "$OS" == *"_NT"* ]]; then
    echo "  构建 Windows .exe ..."
    pyinstaller \
        --windowed \
        --onefile \
        --name "$APP_NAME" \
        --add-data "notify.py;." \
        hook_notify_app.py

    echo ""
    echo "✅ 构建完成！"
    echo "  应用位置: dist/$APP_NAME.exe"
else
    echo "  构建 Linux 可执行文件 ..."
    pyinstaller \
        --windowed \
        --onefile \
        --name "$APP_NAME" \
        --add-data "notify.py:." \
        hook_notify_app.py

    echo ""
    echo "✅ 构建完成！"
    echo "  应用位置: dist/$APP_NAME"
fi
