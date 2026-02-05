# -*- coding: utf-8 -*-
"""
pytest 配置文件

提供通用 fixtures 和测试配置
"""

import pytest
import sys
import os
from pathlib import Path

# 将 src 目录添加到 Python 路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def project_root(tmp_path):
    """创建临时项目根目录"""
    return tmp_path


@pytest.fixture
def agents_dir(project_root):
    """创建 .claude/agents 目录结构"""
    agents_path = project_root / ".claude" / "agents"
    agents_path.mkdir(parents=True, exist_ok=True)

    # 创建最小化的 agent 配置文件
    agent_configs = {
        "01-arch.md": "# Architect\nrole: architect\n",
        "02-tech.md": "# Tech Lead\nrole: tech_lead\n",
        "03-dev.md": "# Developer\nrole: developer\n",
        "04-test.md": "# Tester\nrole: tester\n",
        "05-opti.md": "# Optimizer\nrole: optimizer\n",
        "06-secu.md": "# Security\nrole: security\n",
    }

    for filename, content in agent_configs.items():
        (agents_path / filename).write_text(content, encoding='utf-8')

    return agents_path


@pytest.fixture
def sample_plan_md(project_root):
    """创建示例 PLAN.md 文件"""
    plan_content = """# 实施计划

## 任务概述
测试任务

## 实施步骤
1. 步骤一
2. 步骤二

## 验收标准
- 通过所有测试
"""
    plan_file = project_root / "PLAN.md"
    plan_file.write_text(plan_content, encoding='utf-8')
    return plan_file


@pytest.fixture
def sample_stream_json():
    """示例 stream-json 输出"""
    return {
        "standard": '{"type": "result", "cost_usd": 0.05, "total_tokens": 1500}',
        "alternative": '{"cost": 0.03, "tokens": 1000}',
        "with_usage": '{"usage": {"input_tokens": 500, "output_tokens": 500}}',
        "multiline": '''{"type": "message", "content": "hello"}
{"type": "result", "cost_usd": 0.08, "total_tokens": 2000}''',
        "empty": "",
        "invalid": "not json at all",
    }
