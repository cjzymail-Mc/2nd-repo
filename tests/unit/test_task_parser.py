# -*- coding: utf-8 -*-
"""
TaskParser 单元测试

测试自动模式下的任务解析和复杂度评估
"""

import pytest
import sys
from pathlib import Path

# 确保能导入 src 模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestTaskComplexityEvaluation:
    """测试任务复杂度评估"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """每个测试前导入 TaskParser"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "six_agents",
            Path(__file__).parent.parent.parent / "src" / "orchestrator_v6.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.TaskParser = module.TaskParser
        self.TaskComplexity = module.TaskComplexity
        self.project_root = tmp_path

    def test_complex_task_keywords(self):
        """测试复杂任务关键词识别"""
        parser = self.TaskParser(self.project_root)

        # 复杂任务关键词
        complex_inputs = [
            "帮我设计一个系统架构",
            "重构整个项目",
            "开发一个 webapp",
            "设计数据库结构",
            "创建一个网页游戏",
        ]

        for user_input in complex_inputs:
            _, complexity = parser.parse(user_input)
            assert complexity == self.TaskComplexity.COMPLEX, \
                f"'{user_input}' 应被识别为复杂任务"

    def test_simple_task_keywords(self):
        """测试简单任务关键词识别"""
        parser = self.TaskParser(self.project_root)

        simple_inputs = [
            "修复登录 bug",
            "fix typo in readme",
            "添加日志输出",
            "修复注释错误",
        ]

        for user_input in simple_inputs:
            _, complexity = parser.parse(user_input)
            assert complexity == self.TaskComplexity.SIMPLE, \
                f"'{user_input}' 应被识别为简单任务"

    def test_moderate_task_default(self):
        """测试中等复杂度任务（默认）"""
        parser = self.TaskParser(self.project_root)

        moderate_inputs = [
            "添加一个新功能",
            "优化代码性能",
            "编写单元测试",
        ]

        for user_input in moderate_inputs:
            _, complexity = parser.parse(user_input)
            assert complexity == self.TaskComplexity.MODERATE, \
                f"'{user_input}' 应被识别为中等复杂度任务"

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        parser = self.TaskParser(self.project_root)

        # 大写关键词
        _, complexity = parser.parse("修复 BUG")
        assert complexity == self.TaskComplexity.SIMPLE

        # 混合大小写
        _, complexity = parser.parse("创建 WebApp")
        assert complexity == self.TaskComplexity.COMPLEX

    def test_task_content_preserved(self):
        """测试任务内容保留"""
        parser = self.TaskParser(self.project_root)

        user_input = "帮我修复 src/main.py 中的登录 bug"
        task, _ = parser.parse(user_input)
        assert task == user_input


class TestTaskParserInitialization:
    """测试 TaskParser 初始化"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """每个测试前导入 TaskParser"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "six_agents",
            Path(__file__).parent.parent.parent / "src" / "orchestrator_v6.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.TaskParser = module.TaskParser
        self.project_root = tmp_path

    def test_initialization_with_path(self):
        """测试带路径初始化"""
        parser = self.TaskParser(self.project_root)
        assert parser.project_root == self.project_root

    def test_initialization_with_string_path(self):
        """测试字符串路径初始化"""
        parser = self.TaskParser(Path(str(self.project_root)))
        assert parser.project_root == self.project_root
