# -*- coding: utf-8 -*-
"""
stream-json 解析单元测试

测试 _parse_stream_json 方法的各种输入情况
"""

import pytest
import sys
from pathlib import Path

# 确保能导入 src 模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestStreamJsonParsing:
    """测试 stream-json 输出解析"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前导入 AgentExecutor"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "six_agents",
            Path(__file__).parent.parent.parent / "src" / "6-agents.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.AgentExecutor = module.AgentExecutor

    def test_standard_result_format(self):
        """测试标准 result 格式"""
        executor = self.AgentExecutor.__new__(self.AgentExecutor)
        stdout = '{"type": "result", "cost_usd": 0.05, "total_tokens": 1500}'
        cost, tokens = executor._parse_stream_json(stdout)
        assert cost == 0.05
        assert tokens == 1500

    def test_alternative_field_names(self):
        """测试替代字段名（cost, tokens）"""
        executor = self.AgentExecutor.__new__(self.AgentExecutor)
        stdout = '{"cost": 0.03, "tokens": 1000}'
        cost, tokens = executor._parse_stream_json(stdout)
        assert cost == 0.03
        assert tokens == 1000

    def test_usage_nested_format(self):
        """测试嵌套 usage 格式"""
        executor = self.AgentExecutor.__new__(self.AgentExecutor)
        stdout = '{"usage": {"input_tokens": 500, "output_tokens": 300}}'
        cost, tokens = executor._parse_stream_json(stdout)
        assert tokens == 800  # 500 + 300

    def test_usage_with_total_tokens(self):
        """测试 usage 中包含 total_tokens"""
        executor = self.AgentExecutor.__new__(self.AgentExecutor)
        stdout = '{"usage": {"total_tokens": 1200, "input_tokens": 500, "output_tokens": 700}}'
        cost, tokens = executor._parse_stream_json(stdout)
        assert tokens == 1200

    def test_multiline_output(self):
        """测试多行输出（应取最后有效结果）"""
        executor = self.AgentExecutor.__new__(self.AgentExecutor)
        stdout = '''{"type": "message", "content": "hello"}
{"type": "progress", "tokens": 500}
{"type": "result", "cost_usd": 0.08, "total_tokens": 2000}'''
        cost, tokens = executor._parse_stream_json(stdout)
        assert cost == 0.08
        assert tokens == 2000

    def test_empty_input(self):
        """测试空输入"""
        executor = self.AgentExecutor.__new__(self.AgentExecutor)
        cost, tokens = executor._parse_stream_json("")
        assert cost == 0.0
        assert tokens == 0

        cost, tokens = executor._parse_stream_json("   \n  ")
        assert cost == 0.0
        assert tokens == 0

    def test_invalid_json(self):
        """测试无效 JSON"""
        executor = self.AgentExecutor.__new__(self.AgentExecutor)
        cost, tokens = executor._parse_stream_json("not json at all")
        assert cost == 0.0
        assert tokens == 0

    def test_partial_json_lines(self):
        """测试部分无效 JSON 行"""
        executor = self.AgentExecutor.__new__(self.AgentExecutor)
        stdout = '''some random text
{"type": "result", "cost_usd": 0.1, "total_tokens": 3000}
more random text'''
        cost, tokens = executor._parse_stream_json(stdout)
        assert cost == 0.1
        assert tokens == 3000

    def test_zero_values(self):
        """测试零值情况"""
        executor = self.AgentExecutor.__new__(self.AgentExecutor)
        stdout = '{"cost_usd": 0, "total_tokens": 0}'
        cost, tokens = executor._parse_stream_json(stdout)
        assert cost == 0.0
        assert tokens == 0

    def test_mixed_field_formats(self):
        """测试混合字段格式"""
        executor = self.AgentExecutor.__new__(self.AgentExecutor)
        # cost_usd 优先于 cost
        stdout = '{"cost_usd": 0.05, "cost": 0.03, "tokens": 1000}'
        cost, tokens = executor._parse_stream_json(stdout)
        assert cost == 0.05
        assert tokens == 1000

    def test_verbose_mode(self):
        """测试详细模式（不应崩溃）"""
        executor = self.AgentExecutor.__new__(self.AgentExecutor)
        # 即使在 verbose 模式下，无效输入也不应崩溃
        cost, tokens = executor._parse_stream_json("invalid", verbose=True)
        assert cost == 0.0
        assert tokens == 0
