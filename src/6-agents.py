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
import re
from pathlib import Path
from enum import Enum
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Windows 控制台 UTF-8 编码支持
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


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
                text=True,
                encoding='utf-8'
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

    def get_all_agent_names(self) -> List[str]:
        """获取所有可用的 agent 名称"""
        return list(self.AGENT_CONFIGS.keys())


# ============================================================
# 2.5 ManualTaskParser - 手动任务解析器
# ============================================================

class ManualTaskParser:
    """
    解析手动指定的 agent 任务

    支持语法：
      - @tech_lead 审核代码                    # 单个 agent
      - @tech_lead 审核 && @security 安检      # 并行执行
      - @tech_lead 审核 -> @developer 修复     # 串行执行
      - @tech_lead 审核 -> (@dev 修复 && @sec 安检) -> @tester 测试  # 混合模式
    """

    # Agent 别名映射
    ALIASES = {
        "arch": "architect",
        "架构": "architect",
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

    def __init__(self):
        self.scheduler = AgentScheduler()
        self.valid_agents = self.scheduler.get_all_agent_names()

    def is_manual_mode(self, user_input: str) -> bool:
        """检测是否是手动指定模式（包含 @agent，支持中文别名）"""
        return bool(re.search(r'@[\w\u4e00-\u9fff]+', user_input))

    def resolve_agent_name(self, name: str) -> Optional[str]:
        """解析 agent 名称（支持别名）"""
        name = name.lower().strip()
        if name in self.valid_agents:
            return name
        if name in self.ALIASES:
            return self.ALIASES[name]
        return None

    def parse(self, user_input: str) -> Tuple[List[List[Tuple[str, str]]], bool]:
        """
        解析手动指定的任务

        Args:
            user_input: 用户输入，如 "@tech_lead 审核代码 -> @developer 修复"

        Returns:
            (phases, success)
            phases: [[("agent_name", "task"), ...], ...]  # 每个 phase 包含并行的 agent-task 对
            success: 解析是否成功
        """
        user_input = user_input.strip()

        # 按 -> 分割成多个 phase（串行）
        phase_strs = re.split(r'\s*->\s*', user_input)

        phases = []
        for phase_str in phase_strs:
            phase_str = phase_str.strip()

            # 去除括号
            if phase_str.startswith('(') and phase_str.endswith(')'):
                phase_str = phase_str[1:-1].strip()

            # 按 && 分割成并行任务
            parallel_strs = re.split(r'\s*&&\s*', phase_str)

            phase_tasks = []
            for task_str in parallel_strs:
                task_str = task_str.strip()

                # 解析 @agent_name 任务描述（支持中文别名）
                match = re.match(r'@([\w\u4e00-\u9fff]+)\s+(.+)$', task_str)
                if match:
                    agent_raw, task = match.groups()
                    agent_name = self.resolve_agent_name(agent_raw)

                    if agent_name is None:
                        print(f"❌ 未知的 agent: @{agent_raw}")
                        print(f"   可用的 agents: {', '.join(self.valid_agents)}")
                        return [], False

                    phase_tasks.append((agent_name, task.strip()))
                else:
                    print(f"❌ 无法解析任务: {task_str}")
                    print(f"   请使用格式: @agent_name 任务描述")
                    return [], False

            if phase_tasks:
                phases.append(phase_tasks)

        return phases, True

    def preview(self, phases: List[List[Tuple[str, str]]]) -> None:
        """预览执行计划"""
        print(f"\n📋 手动指定模式 - 执行计划：")
        print(f"   共 {len(phases)} 个阶段")

        for i, phase in enumerate(phases, 1):
            if len(phase) == 1:
                agent, task = phase[0]
                print(f"\n   Phase {i}: @{agent}")
                print(f"      任务: {task[:50]}{'...' if len(task) > 50 else ''}")
            else:
                agents = [f"@{a}" for a, _ in phase]
                print(f"\n   Phase {i}: {' && '.join(agents)}  (并行)")
                for agent, task in phase:
                    print(f"      @{agent}: {task[:40]}{'...' if len(task) > 40 else ''}")


# ============================================================
# 3. AgentExecutor - 执行引擎
# ============================================================

class AgentExecutor:
    """执行claude -p命令、管理子进程、解析输出"""

    def __init__(self, project_root: Path, max_budget: float = 10.0, max_concurrent: int = 2):
        self.project_root = project_root
        self.max_budget = max_budget
        self._semaphore = asyncio.Semaphore(max_concurrent)  # 限制并发数，避免API限流

    def _parse_agent_file(self, content: str) -> Tuple[Dict, str]:
        """
        解析 agent 文件，分离 YAML frontmatter 和正文

        Args:
            content: agent 文件的完整内容

        Returns:
            (metadata, body) - 元数据字典和正文内容
        """
        content = content.strip()

        # 检查是否以 --- 开头
        if not content.startswith('---'):
            # 没有 frontmatter，整个内容都是正文
            return {}, content

        # 更健壮的正则匹配 YAML frontmatter
        # 支持：---\n...\n--- 或 ---\r\n...\r\n--- (Windows换行)
        # 也支持 frontmatter 后面没有换行的情况
        patterns = [
            r'^---[ \t]*[\r\n]+(.*?)[\r\n]+---[ \t]*[\r\n]+(.*)$',  # 标准格式
            r'^---[ \t]*[\r\n]+(.*?)[\r\n]+---[ \t]*$',  # frontmatter 后无内容
            r'^---[ \t]*[\r\n]+---[ \t]*[\r\n]+(.*)$',  # 空 frontmatter
        ]

        metadata = {}
        body = content

        for i, pattern in enumerate(patterns):
            match = re.match(pattern, content, re.DOTALL)
            if match:
                if i == 2:  # 空 frontmatter 模式
                    body = match.group(1).strip() if match.lastindex >= 1 else ""
                elif i == 1:  # frontmatter 后无内容
                    frontmatter_str = match.group(1)
                    body = ""
                    # 解析 frontmatter
                    for line in frontmatter_str.split('\n'):
                        line = line.strip()
                        if ':' in line and not line.startswith('#'):
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
                else:  # 标准格式
                    frontmatter_str = match.group(1)
                    body = match.group(2).strip()
                    # 解析 frontmatter
                    for line in frontmatter_str.split('\n'):
                        line = line.strip()
                        if ':' in line and not line.startswith('#'):
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
                break

        return metadata, body

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

        # 读取并解析 agent 角色配置（分离 YAML frontmatter）
        role_file = self.project_root / config.role_file
        try:
            with open(role_file, 'r', encoding='utf-8') as f:
                content = f.read()
            metadata, role_prompt = self._parse_agent_file(content)
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

        # 从 metadata 中获取 model（如果有的话）
        agent_model = metadata.get('model', 'sonnet')

        # 构建完整提示词
        full_prompt = f"{role_prompt}\n\n---\n\n{task_prompt}"

        # 构建claude命令
        cmd = [
            "claude", "-p", full_prompt,
            "--output-format", "stream-json",
            "--verbose",  # stream-json 格式需要 verbose
            "--model", agent_model,
            "--max-turns", "20",
            "--max-budget-usd", str(self.max_budget),
            "--session-id", session_id,
            "--no-chrome"
        ]

        # 进度指示器
        async def progress_indicator(agent_name: str, start: float):
            """周期性打印进度信息"""
            indicators = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            idx = 0
            while True:
                elapsed = time.time() - start
                print(f"\r      {indicators[idx]} {agent_name} 工作中... ({elapsed:.0f}s)", end="", flush=True)
                idx = (idx + 1) % len(indicators)
                await asyncio.sleep(1)

        # 使用 semaphore 限制并发数（异步执行子进程）
        async with self._semaphore:
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

            # 启动进度指示器
            progress_task = asyncio.create_task(progress_indicator(config.name, start_time))

            # 等待完成（带超时）
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                progress_task.cancel()
                print()  # 换行
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
            finally:
                # 停止进度指示器
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass
                print()  # 换行，结束进度行

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
        自动发送初始任务，用户可继续讨论直到满意

        Returns:
            ExecutionResult with basic info (详细成本等需手动检查)
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        start_time = time.time()

        # 读取并解析 agent 角色配置（分离 YAML frontmatter）
        role_file = self.project_root / config.role_file
        try:
            with open(role_file, 'r', encoding='utf-8') as f:
                content = f.read()
            metadata, role_prompt = self._parse_agent_file(content)
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

        # 从 metadata 中获取 model（如果有的话）
        agent_model = metadata.get('model', 'sonnet')

        # 构建初始提示词，明确指定输出文件位置
        output_instruction = """

---

## 输出要求

请将计划文件保存到项目根目录：
- `PLAN.md` - 实施计划（必须生成）
- `CODEBASE_ANALYSIS.md` - 代码库分析（如果是现有项目）

完成后请告知用户已生成上述文件。
"""
        full_prompt = f"{role_prompt}\n\n---\n\n{task_prompt}{output_instruction}"

        print(f"\n{'='*60}", flush=True)
        print(f"🎯 启动交互式规划会话 - {config.name}", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"📋 初始任务将自动发送，无需手动输入", flush=True)
        print(f"💡 你可以继续与 {config.name} 讨论，直到满意", flush=True)
        print(f"📄 完成后输入 /exit 退出会话", flush=True)
        print(f"{'='*60}\n", flush=True)

        # 构建交互式 claude 命令
        # 直接传入 prompt 参数，claude 会自动执行后保持交互模式
        # 注意：--max-budget-usd 只在 --print 模式下生效，交互式模式下忽略
        cmd = [
            "claude",
            "--model", agent_model,
            "--permission-mode", "plan",  # 自动进入 plan 模式
            "--append-system-prompt", role_prompt,  # 角色定义作为系统提示
            task_prompt + output_instruction,  # 用户任务作为初始 prompt
        ]

        # 同步执行（阻塞等待用户交互）
        try:
            # 设置环境变量，用于 git hook 检测
            env = os.environ.copy()
            env['ORCHESTRATOR_RUNNING'] = 'true'

            # 使用 subprocess.run，不重定向 stdin/stdout/stderr，让用户直接交互
            process = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                env=env
            )

            duration = time.time() - start_time

            # 检查输出文件是否生成
            output_files = self._check_output_files(config.output_files)

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

    def _parse_stream_json(self, stdout: str, verbose: bool = False) -> Tuple[float, int]:
        """
        解析stream-json输出获取成本和tokens（增强版）

        支持多种 JSON 结构：
        - {"cost": x, "tokens": y}
        - {"cost_usd": x, "total_tokens": y}
        - {"type": "result", "cost": x, ...}
        - {"usage": {"input_tokens": x, "output_tokens": y}}

        Args:
            stdout: claude 命令的标准输出
            verbose: 是否输出详细日志

        Returns:
            (cost, tokens) 元组
        """
        if not stdout or not stdout.strip():
            if verbose:
                print("  [调试] stream-json 输出为空")
            return 0.0, 0

        lines = stdout.strip().split('\n')
        best_cost = 0.0
        best_tokens = 0

        # 从后往前查找有效的 JSON 行
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)

                # 优先查找 result 类型消息（通常是最终结果）
                if data.get('type') == 'result':
                    cost = data.get('cost_usd', data.get('cost', 0))
                    tokens = data.get('total_tokens', data.get('tokens', 0))
                    if cost > 0 or tokens > 0:
                        return float(cost), int(tokens)

                # 尝试多种字段名获取 cost
                cost = data.get('cost_usd', 0) or data.get('cost', 0)

                # 尝试多种字段名获取 tokens
                tokens = data.get('tokens', 0)
                if tokens == 0:
                    tokens = data.get('total_tokens', 0)
                if tokens == 0 and 'usage' in data:
                    usage = data['usage']
                    tokens = usage.get('total_tokens', 0)
                    # 如果没有 total_tokens，尝试计算 input + output
                    if tokens == 0:
                        input_tokens = usage.get('input_tokens', 0)
                        output_tokens = usage.get('output_tokens', 0)
                        tokens = input_tokens + output_tokens

                # 保留找到的最大值（避免中间行覆盖最终结果）
                if cost > best_cost:
                    best_cost = float(cost)
                if tokens > best_tokens:
                    best_tokens = int(tokens)

                # 如果找到有效数据就返回
                if best_cost > 0 or best_tokens > 0:
                    return best_cost, best_tokens

            except json.JSONDecodeError as e:
                # 这行不是有效 JSON，继续尝试下一行
                if verbose:
                    print(f"  [调试] JSON 解析失败: {str(e)[:50]}")
                continue
            except (TypeError, ValueError, AttributeError) as e:
                if verbose:
                    print(f"  [调试] 数据类型转换失败: {e}")
                continue

        # 返回找到的最佳值（可能是 0）
        if verbose and best_cost == 0 and best_tokens == 0:
            print("  [调试] 未在输出中找到成本/tokens 信息")
        return best_cost, best_tokens

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

    def _get_next_branch_number(self) -> int:
        """
        获取下一个分支流水号（带文件锁，防止并发竞态）

        Returns:
            3位流水号（从001开始）
        """
        counter_file = self.project_root / ".claude" / "branch_counter.txt"
        counter_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 使用 r+ 模式打开（文件不存在则先创建）
            if not counter_file.exists():
                counter_file.write_text("0", encoding='utf-8')

            with open(counter_file, 'r+', encoding='utf-8') as f:
                # Windows 文件锁
                if sys.platform == 'win32':
                    import msvcrt
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

                try:
                    content = f.read().strip()
                    counter = int(content) if content else 0
                    counter += 1

                    f.seek(0)
                    f.truncate()
                    f.write(str(counter))
                    f.flush()

                    return counter
                finally:
                    # 释放锁
                    if sys.platform == 'win32':
                        f.seek(0)
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

        except Exception:
            # 降级方案：使用时间戳
            return int(time.time()) % 1000

    def _create_feature_branch(self, task_description: str, first_agent: str = "arch") -> Optional[str]:
        """
        为任务创建 feature 分支

        Args:
            task_description: 任务描述（仅用于日志）
            first_agent: 首个执行的 agent 名称

        Returns:
            分支名称，如果失败则返回 None
        """
        # Agent 简写映射
        agent_abbrev = {
            "architect": "arch",
            "tech_lead": "tech",
            "developer": "dev",
            "tester": "test",
            "optimizer": "opti",
            "security": "sec",
        }

        # 获取 agent 简写
        abbrev = agent_abbrev.get(first_agent, first_agent[:4])

        try:
            # 检查是否在 git 仓库中
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode != 0:
                return None  # 不是 git 仓库，跳过分支创建

            # 尝试创建分支，如果已存在则递增编号重试（最多尝试 10 次）
            for _ in range(10):
                branch_num = self._get_next_branch_number()
                branch_name = f"feature/{abbrev}-{branch_num:03d}"

                # 检查分支是否已存在
                check_result = subprocess.run(
                    ["git", "rev-parse", "--verify", branch_name],
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )

                if check_result.returncode != 0:
                    # 分支不存在，可以创建
                    result = subprocess.run(
                        ["git", "checkout", "-b", branch_name],
                        cwd=str(self.project_root),
                        capture_output=True,
                        text=True,
                        encoding='utf-8'
                    )

                    if result.returncode == 0:
                        print(f"🌿 已创建并切换到分支: {branch_name}")
                        return branch_name
                    else:
                        print(f"⚠️ 创建分支失败: {result.stderr}")
                        return None
                # 分支已存在，继续循环尝试下一个编号

            print(f"⚠️ 无法创建分支：尝试了多个编号都已存在")
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
            print("🧹 已清理旧的状态文件和错误日志\n", flush=True)

        # Phase 0.2: 解析任务
        print(f"📋 用户需求: {user_request}", flush=True)
        task_prompt, complexity = self.task_parser.parse(user_request)
        print(f"任务复杂度: {complexity.value}", flush=True)

        # Phase 0.5: 规划执行阶段
        phases = self.scheduler.plan_execution(complexity)
        print(f"执行计划: {len(phases)} 个阶段\n", flush=True)

        # Phase 0.1: 创建 feature 分支（新任务时，需要先知道首个 agent）
        feature_branch = None
        if clean_start and phases:
            first_agent = phases[0][0] if phases[0] else "arch"
            feature_branch = self._create_feature_branch(user_request, first_agent)

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

    async def execute_from_plan(self, plan_content: str, existing_state: Optional[Dict] = None) -> bool:
        """
        从 PLAN.md 开始执行（跳过 architect 阶段）

        用于情景2：半自动模式，architect 已在 claude CLI 中完成
        也用于恢复中断的任务

        Args:
            plan_content: PLAN.md 的内容
            existing_state: 现有状态（用于恢复时跳过已完成的 agent）

        Returns:
            True if successful, False if failed
        """
        start_time = time.time()

        # 所有可能的 agents（跳过 architect）
        all_agents = ["tech_lead", "developer", "tester", "optimizer", "security"]

        # 如果有现有状态，过滤掉已完成的 agents
        if existing_state and existing_state.get("agents_status"):
            completed_agents = [
                agent for agent, status in existing_state["agents_status"].items()
                if status == "completed"
            ]
            remaining_agents = [a for a in all_agents if a not in completed_agents]
            print(f"📂 已完成的 agents: {', '.join(completed_agents) if completed_agents else '无'}")
            print(f"🔄 待执行的 agents: {', '.join(remaining_agents) if remaining_agents else '无'}")
        else:
            remaining_agents = all_agents

        if not remaining_agents:
            print("✅ 所有 agents 已完成，无需继续执行")
            return True

        # 构建提示词（包含 PLAN.md 内容）
        task_prompt = f"""
请根据以下实施计划执行你的职责：

{plan_content}

---

请严格按照计划执行，确保与其他 agents 的工作保持一致。
"""

        # 初始化或恢复状态
        if existing_state:
            state = existing_state
            all_results = {}
            # 恢复已有结果
            for agent_name, result_dict in state.get("results", {}).items():
                if result_dict.get("status") == "completed":
                    # 重建 ExecutionResult 对象用于统计
                    all_results[agent_name] = ExecutionResult(
                        agent_name=result_dict.get("agent_name", agent_name),
                        status=AgentStatus.COMPLETED,
                        session_id=result_dict.get("session_id", ""),
                        exit_code=result_dict.get("exit_code", 0),
                        duration=result_dict.get("duration", 0),
                        cost=result_dict.get("cost", 0),
                        tokens=result_dict.get("tokens", 0),
                        output_files=result_dict.get("output_files", []),
                        error_message=result_dict.get("error_message")
                    )
        else:
            task_id = str(uuid.uuid4())
            state = {
                "task_id": task_id,
                "user_request": "从 PLAN.md 执行",
                "complexity": "from_plan",
                "current_phase": 1,  # 从 phase 1 开始（跳过 phase 0 architect）
                "agents_status": {"architect": "completed"},
                "results": {},
                "total_cost": 0.0,
                "total_tokens": 0
            }
            all_results = {}

        # 计算起始 phase 索引
        start_phase_idx = len(all_agents) - len(remaining_agents) + 2

        # 执行剩余 agents
        for i, agent_name in enumerate(remaining_agents):
            phase_idx = start_phase_idx + i
            self.monitor.display_phase_start(phase_idx, [agent_name])

            config = self.scheduler.get_agent_config(agent_name)
            session_id = str(uuid.uuid4())

            self.monitor.display_agent_start(config.name, session_id)

            result = await self.error_handler.retry_with_backoff(
                self.executor.run_agent,
                config,
                task_prompt,
                session_id=session_id
            )

            self.monitor.display_agent_complete(result)
            all_results[config.name] = result

            # 更新状态
            state["current_phase"] = phase_idx
            state["agents_status"][config.name] = result.status.value
            # 转换 ExecutionResult 为可序列化的字典
            result_dict = asdict(result)
            result_dict["status"] = result.status.value
            state["results"][config.name] = result_dict
            self.state_manager.save_state(state)

            # 如果失败，终止执行
            if result.status == AgentStatus.FAILED:
                print(f"\n❌ {config.name} 执行失败，已保存状态")
                print(f"   修复问题后，运行 python mc-dir.py --resume 继续")
                self._save_final_state(state, all_results, time.time() - start_time)
                return False

        # 成功完成
        total_duration = time.time() - start_time
        self._save_final_state(state, all_results, total_duration)
        self.monitor.display_summary(all_results, total_duration)

        return True

    async def execute_manual(
        self,
        phases: List[List[Tuple[str, str]]],
        clean_start: bool = True
    ) -> bool:
        """
        执行手动指定的 agent 任务

        Args:
            phases: [[("agent_name", "task"), ...], ...]
            clean_start: 是否清理旧状态

        Returns:
            True if successful, False if failed
        """
        start_time = time.time()

        # 清理旧状态
        if clean_start:
            self._cleanup_old_state()
            print("🧹 已清理旧的状态文件\n")

        # 创建 feature 分支（使用首个 agent 名称）
        first_agent = phases[0][0][0] if phases and phases[0] else "arch"
        first_task = phases[0][0][1] if phases and phases[0] else "manual-task"
        feature_branch = self._create_feature_branch(first_task, first_agent)

        # 初始化状态
        task_id = str(uuid.uuid4())
        state = {
            "task_id": task_id,
            "mode": "manual",
            "current_phase": 0,
            "agents_status": {},
            "results": {},
            "total_cost": 0.0,
            "total_tokens": 0
        }

        all_results = {}

        # 执行各阶段
        for phase_idx, phase_tasks in enumerate(phases, 1):
            agent_names = [agent for agent, _ in phase_tasks]
            self.monitor.display_phase_start(phase_idx, agent_names)

            # 准备 agent 配置和提示词
            configs = []
            prompts = {}

            for agent_name, task in phase_tasks:
                config = self.scheduler.get_agent_config(agent_name)
                configs.append(config)
                prompts[agent_name] = self.task_parser.generate_initial_prompt(task, agent_name=agent_name)

            # 串行 or 并行执行
            if len(phase_tasks) == 1:
                # 单个 agent
                config = configs[0]
                agent_name = config.name
                session_id = str(uuid.uuid4())

                # architect 使用交互式模式
                if agent_name == "architect" and self.interactive_architect:
                    print(f"\n💡 {self.monitor._get_agent_display_name(agent_name)} 将在交互式模式下运行")

                    result = await asyncio.to_thread(
                        self.executor.run_agent_interactive,
                        config,
                        prompts[agent_name],
                        session_id
                    )
                else:
                    self.monitor.display_agent_start(agent_name, session_id)

                    result = await self.error_handler.retry_with_backoff(
                        self.executor.run_agent,
                        config,
                        prompts[agent_name],
                        session_id=session_id
                    )

                self.monitor.display_agent_complete(result)
                all_results[agent_name] = result

                if result.status == AgentStatus.FAILED:
                    print(f"\n❌ {agent_name} 执行失败，终止流程")
                    self._save_final_state(state, all_results, time.time() - start_time)
                    return False

            else:
                # 多个 agent 并行执行
                session_ids = {config.name: str(uuid.uuid4()) for config in configs}

                for config in configs:
                    self.monitor.display_agent_start(config.name, session_ids[config.name])

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

                for result in results:
                    self.monitor.display_agent_complete(result)
                    all_results[result.agent_name] = result

                if any(r.status == AgentStatus.FAILED for r in results):
                    failed = [r.agent_name for r in results if r.status == AgentStatus.FAILED]
                    print(f"\n❌ 以下 agents 执行失败: {', '.join(failed)}")
                    self._save_final_state(state, all_results, time.time() - start_time)
                    return False

            # 更新状态
            state["current_phase"] = phase_idx
            for name, result in all_results.items():
                state["agents_status"][name] = result.status.value
                result_dict = asdict(result)
                result_dict["status"] = result.status.value
                state["results"][name] = result_dict
            self.state_manager.save_state(state)

        # 显示汇总
        total_duration = time.time() - start_time
        self.monitor.display_summary(all_results, total_duration)
        self._save_final_state(state, all_results, total_duration)

        # 提示合并
        if feature_branch:
            print(f"\n{'='*60}")
            print(f"✅ 手动任务完成！当前在分支: {feature_branch}")
            print(f"{'='*60}")
            print(f"下一步：git add . && git commit -m \"完成手动任务\"")
            print(f"{'='*60}\n")

        return True


# ============================================================
# CLI接口
# ============================================================

def semi_auto_mode(project_root: Path, config: dict):
    """
    情景2：半自动执行模式

    流程：
    1. 进入 claude CLI（plan 模式）讨论任务需求
    2. 生成 PLAN.md 后退出 claude
    3. 用户确认 PLAN.md
    4. 自动执行剩余 agents
    """
    import subprocess

    # 读取 architect 角色配置
    arch_file = project_root / ".claude" / "agents" / "01-arch.md"
    if arch_file.exists():
        with open(arch_file, 'r', encoding='utf-8') as f:
            content = f.read()
        # 分离 YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                arch_prompt = parts[2].strip()
            else:
                arch_prompt = content
        else:
            arch_prompt = content
    else:
        arch_prompt = "你是一个系统架构师，请分析需求并生成 PLAN.md"

    # 添加强制限制的系统提示
    system_prompt = f"""{arch_prompt}

---

## ⚠️ 关键限制 - 必须严格遵守

**你是 Architect Agent，你的唯一任务是制定计划，而不是实现代码！**

### 你必须做的事：
1. 分析用户需求
2. 如果是现有项目，先探索代码库并生成 `CODEBASE_ANALYSIS.md`
3. 生成详细的 `PLAN.md` 实施计划
4. 完成后告知用户输入 `/exit` 退出会话

### 你绝对不能做的事：
- ❌ 不要编写任何实现代码
- ❌ 不要创建源代码文件（如 .py, .js, .ts 等）
- ❌ 不要修改现有的源代码
- ❌ 不要运行测试或构建命令
- ❌ 不要尝试"帮用户完成任务"

### 为什么？
你是多 Agent 流水线的第一个环节。你的输出（PLAN.md）将交给后续的 Developer、Tester、Security 等 agents 执行。如果你直接实现代码，就破坏了整个流程。

### 输出文件：
- `PLAN.md` - 详细的实施计划（必须生成）
- `CODEBASE_ANALYSIS.md` - 代码库分析（仅现有项目）

当用户描述完需求后，请开始分析并生成计划文件。
"""

    print(f"\n{'='*60}", flush=True)
    print(f"🎯 半自动模式 - 与 Architect 讨论任务", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"💡 在 Claude CLI 中描述你的任务需求", flush=True)
    print(f"📄 讨论完成后，Architect 会生成 PLAN.md", flush=True)
    print(f"🚪 生成完毕后输入 /exit 退出，继续执行后续流程", flush=True)
    print(f"{'='*60}\n", flush=True)

    # 进入 claude CLI（plan 模式）
    cmd = [
        "claude",
        "--permission-mode", "plan",
        "--append-system-prompt", system_prompt,
        "--max-budget-usd", str(config['max_budget']),
    ]

    env = os.environ.copy()
    env['ORCHESTRATOR_RUNNING'] = 'true'

    # 执行 claude（阻塞，用户交互）
    process = subprocess.run(cmd, cwd=str(project_root), env=env)

    # 检查 PLAN.md 是否生成
    plan_file = project_root / "PLAN.md"
    if not plan_file.exists():
        print(f"\n⚠️ 未检测到 PLAN.md，流程终止")
        print(f"   请重新运行并确保生成 PLAN.md")
        return False

    # 提示用户确认
    print(f"\n{'='*60}")
    print(f"📋 已检测到 PLAN.md")
    print(f"   位置: {plan_file}")
    print(f"{'='*60}")

    # 显示 PLAN.md 前几行
    with open(plan_file, 'r', encoding='utf-8') as f:
        preview = f.read(500)
    print(f"\n--- PLAN.md 预览 ---")
    print(preview)
    if len(preview) >= 500:
        print("... (更多内容请查看文件)")
    print(f"--- 预览结束 ---\n")

    confirm = input("确认执行后续 Agents？[Y/n] ").strip().lower()
    if confirm in ['n', 'no', '否']:
        print("已取消。你可以修改 PLAN.md 后重新运行。")
        return False

    # 读取 PLAN.md 作为任务描述
    with open(plan_file, 'r', encoding='utf-8') as f:
        plan_content = f.read()

    # 创建 orchestrator 执行剩余 agents
    orchestrator = Orchestrator(
        project_root=project_root,
        max_budget=config['max_budget'],
        max_retries=config['max_retries'],
        verbose=config['verbose'],
        interactive_architect=False  # architect 已完成
    )

    # 执行剩余阶段（跳过 architect）
    print(f"\n🚀 开始执行后续 Agents...")
    success = asyncio.run(orchestrator.execute_from_plan(plan_content))

    return success


def interactive_mode(project_root: Path):
    """交互式 CLI 模式 - 默认进入半自动模式"""
    print("""
╔════════════════════════════════════════════════════════════╗
║       🚀 mc-dir - 多Agent智能调度系统                       ║
╚════════════════════════════════════════════════════════════╝

选择模式：
  1. 半自动模式（推荐）- 进入 Claude CLI 讨论需求，生成 PLAN.md 后自动执行
  2. 传统交互模式 - 在此输入需求，预览后执行
  3. 退出
""")

    # 默认配置
    config = {
        'max_budget': 10.0,
        'max_retries': 3,
        'verbose': False,
        'auto_architect': False
    }

    choice = input("请选择 [1/2/3]: ").strip()

    if choice == '1' or choice == '':
        # 半自动模式
        success = semi_auto_mode(project_root, config)
        if success:
            print("\n✅ 所有 Agents 执行完成！")
        return

    if choice == '3':
        print("\n👋 再见！")
        return

    # 传统交互模式
    print("\n进入传统交互模式。输入 help 查看帮助，exit 退出。")

    while True:
        try:
            user_input = input("\n💬 有什么可以帮您？\n> ").strip()

            if not user_input:
                continue

            cmd_lower = user_input.lower()

            # 特殊命令
            if cmd_lower in ['exit', 'quit', 'q', '退出']:
                print("\n👋 再见！")
                break

            if cmd_lower in ['help', '?', '帮助']:
                print("""
📖 使用帮助
============================================================

【自动规划模式】直接描述需求：
  帮我写一个网页版的赛车游戏
  修复 src/main.py 中的登录 bug

【手动指定模式】使用 @agent 语法：
  @tech_lead 审核代码                    # 单个 agent
  @tech_lead 审核 && @security 安检      # 并行执行
  @tech_lead 审核 -> @developer 修复     # 串行执行
  @tech 审核 -> (@dev 修复 && @sec 安检) # 混合模式

特殊命令：
  help, ?       - 显示帮助
  agents        - 查看可用 agent 和别名
  config        - 查看/修改配置
  resume        - 恢复上次中断的任务
  status        - 查看当前状态
  exit, quit    - 退出程序

配置选项（在需求后添加）：
  --budget N    - 设置预算（USD）
  --auto        - 跳过交互式规划
  --verbose     - 详细日志
============================================================
""")
                continue

            if cmd_lower in ['agents', 'agent', '列表']:
                print("""
📋 可用的 Agents：
============================================================
  @architect  (别名: @arch, @架构)    - 系统架构师
  @tech_lead  (别名: @tech, @技术)    - 技术负责人
  @developer  (别名: @dev, @开发)     - 开发工程师
  @tester     (别名: @test, @测试)    - 测试工程师
  @optimizer  (别名: @opti, @优化)    - 优化专家
  @security   (别名: @sec, @安全)     - 安全专家

语法说明：
  ->   串行执行（前一个完成后执行下一个）
  &&   并行执行（同时执行）
  ()   分组（用于混合模式）

示例：
  @tech_lead 审核代码 -> @developer 根据建议修复
  @tester 测试 && @security 安全检查
============================================================
""")
                continue

            if cmd_lower == 'config':
                print(f"\n⚙️ 当前配置：")
                print(f"   预算上限: ${config['max_budget']}")
                print(f"   重试次数: {config['max_retries']}")
                print(f"   详细日志: {'是' if config['verbose'] else '否'}")
                print(f"   自动规划: {'是' if config['auto_architect'] else '否（交互式）'}")
                print(f"\n修改配置：config budget 20 / config verbose on")
                continue

            if cmd_lower.startswith('config '):
                parts = cmd_lower.split()
                if len(parts) >= 3:
                    key, value = parts[1], parts[2]
                    if key == 'budget':
                        config['max_budget'] = float(value)
                        print(f"✅ 预算设置为 ${config['max_budget']}")
                    elif key == 'verbose':
                        config['verbose'] = value in ['on', 'true', '1', '是']
                        print(f"✅ 详细日志: {'开启' if config['verbose'] else '关闭'}")
                    elif key == 'auto':
                        config['auto_architect'] = value in ['on', 'true', '1', '是']
                        print(f"✅ 自动规划: {'开启' if config['auto_architect'] else '关闭'}")
                continue

            if cmd_lower == 'resume':
                state_file = project_root / ".claude" / "state.json"
                if state_file.exists():
                    with open(state_file, 'r', encoding='utf-8') as f:
                        state = json.load(f)
                    print(f"📂 找到中断的任务: {state.get('user_request', '未知')}")
                    confirm = input("是否恢复？[Y/n] ").strip().lower()
                    if confirm not in ['n', 'no', '否']:
                        user_input = state['user_request']
                        # 继续执行
                    else:
                        continue
                else:
                    print("❌ 没有找到可恢复的任务")
                    continue

            if cmd_lower == 'status':
                state_file = project_root / ".claude" / "state.json"
                if state_file.exists():
                    with open(state_file, 'r', encoding='utf-8') as f:
                        state = json.load(f)
                    print(f"\n📊 任务状态：")
                    print(f"   任务: {state.get('user_request', '未知')[:50]}")
                    print(f"   复杂度: {state.get('complexity', '未知')}")
                    print(f"   当前阶段: {state.get('current_phase', 0)}")
                    print(f"   总成本: ${state.get('total_cost', 0):.4f}")
                else:
                    print("📊 当前没有进行中的任务")
                continue

            if cmd_lower == 'clear':
                import os
                os.system('cls' if os.name == 'nt' else 'clear')
                continue

            # 解析命令行选项
            max_budget = config['max_budget']
            auto_architect = config['auto_architect']
            verbose = config['verbose']

            if '--budget' in user_input:
                import re
                match = re.search(r'--budget\s+(\d+(?:\.\d+)?)', user_input)
                if match:
                    max_budget = float(match.group(1))
                user_input = re.sub(r'--budget\s+\d+(?:\.\d+)?', '', user_input).strip()

            if '--auto' in user_input:
                auto_architect = True
                user_input = user_input.replace('--auto', '').strip()

            if '--verbose' in user_input:
                verbose = True
                user_input = user_input.replace('--verbose', '').strip()

            if not user_input:
                continue

            # 检测是否是手动指定模式
            manual_parser = ManualTaskParser()

            if manual_parser.is_manual_mode(user_input):
                # ========== 手动指定模式 ==========
                phases, success = manual_parser.parse(user_input)

                if not success:
                    continue

                # 预览执行计划
                manual_parser.preview(phases)
                print(f"   预算上限: ${max_budget}")

                confirm = input("\n确认执行？[Y/n] ").strip().lower()
                if confirm in ['n', 'no', '否']:
                    print("已取消")
                    continue

                # 创建 orchestrator 并执行手动任务
                orchestrator = Orchestrator(
                    project_root=project_root,
                    max_budget=max_budget,
                    max_retries=config['max_retries'],
                    verbose=verbose,
                    interactive_architect=not auto_architect
                )

                success = asyncio.run(orchestrator.execute_manual(phases, clean_start=True))

                if success:
                    print("\n✅ 手动任务完成！可以继续输入新需求。")
                else:
                    print("\n❌ 任务执行失败，请检查错误日志。")

            else:
                # ========== 自动规划模式 ==========
                task_parser = TaskParser(project_root)
                _, complexity = task_parser.parse(user_input)

                scheduler = AgentScheduler()
                phases = scheduler.plan_execution(complexity)
                total_agents = sum(len(p) for p in phases)

                print(f"\n📋 自动规划模式 - 任务预览：")
                print(f"   需求: {user_input[:60]}{'...' if len(user_input) > 60 else ''}")
                print(f"   复杂度: {complexity.value}")
                print(f"   执行阶段: {len(phases)} 个阶段，{total_agents} 个 Agent")
                print(f"   预算上限: ${max_budget}")
                print(f"   规划模式: {'自动' if auto_architect else '交互式'}")

                # 显示执行计划
                print(f"\n   执行计划：")
                for i, phase_agents in enumerate(phases, 1):
                    agent_names = ', '.join(phase_agents)
                    print(f"     Phase {i}: {agent_names}")

                confirm = input("\n确认执行？[Y/n] ").strip().lower()
                if confirm in ['n', 'no', '否']:
                    print("已取消")
                    continue

                # 创建 orchestrator 并执行
                orchestrator = Orchestrator(
                    project_root=project_root,
                    max_budget=max_budget,
                    max_retries=config['max_retries'],
                    verbose=verbose,
                    interactive_architect=not auto_architect
                )

                success = asyncio.run(orchestrator.execute(user_input, clean_start=True))

                if success:
                    print("\n✅ 任务完成！可以继续输入新需求。")
                else:
                    print("\n❌ 任务执行失败，请检查错误日志。")

        except KeyboardInterrupt:
            print("\n\n⚠️ 中断当前任务")
            continue
        except EOFError:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            continue


def main():
    """CLI入口"""
    parser = argparse.ArgumentParser(
        description="mc-dir - 多Agent智能调度系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用方式：

  情景1 - 全自动执行（复杂任务从 md 文件读取）：
    python mc-dir.py task1.md --auto-architect

  情景2 - 半自动执行（进入 Claude CLI 讨论后自动执行）：
    python mc-dir.py

  恢复中断的任务：
    python mc-dir.py --resume
        """
    )

    parser.add_argument(
        "request",
        nargs="?",
        help="任务描述或 .md 文件路径（不指定则进入半自动模式）"
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
        help="全自动模式（跳过交互式规划）"
    )

    args = parser.parse_args()

    # 获取项目根目录
    project_root = Path.cwd()

    # 情景2：无参数时进入半自动模式
    if not args.request and not args.resume:
        interactive_mode(project_root)
        return

    # 情景1：从 .md 文件读取任务描述
    user_request = args.request
    if user_request and user_request.endswith('.md'):
        task_file = project_root / user_request
        if task_file.exists():
            print(f"📄 从文件读取任务: {user_request}", flush=True)
            with open(task_file, 'r', encoding='utf-8') as f:
                user_request = f.read()
        else:
            print(f"❌ 任务文件不存在: {task_file}")
            sys.exit(1)

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
            print(f"📂 恢复任务: {state['user_request'][:50]}...")
            # 检查是否是从 PLAN.md 执行的任务
            if state.get('complexity') == 'from_plan':
                # 读取 PLAN.md 继续执行
                plan_file = project_root / "PLAN.md"
                if plan_file.exists():
                    with open(plan_file, 'r', encoding='utf-8') as f:
                        plan_content = f.read()
                    try:
                        # 传入现有状态，跳过已完成的 agents
                        success = asyncio.run(orchestrator.execute_from_plan(plan_content, existing_state=state))
                        sys.exit(0 if success else 1)
                    except KeyboardInterrupt:
                        print("\n\n⚠️ 用户中断执行")
                        sys.exit(130)
                else:
                    print("❌ PLAN.md 不存在，无法恢复")
                    sys.exit(1)
            else:
                user_request = state['user_request']
        else:
            print("❌ 未找到可恢复的任务")
            sys.exit(1)

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
