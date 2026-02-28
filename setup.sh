#!/bin/bash
#
# Open TKHelper - 一键安装配置脚本
#
# 使用方法:
#   chmod +x setup.sh
#   ./setup.sh
#
# 该脚本会自动完成以下配置:
#   1. 检查并安装 uv (Python 包管理器)
#   2. 检查 Node.js 和 npm
#   3. 检查并安装 OpenCode CLI
#   4. 安装 Playwright MCP
#   5. 安装 Python 依赖
#   6. 安装 Playwright 浏览器
#   7. 检查 ANTHROPIC_API_KEY
#

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 打印分隔线
print_line() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 欢迎信息
clear
print_line
echo -e "${GREEN}  Open TKHelper - 一键安装配置脚本${NC}"
echo -e "${BLUE}  基于 OpenCode 的 TikTok 客服助手${NC}"
print_line
echo ""

# ========== 步骤 1: 检查并安装 uv ==========
log_info "步骤 1/7: 检查 uv (Python 包管理器)..."

if command_exists uv; then
    UV_VERSION=$(uv --version)
    log_success "uv 已安装: $UV_VERSION"
else
    log_warn "uv 未安装，正在安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # 重新加载 shell 配置
    if [ -f "$HOME/.bashrc" ]; then
        source "$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        source "$HOME/.zshrc"
    fi

    # 检查是否安装成功
    if command_exists uv; then
        log_success "uv 安装成功"
    else
        log_error "uv 安装失败，请手动安装: https://github.com/astral-sh/uv"
        exit 1
    fi
fi

# ========== 步骤 2: 检查 Node.js 和 npm ==========
log_info "步骤 2/7: 检查 Node.js 和 npm..."

if command_exists node && command_exists npm; then
    NODE_VERSION=$(node --version)
    NPM_VERSION=$(npm --version)
    log_success "Node.js 已安装: $NODE_VERSION"
    log_success "npm 已安装: $NPM_VERSION"
else
    log_error "Node.js 或 npm 未安装"
    echo ""
    echo "请安装 Node.js (建议 v18 或更高版本):"
    echo "  - macOS: brew install node"
    echo "  - Ubuntu/Debian: sudo apt install nodejs npm"
    echo "  - 或其他方式: https://nodejs.org/"
    exit 1
fi

# ========== 步骤 3: 检查并安装 OpenCode CLI ==========
log_info "步骤 3/7: 检查 OpenCode CLI..."

if command_exists opencode; then
    OPENCODE_VERSION=$(opencode --version)
    log_success "OpenCode CLI 已安装: $OPENCODE_VERSION"
else
    log_warn "OpenCode CLI 未安装，正在安装..."
    npm install -g opencode

    if command_exists opencode; then
        log_success "OpenCode CLI 安装成功"
    else
        log_error "OpenCode CLI 安装失败"
        echo "请尝试手动安装: npm install -g opencode"
        exit 1
    fi
fi

# ========== 步骤 4: 安装 Playwright MCP ==========
log_info "步骤 4/7: 配置 Playwright MCP..."

# 检查是否已配置
if opencode mcp list 2>/dev/null | grep -q "playwright"; then
    log_success "Playwright MCP 已配置"
else
    log_info "正在添加 Playwright MCP..."
    opencode mcp add --name playwright --command npx --args "@playwright/mcp@latest"
    log_success "Playwright MCP 配置成功"
fi

# ========== 步骤 5: 安装 Python 依赖 ==========
log_info "步骤 5/7: 安装 Python 依赖..."

if [ -f "pyproject.toml" ]; then
    uv sync
    log_success "Python 依赖安装完成"
else
    log_warn "未找到 pyproject.toml，跳过依赖安装"
fi

# ========== 步骤 6: 安装 Playwright 浏览器 ==========
log_info "步骤 6/7: 安装 Playwright 浏览器 (Chromium)..."

uv run playwright install chromium
log_success "Chromium 浏览器安装完成"

# ========== 步骤 7: 检查 API Key ==========
log_info "步骤 7/7: 检查 ANTHROPIC_API_KEY..."

if [ -z "$ANTHROPIC_API_KEY" ]; then
    log_warn "未设置 ANTHROPIC_API_KEY 环境变量"
    echo ""
    echo -e "${YELLOW}请设置你的 Anthropic API Key:${NC}"
    echo ""
    echo "临时设置 (当前终端):"
    echo -e "  ${BLUE}export ANTHROPIC_API_KEY=your_api_key_here${NC}"
    echo ""
    echo "永久设置 (推荐):"
    echo "  1. 添加到 ~/.bashrc 或 ~/.zshrc:"
    echo -e "     ${BLUE}export ANTHROPIC_API_KEY=your_api_key_here${NC}"
    echo "  2. 重新加载配置:"
    echo -e "     ${BLUE}source ~/.bashrc${NC}  (或 source ~/.zshrc)"
    echo ""
    echo "获取 API Key: https://console.anthropic.com/"
else
    # 隐藏部分 key 显示
    KEY_PREFIX="${ANTHROPIC_API_KEY:0:10}"
    KEY_SUFFIX="${ANTHROPIC_API_KEY: -4}"
    log_success "ANTHROPIC_API_KEY 已设置: ${KEY_PREFIX}...${KEY_SUFFIX}"
fi

# ========== 完成 ==========
echo ""
print_line
echo -e "${GREEN}  安装配置完成!${NC}"
print_line
echo ""

echo -e "${BLUE}使用方法:${NC}"
echo ""
echo "1. 启动浏览器 (终端1):"
echo -e "   ${GREEN}uv run python browser_launcher.py${NC}"
echo ""
echo "2. 运行 Agent (终端2):"
echo -e "   ${GREEN}export PLAYWRIGHT_MCP_CDP_ENDPOINT=http://localhost:9222${NC}"
echo -e "   ${GREEN}uv run python agent_runner.py${NC}"
echo ""
echo "3. 首次使用需要:"
echo "   - 在浏览器中登录 TikTok 卖家中心"
echo "   - 登录状态会自动保存"
echo ""

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  别忘了设置 ANTHROPIC_API_KEY!${NC}"
    echo ""
fi

echo -e "详细文档: ${BLUE}https://github.com/66Ronghua99/open_tkhelper${NC}"
echo ""
