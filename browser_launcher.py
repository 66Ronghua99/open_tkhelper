#!/usr/bin/env python3
"""
Browser Launcher - CDP 浏览器启动脚本

负责启动浏览器并暴露 CDP endpoint，供 Agent 连接使用。
浏览器保持运行直到手动停止。

【使用方法】

1. 启动浏览器（终端1）：
   uv run python browser_launcher.py

2. 在另一个终端运行 Agent（终端2）：
   export PLAYWRIGHT_MCP_CDP_ENDPOINT=http://localhost:9222
   uv run python agent_runner.py

【前置要求】
- 已安装 Playwright: uv run playwright install chromium
- 已安装 OpenCode: npm install -g opencode
- 已配置 Playwright MCP: opencode mcp add --name playwright --command npx --args "@playwright/mcp@latest"

【注意】
- 首次运行需要手动登录 TikTok，登录状态会自动保存
- 保持此脚本运行以维持浏览器状态
- 按 Ctrl+C 停止浏览器
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# ==================== 配置 ====================
USER_DATA_DIR = Path(__file__).parent / "browser_data"
CDP_PORT = 9222  # Chrome DevTools Protocol 端口


# ==================== 日志工具 ====================
def log(msg: str, level: str = "INFO"):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


# ==================== 浏览器管理（CDP 模式）====================
class BrowserManager:
    """管理浏览器实例，通过 CDP 供 Agent 连接"""

    def __init__(self, user_data_dir: Path, cdp_port: int):
        self.user_data_dir = user_data_dir
        self.cdp_port = cdp_port
        self.cdp_endpoint = f"http://localhost:{cdp_port}"
        self.browser = None
        self.context = None
        self.playwright = None

    def start(self) -> bool:
        """启动浏览器并暴露 CDP endpoint"""
        try:
            from playwright.sync_api import sync_playwright

            log(f"启动浏览器 (CDP port: {self.cdp_port})...")
            self.playwright = sync_playwright().start()

            # 启动持久化上下文并开启远程调试
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                args=[f"--remote-debugging-port={self.cdp_port}"],
                headless=False,
                viewport={"width": 1280, "height": 720},
            )

            # 获取或创建页面
            if self.context.pages:
                page = self.context.pages[0]
            else:
                page = self.context.new_page()

            log(f"浏览器已启动，CDP endpoint: {self.cdp_endpoint}")
            log(f"当前页面: {page.url}")

            return True

        except Exception as e:
            log(f"启动浏览器失败: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    def stop(self):
        """关闭浏览器"""
        try:
            if self.context:
                self.context.close()
                log("浏览器上下文已关闭")
            if self.playwright:
                self.playwright.stop()
                log("Playwright 已停止")
        except Exception as e:
            log(f"关闭浏览器时出错: {e}", "WARN")

    def navigate(self, url: str) -> bool:
        """导航到指定 URL"""
        try:
            if self.context and self.context.pages:
                page = self.context.pages[0]
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                log(f"已导航到: {url}")
                return True
        except Exception as e:
            log(f"导航失败: {e}", "ERROR")
        return False

    def keep_alive(self):
        """保持浏览器运行"""
        log("浏览器保持运行中，按 Ctrl+C 停止...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log("\n收到停止信号...")


# ==================== 入口 ====================
def main():
    log("=" * 60)
    log("Browser Launcher - CDP 浏览器启动器")
    log("=" * 60)

    # 检查 user_data_dir 是否存在
    if not USER_DATA_DIR.exists():
        log(f"创建浏览器数据目录: {USER_DATA_DIR}")
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    else:
        log(f"使用现有浏览器数据目录: {USER_DATA_DIR}")

    # 启动浏览器
    browser_manager = BrowserManager(USER_DATA_DIR, CDP_PORT)
    if not browser_manager.start():
        log("浏览器启动失败，退出", "ERROR")
        sys.exit(1)

    log("=" * 60)
    log("浏览器启动成功！")
    log(f"CDP Endpoint: {browser_manager.cdp_endpoint}")
    log("")
    log("请设置环境变量后运行 agent_runner.py:")
    log(f"  export PLAYWRIGHT_MCP_CDP_ENDPOINT={browser_manager.cdp_endpoint}")
    log("")
    log("或者直接运行:")
    log(f"  PLAYWRIGHT_MCP_CDP_ENDPOINT={browser_manager.cdp_endpoint} uv run python agent_runner.py")
    log("=" * 60)

    try:
        # 保持浏览器运行
        browser_manager.keep_alive()
    finally:
        log("关闭浏览器...")
        browser_manager.stop()
        log("浏览器已关闭")


if __name__ == "__main__":
    main()
