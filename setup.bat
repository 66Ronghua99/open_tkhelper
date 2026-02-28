@echo off
chcp 65001 >nul
REM
REM Open TKHelper - Windows 一键安装配置脚本
REM
REM 使用方法:
REM   双击运行 setup.bat
REM   或在命令提示符中运行: setup.bat
REM
REM 该脚本会自动完成以下配置:
REM   1. 检查 Node.js 和 npm
REM   2. 检查并安装 OpenCode CLI
REM   3. 配置 Playwright MCP
REM   4. 检查 Python 和 uv
REM   5. 安装 Python 依赖
REM   6. 安装 Playwright 浏览器
REM   7. 检查 ANTHROPIC_API_KEY
REM

setlocal enabledelayedexpansion

REM 颜色定义
set "BLUE=[94m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "NC=[0m"

REM 日志函数
:log_info
echo %BLUE%[INFO]%NC% %~1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:log_warn
echo %YELLOW%[WARN]%NC% %~1
goto :eof

:log_error
echo %RED%[ERROR]%NC% %~1
goto :eof

REM 打印分隔线
:print_line
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
goto :eof

REM 欢迎信息
call :print_line
echo %GREEN%  Open TKHelper - Windows 一键安装配置脚本%NC%
echo %BLUE%  基于 OpenCode 的 TikTok 客服助手%NC%
call :print_line
echo.

REM ========== 步骤 1: 检查 Node.js 和 npm ==========
call :log_info "步骤 1/7: 检查 Node.js 和 npm..."

node --version >nul 2>&1
if %errorlevel% neq 0 (
    call :log_error "Node.js 未安装"
    echo.
    echo 请安装 Node.js ^(建议 v18 或更高版本^):
    echo   1. 访问 https://nodejs.org/ 下载安装程序
    echo   2. 或使用 nvm-windows: https://github.com/coreybutler/nvm-windows
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%a in ('node --version') do set NODE_VERSION=%%a
for /f "tokens=*" %%a in ('npm --version') do set NPM_VERSION=%%a
call :log_success "Node.js 已安装: %NODE_VERSION%"
call :log_success "npm 已安装: %NPM_VERSION%"

REM ========== 步骤 2: 检查并安装 OpenCode CLI ==========
call :log_info "步骤 2/7: 检查 OpenCode CLI..."

opencode --version >nul 2>&1
if %errorlevel% neq 0 (
    call :log_warn "OpenCode CLI 未安装，正在安装..."
    npm install -g opencode

    opencode --version >nul 2>&1
    if %errorlevel% neq 0 (
        call :log_error "OpenCode CLI 安装失败"
        echo 请尝试手动安装: npm install -g opencode
        pause
        exit /b 1
    )
)

for /f "tokens=*" %%a in ('opencode --version') do set OPENCODE_VERSION=%%a
call :log_success "OpenCode CLI 已安装: %OPENCODE_VERSION%"

REM ========== 步骤 3: 安装 Playwright MCP ==========
call :log_info "步骤 3/7: 配置 Playwright MCP..."

opencode mcp list 2>nul | findstr "playwright" >nul
if %errorlevel% neq 0 (
    call :log_info "正在添加 Playwright MCP..."
    opencode mcp add --name playwright --command npx --args "@playwright/mcp@latest"
    call :log_success "Playwright MCP 配置成功"
) else (
    call :log_success "Playwright MCP 已配置"
)

REM ========== 步骤 4: 检查 Python 和 uv ==========
call :log_info "步骤 4/7: 检查 Python 和 uv..."

python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        call :log_error "Python 未安装"
        echo.
        echo 请安装 Python 3.12 或更高版本:
        echo   1. 访问 https://python.org/ 下载安装程序
        echo   2. 或使用 Microsoft Store 搜索 "Python"
        echo.
        echo 安装时请务必勾选 "Add Python to PATH"
        pause
        exit /b 1
    ) else (
        set "PYTHON_CMD=python3"
    )
) else (
    set "PYTHON_CMD=python"
)

for /f "tokens=*" %%a in ('%PYTHON_CMD% --version') do set PYTHON_VERSION=%%a
call :log_success "Python 已安装: %PYTHON_VERSION%"

REM 检查 uv
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    call :log_warn "uv 未安装，正在安装..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    REM 刷新环境变量
    call :refresh_env

    uv --version >nul 2>&1
    if %errorlevel% neq 0 (
        call :log_error "uv 安装失败，请手动安装: https://github.com/astral-sh/uv"
        pause
        exit /b 1
    )
)

for /f "tokens=*" %%a in ('uv --version') do set UV_VERSION=%%a
call :log_success "uv 已安装: %UV_VERSION%"

REM ========== 步骤 5: 安装 Python 依赖 ==========
call :log_info "步骤 5/7: 安装 Python 依赖..."

if exist "pyproject.toml" (
    uv sync
    call :log_success "Python 依赖安装完成"
) else (
    call :log_warn "未找到 pyproject.toml，跳过依赖安装"
)

REM ========== 步骤 6: 安装 Playwright 浏览器 ==========
call :log_info "步骤 6/7: 安装 Playwright 浏览器 (Chromium)..."

uv run playwright install chromium
call :log_success "Chromium 浏览器安装完成"

REM ========== 步骤 7: 检查 API Key ==========
call :log_info "步骤 7/7: 检查 ANTHROPIC_API_KEY..."

if "%ANTHROPIC_API_KEY%"=="" (
    call :log_warn "未设置 ANTHROPIC_API_KEY 环境变量"
    echo.
    echo 请设置你的 Anthropic API Key:
    echo.
    echo 临时设置 (当前终端):
    echo   set ANTHROPIC_API_KEY=your_api_key_here
    echo.
    echo 永久设置 (推荐):
    echo   1. 打开 "编辑系统环境变量"
    echo   2. 点击 "环境变量"
    echo   3. 在 "用户变量" 中点击 "新建"
    echo   4. 变量名: ANTHROPIC_API_KEY
    echo   5. 变量值: your_api_key_here
    echo   6. 重启终端
    echo.
    echo 获取 API Key: https://console.anthropic.com/
    echo.
) else (
    call :log_success "ANTHROPIC_API_KEY 已设置"
)

REM ========== 完成 ==========
echo.
call :print_line
echo %GREEN%  安装配置完成!%NC%
call :print_line
echo.

echo %BLUE%使用方法:%NC%
echo.
echo 1. 启动浏览器 (终端1):
echo   %GREEN%uv run python browser_launcher.py%NC%
echo.
echo 2. 运行 Agent (终端2):
echo   %GREEN%set PLAYWRIGHT_MCP_CDP_ENDPOINT=http://localhost:9222%NC%
echo   %GREEN%uv run python agent_runner.py%NC%
echo.
echo 3. 首次使用需要:
echo   - 在浏览器中登录 TikTok 卖家中心
echo   - 登录状态会自动保存
echo.

if "%ANTHROPIC_API_KEY%"=="" (
    call :log_warn "别忘了设置 ANTHROPIC_API_KEY!"
    echo.
)

echo 详细文档: https://github.com/66Ronghua99/open_tkhelper
echo.
pause

REM 刷新环境变量的子程序
:refresh_env
for /f "tokens=*" %%a in ('path') do set "PATH=%%a"
goto :eof
