#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Architect 越权防护 Hook

当 Claude 在 Plan Mode 下尝试修改非 .md 文件时：
1. 输出警告信息
2. 返回错误状态，阻止修改

使用方式：配置在 .claude/settings.json 中的 preToolUse hook
"""
import sys
import json
import os

def main():
    # 读取 Claude 传入的 JSON 数据
    try:
        input_data = json.load(sys.stdin)
    except:
        # 如果无法解析，放行
        print(json.dumps({"continue": True}))
        return

    # 获取工具名称和参数
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # 只检查 Write 和 Edit 工具
    if tool_name not in ["Write", "Edit"]:
        print(json.dumps({"continue": True}))
        return

    # 获取文件路径
    file_path = tool_input.get("file_path", "")

    # 检查是否是 .md 文件
    if file_path.lower().endswith(".md"):
        # .md 文件，放行
        print(json.dumps({"continue": True}))
        return

    # 非 .md 文件，检查是否在 Plan Mode 下（通过环境变量或其他方式判断）
    # 目前简单处理：输出警告但放行（因为可能是其他 agent 在工作）
    # 如果要严格限制，可以改为返回 {"continue": False, "message": "..."}

    # 检查是否有 architect 标识（可以通过 session 文件或环境变量判断）
    # 这里我们通过检查进度文件来判断当前阶段
    progress_file = None
    for f in os.listdir("."):
        if f.startswith("claude-progress") and f.endswith(".md"):
            progress_file = f
            break

    # 如果找到进度文件，检查最后一个 agent 是谁
    current_agent = None
    if progress_file:
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                content = f.read()
                # 简单检查：如果最近记录是 Architect 且没有其他 agent 记录
                if "Architect" in content and "Developer" not in content and "Tech Lead" not in content:
                    current_agent = "architect"
        except:
            pass

    # 如果当前是 architect 阶段且尝试修改非 .md 文件
    if current_agent == "architect":
        warning = f"""
╔════════════════════════════════════════════════════════════╗
║ ⚠️  ARCHITECT 越权警告                                      ║
╠════════════════════════════════════════════════════════════╣
║ 你是 Architect Agent，只能写入 .md 文件！                   ║
║                                                            ║
║ 尝试修改: {file_path[:40]}...
║                                                            ║
║ ❌ 此操作将被阻止                                           ║
║ ✅ 请将代码修改任务交给 Developer Agent                     ║
╚════════════════════════════════════════════════════════════╝
"""
        print(warning, file=sys.stderr)
        print(json.dumps({
            "continue": False,
            "message": f"Architect 不能修改非 .md 文件: {file_path}"
        }))
        return

    # 其他情况放行
    print(json.dumps({"continue": True}))

if __name__ == "__main__":
    main()
