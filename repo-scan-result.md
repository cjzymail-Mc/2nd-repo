# Repo Scan Result

## 技术栈

- **语言**: Python 3.10+
- **异步框架**: asyncio (subprocess 调度)
- **外部工具**: Claude CLI (`claude` 命令行)
- **测试**: pytest
- **版本控制**: Git (代码中直接调用 git 命令)
- **平台**: Windows (MINGW64)，兼容 Linux/Mac

## 项目结构

```
├── src/
│   ├── 6-agents.py          # 主文件（3749行），多Agent调度系统全部逻辑
│   └── hello.py              # 占位/测试文件
├── tests/
│   ├── conftest.py           # pytest fixtures（项目根目录、agent配置、PLAN模板）
│   └── unit/                 # 单元测试（7个测试文件，61个用例）
│       ├── test_agent_scheduler.py
│       ├── test_manual_parser.py
│       ├── test_task_parser.py
│       ├── test_parse_agent_file.py
│       ├── test_state_manager.py
│       ├── test_stream_json.py
│       └── test_error_handler.py
├── .claude/
│   ├── agents/               # 6个Agent角色定义文件
│   │   ├── 01-arch.md        # Architect（制定计划）
│   │   ├── 02-tech.md        # Tech Lead（审核计划）
│   │   ├── 03-dev.md         # Developer（编写代码）
│   │   ├── 04-test.md        # Tester（测试验证）
│   │   ├── 05-opti.md        # Optimizer（性能优化）
│   │   └── 06-secu.md        # Security（安全审计）
│   ├── commands/             # 自定义CLI命令（safe-commit, c-pr, md-update）
│   └── CLAUDE.md             # 项目规范（路径规则、代码风格）
├── debug/                    # 调试记录和备份
├── docs/                     # 文档（Agent使用指南、Git Hooks指南）
├── plan.md                   # 迭代进度记录
└── mission1.md               # 当前需求文档
```

## 核心模块

`src/6-agents.py` 中的核心类（按依赖顺序）：

- `TaskParser` — 解析用户输入，评估任务复杂度(MINIMAL/SIMPLE/MODERATE/COMPLEX)，生成Agent prompt
- `AgentScheduler` — 根据复杂度规划执行阶段（哪些Agent串行、哪些并行）
- `ManualTaskParser` — 解析 `@agent 任务` 语法，支持 `->` 串行、`&&` 并行、`.md` 文件引用
- `AgentExecutor` — 调用 Claude CLI 执行Agent，管理子进程、解析stream-json输出、实时流监控
- `StateManager` — JSON文件持久化执行状态（断点恢复）
- `ErrorHandler` — 指数退避重试（最多3次）+ 错误日志
- `ProgressMonitor` — 终端实时进度显示 + 执行摘要
- `Orchestrator` — 顶层编排器，协调上述所有模块，含5种执行模式

独立函数：`interactive_mode()`（菜单入口）、`semi_auto_mode()`、`from_plan_mode()`

## 代码风格与架构模式

- **命名**: snake_case（函数/变量）、PascalCase（类）
- **架构**: 星型拓扑 + 流水线混合（Orchestrator为中心，Agent通过文件传递结果）
- **并发模型**: asyncio.create_subprocess_exec + asyncio.gather（并行Agent隔离到Git子分支）
- **Agent通信**: 文件系统（PLAN.md、BUG_REPORT.md等中间文件）

## 依赖关系

- `Orchestrator` → `AgentExecutor`、`StateManager`、`ErrorHandler`、`ProgressMonitor`（核心调度）
- `Orchestrator` → `TaskParser`、`AgentScheduler`（任务解析和阶段规划）
- `AgentExecutor` → Claude CLI 子进程（`asyncio.create_subprocess_exec`）
- `interactive_mode()` → `Orchestrator`、`ManualTaskParser`（用户交互入口）
- `semi_auto_mode()` → `AgentExecutor.run_agent_interactive()`（半自动Architect会话）

## 关键业务逻辑

本项目是一个多Agent智能调度系统，通过 Claude CLI 协调6个专业Agent完成软件工程任务。用户输入需求后，系统自动评估复杂度、规划执行阶段、依次或并行调用Agent，支持developer-tester多轮迭代循环。提供5种运行模式：半自动（Architect交互）、从PLAN继续、全自动、手动指派（@语法）、退出。系统具备Git分支隔离、进度文件管理、Architect越权三重防护（Prompt限制+实时流监控+后置回滚）、临时文件自动清理等特性。
