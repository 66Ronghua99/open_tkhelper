# Ralph Loop 项目进度

## 项目背景
Ralph Loop 是一个 TikTok 客服自动回复工具，使用 Playwright 监控 TikTok 卖家客服页面，当检测到新消息时调用 OpenCode 生成并发送回复。

## 架构变更 (2026-02-28)

**当前架构: CDP 持久浏览器模式**
- **Ralph Loop**: 启动浏览器一次，通过 CDP 持久连接，5分钟检查周期
- **OpenCode**: 通过 CDP 复用已有浏览器实例执行检测和回复
- **Cookie 持久化**: 通过 `launch_persistent_context()` 保持登录状态

### 架构演进

| 阶段 | 架构 | 特点 |
|------|------|------|
| 旧架构 | Ralph 管理浏览器 | Ralph 检测消息，调用 OpenCode 仅回复，30秒间隔 |
| 重构 A | OpenCode 全自主 | OpenCode 负责启动/关闭浏览器，15分钟间隔 |
| **当前** | **CDP 持久连接** | **浏览器启动一次，CDP 复用，5分钟间隔** |

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
├── ralph_loop.py        # 主程序 (CDP 持久浏览器模式)
├── ralph_state.json     # 已回复消息状态
├── browser_data/        # 浏览器持久化数据
├── Progress.md          # 本文件
└── Memory.md            # 经验教训
```

## 运行方式
```bash
uv run python ralph_loop.py
```

## 最新更新 (2026-02-28)

### CDP 连接改造完成
- **浏览器管理**: `BrowserManager` 类负责启动浏览器并暴露 CDP endpoint
- **CDP 环境变量**: `PLAYWRIGHT_MCP_CDP_ENDPOINT` 传递给 OpenCode
- **流式输出**: 使用 `subprocess.Popen` + 非阻塞读取实时监控 OpenCode 输出
- **提示词更新**: 移除 `browser_launch` 指令，告知 OpenCode 浏览器已连接
- **MCP 更新**: 使用 `@playwright/mcp@latest` 替代 `@anthropic/playwright-mcp-server`

### 新流程
```
启动浏览器一次 (Python)
  ↓
获取 CDP endpoint (http://localhost:9222)
  ↓
循环开始
  ↓
调用 opencode run (带 CDP 环境变量，流式输出)
  ↓
OpenCode 通过 CDP 连接已有浏览器
  ↓
执行检测/回复 (不关闭浏览器)
  ↓
等待 5 分钟
  ↓
重复 (保持同一浏览器连接)
```
