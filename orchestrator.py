# -*- coding: utf-8 -*-
"""
Orchestrator.py - 星型拓扑多Agent并发调度系统

实现自动化调度6个agents，支持：
- 智能任务解析和复杂度评估
- 星型拓扑 + 流水线混合架构
- 并发执行（asyncio）
- 失败自动重试（最多3次）
- 实时进度监控和成本控制
- 状态持久化和错误日志
"""

import asyncio
import subprocess
import json
import argparse
import sys
import time
import uuid
import os
from pathlib import Path
from enum import Enum
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


# ============================================================
# 数据结构定义
# ============================================================

class AgentStatus(Enum):
    """Agent执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskComplexity(Enum):
    """任务复杂度"""
    SIMPLE = "simple"        # 仅3个agents (architect → developer → tester)
    MODERATE = "moderate"    # 4-5个agents
    COMPLEX = "complex"      # 完整6个agents


@dataclass
class AgentConfig:
    """Agent配置"""
    name: str
    role_file: str           # .claude/agents/xx.md
    output_files: List[str]  # 预期输出文件（如PLAN.md）


@dataclass
class ExecutionResult:
    """Agent执行结果"""
    agent_name: str
    status: AgentStatus
    session_id: str
    exit_code: int
    duration: float          # 执行时长（秒）
    cost: float              # 成本（USD）
    tokens: int              # 总tokens
    output_files: List[str]  # 实际生成的文件
    error_message: Optional[str] = None


# ============================================================
# 1. TaskParser - 任务解析器
# ============================================================

class TaskParser:
    """解析用户需求、评估复杂度"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def parse(self, user_input: str) -> Tuple[str, TaskComplexity]:
        """根据关键词评估复杂度"""
        user_input_lower = user_input.lower()

        # 复杂任务关键词
        complex_keywords = [
            "架构", "重构", "系统", "game", "网页", "webapp",
            "api", "数据库", "微服务", "赛车"
        ]

        # 简单任务关键词
        simple_keywords = [
            "修复", "bug", "日志", "fix", "typo", "注释"
        ]

        if any(kw in user_input_lower for kw in complex_keywords):
            return user_input, TaskComplexity.COMPLEX
        elif any(kw in user_input_lower for kw in simple_keywords):
            return user_input, TaskComplexity.SIMPLE
        else:
            return user_input, TaskComplexity.MODERATE

    def is_existing_project(self) -> bool:
        """检测是否是现有项目（有源码）"""
        # 检查常见源码目录
        source_dirs = ['src', 'lib', 'app', 'components', 'packages']
        for dir_name in source_dirs:
            if (self.project_root / dir_name).exists():
                return True

        # 检查配置文件
        config_files = [
            'package.json', 'requirements.txt', 'pom.xml',
            'Cargo.toml', 'go.mod', 'composer.json'
        ]
        for file_name in config_files:
            if (self.project_root / file_name).exists():
                return True

        # 检查是否有 git 提交历史
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', '-1'],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return True
        except:
            pass

        return False

    def generate_initial_prompt(self, user_request: str, agent_name: str = None) -> str:
        """生成初始任务提示词"""
        base_prompt = f"""用户需求：{user_request}

请严格按照你的角色职责完成任务。
- 如需读取项目文件，请使用相对路径（如 src/main.py）
- 输出文件必须使用正斜杠 / 路径
- 完成后更新相关文档（PLAN.md、PROGRESS.md等）
"""

        # 如果是 architect 且是现有项目，添加代码库分析指令
        if agent_name == "architect" and self.is_existing_project():
            base_prompt += """

⚠️ 重要提示：这是一个现有项目！

请按以下步骤工作：

1. **第一步：代码库分析**
   - 使用 ls、tree、git log 等命令了解项目结构
   - 使用 Read、Glob、Grep 工具探索源代码
   - 生成 CODEBASE_ANALYSIS.md，包含：
     * 项目结构（目录树 + 核心模块说明）
     * 技术栈（语言、框架、库）
     * 代码风格和设计模式
     * 关键文件清单
     * 模块依赖关系

2. **第二步：制定计划**
   - 基于代码库分析，生成 PLAN.md
   - 计划必须遵循现有的架构风格和代码规范
   - 复用现有模块，避免重复造轮子

记住：先理解代码，再做设计！
"""

        return base_prompt


# ============================================================
# 2. AgentScheduler - 调度规划器
# ============================================================

class AgentScheduler:
    """规划执行阶段、管理agent配置"""

    # Agent配置映射
    AGENT_CONFIGS = {
        "architect": AgentConfig(
            name="architect",
            role_file=".claude/agents/01-arch.md",
            output_files=["PLAN.md", "CODEBASE_ANALYSIS.md"]  # 可能生成代码库分析
        ),
        "tech_lead": AgentConfig(
            name="tech_lead",
            role_file=".claude/agents/02-tech.md",
            output_files=["PLAN.md"]  # 审查并更新
        ),
        "developer": AgentConfig(
            name="developer",
            role_file=".claude/agents/03-dev.md",
            output_files=["PROGRESS.md"]
        ),
        "tester": AgentConfig(
            name="tester",
            role_file=".claude/agents/04-test.md",
            output_files=["BUG_REPORT.md"]
        ),
        "optimizer": AgentConfig(
            name="optimizer",
            role_file=".claude/agents/05-opti.md",
            output_files=[]  # 直接修改代码
        ),
        "security": AgentConfig(
            name="security",
            role_file=".claude/agents/06-secu.md",
            output_files=["SECURITY_AUDIT.md"]
        ),
    }

    def plan_execution(self, complexity: TaskComplexity) -> List[List[str]]:
        """
        根据复杂度规划执行阶段
        返回：[[Phase1 agents], [Phase2 agents], ...]
        """
        if complexity == TaskComplexity.SIMPLE:
            return [
                ["architect"],
                ["developer"],
                ["tester"]
            ]
        elif complexity == TaskComplexity.MODERATE:
            return [
                ["architect"],
                ["developer"],
                ["tester", "security"]
            ]
        else:  # COMPLEX
            return [
                ["architect"],
                ["tech_lead"],
                ["developer"],
                ["tester", "security", "optimizer"]
            ]

    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """获取Agent配置"""
        return self.AGENT_CONFIGS[agent_name]


# ============================================================
# 3. AgentExecutor - 执行引擎
# ============================================================

class AgentExecutor:
    """执行claude -p命令、管理子进程、解析输出"""

    def __init__(self, project_root: Path, max_budget: float = 10.0):
        self.project_root = project_root
        self.max_budget = max_budget

    async def run_agent(
        self,
        config: AgentConfig,
        task_prompt: str,
        timeout: int = 600,
        session_id: Optional[str] = None
    ) -> ExecutionResult:
        """
        执行单个agent（异步）

        Args:
            config: Agent配置
            task_prompt: 任务提示词
            timeout: 超时时间（秒）
            session_id: 会话ID（可选，不提供则自动生成）
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        start_time = time.time()

        # 读取agent角色配置
        role_file = self.project_root / config.role_file
        try:
            with open(role_file, 'r', encoding='utf-8') as f:
                role_prompt = f.read()
        except FileNotFoundError:
            return ExecutionResult(
                agent_name=config.name,
                status=AgentStatus.FAILED,
                session_id=session_id,
                exit_code=1,
                duration=0,
                cost=0,
                tokens=0,
                output_files=[],
                error_message=f"角色配置文件不存在: {config.role_file}"
            )

        # 构建完整提示词
        full_prompt = f"{role_prompt}\n\n---\n\n{task_prompt}"

        # 构建claude命令
        cmd = [
            "claude", "-p", full_prompt,
            "--output-format", "stream-json",
            "--verbose",  # stream-json 格式需要 verbose
            "--model", "sonnet",
            "--max-turns", "20",
            "--max-budget-usd", str(self.max_budget),
            "--session-id", session_id,
            "--no-chrome"
        ]

        # 异步执行子进程
        try:
            # 设置环境变量，用于 git hook 检测
            env = os.environ.copy()
            env['ORCHESTRATOR_RUNNING'] = 'true'

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            # 等待完成（带超时）
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return ExecutionResult(
                    agent_name=config.name,
                    status=AgentStatus.FAILED,
                    session_id=session_id,
                    exit_code=-1,
                    duration=time.time() - start_time,
                    cost=0,
                    tokens=0,
                    output_files=[],
                    error_message=f"执行超时（{timeout}s）"
                )

            # 解析stream-json输出获取成本和tokens
            cost, tokens = self._parse_stream_json(stdout.decode('utf-8'))

            duration = time.time() - start_time

            # 检查输出文件是否生成
            output_files = self._check_output_files(config.output_files)

            status = AgentStatus.COMPLETED if process.returncode == 0 else AgentStatus.FAILED

            return ExecutionResult(
                agent_name=config.name,
                status=status,
                session_id=session_id,
                exit_code=process.returncode,
                duration=duration,
                cost=cost,
                tokens=tokens,
                output_files=output_files,
                error_message=stderr.decode('utf-8') if process.returncode != 0 else None
            )

        except Exception as e:
            return ExecutionResult(
                agent_name=config.name,
                status=AgentStatus.FAILED,
                session_id=session_id,
                exit_code=1,
                duration=time.time() - start_time,
                cost=0,
                tokens=0,
                output_files=[],
                error_message=str(e)
            )

    def run_agent_interactive(
        self,
        config: AgentConfig,
        task_prompt: str,
        session_id: Optional[str] = None
    ) -> ExecutionResult:
        """
        以交互式模式执行agent（用于architect阶段）
        用户可以反复讨论计划，直到满意

        Returns:
            ExecutionResult with basic info (详细成本等需手动检查)
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        start_time = time.time()

        # 读取agent角色配置
        role_file = self.project_root / config.role_file
        try:
            with open(role_file, 'r', encoding='utf-8') as f:
                role_prompt = f.read()
        except FileNotFoundError:
            return ExecutionResult(
                agent_name=config.name,
                status=AgentStatus.FAILED,
                session_id=session_id,
                exit_code=1,
                duration=0,
                cost=0,
                tokens=0,
                output_files=[],
                error_message=f"角色配置文件不存在: {config.role_file}"
            )

        # 构建初始提示词
        full_prompt = f"{role_prompt}\n\n---\n\n{task_prompt}"

        print(f"\n{'='*60}")
        print(f"🎯 启动交互式规划会话 - {config.name}")
        print(f"{'='*60}")
        print(f"提示：你可以和 architect 反复讨论计划，直到完美")
        print(f"完成后请确保生成了 PLAN.md 文件，然后退出会话")
        print(f"{'='*60}\n")

        # 写入临时提示文件（避免命令行参数过长）
        temp_prompt_file = self.project_root / ".claude" / f"prompt_{session_id}.txt"
        temp_prompt_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_prompt_file, 'w', encoding='utf-8') as f:
            f.write(full_prompt)

        # 构建交互式claude命令（不使用 -p）
        cmd = [
            "claude",
            "-p", full_prompt,
            "--model", "sonnet",
            "--max-budget-usd", str(self.max_budget),
            "--session-id", session_id
        ]

        # 同步执行（阻塞等待用户交互）
        try:
            # 设置环境变量，用于 git hook 检测
            env = os.environ.copy()
            env['ORCHESTRATOR_RUNNING'] = 'true'

            # 使用 subprocess.run 而不是 asyncio（需要继承 stdin/stdout）
            process = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                env=env
                # 不重定向 stdin/stdout/stderr，让用户直接交互
            )

            duration = time.time() - start_time

            # 检查输出文件是否生成
            output_files = self._check_output_files(config.output_files)

            # 清理临时文件
            if temp_prompt_file.exists():
                temp_prompt_file.unlink()

            status = AgentStatus.COMPLETED if process.returncode == 0 else AgentStatus.FAILED

            # 交互式模式无法准确获取成本，返回估算值
            return ExecutionResult(
                agent_name=config.name,
                status=status,
                session_id=session_id,
                exit_code=process.returncode,
                duration=duration,
                cost=0.0,  # 交互式模式成本需手动查看
                tokens=0,
                output_files=output_files,
                error_message=None if process.returncode == 0 else "交互式会话异常退出"
            )

        except Exception as e:
            # 清理临时文件
            if temp_prompt_file.exists():
                temp_prompt_file.unlink()

            return ExecutionResult(
                agent_name=config.name,
                status=AgentStatus.FAILED,
                session_id=session_id,
                exit_code=1,
                duration=time.time() - start_time,
                cost=0,
                tokens=0,
                output_files=[],
                error_message=str(e)
            )

    async def run_parallel(
        self,
        configs: List[AgentConfig],
        prompts: Dict[str, str]
    ) -> Dict[str, ExecutionResult]:
        """并发执行多个agents"""
        tasks = [
            self.run_agent(config, prompts[config.name])
            for config in configs
        ]
        results = await asyncio.gather(*tasks)
        return {r.agent_name: r for r in results}

    def _parse_stream_json(self, stdout: str) -> Tuple[float, int]:
        """
        解析stream-json输出获取成本和tokens
        简化实现：从最后一行提取
        """
        try:
            lines = stdout.strip().split('\n')
            for line in reversed(lines):
                if line.strip():
                    data = json.loads(line)
                    cost = data.get('cost', 0)
                    tokens = data.get('tokens', 0)
                    return cost, tokens
        except:
            pass
        return 0.0, 0

    def _check_output_files(self, expected_files: List[str]) -> List[str]:
        """检查输出文件是否存在"""
        existing = []
        for file in expected_files:
            file_path = self.project_root / file
            if file_path.exists():
                existing.append(file)
        return existing


# ============================================================
# 4. StateManager - 状态管理器
# ============================================================

class StateManager:
    """持久化状态到.claude/state.json"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.state_file = project_root / ".claude" / "state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def save_state(self, state: Dict) -> None:
        """原子化保存状态"""
        temp_file = self.state_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        temp_file.replace(self.state_file)

    def load_state(self) -> Optional[Dict]:
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def clear_state(self) -> None:
        """清除状态"""
        if self.state_file.exists():
            self.state_file.unlink()


# ============================================================
# 5. ErrorHandler - 错误处理器
# ============================================================

class ErrorHandler:
    """重试机制、错误日志"""

    def __init__(self, project_root: Path, max_retries: int = 3):
        self.project_root = project_root
        self.max_retries = max_retries
        self.backoff_seconds = [5, 10, 20]
        self.error_log_file = project_root / ".claude" / "error_log.json"
        self.error_log_file.parent.mkdir(parents=True, exist_ok=True)

    async def retry_with_backoff(
        self,
        func,
        *args,
        **kwargs
    ) -> ExecutionResult:
        """
        重试最多3次，间隔5s/10s/20s
        3次失败后记录错误并返回
        """
        for attempt in range(self.max_retries):
            result = await func(*args, **kwargs)

            if result.status == AgentStatus.COMPLETED:
                return result

            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries - 1:
                wait_time = self.backoff_seconds[attempt]
                print(f"  [重试] {result.agent_name} 失败，{wait_time}秒后重试（{attempt + 1}/{self.max_retries}）")
                await asyncio.sleep(wait_time)

        # 3次重试后仍失败 → 记录错误
        self.log_error(result)
        return result

    def log_error(self, result: ExecutionResult) -> None:
        """记录错误到error_log.json"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": result.agent_name,
            "exit_code": result.exit_code,
            "error_message": result.error_message,
            "retry_count": self.max_retries,
            "session_id": result.session_id
        }

        # 追加到错误日志
        errors = []
        if self.error_log_file.exists():
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                errors = json.load(f)

        errors.append(error_entry)

        with open(self.error_log_file, 'w', encoding='utf-8') as f:
            json.dump(errors, f, indent=2, ensure_ascii=False)


# ============================================================
# 6. ProgressMonitor - 进度监控器
# ============================================================

class ProgressMonitor:
    """实时进度显示、汇总报告"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def display_phase_start(self, phase_num: int, agents: List[str]) -> None:
        """显示当前执行阶段"""
        print(f"\n{'='*60}")
        print(f"Phase {phase_num}: {', '.join(agents)}")
        print(f"{'='*60}")

    def display_agent_start(self, agent_name: str, session_id: str) -> None:
        """显示agent启动"""
        print(f"  [启动] {self._get_agent_display_name(agent_name)} (session: {session_id})")

    def display_agent_complete(
        self,
        result: ExecutionResult
    ) -> None:
        """显示agent完成"""
        status_icon = "✅" if result.status == AgentStatus.COMPLETED else "❌"

        # 如果有成本信息则显示，否则显示 tokens
        if result.cost > 0:
            cost_info = f"${result.cost:.4f}"
        elif result.tokens > 0:
            cost_info = f"{result.tokens:,} tokens"
        else:
            cost_info = "Pro 订阅"

        print(f"  {status_icon} {self._get_agent_display_name(result.agent_name)} - "
              f"{result.status.value} (耗时 {result.duration:.1f}s, {cost_info})")

        if result.status == AgentStatus.FAILED and result.error_message:
            print(f"      错误: {result.error_message[:100]}")

    def display_summary(
        self,
        all_results: Dict[str, ExecutionResult],
        total_duration: float
    ) -> None:
        """显示执行汇总"""
        total_cost = sum(r.cost for r in all_results.values())
        total_tokens = sum(r.tokens for r in all_results.values())

        print(f"\n{'='*60}")
        print(f"执行完成 - 总耗时 {total_duration:.1f}s")
        print(f"{'='*60}")

        # 智能显示成本或 tokens
        if total_cost > 0:
            print(f"总成本: ${total_cost:.4f}")
            print(f"总tokens: {total_tokens:,}")
        elif total_tokens > 0:
            print(f"总tokens: {total_tokens:,} (Pro 订阅模式)")
        else:
            print(f"计费模式: Pro 订阅（固定月费）")

        print(f"\nAgent 执行结果:")

        for name, result in all_results.items():
            status_icon = "✅" if result.status == AgentStatus.COMPLETED else "❌"

            # 显示成本或 tokens
            if result.cost > 0:
                cost_info = f"${result.cost:.4f}"
            elif result.tokens > 0:
                cost_info = f"{result.tokens:,} tokens"
            else:
                cost_info = "Pro 订阅"

            print(f"  {status_icon} {name:12s} - {result.status.value:10s} "
                  f"(耗时 {result.duration:.1f}s, {cost_info})")

            if result.output_files:
                for file in result.output_files:
                    print(f"      → 输出: {file}")

    def _get_agent_display_name(self, agent_name: str) -> str:
        """获取agent显示名称"""
        name_map = {
            "architect": "系统架构师",
            "tech_lead": "技术负责人",
            "developer": "开发工程师",
            "tester": "测试工程师",
            "optimizer": "优化专家",
            "security": "安全专家"
        }
        return name_map.get(agent_name, agent_name)


# ============================================================
# 7. Orchestrator - 主控类
# ============================================================

class Orchestrator:
    """协调所有模块，执行完整工作流"""

    def __init__(
        self,
        project_root: Path,
        max_budget: float = 10.0,
        max_retries: int = 3,
        verbose: bool = False,
        interactive_architect: bool = True
    ):
        self.project_root = project_root
        self.task_parser = TaskParser(project_root)
        self.scheduler = AgentScheduler()
        self.executor = AgentExecutor(project_root, max_budget)
        self.state_manager = StateManager(project_root)
        self.error_handler = ErrorHandler(project_root, max_retries)
        self.monitor = ProgressMonitor(verbose)
        self.interactive_architect = interactive_architect

    def _cleanup_old_state(self) -> None:
        """清理旧的状态文件和错误日志"""
        files_to_clean = [
            self.state_manager.state_file,
            self.state_manager.state_file.with_suffix('.tmp'),
            self.error_handler.error_log_file
        ]

        for file in files_to_clean:
            if file.exists():
                try:
                    file.unlink()
                except Exception:
                    pass  # 忽略清理失败

        # 清理旧的临时提示文件
        claude_dir = self.project_root / ".claude"
        if claude_dir.exists():
            for temp_file in claude_dir.glob("prompt_*.txt"):
                try:
                    temp_file.unlink()
                except Exception:
                    pass

    def _create_feature_branch(self, task_description: str) -> Optional[str]:
        """
        为任务创建 feature 分支

        Returns:
            分支名称，如果失败则返回 None
        """
        import re
        from datetime import datetime

        # 生成分支名：feature/task-description-timestamp
        # 清理任务描述：只保留字母数字和短横线
        clean_desc = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]+', '-', task_description)
        clean_desc = clean_desc[:30]  # 限制长度
        timestamp = datetime.now().strftime("%m%d-%H%M")
        branch_name = f"feature/orchestrator-{clean_desc}-{timestamp}"

        try:
            # 检查是否在 git 仓库中
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return None  # 不是 git 仓库，跳过分支创建

            # 创建并切换到新分支
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"🌿 已创建并切换到分支: {branch_name}")
                return branch_name
            else:
                print(f"⚠️ 创建分支失败: {result.stderr}")
                return None

        except Exception as e:
            print(f"⚠️ Git 操作失败: {e}")
            return None

    async def execute(self, user_request: str, clean_start: bool = True) -> bool:
        """
        执行完整工作流

        Args:
            user_request: 用户需求描述
            clean_start: 是否清理旧状态（默认True，--resume时为False）

        Returns:
            True if successful, False if failed
        """
        start_time = time.time()

        # Phase 0: 清理旧状态（新任务时）
        if clean_start:
            self._cleanup_old_state()
            print("🧹 已清理旧的状态文件和错误日志\n")

        # Phase 0.1: 创建 feature 分支（新任务时）
        feature_branch = None
        if clean_start:
            feature_branch = self._create_feature_branch(user_request)

        # Phase 0.2: 解析任务
        print(f"📋 用户需求: {user_request}")
        task_prompt, complexity = self.task_parser.parse(user_request)
        print(f"任务复杂度: {complexity.value}")

        # Phase 0.5: 规划执行阶段
        phases = self.scheduler.plan_execution(complexity)
        print(f"执行计划: {len(phases)} 个阶段\n")

        # 初始化状态
        task_id = str(uuid.uuid4())
        state = {
            "task_id": task_id,
            "user_request": user_request,
            "complexity": complexity.value,
            "current_phase": 0,
            "agents_status": {},
            "results": {},
            "total_cost": 0.0,
            "total_tokens": 0
        }

        all_results = {}

        # 执行各阶段
        for phase_idx, agent_names in enumerate(phases, 1):
            self.monitor.display_phase_start(phase_idx, agent_names)

            # 准备agent配置和提示词
            configs = [self.scheduler.get_agent_config(name) for name in agent_names]
            prompts = {
                name: self.task_parser.generate_initial_prompt(user_request, agent_name=name)
                for name in agent_names
            }

            # 串行 or 并行执行
            if len(agent_names) == 1:
                # 单个agent：串行执行（带重试）
                config = configs[0]

                # 生成 session_id
                session_id = str(uuid.uuid4())

                # architect 可选择使用交互式模式
                if config.name == "architect" and self.interactive_architect:
                    print(f"\n💡 {self.monitor._get_agent_display_name(config.name)} 将在交互式模式下运行")
                    print(f"   你可以反复讨论计划，直到满意后退出会话")
                    print(f"   如需跳过交互，下次运行时添加 --auto-architect 参数\n")

                    # 交互式模式（阻塞，在异步上下文中运行同步函数）
                    result = await asyncio.to_thread(
                        self.executor.run_agent_interactive,
                        config,
                        prompts[config.name],
                        session_id
                    )
                else:
                    # 其他agents：无头模式（带重试）
                    self.monitor.display_agent_start(config.name, session_id)

                    result = await self.error_handler.retry_with_backoff(
                        self.executor.run_agent,
                        config,
                        prompts[config.name],
                        session_id=session_id
                    )

                self.monitor.display_agent_complete(result)
                all_results[config.name] = result

                # 如果失败，终止执行
                if result.status == AgentStatus.FAILED:
                    print(f"\n❌ {config.name} 执行失败，终止流程")
                    self._save_final_state(state, all_results, time.time() - start_time)
                    return False

            else:
                # 多个agents：并行执行（每个都带重试）
                # 为每个agent生成session_id
                session_ids = {config.name: str(uuid.uuid4()) for config in configs}

                for config in configs:
                    self.monitor.display_agent_start(config.name, session_ids[config.name])

                # 并行执行所有agents（每个独立重试）
                tasks = [
                    self.error_handler.retry_with_backoff(
                        self.executor.run_agent,
                        config,
                        prompts[config.name],
                        session_id=session_ids[config.name]
                    )
                    for config in configs
                ]
                results = await asyncio.gather(*tasks)

                # 显示结果
                for result in results:
                    self.monitor.display_agent_complete(result)
                    all_results[result.agent_name] = result

                # 如果任何一个失败，终止执行
                if any(r.status == AgentStatus.FAILED for r in results):
                    failed_agents = [r.agent_name for r in results if r.status == AgentStatus.FAILED]
                    print(f"\n❌ 以下agents执行失败: {', '.join(failed_agents)}，终止流程")
                    self._save_final_state(state, all_results, time.time() - start_time)
                    return False

            # 更新状态
            state["current_phase"] = phase_idx
            for name, result in all_results.items():
                state["agents_status"][name] = result.status.value
                # 转换 ExecutionResult 为可序列化的字典
                result_dict = asdict(result)
                result_dict["status"] = result.status.value  # 枚举 -> 字符串
                state["results"][name] = result_dict
            self.state_manager.save_state(state)

        # 显示汇总
        total_duration = time.time() - start_time
        self.monitor.display_summary(all_results, total_duration)

        # 保存最终状态
        self._save_final_state(state, all_results, total_duration)

        # 如果创建了 feature 分支，提示合并
        if feature_branch:
            print(f"\n{'='*60}")
            print(f"✅ 任务完成！当前在分支: {feature_branch}")
            print(f"{'='*60}")
            print(f"下一步操作：")
            print(f"  1. 检查生成的代码和文档")
            print(f"  2. 运行测试确保功能正常")
            print(f"  3. 提交更改：")
            print(f"     git add .")
            print(f"     git commit -m \"完成：{user_request[:50]}\"")
            print(f"  4. 合并到主分支：")
            print(f"     git checkout main")
            print(f"     git merge {feature_branch}")
            print(f"  5. 或创建 Pull Request 进行代码审查")
            print(f"{'='*60}\n")

        return True

    def _save_final_state(
        self,
        state: Dict,
        all_results: Dict[str, ExecutionResult],
        total_duration: float
    ) -> None:
        """保存最终状态"""
        state["total_cost"] = sum(r.cost for r in all_results.values())
        state["total_tokens"] = sum(r.tokens for r in all_results.values())
        state["total_duration"] = total_duration
        self.state_manager.save_state(state)


# ============================================================
# CLI接口
# ============================================================

def main():
    """CLI入口"""
    parser = argparse.ArgumentParser(
        description="Orchestrator - 星型拓扑多Agent并发调度系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 简单任务（architect交互式规划）
  python orchestrator.py "修复src/main.py中的登录bug"

  # 复杂任务（交互式 + 详细日志）
  python orchestrator.py "帮我写一个网页版的赛车游戏" --max-budget 20.0 --verbose

  # 完全自动化执行（跳过交互）
  python orchestrator.py "任务描述" --auto-architect

  # 恢复中断任务
  python orchestrator.py --resume
        """
    )

    parser.add_argument(
        "request",
        nargs="?",
        help="用户需求描述"
    )
    parser.add_argument(
        "--max-budget",
        type=float,
        default=10.0,
        help="最大预算（USD），默认10.0"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="最大重试次数，默认3"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细日志输出"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="从上次中断处恢复"
    )
    parser.add_argument(
        "--auto-architect",
        action="store_true",
        help="architect阶段使用自动模式（默认为交互式）"
    )

    args = parser.parse_args()

    # 获取项目根目录
    project_root = Path.cwd()

    # 创建orchestrator实例
    orchestrator = Orchestrator(
        project_root=project_root,
        max_budget=args.max_budget,
        max_retries=args.max_retries,
        verbose=args.verbose,
        interactive_architect=not args.auto_architect
    )

    # 恢复模式
    if args.resume:
        state = orchestrator.state_manager.load_state()
        if state:
            print(f"📂 恢复任务: {state['user_request']}")
            user_request = state['user_request']
        else:
            print("❌ 未找到可恢复的任务")
            sys.exit(1)
    else:
        if not args.request:
            parser.print_help()
            sys.exit(1)
        user_request = args.request

    # 执行
    try:
        # resume 模式不清理旧状态，新任务则清理
        success = asyncio.run(orchestrator.execute(user_request, clean_start=not args.resume))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断执行")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 执行错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
