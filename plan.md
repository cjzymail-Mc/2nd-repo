# 任务复杂度手动选择功能 - 实施完成

## 功能概述

在交互菜单中增加"任务复杂度"选择，用户可以手动指定：

- **简单任务 (MINIMAL)**: developer + tester（2个agents，快速执行）
- **复杂任务 (COMPLEX)**: 全部6个agents（architect → tech_lead → developer → tester → optimizer → security）

**新菜单流程：**
1. 选择执行模式 (1/2/3/4/5)
2. 选择迭代轮数 (1/2/3)
3. **选择任务复杂度 (简单/复杂)** ← 新增

---

## 已完成的修改

### 修改1: 扩展 TaskComplexity 枚举 ✅

**位置:** src/6-agents.py:47-52

**修改内容:**
```python
class TaskComplexity(Enum):
    MINIMAL = "minimal"      # 2个agents (developer + tester) ← 新增
    SIMPLE = "simple"        # 3个agents (architect → developer → tester)
    MODERATE = "moderate"    # 4-5个agents
    COMPLEX = "complex"      # 6个agents (全流程)
```

### 修改2: 更新 AgentScheduler.plan_execution() ✅

**位置:** src/6-agents.py:224-250

**新增分支:**
```python
if complexity == TaskComplexity.MINIMAL:
    return [
        ["developer"],
        ["tester"]
    ]
```

### 修改3: 新增 _ask_task_complexity() 函数 ✅

**位置:** src/6-agents.py:~2475（_ask_max_rounds之后）

**功能:**
- 询问用户选择任务复杂度
- 返回 TaskComplexity.MINIMAL 或 TaskComplexity.COMPLEX

### 修改4: execute() 支持复杂度覆盖 ✅

**位置:** src/6-agents.py:1202-1235

**新增参数:**
```python
async def execute(
    self,
    user_request: str,
    clean_start: bool = True,
    override_complexity: Optional[TaskComplexity] = None  # 新增
) -> bool:
```

**逻辑:**
- 如果提供 override_complexity，使用用户指定的复杂度
- 否则，使用 TaskParser 自动解析

### 修改5: execute_with_loop() 支持复杂度覆盖 ✅

**位置:** src/6-agents.py:1842-1880

**同步修改:**
- 添加 override_complexity 参数
- 实现与 execute() 相同的复杂度处理逻辑

### 修改6: 更新 interactive_mode() ✅

**位置:** src/6-agents.py:2540-2610

**修改内容:**
1. 在询问迭代轮数后，调用 `_ask_task_complexity()`
2. 显示选择结果
3. 将复杂度传递给 execute/execute_with_loop
4. 对模式1/2添加提示（复杂度设置会被忽略）

---

## 修改文件清单

| 文件 | 修改内容 | 行数 |
|------|----------|------|
| src/6-agents.py | 扩展 TaskComplexity 枚举 | +1 |
| src/6-agents.py | 更新 plan_execution() | +4 |
| src/6-agents.py | 新增 _ask_task_complexity() | +14 |
| src/6-agents.py | 修改 execute() | +8 |
| src/6-agents.py | 修改 execute_with_loop() | +7 |
| src/6-agents.py | 更新 interactive_mode() | +20 |

**总计:** ~54行新增/修改

---

## 测试结果

### 语法检查 ✅
```bash
python -m py_compile src/6-agents.py
# 通过
```

### 单元测试 ✅
```bash
pytest tests/ -v
# 61 passed in 1.29s
```

### 功能验证

#### 测试场景1：简单任务 + MINIMAL

```bash
python src/6-agents.py
# 选择：3（全自动模式）
# 迭代轮数：1
# 任务复杂度：1（简单任务）
# 输入："修复 main.py 中的拼写错误"

预期结果：
✓ 只执行 developer + tester
✓ 跳过 architect, tech_lead, optimizer, security
✓ 快速完成
```

#### 测试场景2：复杂任务 + COMPLEX + 多轮

```bash
python src/6-agents.py
# 选择：3（全自动模式）
# 迭代轮数：2
# 任务复杂度：2（复杂任务）
# 输入："开发一个计算器程序"

预期结果：
✓ 执行全部6个agents
✓ developer-tester 最多循环2轮
```

#### 测试场景3：半自动模式（提示用户）

```bash
python src/6-agents.py
# 选择：1（半自动模式）
# 迭代轮数：1
# 任务复杂度：1（简单任务）

预期结果：
⚠️ 显示提示："半自动模式会由 Architect 自动规划，复杂度设置将被忽略"
✓ 正常进入 Claude CLI
```

---

## 新菜单示例

```
╔════════════════════════════════════════════════════════════╗
║       🚀 mc-dir - 多Agent智能调度系统                       ║
╚════════════════════════════════════════════════════════════╝

选择执行模式：
  1. 半自动模式（推荐）- 进入 Claude CLI 讨论需求，生成 PLAN.md 后自动执行
  2. 从 PLAN.md 继续 - 跳过 Architect，直接从现有计划执行（节省 token）
  3. 全自动模式 - 输入任务后，Architect 自动规划并执行全流程
  4. 传统交互模式 - 在此输入需求，可手动指定 agents
  5. 退出

请选择 [1/2/3/4/5]: 3

开发-测试迭代轮数：
  1. 1轮（默认）- 线性执行，不循环
  2. 2轮 - 如有bug，developer-tester再迭代1次
  3. 3轮 - 最多迭代3次

请选择 [1/2/3，直接回车=1]: 1
✓ 已设置: 最多 1 轮 developer-tester 迭代

任务复杂度：
  1. 简单任务 - 只用 developer + tester（2个agents，快速执行）
  2. 复杂任务 - 完整流程（6个agents，全面保障）

请选择 [1/2，直接回车=2]: 1
✓ 已设置: 简单任务（2个agents）

请输入任务描述（或 .md 文件路径）：
> 修复拼写错误

🚀 全自动模式启动...
📋 用户需求: 修复拼写错误
任务复杂度: minimal（用户指定）
执行计划: 2 个阶段

Phase 1: developer
Phase 2: tester
```

---

## 与现有功能的兼容性

### 向后兼容 ✅
- `execute()` 和 `execute_with_loop()` 的 `override_complexity` 参数为**可选**
- 不传该参数时，保持原有的自动解析行为
- CLI 参数仍然可用（`--auto-architect`, `--max-rounds` 等）

### 复杂度优先级
1. **用户手动选择** (override_complexity) → 最高优先级
2. **自动解析** (TaskParser.parse) → 默认行为

### 特殊模式处理
- **模式1（半自动）**: 复杂度选择被忽略（architect 规划）
- **模式2（从PLAN.md继续）**: 复杂度选择被忽略（已有计划）
- **模式3（全自动）**: 复杂度选择生效
- **模式4（传统交互）**: 不询问复杂度

---

## 复杂度对比表

| 复杂度 | Agents数量 | 执行流程 | 适用场景 |
|--------|-----------|----------|---------|
| MINIMAL | 2个 | developer → tester | 拼写错误、简单bug修复 |
| SIMPLE | 3个 | architect → developer → tester | 小功能添加 |
| MODERATE | 4-5个 | architect → developer → (tester + security) | 中等功能 |
| COMPLEX | 6个 | architect → tech_lead → developer → (tester + security + optimizer) | 大型功能、系统重构 |

---

## 总结

- ✅ 新增 MINIMAL 复杂度选项（2个agents）
- ✅ 在交互菜单中添加第3个选项：任务复杂度
- ✅ 支持用户手动覆盖自动解析
- ✅ 61个单元测试全部通过
- ✅ 保持向后兼容
- ✅ 代码质量：语法检查通过

**预计提升：**
- 简单任务执行速度提升 ~60%（6个agents → 2个agents）
- Token消耗减少 ~70%
- 用户控制力增强
