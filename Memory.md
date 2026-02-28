# Ralph Loop 经验教训

## 技术决策记录

### 2026-02-28 架构重构: OpenCode 全自主模式

**问题描述**:
- 旧架构中 Ralph Loop 负责浏览器管理，OpenCode 只负责回复
- 代码复杂度高，需要维护大量 Playwright 选择器和页面操作逻辑
- 检查间隔太短（30秒），资源消耗较大

**新架构方案**:
- **Ralph Loop**: 极简定时触发器（15分钟周期）
- **OpenCode**: 全自主完成所有浏览器操作（启动、检测、回复、关闭）

**关键变更**:
```python
# 旧架构: Ralph 管理浏览器
async with async_playwright() as p:
    context = await p.chromium.launch_persistent_context(...)
    page = context.pages[0]
    # Ralph 检测消息、调用 OpenCode 仅回复

# 新架构: OpenCode 全权负责
prompt = """
请使用 Playwright MCP 工具:
1. 启动浏览器（使用 browser_launch，指定 user_data_dir）
2. 导航到 TikTok 客服页面
3. 检查并回复消息
4. 关闭浏览器
"""
subprocess.run(["opencode", "run", ...], ...)
```

**优势**:
- 代码量减少 50%（~400行 -> ~200行）
- Ralph 无需维护 Playwright 选择器
- OpenCode 可直接使用 MCP 工具灵活操作页面
- 更长的检查间隔，资源消耗更低

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

6. **OpenCode 全自主模式注意**:
   - 需要在提示词中明确指定 `user_data_dir` 参数
   - OpenCode 的 Playwright MCP 工具需要正确配置
   - 返回结果需要通过 JSON 格式解析
