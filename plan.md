# orchestrator_v6.py 代码质量审查与测试计划

> **更新日期**: 2026-02-07
> **目标**: 对 `src/orchestrator_v6.py`（~3900行 多Agent调度系统）进行全面质量审查
> **执行方式**: Mode 2（从 PLAN.md 继续），建议迭代 2+ 轮

---

## 目标文件

- **主文件**: `src/orchestrator_v6.py`
- **单元测试**: `tests/unit/`
- **不要修改**: `mc-dir-v6.py`、`.claude/` 目录下的所有文件

---

## 一、测试方法

### 1.1 静态分析（Developer + Tester 共同执行）

```bash
# 语法检查
python -c "import ast; ast.parse(open('src/orchestrator_v6.py', encoding='utf-8').read()); print('OK')"

# 运行现有单元测试
pytest tests/unit/ -v

# 如果有 ruff/flake8 可用
ruff check src/orchestrator_v6.py 2>/dev/null || echo "ruff not installed, skip"
```

### 1.2 代码审查重点区域

**Developer 和 Tester 必须逐一审查以下模块，发现问题直接修复或报告：**

#### 区域 A: 异常处理一致性
- **方法**: 搜索所有 `except` 语句，检查是否存在：
  - `except:` (bare except) — 应改为 `except Exception:`
  - 缺少异常保护的文件读写操作（对比周围类似代码）
  - 吞掉异常后无任何日志的 `except: pass`
- **关注的类/函数**: `TaskParser`、`StateManager`、`AgentRunner`、所有 `read_text()` 调用

#### 区域 B: subprocess 健壮性
- **方法**: 搜索所有 `subprocess.run` 调用，检查：
  - 是否都有 `timeout` 参数（git 操作应有 timeout=30）
  - 超时后是否正确处理 `subprocess.TimeoutExpired` 异常
  - 交互式 subprocess（如 `claude` CLI 调用）不应加 timeout
- **关注的类/函数**: `GitBranchManager` 所有方法、`_get_git_state()`、`_validate_architect_changes()`

#### 区域 C: 边界条件与防御性编程
- **方法**: 检查以下场景是否被正确处理：
  - 空列表/空字符串输入（如 `phases = [[]]`、`plan_content = ""`）
  - None 值传入字符串操作（如 `task_desc[:50]` 当 task_desc 为 None）
  - 字典键不存在（`metadata.get()` vs `metadata[]`）
  - 文件不存在时的 fallback 行为
- **关注的函数**: `execute()`、`execute_from_plan()`、`execute_from_plan_with_loop()`、`_check_bug_report()`

#### 区域 D: 异步与并行逻辑
- **方法**: 审查 `asyncio.gather` 相关代码：
  - 并行 agent 是否共享了不应共享的状态（如同一个 dict）
  - `gather` 的 `return_exceptions=True` 是否设置
  - 并行 agent 失败时是否影响其他 agent
- **关注的函数**: `execute()` Phase 3 并行、`execute_from_plan()` 审查阶段并行

#### 区域 E: 用户输入与配置解析
- **方法**: 检查菜单输入、YAML frontmatter 解析、命令行参数：
  - 非法输入是否有友好提示（而非崩溃）
  - `_parse_agent_file()` 对畸形 YAML 的容错
  - `_ask_max_rounds()` 对非数字输入的处理
- **关注的函数**: `main_menu()`、`_parse_agent_file()`、`_ask_max_rounds()`

#### 区域 F: 资源泄漏
- **方法**: 检查文件句柄、进程是否正确释放：
  - `open()` 是否都在 `with` 块中
  - 子进程被 kill 后是否 `await process.wait()`
  - 临时文件（prompt_xxx.txt）是否在 finally 中清理
- **关注的函数**: `run_agent()`、`_monitor_architect_stream()`、`_get_next_branch_number()`

---

## 二、执行步骤

### Developer Agent

1. 读取 `src/orchestrator_v6.py`
2. 按照上述区域 A~F 逐一审查
3. 发现 bug 直接修复（最小改动原则）
4. 修复后运行 `pytest tests/unit/ -v` 确保不破坏现有测试
5. 将修复内容记录到 `claude-progress.md`

### Tester Agent

1. 运行 `pytest tests/unit/ -v`，记录通过/失败情况
2. 运行语法检查
3. 审查 Developer 的改动是否引入新问题
4. 如发现未修复的 bug，写入 `BUG_REPORT.md`（使用 `- [ ]` 格式）

### Optimizer Agent

- 检查修复后代码是否有冗余逻辑
- 检查是否符合 PEP8 风格
- 不要重构、不要改注释风格、不要添加新功能

### Security Agent

- 检查是否有命令注入风险（subprocess 参数拼接）
- 检查文件路径操作是否存在路径遍历风险
- 检查敏感信息是否可能泄漏到日志

---

## 三、约束（所有 Agent 必读）

- **只改** `src/orchestrator_v6.py`
- **不要** 修改 `mc-dir-v6.py`（用户手动同步）
- **不要** 修改 `.claude/` 目录下任何文件（hooks、agents、settings）
- **不要** 重构、添加新功能、改注释风格
- **不要** 删除任何现有功能（即使看起来是死代码）
- **最小改动原则**: 每个修复尽量控制在 1~5 行

---

## 已修复的 Bug（历史记录）

| Bug | 修复版本 | 状态 |
|-----|---------|------|
| 分支创建（模式2/3 未创建分支） | fix6.5 | ✅ |
| 循环终止（BUG_REPORT 格式过严） | fix6.5 | ✅ |
| 循环保底（第1轮无 BUG_REPORT 提前终止） | fix6.5 | ✅ |
| 分支命名（MINIMAL 复杂度下分支名错误） | fix6.5 | ✅ |
| 并行隔离（多 agent 并行无子分支） | fix6.5 | ✅ |
| PLAN.md 位置（保存到 ~/.claude/plans/） | fix6.5 | ✅ |
| Hook 输出格式（JSON → exit code 2） | fix6.6 | ✅ |
| Mode 1 防护缺失（仅2/4层生效） | fix6.6 | ✅ |
| 线性执行（后3个 agent 串行浪费） | fix6.6 | ✅ |
| 菜单冗余（Mode 3 全自动鸡肋） | fix6.6 | ✅ |
| ExitPlanMode 越权执行 → Hook 无条件拦截 | fix6.6 | ✅ |
| post-validation 误回滚全部工作进度 → baseline 对比（已禁用） | fix6.6 | ✅ |
| PLAN.md 未生成 → 去掉 plan mode，改 skip-permissions | fix6.6 | ✅ |
| repo-scan-result.md 只对 architect 加载 → 全 agent 加载 | fix6.6 | ✅ |
| claude-progress 文件递增堆积 → 固定文件名+每次清理 | fix6.6 | ✅ |
| run_agent_interactive 缺少 ORCHESTRATOR_AGENT env var | fix6.6 | ✅ |
