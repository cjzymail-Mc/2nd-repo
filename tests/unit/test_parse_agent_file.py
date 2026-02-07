# -*- coding: utf-8 -*-
"""
AgentExecutor._parse_agent_file 单元测试
"""

import pytest
from pathlib import Path


class TestParseAgentFile:
    """_parse_agent_file 方法测试类"""

    def _get_executor(self, project_root):
        """动态导入并创建 AgentExecutor 实例"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agents_module",
            Path(__file__).parent.parent.parent / "src" / "orchestrator_v6.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.AgentExecutor(project_root)

    def test_standard_frontmatter(self, project_root):
        """测试标准 YAML frontmatter 解析"""
        executor = self._get_executor(project_root)

        content = """---
name: architect
model: sonnet
tools: Read, Write, Edit
---

# 系统架构师

你是一个资深的软件架构师。
"""
        metadata, body = executor._parse_agent_file(content)

        assert metadata.get("name") == "architect"
        assert metadata.get("model") == "sonnet"
        assert metadata.get("tools") == "Read, Write, Edit"
        assert "系统架构师" in body
        assert "---" not in body

    def test_no_frontmatter(self, project_root):
        """测试无 frontmatter 的文件"""
        executor = self._get_executor(project_root)

        content = """# 系统架构师

你是一个资深的软件架构师。

## 职责
- 分析需求
- 设计架构
"""
        metadata, body = executor._parse_agent_file(content)

        assert metadata == {}
        assert "系统架构师" in body
        assert "分析需求" in body

    def test_empty_frontmatter(self, project_root):
        """测试空 frontmatter"""
        executor = self._get_executor(project_root)

        content = """---
---

# 内容开始
这是正文内容。
"""
        metadata, body = executor._parse_agent_file(content)

        # 空 frontmatter 应该返回空字典
        assert metadata == {}
        assert "内容开始" in body

    def test_frontmatter_with_empty_values(self, project_root):
        """测试 frontmatter 中有空值"""
        executor = self._get_executor(project_root)

        content = """---
name: tester
model:
description:
---

# 测试工程师
"""
        metadata, body = executor._parse_agent_file(content)

        assert metadata.get("name") == "tester"
        assert "测试工程师" in body

    def test_frontmatter_with_chinese(self, project_root):
        """测试包含中文的 frontmatter"""
        executor = self._get_executor(project_root)

        content = """---
name: developer
description: 全栈开发工程师
model: sonnet
---

# 开发工程师

负责编写高质量代码。
"""
        metadata, body = executor._parse_agent_file(content)

        assert metadata.get("name") == "developer"
        assert metadata.get("description") == "全栈开发工程师"
        assert "开发工程师" in body

    def test_frontmatter_with_colons_in_value(self, project_root):
        """测试值中包含冒号"""
        executor = self._get_executor(project_root)

        content = """---
name: test
description: 时间格式: HH:MM:SS
---

正文内容
"""
        metadata, body = executor._parse_agent_file(content)

        assert metadata.get("name") == "test"
        # 只分割第一个冒号，后面的保留在值中
        assert "HH" in metadata.get("description", "")

    def test_multiline_body(self, project_root):
        """测试多行正文"""
        executor = self._get_executor(project_root)

        content = """---
name: agent
---

# 标题

第一段内容。

## 子标题

第二段内容。

- 列表项1
- 列表项2
"""
        metadata, body = executor._parse_agent_file(content)

        assert "标题" in body
        assert "子标题" in body
        assert "列表项1" in body
        assert "列表项2" in body

    def test_windows_line_endings(self, project_root):
        """测试 Windows 换行符 (CRLF)"""
        executor = self._get_executor(project_root)

        content = "---\r\nname: test\r\nmodel: sonnet\r\n---\r\n\r\n正文内容\r\n"
        metadata, body = executor._parse_agent_file(content)

        assert metadata.get("name") == "test"
        assert metadata.get("model") == "sonnet"
        assert "正文内容" in body

    def test_empty_content(self, project_root):
        """测试空内容"""
        executor = self._get_executor(project_root)

        metadata, body = executor._parse_agent_file("")

        assert metadata == {}
        assert body == ""

    def test_only_whitespace(self, project_root):
        """测试只有空白字符"""
        executor = self._get_executor(project_root)

        metadata, body = executor._parse_agent_file("   \n\n   \t  ")

        assert metadata == {}

    def test_frontmatter_with_comments(self, project_root):
        """测试 frontmatter 中的注释行"""
        executor = self._get_executor(project_root)

        content = """---
name: agent
# 这是注释
model: sonnet
---

正文
"""
        metadata, body = executor._parse_agent_file(content)

        # 注释行应该被忽略
        assert metadata.get("name") == "agent"
        assert metadata.get("model") == "sonnet"
        assert "这是注释" not in str(metadata)
