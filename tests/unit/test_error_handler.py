# -*- coding: utf-8 -*-
"""
ErrorHandler 单元测试
"""

import pytest
import json
from pathlib import Path


class TestErrorHandler:
    """ErrorHandler 测试类"""

    def _get_classes(self, project_root):
        """动态导入并返回所需的类"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agents_module",
            Path(__file__).parent.parent.parent / "src" / "orchestrator_v6.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.ErrorHandler, module.ExecutionResult, module.AgentStatus

    def test_log_error_new_file(self, project_root):
        """测试首次记录错误（文件不存在）"""
        ErrorHandler, ExecutionResult, AgentStatus = self._get_classes(project_root)
        handler = ErrorHandler(project_root, max_retries=3)

        # 确保错误日志文件不存在
        if handler.error_log_file.exists():
            handler.error_log_file.unlink()

        # 创建一个失败的执行结果
        result = ExecutionResult(
            agent_name="test_agent",
            status=AgentStatus.FAILED,
            session_id="session-123",
            exit_code=1,
            duration=10.5,
            cost=0.0,
            tokens=0,
            output_files=[],
            error_message="Test error message"
        )

        # 记录错误
        handler.log_error(result)

        # 验证文件已创建并包含正确内容
        assert handler.error_log_file.exists()
        with open(handler.error_log_file, 'r', encoding='utf-8') as f:
            errors = json.load(f)

        assert len(errors) == 1
        assert errors[0]["agent"] == "test_agent"
        assert errors[0]["exit_code"] == 1
        assert errors[0]["error_message"] == "Test error message"
        assert errors[0]["session_id"] == "session-123"

    def test_log_error_append(self, project_root):
        """测试追加错误记录"""
        ErrorHandler, ExecutionResult, AgentStatus = self._get_classes(project_root)
        handler = ErrorHandler(project_root, max_retries=3)

        # 先写入一个已有的错误记录
        handler.error_log_file.parent.mkdir(parents=True, exist_ok=True)
        existing_errors = [{"agent": "existing_agent", "error": "old error"}]
        with open(handler.error_log_file, 'w', encoding='utf-8') as f:
            json.dump(existing_errors, f)

        # 创建新的失败结果
        result = ExecutionResult(
            agent_name="new_agent",
            status=AgentStatus.FAILED,
            session_id="session-456",
            exit_code=2,
            duration=5.0,
            cost=0.0,
            tokens=0,
            output_files=[],
            error_message="New error"
        )

        # 记录新错误
        handler.log_error(result)

        # 验证追加成功
        with open(handler.error_log_file, 'r', encoding='utf-8') as f:
            errors = json.load(f)

        assert len(errors) == 2
        assert errors[0]["agent"] == "existing_agent"
        assert errors[1]["agent"] == "new_agent"

    def test_log_error_invalid_json(self, project_root):
        """测试处理损坏的 JSON 文件"""
        ErrorHandler, ExecutionResult, AgentStatus = self._get_classes(project_root)
        handler = ErrorHandler(project_root, max_retries=3)

        # 写入无效的 JSON 内容
        handler.error_log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(handler.error_log_file, 'w', encoding='utf-8') as f:
            f.write("this is not valid json {{{")

        # 创建失败结果
        result = ExecutionResult(
            agent_name="recovery_agent",
            status=AgentStatus.FAILED,
            session_id="session-789",
            exit_code=1,
            duration=1.0,
            cost=0.0,
            tokens=0,
            output_files=[],
            error_message="Error after corruption"
        )

        # 记录错误（不应抛出异常，应该重置为空列表）
        handler.log_error(result)

        # 验证文件已恢复为有效 JSON
        with open(handler.error_log_file, 'r', encoding='utf-8') as f:
            errors = json.load(f)

        # 应该只有新的错误记录（旧的无效数据被重置）
        assert len(errors) == 1
        assert errors[0]["agent"] == "recovery_agent"

    def test_error_log_file_location(self, project_root):
        """测试错误日志文件位置正确"""
        ErrorHandler, _, _ = self._get_classes(project_root)
        handler = ErrorHandler(project_root)

        expected_path = project_root / ".claude" / "error_log.json"
        assert handler.error_log_file == expected_path

    def test_max_retries_setting(self, project_root):
        """测试最大重试次数设置"""
        ErrorHandler, _, _ = self._get_classes(project_root)

        handler = ErrorHandler(project_root, max_retries=5)
        assert handler.max_retries == 5

        handler2 = ErrorHandler(project_root, max_retries=1)
        assert handler2.max_retries == 1
