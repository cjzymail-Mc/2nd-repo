#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Architect 越权防护 Hook

当 Architect Agent 尝试修改非 .md 文件时，阻止操作。
检测方式：环境变量 ORCHESTRATOR_AGENT=architect 或锁文件

输出格式：符合 Claude Code PreToolUse hook 规范
- 阻止: exit code 2 + stderr 提示
- 放行: exit code 0
"""
import sys
import json
import os


def main():
    # 读取 Claude 传入的 JSON 数据
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # 无法解析，放行

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # 只检查 Write 和 Edit 工具
    if tool_name not in ["Write", "Edit"]:
        sys.exit(0)

    file_path = tool_input.get("file_path", "")

    # .md 文件始终放行
    if file_path.lower().endswith(".md"):
        sys.exit(0)

    # 检测当前是否是 architect agent
    is_architect = False

    # 方法1（最可靠）：检查环境变量
    if os.environ.get("ORCHESTRATOR_AGENT") == "architect":
        is_architect = True

    # 方法2（备用）：检查是否存在 architect 锁文件
    lock_file = os.path.join(".claude", "architect_active.lock")
    if os.path.exists(lock_file):
        is_architect = True

    if is_architect:
        # 使用 exit code 2 阻止 + stderr 输出原因
        msg = f"ARCHITECT GUARD: Blocked write to '{file_path}'. Architect can only write .md files."
        print(msg, file=sys.stderr)
        sys.exit(2)

    # 非 architect 阶段，放行
    sys.exit(0)


if __name__ == "__main__":
    main()
