# Repo Scan Result

## 🔍 快速索引（Quick Index）

核心类（按依赖顺序）：
- `TaskParser` @ `src/6-agents.py:87-227` — 解析用户输入，评估任务复杂度(MINIMAL/SIMPLE/MODERATE/COMPLEX)
- `AgentScheduler` @ `src/6-agents.py:228-307` — 根据复杂度规划执行阶段（哪些Agent串行/并行）
- `ManualTaskParser` @ `src/6-agents.py:308-444` — 解析 `@agent 任务` 语法，支持 `->` 串行、`&&` 并行、`.md` 文件引用
- `AgentExecutor` @ `src/6-agents.py:445-1013` — 调用 Claude CLI 执行Agent，管理子进程、解析stream-json、实时流监控
- `StateManager` @ `src/6-agents.py:1014-1047` — JSON文件持久化执行状态（断点恢复）
- `ErrorHandler` @ `src/6-agents.py:1048-1113` — 指数退避重试（最多3次）+ 错误日志记录
- `ProgressMonitor` @ `src/6-agents.py:1114-1209` — 终端实时进度显示 + 执行摘要生成
- `Orchestrator` @ `src/6-agents.py:1210-2859` — 顶层编排器，协调所有模块，含5种执行模式

关键函数：
- `semi_auto_mode()` @ `src/6-agents.py:2860-3057` — 半自动模式（Architect交互会话）
- `from_plan_mode()` @ `src/6-agents.py:3058-3162` — 从PLAN.md继续执行
- `interactive_mode()` @ `src/6-agents.py:3163-3559` — 交互菜单入口
- `main()` @ `src/6-agents.py:3560-3749` — 程序入口，项目根目录检测

## 📋 核心接口定义（API Interfaces）

- `TaskParser.parse(user_request: str) -> TaskComplexity` — 评估任务复杂度
- `AgentScheduler.plan_execution(complexity) -> List[List[str]]` — 规划执行阶段
- `ManualTaskParser.parse_manual_input(input: str) -> ManualTask` — 解析@语法
- `AgentExecutor.run_agent(name, prompt, config) -> AgentResult` — 执行Agent
- `Orchestrator.execute(request, clean_start, override_complexity) -> bool` — 主流程
- `Orchestrator.execute_with_loop(request, max_rounds, complexity) -> bool` — 多轮迭代
- `StateManager.save_state(state) / load_state() -> dict` — 状态持久化
- `ErrorHandler.retry_with_backoff(func, max_retries) -> Any` — 重试包装器

## 🔁 常见模式（Common Patterns）

- **Git 分支**: 创建 `feature/<prefix>-<agent>-<uuid>` → 执行任务 → 合并 → 清理子分支
- **Agent 调用**: prompt生成 → `asyncio.create_subprocess_exec(['claude', '--agent', name])` → 解析stream-json → 三重防护检查
- **错误处理**: try/except → 重试3次（1s, 2s, 4s指数退避） → 记录error_log.json
- **文件传递**: Architect→PLAN.md → Tech Lead审核 → Developer代码 → Tester→BUG_REPORT → Developer修复（循环）

## 🛠️ 技术栈

- **语言**: Python 3.10+
- **异步框架**: asyncio (subprocess 调度)
- **外部工具**: Claude CLI (`claude` 命令行)
- **测试**: pytest (61个单元测试)
- **版本控制**: Git (代码中直接调用 git 命令)
- **平台**: Windows (MINGW64)，兼容 Linux/Mac

## 📁 项目结构

```
├── src/6-agents.py          # 主文件（3749行），全部逻辑
├── tests/unit/              # 7个测试文件，61个用例
├── .claude/agents/          # 6个Agent角色定义（01-arch至06-secu）
├── .claude/CLAUDE.md        # 项目规范
├── plan.md                  # 任务规划
└── repo-scan-result.md      # 代码库扫描结果
```

## 🧩 核心模块

核心类：TaskParser（评估复杂度）、AgentScheduler（规划阶段）、ManualTaskParser（@语法）、AgentExecutor（Agent调度）、StateManager（状态持久化）、ErrorHandler（重试）、ProgressMonitor（进度）、Orchestrator（顶层编排）

独立函数：interactive_mode（菜单）、semi_auto_mode、from_plan_mode、main

## 🏗️ 代码风格与架构

- 命名：snake_case / PascalCase；架构：星型拓扑+流水线；并发：asyncio + Git子分支隔离；通信：文件系统

## 🔗 依赖关系

Orchestrator → AgentExecutor/StateManager/ErrorHandler → Claude CLI子进程 → Agent角色定义文件

## 💼 关键业务逻辑

多Agent智能调度系统，通过Claude CLI协调6个专业Agent完成软件工程任务。自动评估复杂度、规划执行阶段、串行/并行调用Agent，支持多轮迭代。5种模式：半自动、从PLAN继续、全自动、手动指派、退出。特性：Git分支隔离、进度管理、Architect三重防护、临时文件清理。
