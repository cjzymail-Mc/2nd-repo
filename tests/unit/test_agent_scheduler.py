# -*- coding: utf-8 -*-
"""
AgentScheduler 单元测试
"""

import pytest
from pathlib import Path


class TestAgentScheduler:
    """AgentScheduler 测试类"""

    def _get_classes(self):
        """动态导入并返回所需的类"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agents_module",
            Path(__file__).parent.parent.parent / "src" / "orchestrator_v6.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.AgentScheduler, module.TaskComplexity, module.AgentConfig

    def test_plan_simple_complexity(self):
        """测试简单任务规划"""
        AgentScheduler, TaskComplexity, _ = self._get_classes()
        scheduler = AgentScheduler()

        phases = scheduler.plan_execution(TaskComplexity.SIMPLE)

        # 简单任务应该有 3 个阶段
        assert len(phases) == 3
        assert phases[0] == ["architect"]
        assert phases[1] == ["developer"]
        assert phases[2] == ["tester"]

    def test_plan_moderate_complexity(self):
        """测试中等任务规划"""
        AgentScheduler, TaskComplexity, _ = self._get_classes()
        scheduler = AgentScheduler()

        phases = scheduler.plan_execution(TaskComplexity.MODERATE)

        # 中等任务应该有 3 个阶段
        assert len(phases) == 3
        assert phases[0] == ["architect"]
        assert phases[1] == ["developer"]
        assert phases[2] == ["tester", "security"]

    def test_plan_complex_complexity(self):
        """测试复杂任务规划"""
        AgentScheduler, TaskComplexity, _ = self._get_classes()
        scheduler = AgentScheduler()

        phases = scheduler.plan_execution(TaskComplexity.COMPLEX)

        # 复杂任务应该有 4 个阶段
        assert len(phases) == 4
        assert phases[0] == ["architect"]
        assert phases[1] == ["tech_lead"]
        assert phases[2] == ["developer"]
        assert phases[3] == ["tester", "security", "optimizer"]

    def test_get_agent_config(self):
        """测试获取 agent 配置"""
        AgentScheduler, _, AgentConfig = self._get_classes()
        scheduler = AgentScheduler()

        # 测试获取 architect 配置
        config = scheduler.get_agent_config("architect")
        assert config.name == "architect"
        assert config.role_file == ".claude/agents/01-arch.md"
        assert "PLAN.md" in config.output_files

        # 测试获取 developer 配置
        config = scheduler.get_agent_config("developer")
        assert config.name == "developer"
        assert config.role_file == ".claude/agents/03-dev.md"

        # 测试获取 security 配置
        config = scheduler.get_agent_config("security")
        assert config.name == "security"
        assert "SECURITY_AUDIT.md" in config.output_files

    def test_get_all_agent_names(self):
        """测试获取所有 agent 名称"""
        AgentScheduler, _, _ = self._get_classes()
        scheduler = AgentScheduler()

        names = scheduler.get_all_agent_names()

        # 应该有 6 个 agent
        assert len(names) == 6
        assert "architect" in names
        assert "tech_lead" in names
        assert "developer" in names
        assert "tester" in names
        assert "optimizer" in names
        assert "security" in names

    def test_agent_configs_have_required_fields(self):
        """测试所有 agent 配置都有必要字段"""
        AgentScheduler, _, _ = self._get_classes()
        scheduler = AgentScheduler()

        for name in scheduler.get_all_agent_names():
            config = scheduler.get_agent_config(name)
            assert hasattr(config, 'name')
            assert hasattr(config, 'role_file')
            assert hasattr(config, 'output_files')
            assert config.name == name
            assert config.role_file.startswith(".claude/agents/")

    def test_invalid_agent_name_raises_error(self):
        """测试获取无效 agent 名称应抛出 KeyError"""
        AgentScheduler, _, _ = self._get_classes()
        scheduler = AgentScheduler()

        with pytest.raises(KeyError):
            scheduler.get_agent_config("nonexistent_agent")
