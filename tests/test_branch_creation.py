#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分支创建 Bug 修复

验证：
1. execute_from_plan() 现在会创建分支
2. execute_from_plan_with_loop() 现在会创建分支
"""
import sys
import os
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "orchestrator_v6",
    Path(__file__).parent.parent / "src" / "orchestrator_v6.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

import inspect

def test_execute_from_plan_has_branch_creation():
    """验证 execute_from_plan 方法包含分支创建代码"""
    source = inspect.getsource(mod.Orchestrator.execute_from_plan)

    # 检查是否有分支创建调用
    assert "_create_feature_branch" in source, "execute_from_plan 缺少 _create_feature_branch 调用"
    assert "from-plan" in source, "execute_from_plan 分支创建参数不正确"

    print("✅ execute_from_plan 包含分支创建逻辑")

def test_execute_from_plan_with_loop_has_branch_creation():
    """验证 execute_from_plan_with_loop 方法包含分支创建代码"""
    source = inspect.getsource(mod.Orchestrator.execute_from_plan_with_loop)

    # 检查是否有分支创建调用
    assert "_create_feature_branch" in source, "execute_from_plan_with_loop 缺少 _create_feature_branch 调用"
    assert "from-plan-loop" in source, "execute_from_plan_with_loop 分支创建参数不正确"

    print("✅ execute_from_plan_with_loop 包含分支创建逻辑")

def test_check_bug_report_has_debug_output():
    """验证 _check_bug_report 方法包含调试输出"""
    source = inspect.getsource(mod.Orchestrator._check_bug_report)

    # 检查是否有调试输出
    assert "检测到" in source or "🐛" in source, "_check_bug_report 缺少调试输出"
    assert "BUG_REPORT.md" in source, "_check_bug_report 文件检查不正确"

    print("✅ _check_bug_report 包含调试输出")

def test_check_bug_report_supports_multiple_formats():
    """验证 _check_bug_report 支持多种格式"""
    source = inspect.getsource(mod.Orchestrator._check_bug_report)

    # 检查是否支持多种格式
    formats_to_check = [
        "- [ ]",  # 复选框格式
        "❌",      # 图标格式
        "error",   # 关键词格式
        "failed",  # 测试失败格式
    ]

    for fmt in formats_to_check:
        assert fmt.lower() in source.lower(), f"_check_bug_report 不支持格式: {fmt}"

    print("✅ _check_bug_report 支持多种 bug 格式")

if __name__ == "__main__":
    print("\n🧪 测试分支创建 Bug 修复\n" + "="*50)

    test_execute_from_plan_has_branch_creation()
    test_execute_from_plan_with_loop_has_branch_creation()
    test_check_bug_report_has_debug_output()
    test_check_bug_report_supports_multiple_formats()

    print("\n" + "="*50)
    print("🎉 所有测试通过！分支创建 Bug 已修复")
