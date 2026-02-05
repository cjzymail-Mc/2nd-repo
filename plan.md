# 测试和 Debug 实施计划：6-agents.py（完成版）

## 需求总结

对 `src/6-agents.py` 多Agent调度系统进行全面测试和debug，修复发现的bug，确保系统能顺利工作。

---

## 已修复的 Bug（全部完成 ✅）

### P0 - 严重 Bug

| # | 问题 | 状态 | 修复说明 |
|---|------|------|----------|
| B1 | interactive_mode resume 会清空状态 | ✅ 已修复 | 添加 `resume_mode` 标志，执行时传 `clean_start=not resume_mode` |
| B2 | CLI --resume 对非 from_plan 任务无效 | ✅ 已修复 | `execute()` 方法增加 `completed_agents` 检查，跳过已完成的 phase |

### P1 - 高优先级

| # | 问题 | 状态 | 修复说明 |
|---|------|------|----------|
| B3 | log_error 遇到无效 JSON 会崩溃 | ✅ 已修复 | 添加 `try-except` 捕获 `JSONDecodeError` |
| B4 | 文件锁位置错误 | ✅ 已修复 | 在获取锁之前先 `seek(0)` |
| B5 | StateManager.save_state 目录不存在时崩溃 | ✅ 已修复 | 添加 `mkdir(parents=True, exist_ok=True)` |

### 新增功能 - 02-05 Bug 修复

| # | 问题 | 状态 | 修复说明 |
|---|------|------|----------|
| F1 | Architect 直接修改代码 | ✅ 已修复 | `run_agent()` 中 architect 使用 `--permission-mode plan`，其他 agents 使用 `--dangerously-skip-permissions` |
| F2 | 缺少"从 PLAN.md 继续"选项 | ✅ 已修复 | 添加 `from_plan_mode()` 函数、交互菜单选项2、`--from-plan` CLI 参数 |
| F3 | 缺少多轮循环机制 | ✅ 已修复 | 添加 `execute_with_loop()` 方法、`_check_bug_report()` 方法、`--max-rounds` CLI 参数 |

---

## 新增功能详情

### F1: Architect 权限限制

**修改位置**: `run_agent()` 方法（行 ~493-510）

**修改说明**:
```python
# architect 使用 plan 模式限制权限，防止直接修改代码
# 其他 agents 使用 skip-permissions 允许实际执行
if config.name == "architect":
    cmd.extend(["--permission-mode", "plan"])
else:
    cmd.append("--dangerously-skip-permissions")
```

### F2: 从 PLAN.md 继续执行

**新增内容**:
1. `from_plan_mode()` 函数 - 交互式确认后执行
2. 交互菜单新增选项 "2. 从 PLAN.md 继续"
3. `--from-plan` CLI 参数

**使用方式**:
```bash
# CLI 方式
python src/6-agents.py --from-plan

# 交互方式
python src/6-agents.py
# 选择 2. 从 PLAN.md 继续
```

### F3: 多轮循环机制

**新增内容**:
1. `Orchestrator.__init__()` 添加 `max_rounds` 参数
2. `_check_bug_report()` 方法 - 解析 BUG_REPORT.md 中的未解决 bug
3. `_archive_bug_report()` 方法 - 归档每轮的 bug 报告
4. `execute_with_loop()` 方法 - developer-tester 循环执行
5. `--max-rounds` CLI 参数

**执行流程**:
```
Phase 1: architect → tech_lead（只执行一次）
Phase 2: developer → tester（循环执行）
         ↓ 检查 BUG_REPORT.md
         ├─ 无 bug → 继续
         └─ 有 bug → 归档 → 回到 developer（最多 max_rounds 轮）
Phase 3: optimizer → security（只执行一次）
```

**使用方式**:
```bash
# 启用3轮迭代
python src/6-agents.py task.md --auto-architect --max-rounds 3
```

---

## 测试结果

### 单元测试：61 passed ✅

```
tests/unit/test_agent_scheduler.py     7 passed
tests/unit/test_error_handler.py       5 passed
tests/unit/test_manual_parser.py      14 passed
tests/unit/test_parse_agent_file.py   11 passed
tests/unit/test_state_manager.py       6 passed
tests/unit/test_stream_json.py        11 passed
tests/unit/test_task_parser.py         7 passed
-------------------------------------------
Total:                                61 passed
```

---

## 修改的文件

| 文件 | 修改内容 |
|------|----------|
| `src/6-agents.py` | 所有 bug 修复和新功能 |

---

## 验证命令

```bash
# 语法检查
python -m py_compile src/6-agents.py  # ✅ 通过

# 运行所有测试
pytest tests/ -v  # ✅ 61 passed

# 验证 F1 - Architect 权限
python src/6-agents.py task.md --auto-architect
# 确认 architect 只生成 PLAN.md，不修改源代码

# 验证 F2 - 从 PLAN.md 继续
python src/6-agents.py --from-plan

# 验证 F3 - 多轮循环
python src/6-agents.py task.md --auto-architect --max-rounds 3
# 观察 developer-tester 是否进行多轮迭代
```

---

## 总结

- 修复了 5 个原有 bug（2个P0 + 3个P1）
- 新增了 3 个功能（F1-F3）
- 61 个单元测试全部通过
- 所有修改仅在 `src/6-agents.py` 文件中
