# Ralph Loop 经验教训

## 技术决策记录

### 2026-02-28 CDP 持久浏览器模式

**问题描述**:
- 每次调用 OpenCode 都启动新浏览器，效率低下
- 登录状态需要频繁重新验证

**解决方案**:
使用 CDP (Chrome DevTools Protocol) 连接持久浏览器实例

**关键实现**:
```python
# 1. Python 启动浏览器并暴露 CDP
from playwright.sync_api import sync_playwright

self.playwright = sync_playwright().start()
self.context = self.playwright.chromium.launch_persistent_context(
    user_data_dir=str(self.user_data_dir),
    args=[f"--remote-debugging-port={cdp_port}"],
    headless=False,
)

# 2. 设置环境变量调用 OpenCode
env = os.environ.copy()
env["PLAYWRIGHT_MCP_CDP_ENDPOINT"] = f"http://localhost:{cdp_port}"

subprocess.Popen(
    ["opencode", "run", ...],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# 3. 提示词中告知浏览器已连接
prompt = """
## 重要说明
- 浏览器已经通过 CDP 连接启动，**不要**使用 browser_launch
- 直接使用 browser_navigate 等工具操作页面
"""
```

**MCP 配置**:
```bash
# 使用 @playwright/mcp 替代 @anthropic/playwright-mcp-server
opencode mcp add --name playwright --command npx --args "@playwright/mcp@latest"
```

**流式输出调试**:
```python
import select
import fcntl

# 设置非阻塞模式
fd = process.stdout.fileno()
fl = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

# 实时读取输出
while True:
    line = process.stdout.readline()
    if line:
        print(f"[OpenCode stdout] {line}")
```

**优势**:
- 浏览器只启动一次，大幅减少资源消耗
- 登录状态持久保持
- OpenCode 启动更快（无需等待浏览器启动）
- 实时输出便于调试

---

### 2026-02-28 Cookie 持久化方案变更

**问题描述**:
- 使用 `browser.new_context(storage_state=...)` 加载 cookies 后，TikTok 仍然需要重新登录
- 某些网站使用 localStorage、IndexedDB 等多种存储机制，单纯 cookies 不够

**解决方案**:
使用 `launch_persistent_context(user_data_dir=...)` 创建持久化浏览器上下文

**关键差异**:
```python
# 旧方案（不推荐）
browser = await p.chromium.launch(headless=False)
context = await browser.new_context(storage_state="cookies.json")

# 新方案（推荐）
context = await p.chromium.launch_persistent_context(
    user_data_dir="./browser_data",
    headless=False,
)
```

**优势**:
- 自动持久化所有浏览器数据（cookies、localStorage、IndexedDB、登录凭证等）
- 不需要手动 `storage_state` 保存/加载
- 更接近真实用户浏览器行为

---

## 注意事项

1. **首次登录**: 即使使用持久化上下文，首次运行仍需要手动登录，之后会自动保持登录状态

2. **browser_data 目录**: 这是 Chromium 的用户数据目录，包含完整的浏览器状态，不要手动修改

3. **URL 格式**: TikTok 卖家客服的正确地址是 `https://seller.tiktokshopglobalselling.com/chat/inbox/current`，不是 `seller.tiktok.com`

4. **launch_persistent_context 使用注意**:
   - 持久化上下文启动时会自动创建一个默认页面
   - 不要调用 `context.new_page()`，应该使用 `context.pages[0]`
   - 错误示例: `page = await context.new_page()` 会导致页面管理混乱
   - 正确做法: `page = context.pages[0] if context.pages else await context.new_page()`

5. **networkidle 超时问题**:
   - TikTok 页面有持续的网络活动（分析、实时连接等），`networkidle` 状态可能无法达成
   - 解决方案：添加 try/except 捕获超时，或使用较短的 timeout
   ```python
   try:
       await page.wait_for_load_state("networkidle", timeout=10000)
   except Exception:
       log("页面加载超时，继续执行...", "WARN")
   ```

6. **CDP 环境变量**:
   - 环境变量名称: `PLAYWRIGHT_MCP_CDP_ENDPOINT`
   - 格式: `http://localhost:9222` 或 WebSocket URL
   - 需要传递给 OpenCode 进程的环境变量中

7. **流式输出注意**:
   - 使用 `fcntl` 设置非阻塞模式才能实时读取
   - 需要处理 `BlockingIOError` 异常
   - 超时控制很重要，避免进程无限等待
