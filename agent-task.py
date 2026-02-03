# -*- coding: utf-8 -*-
"""
Agent-Task - 单 Agent 任务执行器（交互式 CLI）

使用方式：
  # 交互模式（推荐）
  python agent-task.py

  # 传统命令行模式
  python agent-task.py tech_lead "检查代码" --output advice.md
"""

import argparse
import subprocess
import sys
import time
import os
import re
from pathlib import Path
from datetime import datetime


class AgentTask:
    """单 Agent 任务执行器"""

    # Agent 配置：名称 -> (角色文件, 默认输出文件, 中文名称)
    AGENTS = {
        "architect": (".claude/agents/01-arch.md", "PLAN.md", "系统架构师"),
        "tech_lead": (".claude/agents/02-tech.md", "advice.md", "技术负责人"),
        "developer": (".claude/agents/03-dev.md", "PROGRESS.md", "开发工程师"),
        "tester": (".claude/agents/04-test.md", "BUG_REPORT.md", "测试工程师"),
        "optimizer": (".claude/agents/05-opti.md", "OPTIMIZATION.md", "优化专家"),
        "security": (".claude/agents/06-secu.md", "SECURITY_AUDIT.md", "安全专家"),
    }

    # 别名映射（方便用户输入）
    ALIASES = {
        "arch": "architect",
        "架构": "architect",
        "架构师": "architect",
        "tech": "tech_lead",
        "技术": "tech_lead",
        "dev": "developer",
        "开发": "developer",
        "test": "tester",
        "测试": "tester",
        "opti": "optimizer",
        "优化": "optimizer",
        "sec": "security",
        "安全": "security",
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def resolve_agent_name(self, name: str) -> str:
        """解析 agent 名称（支持别名）"""
        name = name.lower().strip()
        if name in self.AGENTS:
            return name
        if name in self.ALIASES:
            return self.ALIASES[name]
        return None

    def get_agent_info(self, agent_name: str) -> tuple:
        """获取 agent 信息：(角色文件, 默认输出, 中文名称)"""
        return self.AGENTS.get(agent_name)

    def parse_input(self, user_input: str) -> tuple:
        """
        解析用户输入，提取 agent 和任务

        支持格式：
          - @tech_lead 检查代码性能
          - @开发 修复登录 bug
          - tech_lead: 检查代码
          - 让 architect 设计架构

        Returns:
            (agent_name, task, output_file) 或 (None, None, None)
        """
        user_input = user_input.strip()

        # 格式1: @agent_name 任务描述
        match = re.match(r'^@(\w+)\s+(.+)$', user_input)
        if match:
            agent_raw, task = match.groups()
            agent_name = self.resolve_agent_name(agent_raw)
            if agent_name:
                return agent_name, task, None

        # 格式2: @agent_name 任务描述 --output file.md
        match = re.match(r'^@(\w+)\s+(.+?)\s+(?:--output|-o)\s+(\S+)$', user_input)
        if match:
            agent_raw, task, output = match.groups()
            agent_name = self.resolve_agent_name(agent_raw)
            if agent_name:
                return agent_name, task, output

        # 格式3: agent_name: 任务描述
        match = re.match(r'^(\w+)[:：]\s*(.+)$', user_input)
        if match:
            agent_raw, task = match.groups()
            agent_name = self.resolve_agent_name(agent_raw)
            if agent_name:
                return agent_name, task, None

        # 格式4: 让 agent_name 做某事
        match = re.match(r'^(?:让|请|用|使用|call|use)\s*(\w+)\s+(.+)$', user_input, re.IGNORECASE)
        if match:
            agent_raw, task = match.groups()
            agent_name = self.resolve_agent_name(agent_raw)
            if agent_name:
                return agent_name, task, None

        return None, None, None

    def create_branch(self, agent_name: str, task_desc: str) -> str:
        """创建 agent 专用分支"""
        clean_desc = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]+', '-', task_desc)
        clean_desc = clean_desc[:30]
        timestamp = datetime.now().strftime("%m%d-%H%M%S")
        branch_name = f"agent/{agent_name}/{clean_desc}-{timestamp}"

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )
            current_branch = result.stdout.strip()

            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=str(self.project_root),
                check=True
            )

            print(f"🌿 已创建分支: {branch_name}")
            print(f"   (从 {current_branch} 分支创建)\n")
            return branch_name

        except subprocess.CalledProcessError as e:
            print(f"⚠️ 创建分支失败: {e}")
            return None

    def wait_for_file(self, file_path: str, timeout: int = 300):
        """等待文件生成"""
        target_file = self.project_root / file_path
        print(f"⏳ 等待文件生成: {file_path}")

        start_time = time.time()
        while time.time() - start_time < timeout:
            if target_file.exists():
                print(f"✅ 文件已生成: {file_path}\n")
                return True
            time.sleep(2)

        print(f"❌ 等待超时（{timeout}s）: {file_path}")
        return False

    def run_agent(
        self,
        agent_name: str,
        task: str,
        create_branch: bool = True,
        wait_for: str = None,
        output_file: str = None
    ):
        """执行单个 agent 任务"""

        # 获取 agent 信息
        agent_info = self.get_agent_info(agent_name)
        if not agent_info:
            print(f"❌ 未知的 agent: {agent_name}")
            self.show_agents()
            return False

        role_path, default_output, display_name = agent_info
        role_file = self.project_root / role_path

        if not role_file.exists():
            print(f"❌ Agent 配置文件不存在: {role_path}")
            return False

        # 使用默认输出文件（如果未指定）
        if output_file is None:
            output_file = default_output

        # 等待依赖文件
        if wait_for:
            if not self.wait_for_file(wait_for):
                return False

        # 创建分支（可选）
        branch_name = None
        if create_branch:
            branch_name = self.create_branch(agent_name, task)

        # 读取 agent 角色配置
        with open(role_file, 'r', encoding='utf-8') as f:
            role_prompt = f.read()

        # 构建任务提示词
        full_prompt = f"""{role_prompt}

---

用户任务：{task}

请严格按照你的角色职责完成任务。
- 如需读取项目文件，请使用相对路径（如 src/main.py）
- 输出文件必须使用正斜杠 / 路径
- 请将输出保存到: {output_file}
"""

        # 执行 claude 命令（交互式）
        print(f"{'='*60}")
        print(f"🚀 启动 {display_name} ({agent_name})")
        print(f"   输出文件: {output_file}")
        print(f"{'='*60}\n")

        try:
            env = os.environ.copy()
            env['AGENT_TASK'] = 'true'

            subprocess.run(
                ["claude", "-p", full_prompt],
                cwd=str(self.project_root),
                env=env
            )

            print(f"\n{'='*60}")
            print(f"✅ {display_name} 任务完成")
            if output_file:
                print(f"   输出文件: {output_file}")
            print(f"{'='*60}")

            if branch_name:
                print(f"\n当前分支: {branch_name}")
                print(f"下一步：git add . && git commit -m \"完成：{task[:40]}\"")

            return True

        except KeyboardInterrupt:
            print(f"\n\n⚠️ 任务被中断")
            return False

    def show_agents(self):
        """显示可用的 agents"""
        print("\n📋 可用的 Agents：")
        print("-" * 50)
        for name, (_, default_output, display_name) in self.AGENTS.items():
            aliases = [k for k, v in self.ALIASES.items() if v == name]
            alias_str = f" (别名: {', '.join(aliases)})" if aliases else ""
            print(f"  @{name:12s} - {display_name}{alias_str}")
            print(f"                   默认输出: {default_output}")
        print("-" * 50)

    def show_help(self):
        """显示帮助信息"""
        print("""
📖 使用帮助
============================================================

调用 Agent 的方式：
  @agent_name 任务描述          - 推荐方式
  @agent_name 任务 -o file.md   - 指定输出文件
  agent_name: 任务描述          - 冒号格式
  让 agent_name 做某事          - 自然语言

示例：
  @tech_lead 检查 src/main.py 的性能问题
  @开发 修复登录页面的 bug
  @tester 测试新功能 -o test_report.md
  让 architect 设计用户认证模块

特殊命令：
  help, ?      - 显示帮助
  agents, list - 显示所有可用 agents
  exit, quit   - 退出程序
  clear        - 清屏

选项：
  --no-branch  - 不创建新分支
  --wait-for FILE - 等待文件生成后再执行
============================================================
""")

    def interactive_mode(self):
        """交互式 CLI 模式"""
        print("""
╔════════════════════════════════════════════════════════════╗
║           🤖 Agent-Task 交互式命令行                        ║
║                                                            ║
║  输入 @agent_name 任务描述 来调用 agent                     ║
║  输入 help 查看帮助，agents 查看可用 agent                  ║
╚════════════════════════════════════════════════════════════╝
""")

        while True:
            try:
                user_input = input("\n💬 有什么可以帮您？\n> ").strip()

                if not user_input:
                    continue

                # 特殊命令
                cmd_lower = user_input.lower()

                if cmd_lower in ['exit', 'quit', 'q', '退出']:
                    print("\n👋 再见！")
                    break

                if cmd_lower in ['help', '?', '帮助']:
                    self.show_help()
                    continue

                if cmd_lower in ['agents', 'list', '列表']:
                    self.show_agents()
                    continue

                if cmd_lower == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue

                # 解析 --no-branch 选项
                create_branch = True
                if '--no-branch' in user_input:
                    create_branch = False
                    user_input = user_input.replace('--no-branch', '').strip()

                # 解析 --wait-for 选项
                wait_for = None
                wait_match = re.search(r'--wait-for\s+(\S+)', user_input)
                if wait_match:
                    wait_for = wait_match.group(1)
                    user_input = re.sub(r'--wait-for\s+\S+', '', user_input).strip()

                # 解析 agent 和任务
                agent_name, task, output_file = self.parse_input(user_input)

                if agent_name is None:
                    print("\n❓ 无法识别命令。请使用 @agent_name 格式")
                    print("   例如: @tech_lead 检查代码性能")
                    print("   输入 agents 查看可用的 agent")
                    continue

                # 确认执行
                agent_info = self.get_agent_info(agent_name)
                _, default_output, display_name = agent_info
                final_output = output_file or default_output

                print(f"\n📋 任务确认：")
                print(f"   Agent:  {display_name} (@{agent_name})")
                print(f"   任务:   {task}")
                print(f"   输出:   {final_output}")
                print(f"   分支:   {'创建新分支' if create_branch else '当前分支'}")
                if wait_for:
                    print(f"   等待:   {wait_for}")

                confirm = input("\n确认执行？[Y/n] ").strip().lower()
                if confirm in ['n', 'no', '否']:
                    print("已取消")
                    continue

                # 执行任务
                self.run_agent(
                    agent_name=agent_name,
                    task=task,
                    create_branch=create_branch,
                    wait_for=wait_for,
                    output_file=output_file
                )

            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except EOFError:
                print("\n\n👋 再见！")
                break


def main():
    parser = argparse.ArgumentParser(
        description="Agent-Task - 单 Agent 任务执行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
交互模式（推荐）：
  python agent-task.py

  进入后输入：
    @tech_lead 检查 src/main.py 的性能问题
    @开发 修复登录 bug
    @tester 测试新功能 -o report.md

传统命令行模式：
  python agent-task.py tech_lead "检查代码" --output advice.md
  python agent-task.py developer "修复 bug" --no-branch
        """
    )

    parser.add_argument(
        "agent",
        nargs="?",
        help="要执行的 agent（不指定则进入交互模式）"
    )
    parser.add_argument(
        "task",
        nargs="?",
        help="任务描述"
    )
    parser.add_argument(
        "--output", "-o",
        help="指定输出文件（可选，有默认值）"
    )
    parser.add_argument(
        "--wait-for",
        help="等待指定文件生成后再执行"
    )
    parser.add_argument(
        "--no-branch",
        action="store_true",
        help="不创建新分支"
    )

    args = parser.parse_args()

    project_root = Path.cwd()
    executor = AgentTask(project_root)

    # 如果没有指定 agent，进入交互模式
    if args.agent is None:
        executor.interactive_mode()
        return

    # 传统命令行模式
    if args.task is None:
        print("❌ 请提供任务描述")
        print("   示例: python agent-task.py tech_lead \"检查代码\"")
        sys.exit(1)

    # 解析 agent 名称
    agent_name = executor.resolve_agent_name(args.agent)
    if agent_name is None:
        print(f"❌ 未知的 agent: {args.agent}")
        executor.show_agents()
        sys.exit(1)

    success = executor.run_agent(
        agent_name=agent_name,
        task=args.task,
        create_branch=not args.no_branch,
        wait_for=args.wait_for,
        output_file=args.output
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
