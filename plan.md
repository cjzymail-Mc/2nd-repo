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

---

## Tech Lead 审核

### 审核状态：✅ 通过（附带建议）

### 审核意见

**计划完整性：**
- ✅ 包含7个完整测试场景
- ✅ 列出了所有验证点
- ✅ 包含高风险 Bug 列表（按 P0/P1/P2 分类）
- ✅ 提供了核心机制说明和测试执行建议

**可执行性：**
- ✅ 每个场景有明确的命令步骤
- ✅ 验证点清晰可测量
- ✅ 提供了测试优先级指导

**潜在风险：**
1. 测试范围较大（7个场景），建议按优先级分批执行
2. 某些场景需要人工交互（如模式1需要 Claude CLI 会话）
3. 测试可能消耗较多 token，需要控制任务复杂度

**改进建议：**
- 建议先执行 P0 Bug 验证场景（场景2和场景4）
- 建议为每个场景预估测试时间（5-15分钟不等）
- 建议在测试前检查环境依赖（Python、Claude CLI、Git）

---

### 任务分解

根据 PLAN.md，本次任务的性质是「系统功能测试」，需要按场景逐一验证。作为 Tech Lead，我将测试任务按优先级分解如下：

#### 阶段 0：环境准备（前置检查）

- **Task 0.1**: 验证项目环境
  - 检查 `src/orchestrator_v6.py` 文件存在
  - 检查 Python 环境可用
  - 检查 Git 状态（当前分支、未提交的改动）

- **Task 0.2**: 准备测试资源
  - 备份当前 PLAN.md（如果用户需要）
  - 创建测试用的临时 .md 文件（用于场景6）

---

#### 阶段 1：P0 Bug 验证（最高优先级）

**P0 Bug #1 & #2: 循环机制验证（场景2）**

- **Task 1.1**: 执行场景2 - 模式3 + 复杂任务 + 2轮循环
  - 运行命令: `python src/orchestrator_v6.py`
  - 选择: 模式3，2轮，复杂度2
  - 任务: "创建一个简单的计算器程序，支持加减乘除"

- **Task 1.2**: 验证循环机制
  - 检查是否创建 feature 分支
  - 检查是否执行全部6个 agents
  - **重点**: 观察控制台输出 "🐛 检测到 X 个未解决的 bug"
  - **重点**: 验证是否进入第2轮 developer-tester 循环

- **Task 1.3**: 验证 BUG_REPORT.md
  - 检查 tester 是否生成 BUG_REPORT.md
  - 检查格式是否正确（能被 _check_bug_report() 识别）
  - 检查是否归档为 BUG_REPORT_round1.md

**P0 Bug #3: Architect 越权验证（场景4）**

- **Task 1.4**: 执行场景4 - 模式1 半自动模式
  - 运行命令: `python src/orchestrator_v6.py`
  - 选择: 模式1，1轮
  - 进入 Claude CLI 会话

- **Task 1.5**: 验证 Architect 权限隔离
  - **重点**: 检查 architect 是否只生成 .md 文件（PLAN.md）
  - 检查 PLAN.md 是否在项目根目录（不是 ~/.claude/plans/）
  - 使用 `git diff` 验证是否有源码改动
  - 验证退出 CLI 后的两阶段确认流程

---

#### 阶段 2：P1 Bug 验证（重要）

**P1 Bug #5: 分支创建验证（场景3）**

- **Task 2.1**: 确保 PLAN.md 存在（前置条件）

- **Task 2.2**: 执行场景3 - 模式2 从 PLAN.md 继续
  - 运行命令: `python src/orchestrator_v6.py`
  - 选择: 模式2，1轮

- **Task 2.3**: 验证分支和进度文件
  - **重点**: 使用 `git branch` 检查是否创建 feature/tech-XXX 分支
  - 检查是否跳过 architect，从 tech_lead 开始
  - 检查后续 agents 是否正常执行

**P1 Bug #4: 进度文件更新验证**

- **Task 2.4**: 检查 claude-progressXX.md
  - 验证文件是否存在
  - 验证是否包含每个 agent 的工作记录
  - 验证内容是否完整（时间戳、任务描述、执行结果）

---

#### 阶段 3：基础场景验证（常规优先级）

**场景1: 模式3 + 简单任务 + 1轮**

- **Task 3.1**: 执行场景1
  - 运行命令: `python src/orchestrator_v6.py`
  - 选择: 模式3，1轮，复杂度1（简单任务）
  - 任务: "在 src/ 目录下创建 hello.py，输出 Hello World"

- **Task 3.2**: 验证简单任务流程
  - 检查是否只执行 developer + tester（2个 agents）
  - 验证 hello.py 是否正确生成
  - 测试运行: `python src/hello.py`

---

#### 阶段 4：高级场景验证（可选）

**场景5: 模式4 + 多Agent并行**

- **Task 4.1**: 执行场景5
  - 运行命令: `python src/orchestrator_v6.py`
  - 选择: 模式4
  - 输入: `@developer 创建 add.py && @tester 测试 add.py`

- **Task 4.2**: 验证并行机制
  - 检查 @agent 语法解析是否正确
  - 检查是否创建独立子分支（feature/dev-001-developer-xxx）
  - 验证完成后是否自动合并子分支

**场景6: 模式4 + .md 文件支持**

- **Task 4.3**: 创建测试文件
  ```bash
  echo "请创建一个简单的问候函数" > task-dev.md
  echo "请为问候函数编写测试" > task-test.md
  ```

- **Task 4.4**: 执行场景6
  - 运行命令: `python src/orchestrator_v6.py`
  - 选择: 模式4
  - 输入: `@developer task-dev.md && @tester task-test.md`

- **Task 4.5**: 验证文件读取
  - 检查控制台是否显示 "📄 @developer: 从 task-dev.md 读取任务描述"
  - 验证两个 agent 是否正常执行

**场景7: --resume 恢复中断任务**

- **Task 4.6**: 执行中断测试
  - 启动场景3，执行到一半时 Ctrl+C 中断

- **Task 4.7**: 恢复任务
  - 运行命令: `python src/orchestrator_v6.py --resume`

- **Task 4.8**: 验证恢复机制
  - 检查是否加载 .claude/agent_state.json
  - 验证是否跳过已完成的 agents
  - 验证是否从中断点继续
  - 确认不创建新分支（使用原有分支）

---

#### 阶段 5：测试总结与报告

- **Task 5.1**: 汇总测试结果
  - 创建测试报告（建议命名为 TEST_REPORT.md）
  - 记录每个场景的通过/失败状态
  - 记录发现的新 bug（如果有）

- **Task 5.2**: 更新测试完成标准
  - 核对 "测试完成标准" 章节的 checklist
  - 标记已验证的项目

- **Task 5.3**: 更新进度文件
  - 在 claude-progress03.md 中记录完整测试过程
  - 包含测试时间、场景覆盖率、问题列表

---

### 执行建议

**推荐执行顺序：**
1. 阶段 0（环境准备）→ 2分钟
2. 阶段 1（P0 验证）→ 场景2 + 场景4 → 20-30分钟
3. 阶段 2（P1 验证）→ 场景3 → 10分钟
4. 阶段 3（基础场景）→ 场景1 → 5分钟
5. 阶段 4（高级场景）→ 场景5/6/7 → 可选，根据时间和 token 预算

**测试注意事项：**
- 每个场景测试前先检查当前 Git 状态
- 测试完一个场景后清理生成的文件（或切回主分支）
- 记录每个场景的实际执行时间和 token 消耗
- 如遇失败，立即记录错误信息和复现步骤

**Developer 执行提示：**
- 本次任务是「系统测试」，不需要编写新代码
- 主要工作是「运行命令 → 观察输出 → 验证结果 → 记录报告」
- 遇到失败时，不要立即修复代码，先完整记录问题现象
- 测试完成后，将结果汇总到 TEST_REPORT.md

---

**Tech Lead 签名**
- 审核时间: 2026-02-06
- 审核人: Tech Lead Agent
- 状态: ✅ 计划已审核通过，建议按阶段执行
