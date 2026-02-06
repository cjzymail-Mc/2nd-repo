# orchestrator_v6.py 测试执行指南

**目标**: 系统性验证 orchestrator_v6.py 的核心功能
**测试人员**: 用户（手动执行）或 Developer Agent（自动化执行）

---

## 🚀 快速开始

### 准备工作

1. **确认当前位置**
   ```bash
   pwd  # 应该在项目根目录
   ```

2. **检查环境**
   ```bash
   python --version  # 需要 Python 3.8+
   git status        # 确认无重要未提交改动
   ```

3. **备份当前工作**（可选）
   ```bash
   git stash push -m "测试前备份"
   ```

---

## 📋 测试执行清单

### ⚠️ 重要：测试前必读

- 每个场景测试前，确保在干净的 Git 状态
- 测试完成后，可以删除生成的测试分支和文件
- 记录所有输出到 TEST_REPORT.md
- 重点关注 P0 Bug 验证（场景2 和 场景4）

---

### 测试优先级

| 优先级 | 场景 | 预估时间 | Token 预算 | 备注 |
|--------|------|----------|------------|------|
| **P0** | 场景2 | 20-30分钟 | 50k-100k | **必须执行** - 验证循环机制 |
| **P0** | 场景4 | 15-20分钟 | 30k-50k | **必须执行** - 验证 Architect 权限 |
| **P1** | 场景3 | 10-15分钟 | 20k-40k | **推荐执行** - 验证分支创建 |
| P2 | 场景1 | 5-10分钟 | 10k-20k | 基础功能验证 |
| P2 | 场景5 | 10-15分钟 | 20k-40k | 高级特性 |
| P2 | 场景6 | 10-15分钟 | 20k-40k | 高级特性 |
| P2 | 场景7 | 15-20分钟 | 20k-40k | 高级特性 |

---

## 🧪 场景执行模板

### 通用执行流程

```bash
# 1. 检查当前状态
git status
git branch

# 2. 运行程序
python src/orchestrator_v6.py

# 3. 按提示输入（根据场景不同）
# 选择账户: mc (或直接回车)
# 选择模式: X
# 迭代轮数: X
# 任务复杂度: X
# 任务描述: ...

# 4. 观察输出并记录关键信息

# 5. 测试完成后检查生成的文件
ls -la claude-progress*.md
git branch
git diff

# 6. 清理（可选）
git checkout main
git branch -D feature/xxx-xxx  # 删除测试分支
```

---

## 🎯 场景详细步骤

### 场景1: 模式3 + 简单任务 + 1轮

**目的**: 验证基础功能和 MINIMAL 复杂度流程

**命令**:
```bash
python src/orchestrator_v6.py
```

**输入**:
```
账户: mc
模式: 3
轮数: 1
复杂度: 1
任务: 在 src/ 目录下创建 hello.py，输出 Hello World
```

**验证**:
```bash
# 检查分支
git branch | grep feature

# 检查进度文件
cat claude-progress*.md

# 测试生成的代码
python src/hello.py
```

**期望结果**:
- 创建了 feature/dev-XXX 分支
- 只执行了 developer 和 tester
- hello.py 正确输出 "Hello World"

---

### 场景2: 模式3 + 复杂任务 + 2轮循环 ⚠️ **P0 重点**

**目的**: 验证多轮 developer-tester 循环机制（P0 Bug #1 & #2）

**命令**:
```bash
python src/orchestrator_v6.py
```

**输入**:
```
账户: mc
模式: 3
轮数: 2
复杂度: 2
任务: 创建一个简单的计算器程序，支持加减乘除
```

**⚠️ 重点观察**:
1. 控制台是否输出 `🐛 检测到 X 个未解决的 bug`
2. Round 1 完成后是否自动进入 Round 2
3. tester 是否生成 BUG_REPORT.md

**验证**:
```bash
# 检查分支
git branch | grep feature

# 检查 bug 报告
cat BUG_REPORT.md  # 当前 bug 报告
cat BUG_REPORT_round1.md  # 第1轮归档

# 检查进度文件
cat claude-progress*.md | grep -i "round"
```

**期望结果**:
- 执行了全部 6 个 agents
- 第1轮生成 BUG_REPORT.md
- 自动进入第2轮修复
- BUG_REPORT_round1.md 存在

**如果失败**:
- 记录控制台输出（特别是 bug 检测部分）
- 检查 BUG_REPORT.md 格式
- 确认是否提前退出循环

---

### 场景3: 模式2 + 从 PLAN.md 继续 ⚠️ **P1 重点**

**目的**: 验证从现有计划继续执行，检查分支创建（P1 Bug #5）

**前置条件**: 确保 PLAN.md 存在

**命令**:
```bash
# 先检查 PLAN.md
cat PLAN.md

# 执行
python src/orchestrator_v6.py
```

**输入**:
```
账户: mc
模式: 2
轮数: 1
复杂度: (任意，会被忽略)
```

**⚠️ 重点观察**:
1. 是否显示 "从 PLAN.md 继续"
2. 是否创建新的 feature 分支
3. 是否跳过 architect

**验证**:
```bash
# 检查分支（最重要）
git branch --list "feature/tech-*"

# 检查是否跳过 architect
cat claude-progress*.md | grep -i architect
```

**期望结果**:
- 创建了 feature/tech-XXX 分支
- 跳过了 architect
- 从 tech_lead 开始执行

---

### 场景4: 模式1 + 半自动模式 ⚠️ **P0 重点**

**目的**: 验证 Architect 权限隔离（P0 Bug #3）

**命令**:
```bash
python src/orchestrator_v6.py
```

**输入**:
```
账户: mc
模式: 1
轮数: 1
复杂度: (任意，会被忽略)
```

**⚠️ 重点观察**:
1. 进入 Claude CLI 会话
2. 在 CLI 中讨论需求，让 architect 生成计划
3. 退出 CLI 后的确认流程
4. **Architect 是否只生成 .md 文件**

**验证步骤**:
```bash
# 1. Architect 完成后，立即检查改动
git diff --name-only

# 期望结果: 只应该有 PLAN.md 和 claude-progressXX.md
# 不应该有任何源码文件改动

# 2. 检查 PLAN.md 位置
ls -la PLAN.md  # 应该在项目根目录

# 3. 检查分支
git branch | grep feature/arch
```

**期望结果**:
- PLAN.md 在项目根目录（不是 ~/.claude/plans/）
- git diff 只显示 .md 文件改动
- 没有源码被修改

**如果失败**:
- 记录 git diff 输出
- 检查 architect 是否越权修改了源码
- 立即回滚: `git checkout .`

---

### 场景5: 模式4 + 多Agent并行

**目的**: 验证多 agent 并行执行和子分支隔离

**命令**:
```bash
python src/orchestrator_v6.py
```

**输入**:
```
账户: mc
模式: 4
任务: @developer 创建 add.py && @tester 测试 add.py
```

**验证**:
```bash
# 检查子分支
git branch --list "feature/*-developer-*"
git branch --list "feature/*-tester-*"

# 检查是否自动合并
git log --oneline -10
```

**期望结果**:
- 创建了独立子分支
- 完成后自动合并
- 子分支被删除

---

### 场景6: 模式4 + .md 文件支持

**目的**: 验证从文件读取任务描述

**前置条件**: task-dev.md 和 task-test.md 已创建

**命令**:
```bash
# 确认测试文件存在
cat task-dev.md
cat task-test.md

# 执行
python src/orchestrator_v6.py
```

**输入**:
```
账户: mc
模式: 4
任务: @developer task-dev.md && @tester task-test.md
```

**⚠️ 重点观察**:
控制台是否显示 `📄 @developer: 从 task-dev.md 读取任务描述`

**验证**:
```bash
# 检查是否读取了文件内容
cat claude-progress*.md | grep "task-dev.md"
```

---

### 场景7: --resume 恢复中断任务

**目的**: 验证任务恢复机制

**步骤1: 启动并中断**
```bash
python src/orchestrator_v6.py
# 选择: 模式3, 1轮, 复杂度2
# 等待 developer 开始执行后，按 Ctrl+C 中断
```

**步骤2: 恢复任务**
```bash
python src/orchestrator_v6.py --resume
```

**验证**:
```bash
# 检查状态文件
cat .claude/agent_state.json

# 确认使用原有分支（不创建新分支）
git branch
```

**期望结果**:
- 跳过已完成的 agents
- 从中断点继续
- 不创建新分支

---

## 📝 测试记录模板

每个场景测试完成后，在 TEST_REPORT.md 中填写：

```markdown
### 场景X: [场景名称]

**执行时间**: 2026-02-06 XX:XX
**状态**: ✅ 通过 / ❌ 失败

**验证清单**:
- [x] 验证点1
- [x] 验证点2
- [ ] 验证点3 - 失败原因：...

**关键输出**:
```
（粘贴控制台输出）
```

**发现的问题**:
1. [问题描述]
   - 复现步骤: ...
   - 期望结果: ...
   - 实际结果: ...

**生成的文件**:
- src/xxx.py
- claude-progressXX.md
- BUG_REPORT.md
```

---

## 🔧 常见问题处理

### 问题1: 程序卡住不动

**原因**: 可能在等待用户输入或 agent 执行时间较长

**解决**:
- 检查控制台提示
- 等待 2-3 分钟观察
- 如确实卡住，Ctrl+C 中断后用 --resume 恢复

### 问题2: 分支未创建

**检查**:
```bash
git branch -a
git log --oneline -5
```

**记录**:
- 将问题记录到 TEST_REPORT.md
- 截图控制台输出

### 问题3: Agent 执行失败

**处理**:
- 不要立即重试
- 记录完整错误信息
- 检查 .claude/agent_state.json
- 将错误记录到报告

### 问题4: Token 预算不足

**建议**:
- 优先完成 P0 场景（场景2 和 场景4）
- 推迟 P2 场景测试
- 使用更短的任务描述

---

## ✅ 测试完成标准

### 必须通过（P0）

- [ ] 场景2: 2轮循环能正常进入第2轮
- [ ] 场景2: BUG_REPORT.md 能被正确识别
- [ ] 场景4: Architect 没有越权修改源码

### 应该通过（P1）

- [ ] 场景3: 模式2 能创建 feature 分支
- [ ] 所有场景: progress.md 有完整记录

### 可选通过（P2）

- [ ] 场景1: 简单任务流程正常
- [ ] 场景5/6/7: 高级特性正常

---

## 📊 测试总结

测试完成后，在 TEST_REPORT.md 中填写：

1. **测试完成度**: X/7 场景通过
2. **P0 Bug 验证**: X/3 通过
3. **P1 Bug 验证**: X/2 通过
4. **发现的新问题**: 列表
5. **总结和建议**: ...

---

**Good luck! 🚀**
