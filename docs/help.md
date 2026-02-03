# Orchestrator.py 使用手册

> 星型拓扑多Agent并发调度系统 - 自动化调度6个AI专家协同完成复杂任务

---

## 📖 目录

- [快速开始](#快速开始)
- [工作原理](#工作原理)
- [工作流程](#工作流程)
- [输出文件说明](#输出文件说明)
- [使用示例](#使用示例)
- [完整参数列表](#完整参数列表)
- [注意事项](#注意事项)
- [常见问题](#常见问题)

---

## 🚀 快速开始

### 基础用法

```bash
# 最简单的用法（architect 交互式规划）
python orchestrator.py "你的需求描述"

# 例如
python orchestrator.py "帮我写一个待办事项管理应用"
```

### 完整命令格式

```bash
python orchestrator.py "<需求描述>" [选项]
```

---

## 🏗️ 工作原理

### 架构设计：星型拓扑 + 流水线混合

```
                    Orchestrator (中心调度器)
                           |
    ┌──────────────────────┼──────────────────────┐
    ↓                      ↓                      ↓
Phase 1: Architect    Phase 2: Tech Lead    Phase 3: Developer
    |                      |                      |
    └─→ PLAN.md ←─────────┘                      |
                                                  ↓
                                         Phase 4: 并行执行
                                     ┌────────┬────────┬────────┐
                                  Tester  Security  Optimizer
                                     ↓        ↓         ↓
                              BUG_REPORT SECURITY_  优化后
                                  .md    AUDIT.md   的代码
```

### 6个AI专家团队

| Agent | 角色 | 职责 | 输出文件 |
|-------|------|------|---------|
| **Architect** 🏛️ | 系统架构师 | 制定技术方案和架构设计 | `PLAN.md` |
| **Tech Lead** 👔 | 技术负责人 | 审查架构、细化技术选型 | 更新 `PLAN.md` |
| **Developer** 💻 | 开发工程师 | 编写代码实现功能 | `PROGRESS.md` + 代码文件 |
| **Tester** 🧪 | 测试工程师 | 编写测试、发现缺陷 | `BUG_REPORT.md` + 测试代码 |
| **Security** 🔒 | 安全专家 | 安全审计、漏洞检测 | `SECURITY_AUDIT.md` |
| **Optimizer** ⚡ | 优化专家 | 性能优化、代码质量提升 | 优化后的代码 |

### 智能任务分配

Orchestrator 根据任务复杂度自动选择执行策略：

| 复杂度 | 关键词示例 | 执行阶段 | Agents数量 |
|--------|-----------|---------|-----------|
| **SIMPLE** | "修复bug"、"添加日志" | 3阶段 | 3个 (architect → developer → tester) |
| **MODERATE** | "添加功能"、"重构模块" | 3阶段 | 4个 (+ security) |
| **COMPLEX** | "游戏"、"系统"、"架构" | 4阶段 | 6个 (全部) |

---

## 🔄 工作流程

### 完整执行流程（以复杂任务为例）

```
用户输入需求
    ↓
┌─────────────────────────────────────────────┐
│ Phase 0: 任务解析                            │
│ - 评估复杂度 (SIMPLE/MODERATE/COMPLEX)       │
│ - 规划执行阶段                               │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Phase 1: Architect (交互式) 🎯               │
│ - 启动交互式会话                             │
│ - 你可以反复讨论计划                         │
│ - 生成 PLAN.md                               │
│ - 等待你确认并退出会话                       │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Phase 2: Tech Lead (自动) ⚙️                 │
│ - 读取 PLAN.md                               │
│ - 审查技术选型                               │
│ - 细化实施方案                               │
│ - 更新 PLAN.md                               │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Phase 3: Developer (自动) ⚙️                 │
│ - 读取 PLAN.md                               │
│ - 编写代码实现功能                           │
│ - 更新 PROGRESS.md                           │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Phase 4: 并行执行 (自动) ⚡⚡⚡                │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│ │ Tester  │ │Security │ │Optimizer│        │
│ │测试代码 │ │安全审计 │ │性能优化 │        │
│ └─────────┘ └─────────┘ └─────────┘        │
│     ↓            ↓            ↓             │
│ BUG_REPORT  SECURITY_   优化后代码          │
│    .md       AUDIT.md                       │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ 执行完成 - 显示汇总报告                      │
│ - 总耗时、总成本、总tokens                   │
│ - 各Agent执行结果                            │
│ - 生成的文件列表                             │
└─────────────────────────────────────────────┘
```

### 执行模式说明

#### 1. 交互式模式（默认用于 Architect）

```
💡 系统架构师 将在交互式模式下运行
   你可以反复讨论计划，直到满意后退出会话

[启动 Claude Code 会话...]

你: 这个任务需要什么技术栈？
Architect: 建议使用 React + Node.js + MongoDB...
你: 能详细说说为什么选择 MongoDB？
Architect: MongoDB 的文档型数据库更适合...
你: 好的，请生成完整的 PLAN.md
Architect: [生成 PLAN.md...]
你: exit  # 或者 Ctrl+D 退出

[会话结束，自动继续执行后续 agents...]
```

#### 2. 自动模式（用于其他 Agents）

```
============================================================
Phase 3: developer
============================================================
  [启动] 开发工程师 (session: ghi11223...)
  ✅ 开发工程师 - completed (耗时 125.3s, $1.4567)
      → 输出: PROGRESS.md
```

### 失败重试机制

```
如果某个 Agent 执行失败：
    ↓
重试 1/3 (等待 5秒)
    ↓
重试 2/3 (等待 10秒)
    ↓
重试 3/3 (等待 20秒)
    ↓
3次失败后 → 记录到 .claude/error_log.json
    ↓
终止流程，退出码非0
```

---

## 📂 输出文件说明

### 项目文件结构

执行后会在以下位置生成文件：

```
项目根目录/
├── PLAN.md                    # Architect/Tech Lead 生成的架构方案
├── PROGRESS.md                # Developer 生成的开发进度
├── BUG_REPORT.md             # Tester 生成的测试报告
├── SECURITY_AUDIT.md         # Security 生成的安全审计
├── src/                      # 代码文件（根据任务而定）
│   ├── main.py
│   ├── components/
│   └── ...
├── tests/                    # 测试文件
│   └── test_*.py
├── .claude/
│   ├── state.json            # 执行状态（可用于恢复）
│   ├── error_log.json        # 错误日志（失败时生成）
│   └── agents/               # Agent 配置文件（已存在）
│       ├── 01-arch.md
│       ├── 02-tech.md
│       └── ...
└── orchestrator.py           # 本调度器
```

### 关键文件详解

#### 1. PLAN.md - 技术方案文档

```markdown
# 项目技术方案

## 1. 需求分析
[Architect 分析用户需求...]

## 2. 技术选型
- 前端：React 18 + TypeScript
- 后端：Node.js + Express
- 数据库：MongoDB

## 3. 架构设计
[系统架构图...]

## 4. 实施步骤
1. 搭建项目脚手架
2. 实现核心功能
...
```

#### 2. PROGRESS.md - 开发进度

```markdown
# 开发进度

## ✅ 已完成
- [x] 项目初始化
- [x] 用户认证模块
- [x] 数据库连接

## 🚧 进行中
- [ ] 待办事项CRUD

## 📝 待办
- [ ] 前端界面
```

#### 3. BUG_REPORT.md - 测试报告

```markdown
# 测试报告

## 🐛 发现的问题
1. **严重**: 登录时未验证密码强度
2. **一般**: 列表排序功能异常

## ✅ 测试通过
- 用户注册
- 数据持久化
```

#### 4. .claude/state.json - 执行状态

```json
{
  "task_id": "uuid",
  "user_request": "帮我写一个待办事项应用",
  "complexity": "complex",
  "current_phase": 4,
  "agents_status": {
    "architect": "completed",
    "tech_lead": "completed",
    "developer": "completed",
    "tester": "completed",
    "security": "completed",
    "optimizer": "completed"
  },
  "total_cost": 5.23,
  "total_tokens": 248000
}
```

---

## 🎬 使用示例

### 示例 1: 复杂项目 - 网页游戏

```bash
python orchestrator.py "帮我写一个网页版的赛车游戏" --max-budget 20.0 --verbose
```

**执行过程：**

```
📋 用户需求: 帮我写一个网页版的赛车游戏
任务复杂度: complex
执行计划: 4 个阶段

============================================================
Phase 1: architect
============================================================
💡 系统架构师 将在交互式模式下运行
   你可以反复讨论计划，直到满意后退出会话
   如需跳过交互，下次运行时添加 --auto-architect 参数

[Claude Code 交互式会话]
你: 游戏需要哪些功能？
Architect: 建议包含赛道渲染、物理引擎、碰撞检测、计分系统...
你: 用什么技术实现3D效果？
Architect: 推荐 Three.js + WebGL，性能更好...
你: 好的，生成详细计划
Architect: [生成 PLAN.md，包含完整技术栈和架构设计]
你: exit

============================================================
Phase 2: tech_lead
============================================================
  [启动] 技术负责人 (session: def67890...)
  ✅ 技术负责人 - completed (耗时 28.3s, $0.1521)

============================================================
Phase 3: developer
============================================================
  [启动] 开发工程师 (session: ghi11223...)
  ✅ 开发工程师 - completed (耗时 245.7s, $3.2341)
      → 输出: PROGRESS.md

============================================================
Phase 4: tester, security, optimizer
============================================================
  [启动] 测试工程师 (session: jkl44556...)
  [启动] 安全专家 (session: mno77889...)
  [启动] 优化专家 (session: pqr00112...)
  ✅ 测试工程师 - completed (耗时 67.2s, $0.5123)
      → 输出: BUG_REPORT.md
  ✅ 安全专家 - completed (耗时 52.1s, $0.3890)
      → 输出: SECURITY_AUDIT.md
  ✅ 优化专家 - completed (耗时 78.4s, $0.6234)

============================================================
执行完成 - 总耗时 471.7s
============================================================
总成本: $4.9109
总tokens: 245000

Agent 执行结果:
  ✅ architect    - completed  (耗时 0.0s, $0.0000)
      → 输出: PLAN.md
  ✅ tech_lead    - completed  (耗时 28.3s, $0.1521)
  ✅ developer    - completed  (耗时 245.7s, $3.2341)
      → 输出: PROGRESS.md
  ✅ tester       - completed  (耗时 67.2s, $0.5123)
      → 输出: BUG_REPORT.md
  ✅ security     - completed  (耗时 52.1s, $0.3890)
      → 输出: SECURITY_AUDIT.md
  ✅ optimizer    - completed  (耗时 78.4s, $0.6234)
```

**生成的文件：**
```
项目根目录/
├── PLAN.md              # 游戏架构设计
├── PROGRESS.md          # 开发进度
├── BUG_REPORT.md        # 测试报告
├── SECURITY_AUDIT.md    # 安全审计
├── game/
│   ├── index.html       # 游戏入口
│   ├── main.js          # 游戏主逻辑
│   ├── physics.js       # 物理引擎
│   ├── renderer.js      # 渲染引擎
│   └── assets/          # 游戏资源
└── tests/
    └── test_game.js     # 游戏测试
```

---

### 示例 2: 简单任务 - 修复Bug

```bash
python orchestrator.py "修复src/main.py中的登录bug"
```

**执行过程：**

```
📋 用户需求: 修复src/main.py中的登录bug
任务复杂度: simple
执行计划: 3 个阶段

============================================================
Phase 1: architect
============================================================
💡 系统架构师 将在交互式模式下运行
   你可以反复讨论计划，直到满意后退出会话

[交互式会话]
你: 先看看这个bug是什么
Architect: [读取 src/main.py，分析问题...]
         发现登录验证逻辑有误，密码比对使用了 == 而非安全的哈希比对
你: 对，就是这个问题，给出修复方案
Architect: [生成 PLAN.md，包含修复步骤]
你: exit

============================================================
Phase 2: developer
============================================================
  [启动] 开发工程师 (session: abc12345...)
  ✅ 开发工程师 - completed (耗时 18.5s, $0.0823)
      → 输出: PROGRESS.md

============================================================
Phase 3: tester
============================================================
  [启动] 测试工程师 (session: def67890...)
  ✅ 测试工程师 - completed (耗时 25.3s, $0.1234)
      → 输出: BUG_REPORT.md

============================================================
执行完成 - 总耗时 43.8s
============================================================
总成本: $0.2057
总tokens: 10200
```

---

### 示例 3: 完全自动化执行

```bash
python orchestrator.py "添加用户注册功能" --auto-architect --max-budget 5.0
```

**执行过程：**

```
📋 用户需求: 添加用户注册功能
任务复杂度: moderate
执行计划: 3 个阶段

============================================================
Phase 1: architect
============================================================
  [启动] 系统架构师 (session: abc12345...)
  ✅ 系统架构师 - completed (耗时 32.1s, $0.2134)
      → 输出: PLAN.md

============================================================
Phase 2: developer
============================================================
  [启动] 开发工程师 (session: def67890...)
  ✅ 开发工程师 - completed (耗时 95.7s, $0.9823)
      → 输出: PROGRESS.md

============================================================
Phase 3: tester, security
============================================================
  [启动] 测试工程师 (session: ghi11223...)
  [启动] 安全专家 (session: jkl44556...)
  ✅ 测试工程师 - completed (耗时 42.3s, $0.3456)
  ✅ 安全专家 - completed (耗时 38.9s, $0.2890)

============================================================
执行完成 - 总耗时 209.0s
============================================================
总成本: $1.8303
```

---

### 示例 4: 失败重试演示

```bash
python orchestrator.py "复杂任务" --max-budget 0.01  # 故意设置极低预算
```

**执行过程：**

```
============================================================
Phase 1: architect
============================================================
  [启动] 系统架构师 (session: abc12345...)
  ❌ 系统架构师 - failed (耗时 5.2s, $0.0100)
      错误: Budget exceeded: 0.01 USD

  [重试] architect 失败，5秒后重试（1/3）
  [启动] 系统架构师 (session: def67890...)
  ❌ 系统架构师 - failed (耗时 5.1s, $0.0100)

  [重试] architect 失败，10秒后重试（2/3）
  [启动] 系统架构师 (session: ghi11223...)
  ❌ 系统架构师 - failed (耗时 5.0s, $0.0100)

❌ architect 执行失败，终止流程

[错误已记录到 .claude/error_log.json]
```

**查看错误日志：**

```bash
cat .claude/error_log.json
```

```json
[
  {
    "timestamp": "2026-02-03T14:30:00",
    "agent": "architect",
    "exit_code": 1,
    "error_message": "Budget exceeded: 0.01 USD",
    "retry_count": 3,
    "session_id": "ghi11223"
  }
]
```

---

### 示例 5: 恢复中断任务

```bash
# 第一次执行（假设在 Phase 3 时用户按了 Ctrl+C）
python orchestrator.py "写一个博客系统"

# [Phase 1 和 Phase 2 已完成，Phase 3 进行中...]
# ^C  # 用户中断

# 稍后恢复执行
python orchestrator.py --resume
```

**执行过程：**

```
📂 恢复任务: 写一个博客系统

[读取 .claude/state.json...]
任务复杂度: complex
当前进度: Phase 2 已完成

============================================================
Phase 3: developer
============================================================
  [启动] 开发工程师 (session: new_session...)
  ...
```

---

## 📋 完整参数列表

### 位置参数

| 参数 | 说明 | 必需 | 示例 |
|------|------|------|------|
| `request` | 用户需求描述 | 是（除非使用 `--resume`） | `"帮我写一个计算器"` |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--max-budget` | float | 10.0 | **最大预算（USD）**<br>单个agent的最大成本限制<br>超过此值会失败并重试 |
| `--max-retries` | int | 3 | **最大重试次数**<br>agent失败后自动重试的次数<br>间隔：5s/10s/20s |
| `--verbose` | flag | False | **详细日志输出**<br>显示更多调试信息<br>包括agent内部执行细节 |
| `--auto-architect` | flag | False | **跳过交互式规划**<br>architect阶段也使用自动模式<br>适合需求明确的简单任务 |
| `--resume` | flag | False | **恢复中断任务**<br>从上次保存的状态继续执行<br>读取 `.claude/state.json` |

### 参数详解

#### --max-budget （预算控制）

```bash
# 小任务，限制成本
python orchestrator.py "添加日志" --max-budget 2.0

# 大任务，提高预算
python orchestrator.py "重构整个系统" --max-budget 50.0
```

**工作原理：**
- 每个agent启动时传入 `--max-budget-usd` 参数
- 如果某个agent超出预算，会失败并触发重试
- 总成本 = 所有agents成本之和（可能超出单agent预算）

**何时调整：**
- 如果看到 `Budget exceeded` 错误，增加预算
- 复杂任务建议 20-50 USD
- 简单任务 2-5 USD 足够

#### --max-retries （重试控制）

```bash
# 增加重试次数（网络不稳定时）
python orchestrator.py "任务" --max-retries 5

# 减少重试（快速失败）
python orchestrator.py "任务" --max-retries 1
```

**重试间隔：**
- 第1次重试：等待 5 秒
- 第2次重试：等待 10 秒
- 第3次重试：等待 20 秒
- 第N次重试：等待 20 秒（固定）

**何时调整：**
- 网络不稳定 → 增加重试次数
- 快速验证 → 减少重试次数

#### --verbose （详细日志）

```bash
python orchestrator.py "任务" --verbose
```

**输出对比：**

**普通模式：**
```
  ✅ developer - completed (耗时 125.3s, $1.4567)
```

**详细模式：**
```
  ✅ developer - completed (耗时 125.3s, $1.4567)
      Session ID: abc12345
      Tokens: 65432
      Exit code: 0
      Output files: ['PROGRESS.md', 'src/main.py']
```

**何时使用：**
- 调试问题时
- 需要详细成本统计
- 追踪特定会话

#### --auto-architect （自动规划）

```bash
# 默认行为：交互式规划
python orchestrator.py "写个游戏"
→ 启动交互式会话，你可以讨论计划

# 完全自动化
python orchestrator.py "写个游戏" --auto-architect
→ architect也在无头模式下自动运行
```

**对比：**

| 场景 | 交互式模式 | 自动模式 |
|------|-----------|---------|
| **适用任务** | 需求模糊、复杂项目 | 需求明确、简单任务 |
| **用户参与** | 可多轮讨论计划 | 无需参与 |
| **执行时间** | 取决于你的讨论时间 | 更快（无等待） |
| **计划质量** | 更贴合需求 | 依赖AI理解 |

**何时使用自动模式：**
- 需求已经非常明确
- 批量执行多个简单任务
- 在CI/CD流程中使用

#### --resume （恢复任务）

```bash
python orchestrator.py --resume
```

**恢复机制：**
1. 读取 `.claude/state.json`
2. 提取 `user_request` 和 `current_phase`
3. 从中断点继续执行

**限制：**
- 仅恢复最近一次任务
- 如果 state.json 被删除，无法恢复
- 恢复后会重新执行中断的phase（不是接续，而是重跑）

---

## ⚠️ 注意事项

### 1. 依赖要求

**Python 版本：**
- 需要 Python 3.8 或更高版本
- 使用了 `asyncio`、`pathlib` 等标准库

**Claude Code CLI：**
```bash
# 检查是否已安装
claude --version

# 应该输出类似：
# Claude Code CLI v1.x.x
```

如果未安装，请参考 [Claude Code 官方文档](https://docs.anthropic.com/claude-code)

### 2. Agent 配置文件

确保以下文件存在：

```
.claude/agents/
├── 01-arch.md      # Architect 配置
├── 02-tech.md      # Tech Lead 配置
├── 03-dev.md       # Developer 配置
├── 04-test.md      # Tester 配置
├── 05-opti.md      # Optimizer 配置
└── 06-secu.md      # Security 配置
```

如果缺失，orchestrator 会报错：
```
❌ architect 执行失败，终止流程
   错误: 角色配置文件不存在: .claude/agents/01-arch.md
```

### 3. 成本控制

**成本估算参考：**

| 任务类型 | 预估成本 | 建议预算 |
|---------|---------|---------|
| 简单bug修复 | $0.2 - $1 | 2 USD |
| 中等功能开发 | $2 - $5 | 10 USD |
| 复杂项目 | $10 - $30 | 50 USD |

**节省成本技巧：**
1. 使用 `--auto-architect` 跳过交互（减少等待时间成本）
2. 减少 `--max-retries`（避免重复失败）
3. 简单任务使用更低的 `--max-budget`

### 4. 文件冲突

**避免手动修改生成的文件：**
- orchestrator 运行时会覆盖 `PLAN.md`、`PROGRESS.md` 等
- 如需修改，建议在执行完成后进行
- 或者使用 git 管理，随时可以回退

### 5. 并发安全

**Phase 4 并行执行的文件安全：**
- Tester、Security、Optimizer 可能同时修改代码
- orchestrator 会让它们输出到不同文件（BUG_REPORT.md、SECURITY_AUDIT.md）
- 如果它们修改同一文件，可能出现冲突 → 需手动合并

### 6. 交互式会话注意事项

**在 architect 交互式阶段：**
- 必须确保生成了 `PLAN.md`，否则后续agents无法工作
- 不要直接关闭终端，使用 `exit` 或 `Ctrl+D` 正常退出
- 如果意外中断，使用 `--resume` 恢复

### 7. Windows 路径问题

**已处理：**
- orchestrator 使用 `pathlib.Path` 自动处理路径差异
- 支持 Windows、Linux、macOS

**如果遇到路径错误：**
- 检查是否使用了绝对路径（应使用相对路径）
- 检查路径中是否有特殊字符（如中文）

### 8. 超时设置

**默认超时：**
- 每个agent执行超时：600秒（10分钟）
- 如果任务特别复杂，可能超时

**解决方案：**
- 拆分复杂任务为多个简单任务
- 修改 `orchestrator.py` 中的 `timeout` 参数（需手动编辑代码）

---

## ❓ 常见问题

### Q1: 如何查看某个 agent 的详细日志？

**A:** 使用 `--verbose` 参数，或查看会话历史：

```bash
# 方法1：详细模式
python orchestrator.py "任务" --verbose

# 方法2：查看 Claude Code 会话历史
claude history
```

---

### Q2: architect 阶段我不想讨论，直接用默认方案可以吗？

**A:** 可以！进入交互式会话后，直接输入：

```
请直接生成 PLAN.md，无需讨论
```

然后退出会话即可。

或者使用 `--auto-architect` 完全跳过交互。

---

### Q3: 某个 agent 失败了，如何只重跑这一个？

**A:** orchestrator 目前不支持单独重跑某个phase。可以：

**方法1：手动运行**
```bash
cd 项目根目录
claude -p "$(cat .claude/agents/03-dev.md) 请按照 PLAN.md 继续开发"
```

**方法2：修改 state.json 后 `--resume`**（高级用法）
```bash
# 编辑 .claude/state.json，将 current_phase 改为失败的阶段号-1
# 然后运行
python orchestrator.py --resume
```

---

### Q4: 如何限制某个 agent 的执行时间？

**A:** 修改 `orchestrator.py` 中的 `timeout` 参数：

```python
# 找到 AgentExecutor.run_agent() 方法
async def run_agent(
    self,
    config: AgentConfig,
    task_prompt: str,
    timeout: int = 600  # 默认600秒，修改这里
):
```

或者在调用时动态指定（需修改代码支持）。

---

### Q5: 可以自定义 agent 吗？

**A:** 可以！步骤：

1. **创建新的 agent 配置：**
   ```bash
   # 创建 .claude/agents/07-custom.md
   ```

2. **修改 `AgentScheduler.AGENT_CONFIGS`：**
   ```python
   "custom": AgentConfig(
       name="custom",
       role_file=".claude/agents/07-custom.md",
       output_files=["CUSTOM_REPORT.md"]
   )
   ```

3. **修改执行计划：**
   ```python
   def plan_execution(self, complexity: TaskComplexity):
       return [
           ["architect"],
           ["developer"],
           ["custom"]  # 添加你的agent
       ]
   ```

---

### Q6: 执行完成后的文件在哪里？

**A:** 所有文件都在**项目根目录**下：

```bash
ls -la
# 应该看到：
# PLAN.md
# PROGRESS.md
# BUG_REPORT.md
# SECURITY_AUDIT.md
# src/  （代码文件）
# tests/  （测试文件）
```

如果没有生成，检查：
1. agent 是否执行成功（看执行结果）
2. 查看对应 agent 的 `output_files` 配置

---

### Q7: 成本比预期高，如何优化？

**A:** 优化策略：

1. **减少重试次数：**
   ```bash
   --max-retries 1
   ```

2. **使用 Haiku 模型（需修改代码）：**
   ```python
   # 在 AgentExecutor.run_agent() 中
   "--model", "haiku"  # 更便宜，适合简单任务
   ```

3. **跳过非必要 agents：**
   - 简单任务不需要 optimizer
   - 修改 `plan_execution()` 自定义执行计划

4. **使用 `--auto-architect`：**
   - 减少交互等待时间

---

### Q8: 如何在 CI/CD 中使用？

**A:** 完全自动化示例：

```yaml
# GitHub Actions 示例
name: Auto Development
on: [push]
jobs:
  develop:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code
      - name: Run Orchestrator
        run: |
          python orchestrator.py "实现新功能" \
            --auto-architect \
            --max-budget 10.0 \
            --max-retries 1
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

### Q9: 可以暂停执行吗？

**A:** 可以使用 `Ctrl+C` 中断，然后用 `--resume` 恢复。

但注意：
- 恢复时会**重新执行**当前phase（不是接续）
- 如果在交互式会话中中断，建议正常退出后再中断

---

### Q10: orchestrator 和直接用 claude -p 有什么区别？

**A:** 对比：

| 特性 | Orchestrator | `claude -p` |
|------|-------------|-------------|
| **多agent协同** | ✅ 自动调度6个experts | ❌ 单一会话 |
| **并发执行** | ✅ Phase 4并行 | ❌ 串行 |
| **失败重试** | ✅ 自动重试3次 | ❌ 手动重试 |
| **进度追踪** | ✅ state.json | ❌ 无状态 |
| **交互式规划** | ✅ architect阶段 | ✅ 所有阶段 |
| **适用场景** | 复杂项目、团队协作 | 简单任务、探索性工作 |

---

## 📚 延伸阅读

- **Claude Code 官方文档**: https://docs.anthropic.com/claude-code
- **Agent 配置规范**: `.claude/agents/README.md`（如果有）
- **CLAUDE.md 项目规范**: `.claude/CLAUDE.md`

---

## 🆘 获取帮助

如有问题，请：
1. 查看 `.claude/error_log.json` 错误日志
2. 使用 `--verbose` 重新运行获取详细信息
3. 检查 `.claude/state.json` 当前状态

---

**最后更新**: 2026-02-03
**版本**: Orchestrator v1.0
**作者**: Claude Sonnet 4.5
