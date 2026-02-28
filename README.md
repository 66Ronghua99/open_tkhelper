# Open TKHelper - 基于 OpenCode 的 TikTok 客服助手

一个基于 OpenCode + Playwright MCP 的 TikTok 客服自动回复工具。通过 CDP（Chrome DevTools Protocol）连接浏览器，让 AI 代理自动监控和回复客服消息。

## 架构

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ browser_launcher.py │────▶│   CDP 浏览器实例     │◀────│  agent_runner.py    │
│   (浏览器管理)       │     │  http://localhost:   │     │   (Agent 操作)       │
└─────────────────────┘     │       9222           │     └─────────────────────┘
                            └─────────────────────┘              │
                                                                   │
                            ┌─────────────────────┐              │
                            │   OpenCode CLI      │◀─────────────┘
                            │ + Playwright MCP    │
                            └─────────────────────┘
                                    │
                                    ▼
                            ┌─────────────────────┐
                            │  TikTok 卖家中心    │
                            │     客服聊天        │
                            └─────────────────────┘
```

**分离式架构优势：**
- 浏览器独立运行，Agent 可多次连接
- 登录状态持久保持，无需重复登录
- 支持多个 Agent 复用同一浏览器

## 安装配置

### 快速安装（推荐）

#### macOS / Linux

使用一键安装脚本自动完成所有配置：

```bash
git clone https://github.com/66Ronghua99/open_tkhelper.git
cd open_tkhelper
chmod +x setup.sh
./setup.sh
```

#### Windows

**方式 1：PowerShell 脚本（推荐）**

```powershell
# 克隆仓库
git clone https://github.com/66Ronghua99/open_tkhelper.git
cd open_tkhelper

# 运行安装脚本（可能需要以管理员身份运行 PowerShell）
.\setup.ps1
```

**方式 2：命令提示符 (CMD)**

```cmd
# 克隆仓库
git clone https://github.com/66Ronghua99/open_tkhelper.git
cd open_tkhelper

# 运行安装脚本
setup.bat
```

**注意**：如果 PowerShell 脚本无法运行，可能需要先设置执行策略：
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

该脚本会自动完成：
- ✅ 检查并安装 uv (Python 包管理器)
- ✅ 检查 Node.js 和 npm
- ✅ 检查并安装 OpenCode CLI
- ✅ 配置 Playwright MCP
- ✅ 安装 Python 依赖
- ✅ 安装 Chromium 浏览器
- ✅ 检查 ANTHROPIC_API_KEY

### 手动安装

如果你更喜欢手动配置，或一键安装脚本在你的环境遇到问题，可以按以下步骤操作：

#### 1. 克隆仓库

```bash
git clone https://github.com/66Ronghua99/open_tkhelper.git
cd open_tkhelper
```

#### 2. 安装 Python 依赖

本项目使用 `uv` 作为包管理器：

```bash
# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync
```

#### 3. 安装 OpenCode CLI

```bash
# 通过 npm 安装
npm install -g opencode

# 验证安装
opencode --version
```

#### 4. 配置 Playwright MCP

```bash
# 检查是否已配置
opencode mcp list

# 如未配置，添加 Playwright MCP
opencode mcp add --name playwright --command npx --args "@playwright/mcp@latest"
```

#### 5. 配置 OpenCode API Key

```bash
# 设置环境变量
export ANTHROPIC_API_KEY=your_api_key_here

# 或者使用 opencode 配置
opencode config set api_key your_api_key_here
```

## 使用方式

### 方式一：分离运行（推荐）

**终端 1 - 启动浏览器：**

```bash
uv run python browser_launcher.py
```

浏览器启动后会显示 CDP endpoint，保持此终端运行。

**终端 2 - 运行 Agent：**

**macOS / Linux：**
```bash
# 设置环境变量
export PLAYWRIGHT_MCP_CDP_ENDPOINT=http://localhost:9222

# 运行 Agent（循环模式，每 5 分钟检查一次）
uv run python agent_runner.py
```

**Windows (PowerShell)：**
```powershell
# 设置环境变量
$env:PLAYWRIGHT_MCP_CDP_ENDPOINT = "http://localhost:9222"

# 运行 Agent
uv run python agent_runner.py
```

**Windows (CMD)：**
```cmd
# 设置环境变量
set PLAYWRIGHT_MCP_CDP_ENDPOINT=http://localhost:9222

# 运行 Agent
uv run python agent_runner.py
```

或者单次运行（macOS/Linux）：
```bash
PLAYWRIGHT_MCP_CDP_ENDPOINT=http://localhost:9222 uv run python agent_runner.py
```

### 方式二：快捷脚本

创建一个启动脚本 `start.sh`：

```bash
#!/bin/bash
# 启动浏览器（后台运行）
uv run python browser_launcher.py &
BROWSER_PID=$!

# 等待浏览器启动
sleep 3

# 运行 Agent
export PLAYWRIGHT_MCP_CDP_ENDPOINT=http://localhost:9222
uv run python agent_runner.py

# 清理
kill $BROWSER_PID
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `setup.sh` | **macOS/Linux 一键安装脚本** |
| `setup.bat` | **Windows CMD 一键安装脚本** |
| `setup.ps1` | **Windows PowerShell 一键安装脚本** |
| `browser_launcher.py` | 浏览器启动器，管理 CDP 浏览器实例 |
| `agent_runner.py` | Agent 操作脚本，调用 OpenCode 执行客服任务 |
| `ralph_state.json` | 已回复消息记录（自动生成） |
| `browser_data/` | 浏览器持久化数据目录（包含登录状态） |

## 工作流程

```
启动 browser_launcher.py
        │
        ▼
启动浏览器 + CDP 调试端口
        │
        ▼
等待 Agent 连接（保持运行）
        │
        ◀──────────────────┐
        │                   │
   Agent Runner 启动        │
        │                   │
        ▼                   │
通过 CDP 连接浏览器         │
        │                   │
        ▼                   │
┌──────────────┐           │
│   主循环     │◀──────────┤
│              │           │
│ 1. 访问页面  │           │
│ 2. 检查未读  │           │
│ 3. 有新消息? │──否───────┤
└──────────────┘           │
        │                  │
       是                  │
        │                  │
        ▼                  │
┌──────────────┐          │
│ 获取买家消息 │          │
│ 生成回复     │          │
│ 发送消息     │          │
└──────────────┘          │
        │                 │
        └─────────────────┘
                │
                ▼
        等待 5 分钟后再次检查
```

## 配置说明

### 检查间隔

在 `agent_runner.py` 中修改：

```python
CHECK_INTERVAL = 300  # 5 分钟（秒）
```

### TikTok 客服地址

```python
TIKTOK_URL = "https://seller.tiktokshopglobalselling.com/chat/inbox/current"
```

### CDP 端口

在 `browser_launcher.py` 中修改：

```python
CDP_PORT = 9222  # Chrome DevTools Protocol 端口
```

## 首次使用

1. **启动浏览器**
   ```bash
   uv run python browser_launcher.py
   ```

2. **手动登录 TikTok**
   - 浏览器窗口会自动打开
   - 访问 TikTok 卖家中心并登录
   - 登录状态会自动保存到 `browser_data/`

3. **运行 Agent**
   ```bash
   export PLAYWRIGHT_MCP_CDP_ENDPOINT=http://localhost:9222
   uv run python agent_runner.py
   ```

4. **验证工作**
   - Agent 会访问客服页面
   - 检查未读消息并自动回复
   - 查看终端输出确认运行正常

## 注意事项

1. **登录状态**：首次登录后，Cookie 会保存在 `browser_data/` 目录，后续无需重复登录
2. **消息去重**：已回复的消息记录在 `ralph_state.json`，避免重复回复
3. **Rate Limiting**：默认 5 分钟检查一次，避免过于频繁
4. **安全性**：`browser_data/` 包含登录凭证，不要提交到 Git（已在 `.gitignore` 中排除）
5. **浏览器保持**：`browser_launcher.py` 需要保持运行以维持浏览器状态

## 故障排查

### Windows: PowerShell 脚本无法运行

如果遇到 "无法加载脚本" 错误，需要设置执行策略：

```powershell
# 临时设置（推荐）
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 然后运行脚本
.\setup.ps1
```

### OpenCode 未找到 MCP

```bash
# macOS / Linux
opencode mcp add --name playwright --command npx --args "@playwright/mcp@latest"

# Windows
opencode mcp add --name playwright --command npx --args "@playwright/mcp@latest"
```

### CDP 连接失败

1. 检查浏览器是否已启动：
   ```bash
   curl http://localhost:9222/json/version
   ```

2. 检查环境变量是否设置：
   ```bash
   echo $PLAYWRIGHT_MCP_CDP_ENDPOINT
   ```

### 浏览器无法启动

1. 检查 Playwright 浏览器是否已安装：
   ```bash
   uv run playwright install chromium
   ```

2. 检查端口 9222 是否被占用：
   ```bash
   lsof -i :9222
   ```

### 消息检测失败

- 检查页面是否正常加载
- 查看 OpenCode 输出日志
- 确认 TikTok 页面结构是否有变化

## 技术栈

- **Python 3.12+**
- **Playwright** - 浏览器自动化
- **OpenCode** - AI 代理框架
- **CDP (Chrome DevTools Protocol)** - 浏览器远程调试
- **uv** - Python 包管理

## 许可证

MIT License
