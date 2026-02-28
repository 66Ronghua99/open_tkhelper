#!/usr/bin/env python3
"""
Agent Runner - TikTok 客服 Agent 操作脚本

负责调用 OpenCode 执行具体的客服操作（检查未读消息、自动回复）。
需要配合 browser_launcher.py 启动的 CDP 浏览器使用。

【使用方法】

1. 先启动浏览器（终端1）：
   uv run python browser_launcher.py

2. 再运行 Agent（终端2）：
   export PLAYWRIGHT_MCP_CDP_ENDPOINT=http://localhost:9222
   uv run python agent_runner.py

3. 或者单次运行：
   PLAYWRIGHT_MCP_CDP_ENDPOINT=http://localhost:9222 uv run python agent_runner.py

【配置说明】
- CHECK_INTERVAL: 检查间隔（默认 300 秒 = 5 分钟）
- TIKTOK_URL: TikTok 客服页面地址
- STATE_FILE: 已回复消息记录文件

【前置要求】
- OpenCode CLI 已安装: npm install -g opencode
- ANTHROPIC_API_KEY 已设置: export ANTHROPIC_API_KEY=your_key
- browser_launcher.py 已在运行

【工作流程】
1. 连接 CDP 浏览器
2. 访问 TikTok 客服页面
3. 检查未分配/未读消息
4. 分配消息给自己
5. 生成并发送回复
6. 等待下一轮检查
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ==================== 配置 ====================
# 检查间隔（秒）- 默认 5 分钟
CHECK_INTERVAL = 300

# TikTok 卖家客服页面地址
TIKTOK_URL = "https://seller.tiktokshopglobalselling.com/chat/inbox/current"

# 已回复消息状态文件（自动创建）
STATE_FILE = Path(__file__).parent / "ralph_state.json"

# CDP Endpoint - 默认从环境变量读取，否则使用默认值
CDP_ENDPOINT = os.environ.get("PLAYWRIGHT_MCP_CDP_ENDPOINT", "http://localhost:9222")


# ==================== 日志工具 ====================
def log(msg: str, level: str = "INFO"):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


# ==================== 状态管理 ====================
class StateManager:
    """管理已回复的消息，避免重复回复"""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.replied_msgs: set = set()
        self.load()

    def load(self):
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self.replied_msgs = set(data.get("replied", []))
                log(f"加载状态: {len(self.replied_msgs)} 条已回复消息")
            except Exception as e:
                log(f"加载状态失败: {e}", "WARN")

    def save(self):
        try:
            data = {"replied": list(self.replied_msgs)}
            self.state_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            log(f"保存状态失败: {e}", "WARN")

    def has_replied(self, msg_id: str) -> bool:
        return msg_id in self.replied_msgs

    def mark_replied(self, msg_id: str):
        self.replied_msgs.add(msg_id)
        self.save()
        log(f"标记已回复: {msg_id[:50]}...")

    def get_replied_list_text(self) -> str:
        """获取已回复消息列表文本，用于提示词"""
        if not self.replied_msgs:
            return "无"
        return "\n".join([f"- {msg_id}" for msg_id in list(self.replied_msgs)[-10:]])


# ==================== OpenCode 提示词构建 ====================
def build_opencode_prompt(tiktok_url: str, replied_msgs: str) -> str:
    """构建 OpenCode 提示词（CDP 模式，不启动浏览器）"""

    return f"""## 任务
你是 TikTok 客服助手。请使用 Playwright MCP 工具完成以下工作。

## 重要说明
- 浏览器已经通过 CDP 连接启动，**不要**使用 browser_launch
- 直接使用 browser_navigate 等工具操作页面

## 目标页面: {tiktok_url}

## 操作步骤
1. 直接导航到 {tiktok_url}（浏览器已连接，无需启动）
2. 等待页面加载（2-3秒）
3. 截图检查页面状态
4. 如需要登录，请等待用户手动登录后按回车继续
5. 检查是否有**未分配**，**未读消息**，**紧急消息**等（红点、数字徽章、新消息提示等）
6. 如果有未分配的消息，全部分配给自己，直到没有未分配消息
7. 如有未回复消息：
   - 点击进入聊天会话
   - 截图阅读买家最新消息
   - 生成友好、专业的中文回复
   - 在输入框输入回复内容
   - 点击发送按钮
   - 等待消息发送成功
8. 重复步骤5-7，直到没有未回复消息或达到操作限制(**每次最多回复10个用户**，保持上下文干净)

## 已回复消息（避免重复回复）
{replied_msgs}

## 回复要求
- 语气友好、专业、简洁
- 如果是产品咨询，提供有帮助的信息
- 如果是售后问题，表示愿意协助解决
- 回复控制在 50 字以内
- 如果是重复消息，请跳过回复
- **!!重要!!**: 如果无法确定回复内容，可以回复“感谢您的消息，我们会尽快回复您！”等通用回复

```
"""


# ==================== OpenCode 调用 ====================
def call_opencode(prompt: str, working_dir: str, cdp_endpoint: str) -> dict:
    """
    调用 OpenCode 执行浏览器任务（CDP 模式，流式输出）
    返回解析后的 JSON 结果
    """
    log("调用 OpenCode...")

    # 创建临时文件存储提示词
    prompt_file = Path("/tmp/ralph_prompt.txt")
    prompt_file.write_text(prompt)
    log(f"提示词已写入临时文件: {prompt_file}")

    # 设置 CDP 环境变量
    env = os.environ.copy()
    env["PLAYWRIGHT_MCP_CDP_ENDPOINT"] = cdp_endpoint
    log(f"使用 CDP endpoint: {cdp_endpoint}")

    output_lines = []
    error_lines = []

    try:
        # 使用 Popen 实现流式输出
        process = subprocess.Popen(
            [
                "opencode", "run",
                "--file", str(prompt_file),
                "--dir", working_dir,
                "--title", f"ralph-{datetime.now().strftime('%H%M%S')}",
                "请根据提示词完成 TikTok 客服任务，并返回 JSON 格式结果"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )

        log("OpenCode 进程已启动，开始实时监控输出...")

        # 实时读取 stdout
        import select
        import fcntl
        import os as os_module

        # 设置非阻塞模式
        if process.stdout:
            fd = process.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os_module.O_NONBLOCK)

        if process.stderr:
            fd = process.stderr.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os_module.O_NONBLOCK)

        # 实时读取输出（带超时）
        start_time = time.time()
        timeout = 900  # 15 分钟

        while True:
            # 检查进程是否结束
            ret_code = process.poll()

            # 读取 stdout
            try:
                if process.stdout:
                    while True:
                        line = process.stdout.readline()
                        if not line:
                            break
                        line = line.rstrip()
                        if line:
                            output_lines.append(line)
                            print(f"[OpenCode stdout] {line}", flush=True)
            except (IOError, BlockingIOError):
                pass

            # 读取 stderr
            try:
                if process.stderr:
                    while True:
                        line = process.stderr.readline()
                        if not line:
                            break
                        line = line.rstrip()
                        if line:
                            error_lines.append(line)
                            print(f"[OpenCode stderr] {line}", flush=True)
            except (IOError, BlockingIOError):
                pass

            # 检查是否结束
            if ret_code is not None:
                log(f"OpenCode 进程结束，返回码: {ret_code}")
                break

            # 检查超时
            if time.time() - start_time > timeout:
                log("OpenCode 超时，终止进程...", "ERROR")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                return {"success": False, "error": "timeout", "result": {}}

            time.sleep(0.1)  # 短暂休眠避免 CPU 占用过高

        # 合并输出
        output = "\n".join(output_lines)
        stderr_output = "\n".join(error_lines)

        if stderr_output:
            log(f"OpenCode stderr 摘要: {stderr_output[:500]}", "DEBUG")

        # 尝试提取 JSON 部分
        # json_result = extract_json_from_output(output)

        return {
            "success": process.returncode == 0,
            "output": output,
            # "result": output
        }

    except Exception as e:
        log(f"OpenCode 调用失败: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "result": {}}


def extract_json_from_output(output: str) -> dict:
    """从 OpenCode 输出中提取 JSON 结果"""
    try:
        # 查找 ```json 代码块
        if "```json" in output:
            start = output.find("```json") + 7
            end = output.find("```", start)
            json_str = output[start:end].strip()
            return json.loads(json_str)

        # 查找 ``` 代码块
        if "```" in output:
            start = output.rfind("```") + 3
            end = output.find("```", start)
            if end > start:
                json_str = output[start:end].strip()
                return json.loads(json_str)

        # 尝试直接解析整个输出
        return json.loads(output.strip())

    except Exception as e:
        log(f"解析 JSON 失败: {e}", "DEBUG")
        return {}


# ==================== MCP 配置检查 ====================
def setup_mcp():
    """配置 OpenCode MCP（如果未配置）"""
    log("检查 MCP 配置...")

    try:
        result = subprocess.run(
            ["opencode", "mcp", "list"],
            capture_output=True,
            text=True
        )

        if "playwright" not in result.stdout.lower():
            log("添加 Playwright MCP 服务器...")
            subprocess.run([
                "opencode", "mcp", "add",
                "--name", "playwright",
                "--command", "npx",
                "--args", "@playwright/mcp@latest"
            ])
            log("Playwright MCP 已添加")
        else:
            log("Playwright MCP 已配置")

    except Exception as e:
        log(f"MCP 配置检查失败: {e}", "WARN")


# ==================== 单次运行 ====================
def run_once(state: StateManager, working_dir: str, cdp_endpoint: str) -> dict:
    """执行单次检查"""
    log("-" * 50)
    log("开始检查...")

    # 1. 构建 OpenCode 提示词
    prompt = build_opencode_prompt(
        TIKTOK_URL,
        state.get_replied_list_text()
    )

    # 2. 调用 OpenCode
    response = call_opencode(prompt, working_dir, cdp_endpoint)

    # 3. 解析结果
    if response.get("success"):
        result = response.get("result", {})

        has_new = result.get("has_new_message", False)
        replied = result.get("replied", False)
        msg_id = result.get("msg_id", "")
        buyer_msg = result.get("buyer_msg", "")

        if has_new:
            log(f"[检测到新消息] 买家: {buyer_msg[:50]}...")

            if replied and msg_id:
                state.mark_replied(msg_id)
                reply_content = result.get("reply_content", "")
                log(f"[已回复] {reply_content[:50]}...")
            elif not replied:
                log("[未回复] 可能是重复消息或无需回复")
        else:
            log("[无新消息]")
    else:
        error = response.get("error", "unknown")
        log(f"[OpenCode 失败] {error}", "ERROR")

    return response


# ==================== 主循环 ====================
def main_loop(cdp_endpoint: str):
    """主监控循环"""
    state = StateManager(STATE_FILE)
    working_dir = str(Path(__file__).parent)

    log("=" * 50)
    log("Agent Runner 已启动")
    log(f"CDP Endpoint: {cdp_endpoint}")
    log(f"检查间隔: {CHECK_INTERVAL} 秒 ({CHECK_INTERVAL // 60} 分钟)")
    log("=" * 50)

    try:
        while True:
            try:
                run_once(state, working_dir, cdp_endpoint)

                # 等待下一轮
                log(f"等待 {CHECK_INTERVAL} 秒后再次检查...")
                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                log("\n用户中断，退出...")
                break
            except Exception as e:
                log(f"循环出错: {e}", "ERROR")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # 出错后等待 1 分钟再重试

    finally:
        log("Agent Runner 已停止")


# ==================== 入口 ====================
def main():
    log("Agent Runner 启动中...")

    # 检查 opencode 是否可用
    try:
        subprocess.run(["opencode", "--version"], capture_output=True, check=True)
        log("OpenCode CLI 已安装")
    except Exception:
        log("错误: opencode CLI 未安装或不在 PATH 中", "ERROR")
        log("请安装 OpenCode: npm install -g opencode", "ERROR")
        sys.exit(1)

    # 设置 MCP
    setup_mcp()

    # 获取 CDP endpoint
    cdp_endpoint = CDP_ENDPOINT
    log(f"使用 CDP endpoint: {cdp_endpoint}")

    # 启动主循环
    main_loop(cdp_endpoint)


if __name__ == "__main__":
    main()
