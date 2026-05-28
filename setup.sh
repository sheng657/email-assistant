#!/bin/bash
# Email Assistant — 一键环境检测与安装脚本
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "  Email Assistant 环境检测"
echo "========================================="
echo ""

# 1. 检测 Python 版本
echo -n "检测 Python 版本... "
PYTHON=""
for cmd in python3.12 python3.11 python3.10 python3.9 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        MAJOR=$("$cmd" -c "import sys; print(sys.version_info.major)")
        MINOR=$("$cmd" -c "import sys; print(sys.version_info.minor)")
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 9 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}未找到 Python 3.9+${NC}"
    echo ""
    echo "请先安装 Python 3.9 或更高版本："
    echo ""
    echo "  Ubuntu/Debian:  sudo apt update && sudo apt install python3 python3-venv"
    echo "  CentOS/RHEL:    sudo yum install python3"
    echo "  macOS:          brew install python@3.11"
    echo "  Windows:        从 https://www.python.org/downloads/ 下载安装"
    echo "  WSL:            sudo apt update && sudo apt install python3 python3-venv"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ $PYTHON (版本 $VER)${NC}"

# 2. 检测 pip/venv
echo -n "检测 venv 模块... "
if "$PYTHON" -c "import venv" 2>/dev/null; then
    echo -e "${GREEN}✓ 已安装${NC}"
else
    echo -e "${YELLOW}⚠ 未安装，尝试安装...${NC}"
    if command -v apt &>/dev/null; then
        sudo apt install -y python3-venv 2>/dev/null && echo -e "${GREEN}✓ 安装成功${NC}" || echo -e "${RED}✗ 安装失败，请手动安装 python3-venv${NC}"
    elif command -v brew &>/dev/null; then
        echo -e "${YELLOW}macOS 自带 venv，无需额外安装${NC}"
    else
        echo -e "${RED}✗ 请手动安装 python3-venv${NC}"
    fi
fi

# 3. 创建虚拟环境（如果不存在）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo -n "创建虚拟环境... "
    "$PYTHON" -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ $VENV_DIR${NC}"
fi

# 4. 激活虚拟环境并测试脚本
echo -n "测试邮件脚本... "
source "$VENV_DIR/bin/activate"
RESULT=$("$PYTHON" "$SCRIPT_DIR/scripts/fetch_emails.py" --help 2>&1)
if echo "$RESULT" | grep -q "usage:"; then
    echo -e "${GREEN}✓ 脚本可运行${NC}"
else
    echo -e "${RED}✗ 脚本异常${NC}"
    echo "$RESULT"
fi

echo ""
echo "========================================="
echo "  环境就绪！"
echo "========================================="
echo ""
echo "使用方式："
echo "  source $VENV_DIR/bin/activate"
echo "  export EMAIL_PASSWORD='你的授权码'"
echo '  python scripts/fetch_emails.py --account 你的邮箱@qq.com --mode headers'
echo ""
echo "或直接告诉 Hermes：\"帮我处理邮件\""
