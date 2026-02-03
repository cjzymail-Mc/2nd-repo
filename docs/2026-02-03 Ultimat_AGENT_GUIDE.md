# Multi-Agent 调度系统使用指南

## 快速开始

```bash
# 多 Agent 协作（推荐）
python orchestrator.py

# 单 Agent 任务
python agent-task.py
```

---

## orchestrator.py - 多 Agent 调度

### 模式一：自动规划

```
💬 有什么可以帮您？
> 帮我写一个用户登录模块

# 系统自动规划：architect → tech_lead → developer → tester + security
```

### 模式二：手动指定

```
💬 有什么可以帮您？
> @tech_lead 审核 src/main.py 的代码质量
```

#### 语法

| 语法 | 含义 | 示例 |
|------|------|------|
| `@agent 任务` | 单个 | `@tech_lead 审核代码` |
| `->` | 串行 | `@tech 审核 -> @dev 修复` |
| `&&` | 并行 | `@tester 测试 && @security 安检` |
| `()` | 分组 | `@tech -> (@dev && @sec) -> @test` |

#### 典型用例

```bash
# 代码审核 + 修复
@tech_lead 审核代码 -> @developer 根据建议修复

# 并行测试
@tester 功能测试 && @security 安全审计

# 完整流程
@tech 审核 -> (@dev 修复 && @sec 安检) -> @tester 回归测试
```

#### 别名

| Agent | 别名 |
|-------|------|
| `@architect` | `@arch`, `@架构` |
| `@tech_lead` | `@tech`, `@技术` |
| `@developer` | `@dev`, `@开发` |
| `@tester` | `@test`, `@测试` |
| `@optimizer` | `@opti`, `@优化` |
| `@security` | `@sec`, `@安全` |

---

## agent-task.py - 单 Agent 执行

```bash
python agent-task.py
```

```
💬 有什么可以帮您？
> @tech_lead 检查 src/main.py 的性能问题
> @dev 修复登录 bug -o fix_report.md
> @tester 测试新功能 --no-branch
```

### 默认输出文件

| Agent | 输出文件 |
|-------|----------|
| `@architect` | `PLAN.md` |
| `@tech_lead` | `advice.md` |
| `@developer` | `PROGRESS.md` |
| `@tester` | `BUG_REPORT.md` |
| `@optimizer` | `OPTIMIZATION.md` |
| `@security` | `SECURITY_AUDIT.md` |

---

## 使用场景

| 场景 | 推荐方式 |
|------|----------|
| 简单任务（改 bug、加功能） | 直接用 Claude Code |
| 需要特定 agent 意见 | `agent-task.py` 或 `orchestrator @agent` |
| 多 agent 协作 | `orchestrator.py` 手动指定 |
| 复杂新功能开发 | `orchestrator.py` 自动规划 |

---

## 常用命令

```bash
# 查看帮助
> help

# 查看可用 agent
> agents

# 查看/修改配置
> config
> config budget 20

# 恢复中断任务
> resume

# 退出
> exit
```
