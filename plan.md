# 测试和 Debug 实施计划：6-agents.py

## 需求总结

对 `src/6-agents.py` 多Agent调度系统进行全面测试和debug，修复发现的bug，确保系统能顺利工作。

---

## 第二轮工作发现（重要更新）

### ✅ Agent 配置文件状态（重大修正）

**初始评估"不完整"是误判！所有6个文件都是完整的高质量配置：**

| 文件 | 行数 | 状态 | 评级 |
|------|------|------|------|
| 01-arch.md | 277 | ✅ 完整 | ★★★★★ |
| 02-tech.md | 199 | ✅ 完整 | ★★★★★ |
| 03-dev.md | 282 | ✅ 完整 | ★★★★★ |
| 04-test.md | 355 | ✅ 完整 | ★★★★★ |
| 05-opti.md | 327 | ✅ 完整 | ★★★★★ |
| 06-secu.md | 384 | ✅ 完整 | ★★★★★ |

**结论：无需修改 Agent 配置文件**

---

### ✅ 测试现状

**已有测试（32个，全部通过）：**
- `tests/conftest.py` - pytest 配置和 fixtures（78行）
- `tests/unit/test_manual_parser.py` - ManualTaskParser 单元测试（14个）
- `tests/unit/test_stream_json.py` - stream-json 解析测试（11个）
- `tests/unit/test_task_parser.py` - TaskParser 单元测试（7个）

**当前覆盖率：约 30%**

**已覆盖：**
- ✅ 中文别名识别（@架构、@开发 等）
- ✅ stream-json 多格式解析
- ✅ 任务复杂度判断

**未覆盖（关键缺失）：**
- ❌ AgentExecutor.run_agent（核心执行）
- ❌ Orchestrator 主控流程
- ❌ StateManager（状态管理）
- ❌ ErrorHandler（错误恢复）
- ❌ 异步/并发测试
- ❌ 异常场景测试

---

## 问题清单（已验证 + 新发现）

### 🔴 P0 - 必须修复

| # | 问题 | 位置 | 说明 |
|---|------|------|------|
| ~~1~~ | ~~Agent配置文件不完整~~ | - | ✅ 已验证完整，无需修复 |
| ~~2~~ | ~~中文别名正则不支持~~ | - | ✅ 已验证支持，代码正确 |

### 🟡 P1 - 高优先级（需修复）

| # | 问题 | 位置 | 说明 |
|---|------|------|------|
| 3 | stream-json `or` 操作符缺陷 | 行 771 | `0 or value` 返回 value 而非 0 |
| 4 | stdout/stderr 解码无容错 | 行 562, 580 | 无效UTF-8会抛异常 |
| 5 | 分支编号创建竞态窗口 | 行 1072-1073 | 文件创建在加锁之前 |
| 6 | 分支编号降级方案精度过低 | 行 1100 | 秒级时间戳可能重复 |

### 🟢 P2 - 中等优先级

| # | 问题 | 位置 | 说明 |
|---|------|------|------|
| 7 | 异常处理过于宽泛 | 行 1048, 1057 | `except Exception: pass` 吃掉错误 |
| 8 | 状态保存潜在竞态 | 行 833-838 | temp文件名可能冲突 |
| 9 | 子进程未等待真正终止 | 行 540 | `process.kill()` 后无 `await wait()` |
| 10 | phase索引计算脆弱 | 行 1437 | 硬编码依赖 agent 列表长度 |
| 11 | 文件权限异常捕获不完整 | 多处 | 只捕获 FileNotFoundError |

### 🔵 P3 - 低优先级

| # | 问题 | 位置 | 说明 |
|---|------|------|------|
| 12 | 进度指示器任务泄漏风险 | 行 529-551 | cancel 后未等待清理 |
| 13 | 重试日志消息时序不合理 | 行 886 | "X秒后重试"显示在等待前 |
| 14 | PLAN.md 空白检查不够 | 行 1764 | 只检查空白，不检查有效内容 |

---

## 实施方案

### 修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/6-agents.py` | 修改 | 修复 P1-P2 共 9 处 bug |
| ~~`.claude/agents/02-06*.md`~~ | ~~修改~~ | ✅ 无需修改 |
| `tests/unit/test_executor.py` | 新增 | AgentExecutor 测试 |
| `tests/unit/test_state.py` | 新增 | StateManager 测试 |
| `tests/integration/test_orchestrator.py` | 新增 | 集成测试 |

---

## 分步实施路径

### Step 1: 修复 stream-json `or` 操作符缺陷 (P1)

**文件**: `src/6-agents.py`，行 771

```python
# 原代码
cost = data.get('cost_usd', 0) or data.get('cost', 0)

# 修改为（正确处理 0 值）
cost = data.get('cost_usd') if 'cost_usd' in data else data.get('cost', 0)
```

### Step 2: 修复 stdout/stderr 解码无容错 (P1)

**文件**: `src/6-agents.py`，行 562, 580

```python
# 原代码
cost, tokens = self._parse_stream_json(stdout.decode('utf-8'))
error_message=stderr.decode('utf-8') if process.returncode != 0 else None

# 修改为
cost, tokens = self._parse_stream_json(stdout.decode('utf-8', errors='replace'))
error_message=stderr.decode('utf-8', errors='replace') if process.returncode != 0 else None
```

### Step 3: 修复分支编号竞态窗口 (P1)

**文件**: `src/6-agents.py`，行 1072-1073

```python
# 原代码（竞态窗口）
if not counter_file.exists():
    counter_file.write_text("0", encoding='utf-8')

with open(counter_file, 'r+', encoding='utf-8') as f:
    # 加锁...

# 修改为（文件创建也在锁内）
with open(counter_file, 'a+', encoding='utf-8') as f:
    # 先加锁
    if sys.platform == 'win32':
        import msvcrt
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
    # 再读写
    f.seek(0)
    content = f.read().strip()
    if not content:
        counter = 0
    else:
        counter = int(content)
    # ...
```

### Step 4: 修复分支编号降级方案精度 (P1)

**文件**: `src/6-agents.py`，行 1100

```python
# 原代码（秒级精度）
counter = int(time.time()) % 1000

# 修改为（毫秒级 + 随机数）
import random
counter = int(time.time() * 1000) % 100000 + random.randint(0, 99)
```

### Step 5: 修复异常处理过于宽泛 (P2)

**文件**: `src/6-agents.py`，行 1048, 1057

```python
# 原代码
except Exception:
    pass

# 修改为
except (OSError, FileNotFoundError):
    pass
```

### Step 6: 修复子进程未等待终止 (P2)

**文件**: `src/6-agents.py`，行 540

```python
# 原代码
process.kill()
return ExecutionResult(...)

# 修改为
process.kill()
try:
    await asyncio.wait_for(process.wait(), timeout=5.0)
except asyncio.TimeoutError:
    pass  # 强制终止后仍超时，忽略
return ExecutionResult(...)
```

### Step 7: 修复文件权限异常捕获 (P2)

**文件**: `src/6-agents.py`，多处

```python
# 原代码
except FileNotFoundError:
    ...

# 修改为
except (FileNotFoundError, PermissionError, IOError):
    ...
```

### Step 8: 补充核心测试用例

**新建文件**:
- `tests/unit/test_executor.py` - AgentExecutor 测试（mock subprocess）
- `tests/unit/test_state.py` - StateManager 测试
- `tests/integration/test_orchestrator.py` - 集成测试

**测试重点**:
1. AgentExecutor.run_agent（mock 子进程）
2. StateManager save/load/clear
3. ErrorHandler.retry_with_backoff（重试机制）
4. 超时、文件缺失等异常场景

---

## 验证方法

### 1. 单元测试
```bash
pip install pytest pytest-asyncio
pytest tests/unit -v
```

### 2. 集成测试
```bash
pytest tests/integration -v
```

### 3. 端到端验证
```bash
# 全自动模式
python src/6-agents.py task2.md --auto-architect --max-budget 0.5

# 手动模式（中文别名）
python src/6-agents.py
# 输入: @架构 分析代码结构

# 恢复机制
python src/6-agents.py --resume
```

### 4. 代码静态检查
```bash
# 检查语法错误
python -m py_compile src/6-agents.py

# 可选：类型检查
mypy src/6-agents.py --ignore-missing-imports
```

---

## 风险和注意事项

1. **Windows 兼容性**: 文件锁使用 `msvcrt`
2. **路径规范**: 始终使用正斜杠 `/`
3. **测试依赖**: 需要 `pytest pytest-asyncio`
4. **Claude CLI**: 端到端测试需要 claude CLI 可用
5. **Git 分支**: 测试时注意当前分支状态

---

## 预期成果

1. ✅ 9 处已确认 bug 全部修复
2. ✅ 新增 3 个测试文件，覆盖率提升至 >60%
3. ✅ 系统可正常执行三种模式（全自动/半自动/手动）
4. ✅ 异常场景有合理的容错和恢复机制

---

## 工作量估算

| 任务 | 工作量 |
|------|--------|
| P1 bug 修复（4处） | 约 1 小时 |
| P2 bug 修复（5处） | 约 1 小时 |
| 核心测试用例补充 | 约 2-3 小时 |
| 端到端验证 | 约 1 小时 |
| **总计** | **约 5-6 小时** |
