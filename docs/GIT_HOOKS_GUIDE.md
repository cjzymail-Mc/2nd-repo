# Git Hooks 使用指南

> 防止 AI Agent 在主分支直接提交，保护代码库安全

---

## 📋 问题背景

### 为什么需要 Git Hook？

虽然 `orchestrator.py` 和 `agent-task.py` 都会**自动创建分支**，但仍然存在以下风险：

| 风险场景 | 说明 | 后果 |
|---------|------|------|
| **直接用 CLI** | 用户绕过工具，直接运行 `claude -p "..."` | AI 可能在主分支提交 |
| **工具出 Bug** | 分支创建逻辑失败（网络/权限问题） | 意外污染主分支 |
| **误操作** | 用户修改了工具代码，破坏了分支逻辑 | 主分支被修改 |

### Hook 的作用：最后一道防线

```
用户操作
  ↓
工具（orchestrator / agent-task）
  ↓ 自动创建分支（第一道防线）
  ↓
AI Agent 执行任务
  ↓
尝试 git commit
  ↓
Git Hook 检查（第二道防线）
  ├─ AI 在主分支？ → ❌ 拒绝
  ├─ AI 在 feature 分支？ → ✅ 允许
  └─ 人类在主分支？ → ⚠️ 警告但允许
```

---

## 🚀 快速安装

### Windows

```bash
setup\install-hooks.bat
```

或从 setup 目录运行：
```bash
cd setup
install-hooks.bat
```

### Linux/Mac

```bash
chmod +x setup/install-hooks.sh
./setup/install-hooks.sh
```

或从 setup 目录运行：
```bash
cd setup
./install-hooks.sh
```

**优点**：无论从哪个目录运行，脚本都会自动找到项目根目录并正确安装。

### 验证安装

```bash
# 检查 hook 是否存在
ls -la .git/hooks/pre-commit

# 应该看到可执行文件
```

---

## 🔍 工作原理

### 检测逻辑

Hook 通过**环境变量**区分 AI 和人类：

| 操作者 | 环境变量 | Hook 行为 |
|-------|---------|----------|
| **orchestrator.py** | `ORCHESTRATOR_RUNNING=true` | 在主分支 → ❌ 拒绝 |
| **agent-task.py** | `AGENT_TASK=true` | 在主分支 → ❌ 拒绝 |
| **人类** | 无 | 在主分支 → ⚠️ 警告 |

### 代码实现

```bash
# .git/hooks/pre-commit

# 检查是否在主分支
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" = "main" ]; then

    # 检查是否是 AI Agent
    if [ -n "$AGENT_TASK" ] || [ -n "$ORCHESTRATOR_RUNNING" ]; then
        echo "❌ AI Agent 不允许在主分支提交"
        exit 1  # 拒绝提交
    fi

    # 人类提交 → 警告
    read -p "确定在主分支提交吗？(y/N) "
    # ...
fi
```

---

## 🧪 测试 Hook

### 测试 1：AI 在主分支提交（应该被拒绝）

```bash
# 切换到主分支
git checkout main

# 模拟 AI 操作
export AGENT_TASK=true

# 尝试提交
echo "test" > test.txt
git add test.txt
git commit -m "test"

# 预期结果：
# ❌ 错误：AI Agent 不允许在主分支直接提交
```

### 测试 2：AI 在 feature 分支提交（应该成功）

```bash
# 创建分支
git checkout -b feature/test

# 模拟 AI 操作
export AGENT_TASK=true

# 提交
git commit -m "test"

# 预期结果：✅ 提交成功
```

### 测试 3：人类在主分支提交（警告但允许）

```bash
# 切换到主分支
git checkout main

# 清除环境变量（模拟人类）
unset AGENT_TASK
unset ORCHESTRATOR_RUNNING

# 提交
git commit -m "test"

# 预期结果：
# ⚠️ 警告：你正在主分支上提交
# 确定要在主分支提交吗？(y/N)
```

---

## 📊 是否必须安装？

### 我的建议：**推荐但不强制**

| 场景 | 是否需要 Hook？ |
|------|----------------|
| **个人项目** | 可选（工具已有分支保护） |
| **团队协作** | **推荐**（防止他人误操作） |
| **生产环境** | **强烈推荐**（安全第一） |
| **学习/测试** | 可选 |

### 优缺点分析

**优点**：
- ✅ 最后一道防线，防止意外
- ✅ 对人类友好（只警告不拒绝）
- ✅ 轻量级，几乎无性能影响

**缺点**：
- ⚠️ 需要手动安装（每个仓库都要装）
- ⚠️ 依赖环境变量（可能被绕过）
- ⚠️ 如果卸载工具，hook 可能失效

---

## 🛠️ 高级配置

### 自定义保护分支

编辑 `.git/hooks/pre-commit`：

```bash
# 默认只保护 main 和 master
PROTECTED_BRANCHES=("main" "master")

# 添加更多分支
PROTECTED_BRANCHES=("main" "master" "production" "release")
```

### 完全禁止主分支提交

如果你想**完全禁止**在主分支提交（包括人类）：

```bash
# 修改 hook，移除"人类提交警告"部分
if [ "$BRANCH" = "main" ]; then
    echo "❌ 禁止在主分支直接提交（请使用 feature 分支）"
    exit 1
fi
```

### 与现有 Hook 集成

如果你已经有 pre-commit hook（比如 Husky、lint-staged）：

```bash
# .git/hooks/pre-commit

# 你现有的 hook 逻辑
npm run lint
pytest

# 追加 AI Agent 检查
if [ "$BRANCH" = "main" ] && [ -n "$AGENT_TASK" ]; then
    echo "❌ AI Agent 不允许在主分支提交"
    exit 1
fi
```

---

## 🔧 卸载 Hook

```bash
# 删除 hook
rm .git/hooks/pre-commit

# 或恢复备份
cp .git/hooks/pre-commit.backup.* .git/hooks/pre-commit
```

---

## ❓ 常见问题

### Q1: Hook 对正常开发有影响吗？

**A:** 几乎没有。只有在以下情况会触发：
- AI Agent 尝试在主分支提交 → 拒绝
- 人类在主分支提交 → 警告（可选择继续）
- 在 feature 分支 → 完全不影响

---

### Q2: Hook 会被 Git 同步吗？

**A:** **不会**。`.git/hooks/` 是本地目录，不会被 Git 跟踪。

每个开发者需要**手动安装**：
```bash
# 新克隆仓库后
git clone <repo>
cd <repo>
./setup-git-hooks.sh  # 或 .bat
```

**建议**：在 README.md 中提醒团队成员安装。

---

### Q3: 能否绕过 Hook？

**A:** 可以，使用 `--no-verify`：
```bash
git commit -m "紧急修复" --no-verify
```

这是 Git 的标准功能，用于**紧急情况**（不推荐日常使用）。

---

### Q4: Hook 失败了怎么办？

**A:** 检查以下几点：

1. **Hook 是否可执行？**
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

2. **是否在 Git Bash 中运行？**（Windows）
   - Hook 需要 bash 环境
   - CMD/PowerShell 不支持

3. **环境变量是否生效？**
   ```bash
   echo $AGENT_TASK  # 应该输出 true
   ```

---

### Q5: 为什么不直接在工具中禁止主分支操作？

**A:** 几个原因：

1. **Git 是真理来源**：Hook 是 Git 官方机制，更可靠
2. **防御深度**：工具可能出 bug，Hook 是兜底
3. **灵活性**：用户可以选择是否安装 Hook

---

## 📚 延伸阅读

- [Git Hooks 官方文档](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
- [Pre-commit Hook 最佳实践](https://pre-commit.com/)
- [AGENT_USAGE_GUIDE.md](../AGENT_USAGE_GUIDE.md) - Agent 使用指南

---

**总结**：

✅ **推荐安装**（特别是团队项目）
⚠️ **不强制**（个人项目可选）
🛡️ **安全第一**（防御大于进攻）

---

**最后更新**: 2026-02-03
**作者**: Claude Sonnet 4.5
