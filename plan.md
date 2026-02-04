# 测试和 Debug 实施计划：6-agents.py

## 需求总结

对 `src/6-agents.py` 多Agent调度系统进行全面测试和debug，修复发现的bug，确保系统能顺利工作。

---

## 代码库分析

### 项目结构
```
2nd-repo/
├── src/
│   └── 6-agents.py        # 主程序 (2113行)
├── .claude/
│   ├── agents/            # 6个Agent配置文件
│   │   ├── 01-arch.md     # Architect (263行，完整)
│   │   ├── 02-tech.md     # Tech Lead (17行，不完整)
│   │   ├── 03-dev.md      # Developer (18行，不完整)
│   │   ├── 04-test.md     # Tester (18行，不完整)
│   │   ├── 05-opti.md     # Optimizer (17行，不完整)
│   │   └── 06-secu.md     # Security (17行，不完整)
│   ├── state.json         # 状态持久化
│   └── branch_counter.txt # 分支计数器
├── mc-dir-v1.py           # 旧版本
├── mc-dir-v2.py           # 旧版本
└── task2.md               # 任务描述
```

### 技术栈
- **语言**: Python 3.x
- **异步**: asyncio
- **CLI**: argparse + subprocess (调用 claude CLI)
- **依赖**: 纯标准库，无第三方依赖

---

## 发现的问题

### 🔴 P0 - 严重问题（必须修复）

| # | 问题 | 位置 | 影响 |
|---|------|------|------|
| 1 | Agent配置文件内容不完整 | 02~06-*.md | Agent缺乏详细工作指导 |
| 2 | 中文别名正则不支持 | 行 292, 336 | `@架构` `@开发` 等无法使用 |

### 🟡 P1 - 高优先级

| # | 问题 | 位置 | 影响 |
|---|------|------|------|
| 3 | stream-json解析脆弱 | 行 723-774 | 成本/tokens统计可能失败 |
| 4 | 并发无速率限制 | 行 1235-1244 | 可能触发API限流 |

### 🟢 P2 - 中等优先级

| # | 问题 | 位置 | 影响 |
|---|------|------|------|
| 5 | 分支编号竞态条件 | 行 1025-1049 | 并发时可能创建重名分支 |
| 6 | PLAN.md读取无容错 | 行 1675-1680 | 文件缺失时报错不友好 |

---

## 实施方案

### 修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/6-agents.py` | 修改 | 修复 4 处 bug |
| `.claude/agents/02-tech.md` | 修改 | 扩展到 ~100 行 |
| `.claude/agents/03-dev.md` | 修改 | 扩展到 ~100 行 |
| `.claude/agents/04-test.md` | 修改 | 扩展到 ~100 行 |
| `.claude/agents/05-opti.md` | 修改 | 扩展到 ~100 行 |
| `.claude/agents/06-secu.md` | 修改 | 扩展到 ~100 行 |
| `tests/conftest.py` | 新增 | 测试配置和fixtures |
| `tests/unit/test_*.py` | 新增 | 单元测试文件 |

### 无依赖变更
代码使用纯标准库，无需安装额外依赖。测试需要 `pytest pytest-asyncio`。

---

## 分步实施路径

### Step 1: 修复中文别名正则 (P0)

**文件**: `src/6-agents.py`

**修改 1 - 行 292** (`is_manual_mode` 方法):
```python
# 原代码
return bool(re.search(r'@\w+', user_input))

# 修改为
return bool(re.search(r'@[\w\u4e00-\u9fff]+', user_input))
```

**修改 2 - 行 336** (`_parse_single_task` 方法):
```python
# 原代码
match = re.match(r'@(\w+)\s+(.+)$', task_str)

# 修改为
match = re.match(r'@([\w\u4e00-\u9fff]+)\s+(.+)$', task_str)
```

### Step 2: 增强 stream-json 解析 (P1)

**文件**: `src/6-agents.py`，行 723-774

增强 `_parse_stream_json` 方法：
- 添加多种 JSON 结构的支持
- 添加 `cost_usd` 字段兼容
- 添加 `usage.input_tokens + output_tokens` 计算
- 添加空值和异常保护

### Step 3: 添加并发限制 (P1)

**文件**: `src/6-agents.py`

在 `AgentExecutor.__init__` 中添加:
```python
self._semaphore = asyncio.Semaphore(max_concurrent)  # 默认 2-3
```

在 `run_agent` 方法中使用:
```python
async with self._semaphore:
    # 原有执行逻辑
```

### Step 4: 修复分支编号竞态 (P2)

**文件**: `src/6-agents.py`，行 1025-1049

使用 Windows 兼容的文件锁:
```python
import msvcrt  # Windows
# 或 fcntl (Unix)
```

### Step 5: 完善 Agent 配置文件 (P0)

**参考模板**: `01-arch.md` (263行)

每个文件需包含:
1. YAML frontmatter (name, description, model, tools)
2. 角色定义
3. 核心职责（详细）
4. 工作流程（分步骤）
5. 约束条件（DO / DO NOT）
6. 输出文件格式示例

**02-tech.md** 扩展内容:
- 计划审核标准
- 任务分解方法
- 代码规范检查清单

**03-dev.md** 扩展内容:
- 编码规范
- PROGRESS.md 更新格式
- 错误处理要求

**04-test.md** 扩展内容:
- 测试策略（单元/集成/E2E）
- BUG_REPORT.md 格式模板
- 测试用例编写规范

**05-opti.md** 扩展内容:
- 优化优先级标准
- 重构原则
- 性能基准要求

**06-secu.md** 扩展内容:
- OWASP Top 10 检查清单
- SECURITY_AUDIT.md 格式
- 常见漏洞检测方法

### Step 6: 编写测试用例

**创建文件**:
- `tests/conftest.py` - 共享 fixtures
- `tests/unit/test_manual_parser.py` - 中文别名测试
- `tests/unit/test_stream_json.py` - JSON解析测试
- `tests/unit/test_task_parser.py` - 任务解析测试

---

## 验证方法

### 1. 中文别名验证
```bash
python -c "
from src.six_agents import ManualTaskParser
p = ManualTaskParser()
print(p.is_manual_mode('@架构 分析需求'))  # 应输出 True
"
```

### 2. 单元测试验证
```bash
pip install pytest pytest-asyncio
pytest tests/unit -v
```

### 3. 端到端验证
```bash
# 测试全自动模式
python src/6-agents.py task2.md --auto-architect --max-budget 0.5

# 测试手动模式
python src/6-agents.py
# 输入: @architect 分析代码结构
```

### 4. 恢复机制验证
```bash
# 启动任务后 Ctrl+C 中断
python src/6-agents.py task2.md --auto-architect

# 恢复执行
python src/6-agents.py --resume
```

---

## 风险和注意事项

1. **Windows 兼容性**: 文件锁使用 `msvcrt` 而非 `fcntl`
2. **路径规范**: 始终使用正斜杠 `/`，遵循 CLAUDE.md 规范
3. **测试依赖**: 需要安装 `pytest pytest-asyncio`
4. **Claude CLI**: 端到端测试需要 claude CLI 可用且有额度
5. **Git 分支**: 测试时注意当前分支状态

---

## 预期成果

1. 6-agents.py 所有已知 bug 修复
2. 5 个 Agent 配置文件完善（各约 100 行）
3. 完整的单元测试套件（覆盖率 > 80%）
4. 系统可正常执行三种模式（全自动/半自动/手动）
