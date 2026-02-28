# Ralph Loop 项目进度

## 项目背景
Ralph Loop 是一个 TikTok 客服自动回复工具，使用 Playwright 监控 TikTok 卖家客服页面，当检测到新消息时调用 OpenCode 生成并发送回复。

## 架构变更 (2026-02-28)

**当前架构: CDP 持久浏览器模式（分离式）**
- **browser_launcher.py**: 启动浏览器并暴露 CDP endpoint，保持运行
- **agent_runner.py**: 调用 OpenCode 执行客服操作，可多次运行
- **OpenCode**: 通过 CDP 复用已有浏览器实例执行检测和回复
- **Cookie 持久化**: 通过 `launch_persistent_context()` 保持登录状态

### 架构演进

| 阶段 | 架构 | 特点 |
|------|------|------|
| 旧架构 | Ralph 管理浏览器 | Ralph 检测消息，调用 OpenCode 仅回复，30秒间隔 |
| 重构 A | OpenCode 全自主 | OpenCode 负责启动/关闭浏览器，15分钟间隔 |
| 重构 B | CDP 持久连接 | 浏览器启动一次，CDP 复用，5分钟间隔 |
| **当前** | **分离式 CDP** | **browser_launcher + agent_runner 分离，可独立运行** |

## 当前状态

### 已完成 ✅
- [x] 基础架构搭建（Playwright + OpenCode 集成）
- [x] 消息监控功能（未读消息检测、聊天列表获取）
- [x] OpenCode 代理集成（自动回复生成）
- [x] 状态管理（已回复消息去重）
- [x] **Cookie 持久化** - 使用 `launch_persistent_context()` 替代手动 cookie 管理
- [x] **URL 更新** - 更新为正确的 TikTok 客服地址
- [x] **CDP 连接改造** - 浏览器启动一次，OpenCode 通过 CDP 复用
- [x] **流式输出监控** - 实时显示 OpenCode stdout/stderr 便于调试
- [x] **MCP 配置更新** - 使用 `@playwright/mcp@latest` 支持 CDP
- [x] **脚本分离** - 将 `ralph_loop.py` 拆分为 `browser_launcher.py` 和 `agent_runner.py`
- [x] **文档完善** - 更新 README.md，添加完整的安装配置说明
- [x] **一键安装脚本** - 创建 setup.sh 自动完成环境配置

### 待办事项 📝
- [ ] 测试 CDP 连接是否正常工作
- [ ] 验证 OpenCode 是否能正确复用 CDP 浏览器
- [ ] 验证消息检测和回复流程
- [ ] 添加更多错误处理和重试机制

## 技术栈
- Python 3.12+
- Playwright (Python + Node.js MCP)
- OpenCode (AI 代理)
- CDP (Chrome DevTools Protocol)

## 文件结构
```
ralph-loop/
├── browser_launcher.py  # CDP 浏览器启动脚本（保持浏览器运行）
├── agent_runner.py      # Agent 操作脚本（调用 OpenCode 执行客服任务）
├── ralph_state.json     # 已回复消息状态
├── browser_data/        # 浏览器持久化数据
├── Progress.md          # 本文件
└── Memory.md            # 经验教训
```

## 运行方式

### 方式1: 分离运行（推荐）

终端1 - 启动浏览器：
```bash
uv run python browser_launcher.py
```

终端2 - 运行 Agent：
```bash
export PLAYWRIGHT_MCP_CDP_ENDPOINT=http://localhost:9222
uv run python agent_runner.py
```

或者单次运行：
```bash
PLAYWRIGHT_MCP_CDP_ENDPOINT=http://localhost:9222 uv run python agent_runner.py
```

### 方式2: 直接使用（会自动检测 CDP）
```bash
uv run python agent_runner.py
```
（需要先在另一个终端启动 browser_launcher.py）

## 最新更新 (2026-02-28)

### 脚本分离完成
- **browser_launcher.py**: 专门负责启动浏览器并暴露 CDP endpoint
  - 独立的浏览器管理进程
  - 显示 CDP endpoint 环境变量供复制使用
  - 保持浏览器运行直到手动停止

- **agent_runner.py**: 专门负责调用 OpenCode 执行客服操作
  - 从环境变量读取 CDP endpoint
  - 支持循环运行或单次运行
  - 可多次独立运行，复用同一浏览器

### CDP 连接改造完成
- **浏览器管理**: `BrowserManager` 类负责启动浏览器并暴露 CDP endpoint
- **CDP 环境变量**: `PLAYWRIGHT_MCP_CDP_ENDPOINT` 传递给 OpenCode
- **流式输出**: 使用 `subprocess.Popen` + 非阻塞读取实时监控 OpenCode 输出
- **提示词更新**: 移除 `browser_launch` 指令，告知 OpenCode 浏览器已连接
- **MCP 更新**: 使用 `@playwright/mcp@latest` 替代 `@anthropic/playwright-mcp-server`

### 新流程（分离式）
```
终端1: 启动 browser_launcher.py
  ↓
浏览器启动，暴露 CDP endpoint (http://localhost:9222)
  ↓
保持运行...

终端2: 运行 agent_runner.py
  ↓
读取 CDP_ENDPOINT 环境变量
  ↓
调用 opencode run (带 CDP 环境变量，流式输出)
  ↓
OpenCode 通过 CDP 连接已有浏览器
  ↓
执行检测/回复
  ↓
可多次运行 agent_runner.py，复用同一浏览器
```
