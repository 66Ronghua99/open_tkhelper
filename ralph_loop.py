#!/usr/bin/env python3
"""
Ralph Loop - TikTok 客服自动回复循环 (简化版)

架构: OpenCode 全自主模式
- Ralph Loop: 极简定时触发器 (15分钟周期)
- OpenCode: 负责所有浏览器操作 (启动、检测、回复、关闭)
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ==================== 配置 ====================
CHECK_INTERVAL = 60  # 15 分钟 (秒)
USER_DATA_DIR = Path(__file__).parent / "browser_data"
TIKTOK_URL = "https://seller.tiktokshopglobalselling.com/chat/inbox/current"
STATE_FILE = Path(__file__).parent / "ralph_state.json"


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
def build_opencode_prompt(user_data_dir: Path, tiktok_url: str, replied_msgs: str) -> str:
    """构建 OpenCode 提示词"""

    return f"""## 任务
你是 TikTok 客服助手。请使用 Playwright MCP 工具完成以下工作：

## 环境信息
- 浏览器数据目录: {user_data_dir}
- 目标页面: {tiktok_url}

## 操作步骤
1. 启动浏览器（使用 browser_launch，指定 user_data_dir）
2. 导航到 {tiktok_url}
3. 截图检查页面状态
4. 如需要登录，请等待用户手动登录后按回车继续
5. 检查是否有未读消息（红点、数字徽章、新消息提示等）
6. 如有新消息：
   - 点击进入聊天会话
   - 截图阅读买家最新消息
   - 生成友好、专业的中文回复
   - 在输入框输入回复内容
   - 点击发送按钮
   - 等待消息发送成功
7. 关闭浏览器

## 已回复消息（避免重复回复）
{replied_msgs}

## 回复要求
- 语气友好、专业、简洁
- 如果是产品咨询，提供有帮助的信息
- 如果是售后问题，表示愿意协助解决
- 回复控制在 100 字以内
- 如果是重复消息，请跳过回复

## 返回格式（JSON）
请在最后输出以下 JSON 格式的结果：
```json
{{
    "has_new_message": true/false,
    "msg_id": "消息唯一标识（如买家名称+时间+内容摘要）",
    "buyer_msg": "买家消息内容",
    "replied": true/false,
    "reply_content": "回复内容"
}}
```
"""


# ==================== OpenCode 调用 ====================
def call_opencode(prompt: str, working_dir: str) -> dict:
    """
    调用 OpenCode 执行浏览器任务
    返回解析后的 JSON 结果
    """
    log("调用 OpenCode...")

    # 创建临时文件存储提示词
    prompt_file = Path("/tmp/ralph_prompt.txt")
    prompt_file.write_text(prompt)

    try:
        # 调用 OpenCode CLI
        result = subprocess.run(
            [
                "opencode", "run",
                "--file", str(prompt_file),
                "--dir", working_dir,
                "--title", f"ralph-{datetime.now().strftime('%H%M%S')}",
                "请根据提示词完成 TikTok 客服任务，并返回 JSON 格式结果"
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 分钟超时
        )

        log(f"OpenCode 返回码: {result.returncode}")

        if result.stderr:
            log(f"OpenCode stderr: {result.stderr[:500]}", "DEBUG")

        # 从输出中解析 JSON 结果
        output = result.stdout

        # 尝试提取 JSON 部分
        json_result = extract_json_from_output(output)

        return {
            "success": result.returncode == 0,
            "output": output,
            "result": json_result
        }

    except subprocess.TimeoutExpired:
        log("OpenCode 调用超时", "ERROR")
        return {"success": False, "error": "timeout", "result": {}}
    except Exception as e:
        log(f"OpenCode 调用失败: {e}", "ERROR")
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
                "--args", "@anthropic/playwright-mcp-server"
            ])
            log("Playwright MCP 已添加")
        else:
            log("Playwright MCP 已配置")

    except Exception as e:
        log(f"MCP 配置检查失败: {e}", "WARN")


# ==================== 主循环 ====================
def main_loop():
    """主监控循环 - 简化版"""

    state = StateManager(STATE_FILE)
    working_dir = str(Path(__file__).parent)

    log("=" * 50)
    log("Ralph Loop 已启动 (OpenCode 全自主模式)")
    log(f"检查间隔: {CHECK_INTERVAL} 秒 ({CHECK_INTERVAL // 60} 分钟)")
    log(f"浏览器数据目录: {USER_DATA_DIR}")
    log("=" * 50)

    while True:
        try:
            log("-" * 50)
            log("开始新一轮检查...")

            # 1. 构建 OpenCode 提示词
            prompt = build_opencode_prompt(
                USER_DATA_DIR,
                TIKTOK_URL,
                state.get_replied_list_text()
            )

            # 2. 调用 OpenCode
            response = call_opencode(prompt, working_dir)

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

            # 4. 等待下一轮
            log(f"等待 {CHECK_INTERVAL} 秒后再次检查...")
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            log("\n用户中断，退出...")
            sys.exit(0)
        except Exception as e:
            log(f"循环出错: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            time.sleep(60)  # 出错后等待 1 分钟再重试


# ==================== 入口 ====================
if __name__ == "__main__":
    log("Ralph Loop 启动中...")

    # 检查 opencode 是否可用
    try:
        subprocess.run(["opencode", "--version"], capture_output=True, check=True)
        log("OpenCode CLI 已安装")
    except Exception:
        log("错误: opencode CLI 未安装或不在 PATH 中", "ERROR")
        log("请安装 OpenCode: npm install -g opencode", "ERROR")
        sys.exit(1)

    # 检查 user_data_dir 是否存在
    if not USER_DATA_DIR.exists():
        log(f"创建浏览器数据目录: {USER_DATA_DIR}")
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    else:
        log(f"使用现有浏览器数据目录: {USER_DATA_DIR}")

    # 设置 MCP
    setup_mcp()

    # 启动主循环
    main_loop()
