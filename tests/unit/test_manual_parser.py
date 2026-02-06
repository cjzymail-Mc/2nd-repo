# -*- coding: utf-8 -*-
"""
ManualTaskParser 单元测试

测试手动模式解析，包括：
- 中文别名识别
- @agent 语法解析
- 串行/并行任务解析
"""

import pytest
import sys
from pathlib import Path

# 确保能导入 src 模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestManualModeDetection:
    """测试手动模式检测"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前导入 ManualTaskParser"""
        # 动态导入避免模块级别错误
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "six_agents",
            Path(__file__).parent.parent.parent / "src" / "orchestrator_v6.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.ManualTaskParser = module.ManualTaskParser

    def test_detect_english_agent(self):
        """测试英文 @agent 识别"""
        parser = self.ManualTaskParser()
        assert parser.is_manual_mode("@architect 分析需求") is True
        assert parser.is_manual_mode("@developer fix bug") is True
        assert parser.is_manual_mode("@tech_lead review code") is True

    def test_detect_chinese_alias(self):
        """测试中文别名识别"""
        parser = self.ManualTaskParser()
        assert parser.is_manual_mode("@架构 分析需求") is True
        assert parser.is_manual_mode("@开发 修复bug") is True
        assert parser.is_manual_mode("@测试 编写测试") is True
        assert parser.is_manual_mode("@安全 检查漏洞") is True

    def test_no_agent_tag(self):
        """测试无 @agent 标记"""
        parser = self.ManualTaskParser()
        assert parser.is_manual_mode("帮我写一个网页游戏") is False
        assert parser.is_manual_mode("修复登录 bug") is False
        assert parser.is_manual_mode("architect 分析") is False  # 缺少 @


class TestAgentNameResolution:
    """测试 agent 名称解析"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前导入 ManualTaskParser"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "six_agents",
            Path(__file__).parent.parent.parent / "src" / "orchestrator_v6.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.ManualTaskParser = module.ManualTaskParser

    def test_full_names(self):
        """测试完整名称解析"""
        parser = self.ManualTaskParser()
        assert parser.resolve_agent_name("architect") == "architect"
        assert parser.resolve_agent_name("tech_lead") == "tech_lead"
        assert parser.resolve_agent_name("developer") == "developer"
        assert parser.resolve_agent_name("tester") == "tester"
        assert parser.resolve_agent_name("optimizer") == "optimizer"
        assert parser.resolve_agent_name("security") == "security"

    def test_english_aliases(self):
        """测试英文别名解析"""
        parser = self.ManualTaskParser()
        assert parser.resolve_agent_name("arch") == "architect"
        assert parser.resolve_agent_name("tech") == "tech_lead"
        assert parser.resolve_agent_name("dev") == "developer"
        assert parser.resolve_agent_name("test") == "tester"
        assert parser.resolve_agent_name("opti") == "optimizer"
        assert parser.resolve_agent_name("sec") == "security"

    def test_chinese_aliases(self):
        """测试中文别名解析"""
        parser = self.ManualTaskParser()
        assert parser.resolve_agent_name("架构") == "architect"
        assert parser.resolve_agent_name("技术") == "tech_lead"
        assert parser.resolve_agent_name("开发") == "developer"
        assert parser.resolve_agent_name("测试") == "tester"
        assert parser.resolve_agent_name("优化") == "optimizer"
        assert parser.resolve_agent_name("安全") == "security"

    def test_invalid_names(self):
        """测试无效名称"""
        parser = self.ManualTaskParser()
        assert parser.resolve_agent_name("unknown") is None
        assert parser.resolve_agent_name("hacker") is None
        assert parser.resolve_agent_name("不存在") is None


class TestTaskParsing:
    """测试任务解析"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前导入 ManualTaskParser"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "six_agents",
            Path(__file__).parent.parent.parent / "src" / "orchestrator_v6.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.ManualTaskParser = module.ManualTaskParser

    def test_single_task(self):
        """测试单个任务解析"""
        parser = self.ManualTaskParser()
        phases, success = parser.parse("@architect 分析代码结构")
        assert success is True
        assert len(phases) == 1
        assert phases[0] == [("architect", "分析代码结构")]

    def test_serial_tasks(self):
        """测试串行任务（->）解析"""
        parser = self.ManualTaskParser()
        phases, success = parser.parse("@tech_lead 审核 -> @developer 修复")
        assert success is True
        assert len(phases) == 2
        assert phases[0] == [("tech_lead", "审核")]
        assert phases[1] == [("developer", "修复")]

    def test_parallel_tasks(self):
        """测试并行任务（&&）解析"""
        parser = self.ManualTaskParser()
        phases, success = parser.parse("@tester 测试 && @security 安全检查")
        assert success is True
        assert len(phases) == 1
        assert len(phases[0]) == 2
        assert ("tester", "测试") in phases[0]
        assert ("security", "安全检查") in phases[0]

    def test_mixed_tasks(self):
        """测试混合模式解析"""
        parser = self.ManualTaskParser()
        phases, success = parser.parse("@tech 审核 -> (@dev 修复 && @test 测试)")
        assert success is True
        assert len(phases) == 2
        assert phases[0] == [("tech_lead", "审核")]
        assert len(phases[1]) == 2

    def test_chinese_alias_task(self):
        """测试使用中文别名的任务"""
        parser = self.ManualTaskParser()
        phases, success = parser.parse("@架构 分析 -> @开发 实现")
        assert success is True
        assert len(phases) == 2
        assert phases[0] == [("architect", "分析")]
        assert phases[1] == [("developer", "实现")]

    def test_invalid_agent(self):
        """测试无效 agent 名称"""
        parser = self.ManualTaskParser()
        phases, success = parser.parse("@unknown_agent 做事情")
        assert success is False
        assert phases == []

    def test_malformed_input(self):
        """测试格式错误的输入"""
        parser = self.ManualTaskParser()
        phases, success = parser.parse("architect 没有@符号")
        assert success is False
        assert phases == []
