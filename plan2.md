# orchestrator_v6.py 全场景测试计划

## 任务目标

对 `src/orchestrator_v6.py` 多Agent调度系统进行全场景测试，遍历所有入口模式，验证核心功能正常。

> 注：文件已从 `6-agents.py` 改名为 `orchestrator_v6.py`，符合 Python 模块命名规范。

---

## 程序入口菜单

```
选择执行模式：
  1. 半自动模式 - 进入 Claude CLI 讨论需求，生成 PLAN.md 后自动执行
  2. 从 PLAN.md 继续 - 跳过 Architect，直接从现有计划执行
  3. 全自动模式 - 输入任务后，Architect 自动规划并执行全流程
  4. （ADV）多agent模式 - 可同时指派多名 Agents
  5. 退出
```

---

## 测试场景清单

### 场景1: 模式3 + 简单任务 + 1轮

**测试命令**：
```bash
python src/orchestrator_v6.py
# 选择: 3 (全自动模式)
# 迭代轮数: 1
# 任务复杂度: 1 (简单任务 - 2个agents)
# 输入: "在 src/ 目录下创建 hello.py，输出 Hello World"
```

**验证点**：
- [ ] 自动创建 feature 分支（如 `feature/dev-001`）
- [ ] 只执行 developer + tester（2个agents）
- [ ] 生成 claude-progressXX.md 进度文件
- [ ] hello.py 正确生成并可运行

---

### 场景2: 模式3 + 复杂任务 + 2轮循环

**测试命令**：
```bash
python src/orchestrator_v6.py
# 选择: 3 (全自动模式)
# 迭代轮数: 2
# 任务复杂度: 2 (复杂任务 - 6个agents)
# 输入: "创建一个简单的计算器程序，支持加减乘除"
```

**验证点**：
- [ ] 自动创建 feature 分支
- [ ] 执行全部6个agents（architect → tech_lead → developer → tester → optimizer → security）
- [ ] 如果 tester 发现 bug，进入第2轮 developer-tester 循环
- [ ] 显示 BUG_REPORT.md 检测结果（调试输出）
- [ ] 生成进度文件记录所有 agent 工作

---

### 场景3: 模式2 + 从 PLAN.md 继续

**前置条件**：确保根目录存在 `PLAN.md` 文件

**测试命令**：
```bash
python src/orchestrator_v6.py
# 选择: 2 (从 PLAN.md 继续)
# 迭代轮数: 1
# 任务复杂度: 任意（会被忽略）
```

**验证点**：
- [ ] 正确检测并读取 PLAN.md
- [ ] 自动创建 feature 分支（修复后应生成 `feature/tech-001`）
- [ ] 跳过 architect，从 tech_lead 开始执行
- [ ] 后续 agents 正常执行

---

### 场景4: 模式1 + 半自动模式

**测试命令**：
```bash
python src/orchestrator_v6.py
# 选择: 1 (半自动模式)
# 迭代轮数: 1
# 任务复杂度: 任意（会被忽略，显示提示）
```

**验证点**：
- [ ] 显示 "复杂度设置将被忽略" 提示
- [ ] 正确进入 Claude CLI 会话
- [ ] architect 生成 PLAN.md 到项目根目录（不是 ~/.claude/plans/）
- [ ] 退出 CLI 后，显示两阶段确认（编辑/执行）
- [ ] 确认后自动执行后续 agents

---

### 场景5: 模式4 + 多Agent并行

**测试命令**：
```bash
python src/orchestrator_v6.py
# 选择: 4 (多agent模式)
# 输入: @developer 创建 add.py && @tester 测试 add.py
```

**验证点**：
- [ ] 正确解析 @agent 语法
- [ ] 并行 agents 创建独立子分支（如 `feature/dev-001-developer-abc123`）
- [ ] 完成后自动合并子分支
- [ ] 冲突时保留分支并提示用户

---

### 场景6: 模式4 + 支持 .md 文件

**前置条件**：创建测试任务文件

```bash
echo "请创建一个简单的问候函数" > task-dev.md
echo "请为问候函数编写测试" > task-test.md
```

**测试命令**：
```bash
python src/orchestrator_v6.py
# 选择: 4 (多agent模式)
# 输入: @developer task-dev.md && @tester task-test.md
```

**验证点**：
- [ ] 正确读取 .md 文件内容作为任务描述
- [ ] 显示 "📄 @developer: 从 task-dev.md 读取任务描述"
- [ ] 两个 agent 正常执行

---

### 场景7: --resume 恢复中断任务

**测试命令**：
```bash
# 先启动一个任务，中途 Ctrl+C 中断
python src/orchestrator_v6.py
# 选择: 3，开始执行后 Ctrl+C

# 然后恢复
python src/orchestrator_v6.py --resume
```

**验证点**：
- [ ] 正确加载 .claude/agent_state.json
- [ ] 跳过已完成的 agents
- [ ] 从中断点继续执行
- [ ] 不创建新分支（使用原有分支）

---

## 🚨 重点测试：高风险 Bug（按优先级排序）

### P0 - 必须验证（可能导致功能失效）

| # | Bug 描述 | 风险 | 验证方法 |
|---|---------|------|---------|
| 1 | **Tester 不生成 BUG_REPORT.md** | 循环提前终止，无法继续迭代 | 设置2轮循环，检查是否进入第2轮 |
| 2 | **循环检测格式不匹配** | tester 生成了 bug 报告但未被识别 | 检查调试输出 "🐛 检测到 X 个未解决的 bug" |
| 3 | **Architect 越权执行代码** | Plan Mode 下跳过防护，直接修改源码 | 模式1测试，检查 architect 是否只生成 .md |

### P1 - 重要验证（影响用户体验）

| # | Bug 描述 | 风险 | 验证方法 |
|---|---------|------|---------|
| 4 | **progress.md 未被更新** | 用户无法了解 agent 工作细节 | 检查文件内容是否有每个 agent 的记录 |
| 5 | **分支未创建（模式2）** | 改动直接在当前分支，无隔离 | 模式2执行后检查 `git branch` |
| 6 | **repo-scan-result.md 未自动加载** | 浪费 token 重复扫描代码库 | 检查 architect 是否使用该文件 |

### P2 - 一般验证

| # | Bug 描述 | 风险 | 验证方法 |
|---|---------|------|---------|
| 7 | **并行 agent 文件冲突** | 同时修改同一文件导致覆盖 | 模式4并行测试 |
| 8 | **恢复模式状态丢失** | --resume 无法正确恢复 | 中断后恢复测试 |

---

## 核心机制说明（测试时必须了解）

### 1. 多轮循环机制

设置 `max_rounds=3` 时的执行流程：

```
Round 1:
  developer 修复代码 → tester 测试
  ├── 发现 bug → 生成 BUG_REPORT.md → 继续 Round 2 ✅
  ├── 无 bug → 提前完成 ⏹️
  └── 无 BUG_REPORT.md（保底机制）→ 继续 Round 2 ✅

Round 2:
  developer 根据 BUG_REPORT.md 修复 → tester 再测试
  ├── 仍有 bug → 继续 Round 3
  └── 无 bug → 完成

Round 3:
  最后一轮修复 → 测试
  └── 达到最大轮数 → 显示剩余 bug 提示 → 进入 optimizer/security
```

**关键点**：
- 只有 `AgentStatus.FAILED`（进程崩溃）才会完全停止
- 发现 bug 不会停止，会继续下一轮
- 新增保底机制：第1轮无 BUG_REPORT.md 也会继续

### 2. 资源管理机制

| 资源 | 创建时机 | 数量 | 生命周期 |
|------|---------|------|---------|
| `claude-progressXX.md` | 任务开始 | 1个 | 所有 agent 共用，追加更新 |
| `feature/xxx-001` | 任务开始 | 1个 | 所有 round 共用 |
| `BUG_REPORT.md` | 每轮 tester | 每轮覆盖 | 上轮归档为 `BUG_REPORT_roundX.md` |

### 3. Architect 三重防护

| 层级 | 机制 | 生效范围 |
|------|------|---------|
| Prompt 层 | 追加权限限制到 prompt | 模式1/2/3 ✅ |
| 实时监控 | stream 检测到越权立即 kill | 模式1/2/3 ✅ |
| 后置回滚 | 校验 git diff，回滚非 .md 文件 | 模式1/2/3 ✅ |
| Hooks 防护 | `.claude/hooks/architect_guard.py` | Plan Mode ⚠️ |

**注意**：Plan Mode（直接运行 `claude` 命令）不经过 Orchestrator，只有 Hooks 防护生效。

---

## 已修复的 Bug（供参考）

| Bug | 描述 | 修复状态 |
|-----|------|---------|
| 分支创建 | 模式2/3 从 plan.md 开始时未创建分支 | ✅ 已修复 |
| 循环终止 | _check_bug_report() 检测格式过严，导致循环提前退出 | ✅ 已修复 |
| 循环保底 | 第1轮无 BUG_REPORT.md 时提前终止 | ✅ 已修复（新增保底机制） |
| 分支命名 | MINIMAL 复杂度下分支名错误（arch → dev） | ✅ 已修复 |
| 并行隔离 | 多 agent 并行时无子分支隔离 | ✅ 已修复 |
| PLAN.md 位置 | architect 保存到 ~/.claude/plans/ 而非项目根目录 | ✅ 已修复（通过 agent prompt） |
| Hooks 防护 | Plan Mode 下无越权拦截 | ✅ 已修复（新增 hooks 脚本） |

---

## 测试执行建议

### 第一优先级：验证 P0 Bug

1. **场景2（模式3 + 2轮循环）**：
   - 验证循环是否正常进入第2轮
   - 检查 BUG_REPORT.md 检测是否生效
   - 观察调试输出 "🐛 检测到 X 个未解决的 bug"

2. **场景4（模式1 半自动）**：
   - 验证 architect 是否只生成 .md 文件
   - 检查是否越权修改源码

### 第二优先级：验证 P1 Bug

3. **场景3（模式2 从 PLAN.md）**：
   - 验证分支是否被创建
   - 检查 progress.md 是否有内容

4. **任意场景执行后**：
   - 检查 `claude-progressXX.md` 是否记录了每个 agent 的工作

### 第三优先级：其他场景

5. 场景1、5、6、7 按顺序测试

---

## 测试完成标准

**必须通过**：
- [ ] P0 Bug #1: 2轮循环能正常进入第2轮
- [ ] P0 Bug #2: BUG_REPORT.md 能被正确识别
- [ ] P0 Bug #3: Architect 没有越权修改源码
- [ ] P1 Bug #5: 模式2 能创建 feature 分支

**应该通过**：
- [ ] 所有7个场景执行成功
- [ ] progress.md 有完整记录
- [ ] 无新 bug 引入

---

## 注意事项

- `mc-dir-v6.py` 是备份文件，不要修改
- 测试时注意 token 消耗，简单任务优先
- 如遇问题，检查 `.claude/agent_state.json` 状态文件
- 循环测试时，观察控制台输出的调试信息
