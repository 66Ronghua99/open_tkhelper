# Ralph Loop - TikTok 客服自动回复

一个基于 Playwright + OpenCode MCP 的 TikTok 客服自动回复工具。

## 架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  ralph_loop.py  │────▶│  OpenCode CLI   │────▶│ TikTok 卖家中心  │
│                 │     │  + Playwright   │     │    客服聊天      │
└─────────────────┘     │     MCP         │     └─────────────────┘
                        └─────────────────┘
```

## 快速开始

### 1. 安装依赖

```bash
cd ~/codes/ralph-loop
uv sync
```

### 2. 配置 Playwright MCP

确保 OpenCode 已配置 Playwright MCP:

```bash
# 检查是否已配置
opencode mcp list

# 如未配置，手动添加
opencode mcp add playwright --command "npx" --args "@anthropic/playwright-mcp-server"
```

### 3. 调试选择器（首次运行）

TikTok 页面结构可能变化，先运行调试工具确认选择器:

```bash
uv run python debug_selectors.py
```

按提示操作，根据输出更新 `ralph_loop.py` 中的 `SELECTORS` 配置。

### 4. 运行主程序

```bash
uv run python ralph_loop.py
```

首次运行需要手动登录 TikTok，登录后 Cookie 会自动保存。

## 文件说明

| 文件 | 说明 |
|------|------|
| `ralph_loop.py` | 主程序，监控循环 |
| `debug_selectors.py` | 调试工具，帮助识别页面选择器 |
| `tiktok_cookies.json` | 登录状态（自动生成） |
| `ralph_state.json` | 已回复消息记录（自动生成） |

## 配置说明

### SELECTORS 配置

在 `ralph_loop.py` 中修改选择器以匹配实际页面:

```python
SELECTORS = {
    "unread_badge": "...",     # 未读消息徽章
    "chat_list_item": "...",   # 聊天列表项
    "message_bubble": "...",   # 消息气泡
    "chat_input": "...",       # 输入框
    "send_button": "...",      # 发送按钮
}
```

### 运行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `CHECK_INTERVAL` | 30 | 检查间隔（秒） |
| `TIKTOK_SELLER_URL` | https://seller.tiktok.com | 卖家中心地址 |
| `CHAT_URL` | .../apps/seller-chat | 客服聊天地址 |

## 工作流程

```
启动
  │
  ▼
检查 Cookie ──无──▶ 打开登录页 ──▶ 手动登录 ──▶ 保存 Cookie
  │
  有
  ▼
加载 Cookie
  │
  ▼
访问客服聊天页
  │
  ▼
┌──────────────┐
│   主循环     │◄──────────────────┐
│              │                   │
│ 1. 刷新页面  │                   │
│ 2. 检查未读  │                   │
│ 3. 有新消息? │──否──┐            │
└──────────────┘      │            │
      │              │            │
     是              │            │
      │              │            │
      ▼              │            │
┌──────────────┐     │            │
│ 获取买家消息 │     │            │
│ 调用 OpenCode│     │            │
│ 生成并发送   │     │            │
│ 回复         │     │            │
└──────────────┘     │            │
      │              │            │
      └──────────────┘            │
              │                   │
              ▼                   │
        等待 30 秒 ───────────────┘
```

## 注意事项

1. **选择器适配**: TikTok 页面可能更新，需要使用 `debug_selectors.py` 重新识别
2. **Rate Limiting**: 避免过于频繁的检查，建议间隔 ≥30 秒
3. **消息去重**: 已回复的消息会记录在 `ralph_state.json` 中，避免重复回复
4. **安全性**: Cookie 文件包含登录凭证，不要提交到 Git

## 故障排查

### OpenCode 未找到 MCP

```bash
opencode mcp add playwright --command "npx" --args "@anthropic/playwright-mcp-server"
```

### 选择器不匹配

运行调试工具获取正确的选择器:

```bash
uv run python debug_selectors.py
```

### 消息检测失败

检查页面是否正常加载，尝试增加等待时间:

```python
await asyncio.sleep(5)  # 增加等待时间
```
