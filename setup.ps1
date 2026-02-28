#
# Open TKHelper - Windows PowerShell 一键安装配置脚本
#
# 使用方法:
#   右键选择 "使用 PowerShell 运行"
#   或在 PowerShell 中运行: .\setup.ps1
#
# 该脚本会自动完成以下配置:
#   1. 检查 Node.js 和 npm
#   2. 检查并安装 OpenCode CLI
#   3. 配置 Playwright MCP
#   4. 检查 Python 和 uv
#   5. 安装 Python 依赖
#   6. 安装 Playwright 浏览器
#   7. 检查 ANTHROPIC_API_KEY
#

# 设置执行策略检查
try {
    $executionPolicy = Get-ExecutionPolicy -Scope Process
    if ($executionPolicy -eq 'Restricted') {
        Write-Host "[WARN] 当前执行策略为 Restricted，正在尝试修改..." -ForegroundColor Yellow
        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
    }
} catch {
    Write-Host "[WARN] 无法修改执行策略，如果脚本无法运行，请以管理员身份运行 PowerShell 并执行:" -ForegroundColor Yellow
    Write-Host '  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass' -ForegroundColor Cyan
    Write-Host ""
}

# 颜色定义
$Blue = "Cyan"
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"

# 日志函数
function Log-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Blue
}

function Log-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Green
}

function Log-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor $Yellow
}

function Log-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

# 打印分隔线
function Print-Line {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 检查命令是否存在
function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# 刷新环境变量
function Refresh-Env {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# 欢迎信息
Clear-Host
Print-Line
Write-Host "  Open TKHelper - Windows PowerShell 一键安装配置脚本" -ForegroundColor $Green
Write-Host "  基于 OpenCode 的 TikTok 客服助手" -ForegroundColor $Blue
Print-Line
Write-Host ""

# ========== 步骤 1: 检查 Node.js 和 npm ==========
Log-Info "步骤 1/7: 检查 Node.js 和 npm..."

if (-not (Test-Command "node")) {
    Log-Error "Node.js 未安装"
    Write-Host ""
    Write-Host "请安装 Node.js (建议 v18 或更高版本):" -ForegroundColor Yellow
    Write-Host "  1. 访问 https://nodejs.org/ 下载安装程序"
    Write-Host "  2. 或使用 nvm-windows: https://github.com/coreybutler/nvm-windows"
    Write-Host ""
    Write-Host "按任意键退出..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

$NODE_VERSION = node --version
$NPM_VERSION = npm --version
Log-Success "Node.js 已安装: $NODE_VERSION"
Log-Success "npm 已安装: $NPM_VERSION"

# ========== 步骤 2: 检查并安装 OpenCode CLI ==========
Log-Info "步骤 2/7: 检查 OpenCode CLI..."

if (-not (Test-Command "opencode")) {
    Log-Warn "OpenCode CLI 未安装，正在安装..."
    npm install -g opencode

    Refresh-Env

    if (-not (Test-Command "opencode")) {
        Log-Error "OpenCode CLI 安装失败"
        Write-Host "请尝试手动安装: npm install -g opencode"
        Write-Host "按任意键退出..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}

$OPENCODE_VERSION = opencode --version
Log-Success "OpenCode CLI 已安装: $OPENCODE_VERSION"

# ========== 步骤 3: 安装 Playwright MCP ==========
Log-Info "步骤 3/7: 配置 Playwright MCP..."

$mcpList = opencode mcp list 2>$null
if ($mcpList -match "playwright") {
    Log-Success "Playwright MCP 已配置"
} else {
    Log-Info "正在添加 Playwright MCP..."
    opencode mcp add --name playwright --command npx --args "@playwright/mcp@latest"
    Log-Success "Playwright MCP 配置成功"
}

# ========== 步骤 4: 检查 Python 和 uv ==========
Log-Info "步骤 4/7: 检查 Python 和 uv..."

$pythonCmd = $null
if (Test-Command "python") {
    $pythonCmd = "python"
} elseif (Test-Command "python3") {
    $pythonCmd = "python3"
} elseif (Test-Command "py") {
    $pythonCmd = "py"
}

if ($null -eq $pythonCmd) {
    Log-Error "Python 未安装"
    Write-Host ""
    Write-Host "请安装 Python 3.12 或更高版本:" -ForegroundColor Yellow
    Write-Host "  1. 访问 https://python.org/ 下载安装程序"
    Write-Host "  2. 或使用 Microsoft Store 搜索 'Python'"
    Write-Host ""
    Write-Host "安装时请务必勾选 'Add Python to PATH'"
    Write-Host ""
    Write-Host "按任意键退出..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

$PYTHON_VERSION = & $pythonCmd --version
Log-Success "Python 已安装: $PYTHON_VERSION"

# 检查 uv
if (-not (Test-Command "uv")) {
    Log-Warn "uv 未安装，正在安装..."
    irm https://astral.sh/uv/install.ps1 | iex

    Refresh-Env

    if (-not (Test-Command "uv")) {
        Log-Error "uv 安装失败，请手动安装: https://github.com/astral-sh/uv"
        Write-Host "按任意键退出..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}

$UV_VERSION = uv --version
Log-Success "uv 已安装: $UV_VERSION"

# ========== 步骤 5: 安装 Python 依赖 ==========
Log-Info "步骤 5/7: 安装 Python 依赖..."

if (Test-Path "pyproject.toml") {
    uv sync
    Log-Success "Python 依赖安装完成"
} else {
    Log-Warn "未找到 pyproject.toml，跳过依赖安装"
}

# ========== 步骤 6: 安装 Playwright 浏览器 ==========
Log-Info "步骤 6/7: 安装 Playwright 浏览器 (Chromium)..."

uv run playwright install chromium
Log-Success "Chromium 浏览器安装完成"

# ========== 步骤 7: 检查 API Key ==========
Log-Info "步骤 7/7: 检查 ANTHROPIC_API_KEY..."

$apiKey = [System.Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY")
if ([string]::IsNullOrEmpty($apiKey)) {
    Log-Warn "未设置 ANTHROPIC_API_KEY 环境变量"
    Write-Host ""
    Write-Host "请设置你的 Anthropic API Key:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "临时设置 (当前终端):" -ForegroundColor Cyan
    Write-Host '  $env:ANTHROPIC_API_KEY = "your_api_key_here"' -ForegroundColor Green
    Write-Host ""
    Write-Host "永久设置 (推荐):" -ForegroundColor Cyan
    Write-Host "  1. 打开 '编辑系统环境变量'"
    Write-Host "  2. 点击 '环境变量'"
    Write-Host "  3. 在 '用户变量' 中点击 '新建'"
    Write-Host "  4. 变量名: ANTHROPIC_API_KEY"
    Write-Host "  5. 变量值: your_api_key_here"
    Write-Host "  6. 重启终端"
    Write-Host ""
    Write-Host "获取 API Key: https://console.anthropic.com/"
    Write-Host ""
} else {
    $keyPrefix = $apiKey.Substring(0, [Math]::Min(10, $apiKey.Length))
    $keySuffix = $apiKey.Substring($apiKey.Length - 4)
    Log-Success "ANTHROPIC_API_KEY 已设置: ${keyPrefix}...${keySuffix}"
}

# ========== 完成 ==========
Write-Host ""
Print-Line
Write-Host "  安装配置完成!" -ForegroundColor $Green
Print-Line
Write-Host ""

Write-Host "使用方法:" -ForegroundColor $Blue
Write-Host ""
Write-Host "1. 启动浏览器 (终端1):" -ForegroundColor White
Write-Host "   uv run python browser_launcher.py" -ForegroundColor $Green
Write-Host ""
Write-Host "2. 运行 Agent (终端2):" -ForegroundColor White
Write-Host '   $env:PLAYWRIGHT_MCP_CDP_ENDPOINT = "http://localhost:9222"' -ForegroundColor $Green
Write-Host "   uv run python agent_runner.py" -ForegroundColor $Green
Write-Host ""
Write-Host "3. 首次使用需要:" -ForegroundColor White
Write-Host "   - 在浏览器中登录 TikTok 卖家中心"
Write-Host "   - 登录状态会自动保存"
Write-Host ""

$apiKey = [System.Environment]::GetEnvironmentVariable("ANTHROPIC_API_KEY")
if ([string]::IsNullOrEmpty($apiKey)) {
    Log-Warn "别忘了设置 ANTHROPIC_API_KEY!"
    Write-Host ""
}

Write-Host "详细文档: https://github.com/66Ronghua99/open_tkhelper" -ForegroundColor $Blue
Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
