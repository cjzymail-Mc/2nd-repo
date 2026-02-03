# -*- coding: utf-8 -*-
"""
Agent-Task - 单 Agent 任务执行器（支持分支隔离）

使用场景：
- 日常开发中调用单个 agent
- 自动创建分支避免冲突
- 适合迭代开发和并行任务

示例：
  # 让 tech_lead 检查函数并生成建议
  python agent-task.py tech_lead "检查 src/main.py 中的 process_data 函数并生成优化建议" --output advice.md

  # 同时在另一个窗口让 developer 修改代码
  python agent-task.py developer "根据 advice.md 重构 src/utils.py" --wait-for advice.md
"""

import argparse
import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime
import re


class AgentTask:
    """单 Agent 任务执行器"""

    AGENTS = {
        "architect": ".claude/agents/01-arch.md",
        "tech_lead": ".claude/agents/02-tech.md",
        "developer": ".claude/agents/03-dev.md",
        "tester": ".claude/agents/04-test.md",
        "optimizer": ".claude/agents/05-opti.md",
        "security": ".claude/agents/06-secu.md"
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def create_branch(self, agent_name: str, task_desc: str) -> str:
        """创建 agent 专用分支"""
        # 生成分支名
        clean_desc = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]+', '-', task_desc)
        clean_desc = clean_desc[:30]
        timestamp = datetime.now().strftime("%m%d-%H%M%S")
        branch_name = f"agent/{agent_name}/{clean_desc}-{timestamp}"

        try:
            # 检查当前分支
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )
            current_branch = result.stdout.strip()

            # 创建新分支
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=str(self.project_root),
                check=True
            )

            print(f"🌿 已创建分支: {branch_name}")
            print(f"   (从 {current_branch} 分支创建)\n")

            return branch_name

        except subprocess.CalledProcessError as e:
            print(f"❌ 创建分支失败: {e}")
            sys.exit(1)

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

        # 检查 agent 是否存在
        if agent_name not in self.AGENTS:
            print(f"❌ 未知的 agent: {agent_name}")
            print(f"可用的 agents: {', '.join(self.AGENTS.keys())}")
            sys.exit(1)

        role_file = self.project_root / self.AGENTS[agent_name]
        if not role_file.exists():
            print(f"❌ Agent 配置文件不存在: {self.AGENTS[agent_name]}")
            sys.exit(1)

        # 等待依赖文件
        if wait_for:
            if not self.wait_for_file(wait_for):
                sys.exit(1)

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
"""

        if output_file:
            full_prompt += f"\n- 请将输出保存到: {output_file}"

        # 执行 claude 命令（交互式）
        print(f"{'='*60}")
        print(f"🚀 启动 {agent_name} (交互式会话)")
        print(f"{'='*60}\n")

        try:
            # 设置环境变量，用于 git hook 检测
            env = os.environ.copy()
            env['AGENT_TASK'] = 'true'

            subprocess.run(
                ["claude", "-p", full_prompt],
                cwd=str(self.project_root),
                env=env
            )

            print(f"\n{'='*60}")
            print(f"✅ {agent_name} 任务完成")
            print(f"{'='*60}")

            if branch_name:
                print(f"\n当前分支: {branch_name}")
                print(f"下一步操作：")
                print(f"  1. 检查生成的文件")
                print(f"  2. 提交更改：git add . && git commit -m \"任务：{task[:40]}\"")
                print(f"  3. 合并到主分支或创建 PR")

        except KeyboardInterrupt:
            print(f"\n\n⚠️ 任务被中断")
            if branch_name:
                print(f"当前仍在分支: {branch_name}")
                print(f"可以继续工作或切回主分支: git checkout main")
            sys.exit(130)


def main():
    parser = argparse.ArgumentParser(
        description="Agent-Task - 单 Agent 任务执行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 基础用法
  python agent-task.py tech_lead "检查 src/main.py 的性能问题"

  # 指定输出文件
  python agent-task.py tech_lead "分析代码并生成建议" --output advice.md

  # 等待文件生成后再执行
  python agent-task.py developer "根据 advice.md 优化代码" --wait-for advice.md

  # 不创建分支（在当前分支工作）
  python agent-task.py tester "测试新功能" --no-branch

并行工作示例：
  # 窗口1：生成建议
  python agent-task.py tech_lead "分析 src/main.py" --output advice.md

  # 窗口2：等待建议后重构代码
  python agent-task.py developer "根据 advice.md 重构代码" --wait-for advice.md
        """
    )

    parser.add_argument(
        "agent",
        choices=list(AgentTask.AGENTS.keys()),
        help="要执行的 agent"
    )
    parser.add_argument(
        "task",
        help="任务描述"
    )
    parser.add_argument(
        "--output",
        help="指定输出文件（可选）"
    )
    parser.add_argument(
        "--wait-for",
        help="等待指定文件生成后再执行（适合依赖关系）"
    )
    parser.add_argument(
        "--no-branch",
        action="store_true",
        help="不创建新分支（在当前分支工作）"
    )

    args = parser.parse_args()

    # 获取项目根目录
    project_root = Path.cwd()

    # 创建执行器
    executor = AgentTask(project_root)

    # 执行任务
    executor.run_agent(
        agent_name=args.agent,
        task=args.task,
        create_branch=not args.no-branch,
        wait_for=args.wait_for,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
