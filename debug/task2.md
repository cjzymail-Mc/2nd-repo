我在src文件夹中有一个 6-agent.py 程序，可以完成西面情景的任务：
  ---
  情景1：全自动执行

  python mc-dir.py task1.md --auto-architect

  - 从 task1.md 读取详细任务描述
  - 全自动执行 6 个 agents
  - 无需人工干预

  ---
  情景2：半自动执行

  python mc-dir.py

  流程：
  1. 选择模式（默认半自动）
  2. 进入 Claude CLI（plan 模式）讨论需求
  3. 生成 PLAN.md 后输入 /exit 退出
  4. 程序自动检测 PLAN.md，显示预览
  5. 用户确认后自动执行剩余 agents
  6. 失败后可用 python mc-dir.py --resume 恢复

  ---
  关于恢复机制
  ┌─────────────────┬───────────────────────────────────────┐
  │      情况       │               处理方式                │
  ├─────────────────┼───────────────────────────────────────┤
  │ 3 次重试后失败  │ 保存状态，提示用户修复后运行 --resume │
  ├─────────────────┼───────────────────────────────────────┤
  │ Token 限制中断  │ 状态已保存，等待后运行 --resume 继续  │
  ├─────────────────┼───────────────────────────────────────┤
  │ Ctrl+C 手动中断 │ 状态已保存，可随时 --resume           │
  └─────────────────┴───────────────────────────────────────┘
  状态文件位置：.claude/state.json


  你帮我对6-agent.py 文件，进行全面测试和debug，让它能够顺利工作，并修复发现的bug


  ------工作进度------

  在上一次调用claude code 过程中，由于 token消耗达到 limit，工作任务仅完成一部分。

  当前工作进度如下：

# 任务进度精简版：测试和Debug src/6-agents.py

## 任务描述
从task2.md：对src/6-agents.py多Agent调度系统进行全面测试和debug，修复bug，确保系统顺利工作。

## 代码库结构
- src/6-agents.py (2113行，主程序)
- .claude/agents/ (Agent配置文件)
  - 01-arch.md (263行，完整)
  - 02-tech.md ~ 06-secu.md (原17-18行，已扩展到~100-300行)
- 其他：state.json, branch_counter.txt, mc-dir-v*.py, task2.md

## 发现的问题
### P0 (严重)
1. Agent配置文件不完整 (02~06-*.md)
2. 中文别名正则不支持 (行292,336)

### P1 (高优先级)
3. stream-json解析脆弱 (行723-774)
4. 并发无速率限制 (行1235-1244)

### P2 (中等优先级)
5. 分支编号竞态条件 (行1025-1049)
6. PLAN.md读取无容错 (行1675-1680)

## 用户额外bug
1. plan.md存放位置/命名不对：应生成plan.md到根目录。
2. Agent生成的md文件未生成/未可见。
3. plan.md中的修复任务未被剩余Agent执行。

## 实施计划
修改范围：
- src/6-agents.py：修复4处bug
- 02-tech.md ~ 06-secu.md：扩展配置
- 新增：tests/conftest.py, tests/unit/test_*.py

步骤：
1. 修复中文别名正则 (完成)
2. 增强stream-json解析 (完成)
3. 添加并发限制 (Semaphore, max_concurrent=2) (完成)
4. 修复分支编号竞态 (使用msvcrt文件锁) (完成)
5. 完善5个Agent配置文件 (完成，扩展为详细内容，包括YAML、职责、工作流程、约束、输出示例)
6. 编写单元测试 (未完成：conftest.py, test_manual_parser.py, test_stream_json.py, test_task_parser.py)

验证方法：
- 中文别名：python -c "from src.six_agents import ManualTaskParser; p=ManualTaskParser(); print(p.is_manual_mode('@架构 分析需求'))" → True
- 单元测试：pytest tests/unit -v
- E2E：python src/6-agents.py task2.md --auto-architect --max-budget 0.5
- 手动：python src/6-agents.py → @architect 分析代码结构
- 恢复：中断后 --resume

风险：
- Windows兼容：使用msvcrt锁
- 测试依赖：pytest, pytest-asyncio
- Claude CLI可用

预期成果：
- Bug修复
- 配置完善
- 单元测试覆盖>80%
- 支持三种模式（全自动/半自动/手动）

## 已完成修复详情
### src/6-agents.py 修改
- 中文别名：re.search(r'@[\w\u4e00-\u9fff]+')
- stream-json：支持多种结构、cost_usd、usage计算、异常保护
- 并发：添加asyncio.Semaphore(2) in __init__ and run_agent
- 分支竞态：使用msvcrt.locking in _get_next_branch_number

### Agent配置文件扩展
- 02-tech.md：计划审核、任务分解、规范检查 (188行)
- 03-dev.md：编码规范、PROGRESS.md更新、错误处理 (270行)
- 04-test.md：测试策略、BUG_REPORT.md模板、规范 (343行)
- 05-opti.md：优化优先级、重构原则、性能基准 (316行)
- 06-secu.md：OWASP检查、SECURITY_AUDIT.md格式、漏洞检测 (373行)

## 剩余工作
~~- Step 6: 编写单元测试文件~~ ✅ 已完成
~~- P2问题6: PLAN.md读取容错~~ ✅ 已完成
~~- 修复用户bug：plan.md位置/命名~~ ✅ 已完成
~~- Agent文件生成可见性~~ ✅ 已完成（通过明确路径指示）
- 完整验证系统运行（需用户实际测试）

## 2026-02-04 完成的工作

### Step 6: 单元测试文件已创建
创建了以下测试文件：
- tests/conftest.py - pytest 配置和 fixtures
- tests/unit/test_manual_parser.py - ManualTaskParser 测试（14个测试）
- tests/unit/test_stream_json.py - stream-json 解析测试（11个测试）
- tests/unit/test_task_parser.py - TaskParser 测试（7个测试）

测试结果：**32 passed in 0.15s** ✅

### P2 问题 6: PLAN.md 读取容错已修复
- 添加了 try-except 处理文件读取错误
- 添加了 encoding='utf-8', errors='replace' 处理编码问题
- 添加了空文件检查

验证命令：
```bash
# 运行单元测试
python -m pytest tests/unit -v

# 验证中文别名
python -c "from src import ...; p.is_manual_mode('@架构 分析需求')"
```

### 用户 Bug 修复：plan.md 位置/命名问题

**问题原因**：
Claude CLI 的 plan 模式会将计划文件保存到 `~/.claude/plans/` 目录，而不是项目根目录。

**修复措施**：

1. **更新 src/6-agents.py 半自动模式 system_prompt**：
   - 添加明确的输出文件位置说明
   - 强调使用 Write 工具写入项目根目录
   - 添加项目根目录路径变量

2. **更新 src/6-agents.py generate_initial_prompt 方法**：
   - 添加文件路径规范说明
   - 强调输出文件必须保存在项目根目录

3. **更新所有 Agent 配置文件**（.claude/agents/*.md）：
   - 01-arch.md: 添加输出文件位置表格，强调使用 Write 工具
   - 02-tech.md: 添加 PLAN.md 更新位置说明
   - 03-dev.md: 添加 PROGRESS.md 位置说明
   - 04-test.md: 添加 BUG_REPORT.md 位置说明
   - 05-opti.md: 添加 PROGRESS.md 更新位置说明
   - 06-secu.md: 添加 SECURITY_AUDIT.md 位置说明

**修复后的输出文件规范**：

| Agent | 输出文件 | 位置 |
|-------|----------|------|
| architect | PLAN.md, CODEBASE_ANALYSIS.md | 项目根目录 |
| tech_lead | 更新 PLAN.md | 项目根目录 |
| developer | PROGRESS.md, 源代码 | 项目根目录, src/ |
| tester | BUG_REPORT.md, tests/*.py | 项目根目录, tests/ |
| optimizer | 更新 PROGRESS.md | 项目根目录 |
| security | SECURITY_AUDIT.md | 项目根目录 |