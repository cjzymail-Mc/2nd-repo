# -*- coding: utf-8 -*-
"""
StateManager 单元测试
"""

import pytest
import json
from pathlib import Path


class TestStateManager:
    """StateManager 测试类"""

    def _get_state_manager(self, project_root):
        """动态导入并创建 StateManager 实例"""
        # 动态导入模块名中带数字的模块
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agents_module",
            Path(__file__).parent.parent.parent / "src" / "orchestrator_v6.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.StateManager(project_root)

    def test_save_and_load_state(self, project_root):
        """测试状态保存和加载"""
        state_manager = self._get_state_manager(project_root)

        test_state = {
            "task_id": "test-123",
            "user_request": "测试任务",
            "complexity": "simple",
            "current_phase": 2,
            "agents_status": {"architect": "completed"},
            "results": {},
            "total_cost": 0.05,
            "total_tokens": 1000
        }

        # 保存状态
        state_manager.save_state(test_state)

        # 加载状态
        loaded_state = state_manager.load_state()

        assert loaded_state is not None
        assert loaded_state["task_id"] == "test-123"
        assert loaded_state["user_request"] == "测试任务"
        assert loaded_state["current_phase"] == 2
        assert loaded_state["agents_status"]["architect"] == "completed"

    def test_load_nonexistent_state(self, project_root):
        """测试加载不存在的状态文件"""
        state_manager = self._get_state_manager(project_root)

        # 确保状态文件不存在
        state_file = project_root / ".claude" / "state.json"
        if state_file.exists():
            state_file.unlink()

        # 加载应返回 None
        loaded_state = state_manager.load_state()
        assert loaded_state is None

    def test_clear_state(self, project_root):
        """测试清除状态"""
        state_manager = self._get_state_manager(project_root)

        # 先保存一个状态
        test_state = {"task_id": "test-456"}
        state_manager.save_state(test_state)

        # 确认文件存在
        assert state_manager.state_file.exists()

        # 清除状态
        state_manager.clear_state()

        # 确认文件已删除
        assert not state_manager.state_file.exists()

    def test_clear_nonexistent_state(self, project_root):
        """测试清除不存在的状态（不应抛出异常）"""
        state_manager = self._get_state_manager(project_root)

        # 确保文件不存在
        if state_manager.state_file.exists():
            state_manager.state_file.unlink()

        # 清除应该不抛出异常
        state_manager.clear_state()  # 不应抛出异常

    def test_state_file_location(self, project_root):
        """测试状态文件位置正确"""
        state_manager = self._get_state_manager(project_root)

        expected_path = project_root / ".claude" / "state.json"
        assert state_manager.state_file == expected_path

    def test_save_creates_directory(self, project_root):
        """测试保存时自动创建目录"""
        state_manager = self._get_state_manager(project_root)

        # 确保 .claude 目录不存在
        claude_dir = project_root / ".claude"
        if claude_dir.exists():
            import shutil
            shutil.rmtree(claude_dir)

        # 保存状态应该自动创建目录
        state_manager.save_state({"task_id": "test"})

        assert claude_dir.exists()
        assert state_manager.state_file.exists()
