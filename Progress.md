# Ralph Loop 项目进度

## 项目背景
Ralph Loop 是一个 TikTok 客服自动回复工具，使用 Playwright 监控 TikTok 卖家客服页面，当检测到新消息时调用 OpenCode 生成并发送回复。

## 架构变更 (2026-02-28)

**方案 A: OpenCode 全自主模式**
- **Ralph Loop**: 极简定时触发器（15分钟周期）
- **OpenCode**: 负责所有浏览器操作（启动、检测消息、回复、关闭）
- **Cookie 持久化**: 通过 `user_data_dir` 参数传递给 OpenCode

### 架构对比

| 旧架构 | 新架构 |
|--------|--------|
| Ralph 启动浏览器并保持运行 | Ralph 只负责定时触发 |
| Ralph 检测消息，调用 OpenCode 仅回复 | OpenCode 全权负责浏览器操作 |
| 30 秒检查间隔 | 15 分钟检查间隔 |
| ~400 行代码 | ~200 行代码 |

## 当前状态

### 已完成 ✅
- [x] 基础架构搭建（Playwright + OpenCode 集成）
- [x] 消息监控功能（未读消息检测、聊天列表获取）
- [x] OpenCode 代理集成（自动回复生成）
- [x] 状态管理（已回复消息去重）
- [x] **Bug Fix: Cookie 持久化** - 使用 `launch_persistent_context()` 替代手动 cookie 管理
- [x] **Bug Fix: URL 更新** - 更新为正确的 TikTok 客服地址
- [x] **架构重构: OpenCode 全自主模式** - 简化 Ralph Loop，OpenCode 负责所有浏览器操作

### 待办事项 📝
- [ ] 测试重构后的架构
- [ ] 验证 OpenCode 是否能正确处理登录状态
- [ ] 验证消息检测和回复流程
- [ ] 调整检查间隔（如有需要）
- [ ] 添加更多错误处理和重试机制

## 技术栈
- Python 3.12+
- Playwright (浏览器自动化，通过 OpenCode MCP 调用)
- OpenCode (AI 代理，全自主模式)

## 文件结构
```
ralph-loop/
├── ralph_loop.py        # 主程序（简化版定时触发器）
├── ralph_state.json     # 已回复消息状态
├── browser_data/        # 浏览器持久化数据（已存在）
├── Progress.md          # 本文件
└── Memory.md            # 经验教训
```

## 运行方式
```bash
uv run python ralph_loop.py
```

## 最新更新 (2026-02-28)

### 架构重构完成
- **Ralph Loop 简化**: 从 ~400 行简化为 ~200 行，只保留定时触发和状态管理
- **OpenCode 全自主**: OpenCode 负责启动浏览器、检测消息、生成回复、关闭浏览器
- **检查间隔**: 从 30 秒调整为 15 分钟（减少资源消耗）
- **Cookie 持久化**: 通过 `user_data_dir` 参数传递给 OpenCode，保持登录状态
