# Claude 多账户配置指南

## 功能概述

6-agents.py 现在支持在多个 Claude Pro 账户之间切换，启动时会提示选择账户。

---

## 前置准备

### 1. 安装 Claude CLI 的多账户别名

```bash
# 为账户1 (mc) 创建别名
alias claude-mc='CLAUDE_CONFIG_DIR=~/.claude-mc claude'

# 为账户2 (xh) 创建别名
alias claude-xh='CLAUDE_CONFIG_DIR=~/.claude-xh claude'
```

**Windows PowerShell**:
```powershell
# 创建函数别名
function claude-mc { $env:CLAUDE_CONFIG_DIR="$HOME\.claude-mc"; claude @args }
function claude-xh { $env:CLAUDE_CONFIG_DIR="$HOME\.claude-xh"; claude @args }
```

### 2. 初始化账户配置

首次使用前，需要分别初始化两个账户：

```bash
# 初始化账户 mc
claude-mc

# 初始化账户 xh
claude-xh
```

按照提示登录对应的 Claude Pro 账户。

---

## 目录结构

初始化后，你的配置目录结构如下：

```
~/.claude-mc/          # 账户1配置
  ├── config.json
  └── ...

~/.claude-xh/          # 账户2配置
  ├── config.json
  └── ...
```

---

## 使用方式

### 启动 6-agents.py

```bash
python src/6-agents.py
```

### 选择账户

启动时会看到账户选择界面：

```
╔════════════════════════════════════════════════════════════╗
║       🔐 Claude 账户选择                                    ║
╚════════════════════════════════════════════════════════════╝

可用账户：
  mc - Claude Pro 账户 (mc)
  xh - Claude Pro 账户 (xh)

请选择账户 [mc/xh，直接回车=mc]:
```

输入 `mc` 或 `xh` 选择账户，直接回车默认选择 `mc`。

### 完整流程示例

```bash
$ python src/6-agents.py

🔐 Claude 账户选择
请选择账户 [mc/xh，直接回车=mc]: xh
✓ 已选择账户: xh
✓ 配置目录: C:\Users\xy24\.claude-xh

╔════════════════════════════════════════════════════════════╗
║       🚀 mc-dir - 多Agent智能调度系统                       ║
╚════════════════════════════════════════════════════════════╝

选择执行模式：
  1. 半自动模式（推荐）
  2. 从 PLAN.md 继续
  3. 全自动模式
  4. 传统交互模式
  5. 退出

请选择 [1/2/3/4/5]: 3
...
```

---

## 工作原理

### 环境变量机制

程序通过设置 `CLAUDE_CONFIG_DIR` 环境变量来切换账户：

```python
# 选择账户 mc
os.environ['CLAUDE_CONFIG_DIR'] = '~/.claude-mc'

# 所有后续的 claude CLI 调用都会使用这个配置目录
subprocess.run(['claude', ...], env=os.environ.copy())
```

### 继承机制

- `_select_account()` 在 main() 开始时执行
- 设置 `CLAUDE_CONFIG_DIR` 环境变量
- 所有子进程（包括6个agents）自动继承这个环境变量
- 无需修改每个 agent 的调用代码

---

## 配置文件

配置在 `src/6-agents.py` 的第30-35行：

```python
# Claude 账户配置目录
CLAUDE_CONFIG_DIRS = {
    'mc': os.path.expanduser('~/.claude-mc'),  # 账户1: mc
    'xh': os.path.expanduser('~/.claude-xh')   # 账户2: xh
}
```

### 添加更多账户

修改 `CLAUDE_CONFIG_DIRS` 字典：

```python
CLAUDE_CONFIG_DIRS = {
    'mc': os.path.expanduser('~/.claude-mc'),
    'xh': os.path.expanduser('~/.claude-xh'),
    'dev': os.path.expanduser('~/.claude-dev'),  # 新增账户
}
```

然后初始化：
```bash
alias claude-dev='CLAUDE_CONFIG_DIR=~/.claude-dev claude'
claude-dev
```

---

## 常见问题

### Q1: 提示"配置目录不存在"

**原因**: 账户未初始化

**解决**:
```bash
claude-mc  # 初始化 mc 账户
claude-xh  # 初始化 xh 账户
```

### Q2: 切换账户后仍在使用旧账户

**原因**: 环境变量未正确设置

**解决**: 重启 6-agents.py，重新选择账户

### Q3: 如何验证当前使用的账户？

运行 claude CLI 时会显示当前账户信息：
```bash
# 设置环境变量
export CLAUDE_CONFIG_DIR=~/.claude-mc
claude

# 会显示 mc 账户的配置
```

### Q4: 可以同时运行两个账户吗？

**可以**，在不同终端窗口分别启动：

**终端1**:
```bash
python src/6-agents.py
# 选择: mc
```

**终端2**:
```bash
python src/6-agents.py
# 选择: xh
```

---

## 最佳实践

1. **合理分配任务**
   - 账户1 (mc): 处理复杂任务
   - 账户2 (xh): 处理简单任务

2. **避免冲突**
   - 不要在同一个项目目录用不同账户同时执行任务
   - 可能导致 git 冲突和状态文件混乱

3. **监控用量**
   - 定期检查两个账户的 token 使用情况
   - 根据剩余额度选择账户

---

## 技术细节

### 修改的文件

| 文件 | 修改内容 |
|------|----------|
| src/6-agents.py | +37行（账户选择功能） |

### 修改位置

1. **第30-35行**: 添加 `CLAUDE_CONFIG_DIRS` 配置
2. **第2870-2907行**: 新增 `_select_account()` 函数
3. **第2912行**: main() 开始调用账户选择

### 代码量

- 新增代码: ~40行
- 修改代码: 0行
- 破坏性修改: 无

---

## 验证测试

```bash
# 语法检查
python -m py_compile src/6-agents.py

# 单元测试
pytest tests/ -v
# 结果: 61 passed ✅

# 功能测试
python src/6-agents.py
# 选择账户: mc
# 执行简单任务验证
```
