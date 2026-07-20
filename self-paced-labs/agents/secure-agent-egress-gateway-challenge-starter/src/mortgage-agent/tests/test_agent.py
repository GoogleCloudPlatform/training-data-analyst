# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for mortgage agent error handling logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx

from agent import agent as agent_module
from agent.agent import (
    _discover_mcp_toolsets,
    _find_http_status_error,
    _handle_tool_error,
    _render_mcp_services_doc,
)


def _make_http_status_error(status_code: int) -> httpx.HTTPStatusError:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    return httpx.HTTPStatusError("error", request=MagicMock(), response=response)


class TestFindHttpStatusError:
    def test_direct_match(self):
        exc = _make_http_status_error(403)
        assert _find_http_status_error(exc, 403) is True

    def test_wrong_status_code(self):
        exc = _make_http_status_error(500)
        assert _find_http_status_error(exc, 403) is False

    def test_chained_via_cause(self):
        inner = _make_http_status_error(403)
        outer = RuntimeError("wrapper")
        outer.__cause__ = inner
        assert _find_http_status_error(outer, 403) is True

    def test_chained_via_context(self):
        inner = _make_http_status_error(403)
        outer = RuntimeError("wrapper")
        outer.__context__ = inner
        assert _find_http_status_error(outer, 403) is True

    def test_exception_group(self):
        inner = _make_http_status_error(403)
        group = BaseExceptionGroup("group", [RuntimeError("other"), inner])
        assert _find_http_status_error(group, 403) is True

    def test_no_match(self):
        exc = RuntimeError("unrelated")
        assert _find_http_status_error(exc, 403) is False

    def test_nested_exception_group(self):
        inner = _make_http_status_error(403)
        inner_group = BaseExceptionGroup("inner", [inner])
        outer_group = BaseExceptionGroup("outer", [inner_group])
        assert _find_http_status_error(outer_group, 403) is True


def _make_tool_context(state: dict | None = None) -> MagicMock:
    """ToolContext mock whose `.state` is a real dict so .get/__setitem__ work."""
    ctx = MagicMock()
    ctx.state = {} if state is None else state
    return ctx


class TestHandleToolError:
    def test_403_returns_block_message(self):
        tool = MagicMock()
        tool.name = "send_email"
        error = _make_http_status_error(403)
        result = _handle_tool_error(tool, {}, _make_tool_context(), error)
        assert result is not None
        assert "send_email" in result["error"]
        assert "authorization policies" in result["error"]
        # No retries: the very first 403 is the hard-stop message.
        assert "Do not call this tool again" in result["error"]

    def test_non_403_returns_none(self):
        tool = MagicMock()
        tool.name = "read_email"
        error = _make_http_status_error(500)
        result = _handle_tool_error(tool, {}, _make_tool_context(), error)
        assert result is None

    def test_non_http_error_returns_none(self):
        tool = MagicMock()
        tool.name = "read_email"
        error = RuntimeError("something broke")
        result = _handle_tool_error(tool, {}, _make_tool_context(), error)
        assert result is None

    def test_403_blocks_immediately_and_counts_attempts(self):
        tool = MagicMock()
        tool.name = "send_email"
        error = _make_http_status_error(403)
        ctx = _make_tool_context()

        first = _handle_tool_error(tool, {}, ctx, error)
        assert "Do not call this tool again" in first["error"]
        assert ctx.state["_denied_mcp_tools"]["send_email"] == 1

        second = _handle_tool_error(tool, {}, ctx, error)
        assert "Do not call this tool again" in second["error"]
        assert ctx.state["_denied_mcp_tools"]["send_email"] == 2

    def test_403_per_tool_counters_are_independent(self):
        tool_a = MagicMock()
        tool_a.name = "send_email"
        tool_b = MagicMock()
        tool_b.name = "read_email"
        error = _make_http_status_error(403)
        ctx = _make_tool_context()

        # Tool A is called twice; its counter is independent of tool B's.
        _handle_tool_error(tool_a, {}, ctx, error)
        _handle_tool_error(tool_a, {}, ctx, error)
        assert ctx.state["_denied_mcp_tools"]["send_email"] == 2

        # Tool B's first 403 blocks immediately with its own counter.
        result = _handle_tool_error(tool_b, {}, ctx, error)
        assert "Do not call this tool again" in result["error"]
        assert "authorization policies" in result["error"]
        assert ctx.state["_denied_mcp_tools"]["read_email"] == 1


class TestInstructionRendering:
    """The instruction must enumerate live registry tool names, not just prefixes,
    so the LLM has no room to invent plausible-but-wrong tool names."""

    _DISCOVERED = [
        {
            "name": "legacy-dms",
            "tool_name_prefix": "legacy_dms",
            "tools": ["search_documents", "get_document"],
        },
        {
            "name": "corporate-email",
            "tool_name_prefix": "corporate_email",
            "tools": ["list_messages", "get_message"],
        },
        {
            "name": "income-verification",
            "tool_name_prefix": "income_verification",
            "tools": ["verify_income"],
        },
    ]

    def test_render_includes_live_tool_names_and_descriptions(self):
        with patch.object(agent_module, "DISCOVERED_MCP_SERVERS", self._DISCOVERED):
            doc = _render_mcp_services_doc()
        # Concrete prefixed names appear.
        assert "`legacy_dms_search_documents`" in doc
        assert "`legacy_dms_get_document`" in doc
        assert "`corporate_email_list_messages`" in doc
        assert "`corporate_email_get_message`" in doc
        assert "`income_verification_verify_income`" in doc
        # The wildcard form must NOT appear when tools are known — that
        # wildcard is what gave the LLM rope to invent names.
        assert "`legacy_dms_*`" not in doc
        assert "`corporate_email_*`" not in doc
        assert "`income_verification_*`" not in doc
        # Descriptions for known services come through.
        assert "legacy document management system" in doc
        assert "corporate communications system" in doc
        assert "third-party income verification vendor" in doc

    def test_render_handles_empty_discovery(self):
        with patch.object(agent_module, "DISCOVERED_MCP_SERVERS", []):
            doc = _render_mcp_services_doc()
        assert "no MCP services discovered" in doc

    def test_render_handles_unknown_service_with_tools(self):
        with patch.object(
            agent_module,
            "DISCOVERED_MCP_SERVERS",
            [
                {
                    "name": "future-service",
                    "tool_name_prefix": "future_service",
                    "tools": ["do_thing"],
                }
            ],
        ):
            doc = _render_mcp_services_doc()
        assert "**future-service** (tools: `future_service_do_thing`)" in doc
        # No description prose appended for unknown services.
        assert "connects to" not in doc

    def test_render_falls_back_to_wildcard_when_tools_empty(self):
        with patch.object(
            agent_module,
            "DISCOVERED_MCP_SERVERS",
            [{"name": "future-service", "tool_name_prefix": "future_service", "tools": []}],
        ):
            doc = _render_mcp_services_doc()
        assert "**future-service** (tools prefixed `future_service_*`)" in doc

    def test_render_handles_service_with_no_tools_field(self):
        # An entry that has neither `tools` key set nor a populated list —
        # `entry.get("tools") or []` must coerce both to the same fallback.
        with patch.object(
            agent_module,
            "DISCOVERED_MCP_SERVERS",
            [{"name": "future-service", "tool_name_prefix": "future_service"}],
        ):
            doc = _render_mcp_services_doc()
        assert "**future-service** (tools prefixed `future_service_*`)" in doc

    def test_render_handles_service_with_no_prefix_and_no_tools(self):
        with patch.object(
            agent_module,
            "DISCOVERED_MCP_SERVERS",
            [{"name": "broken-service"}],
        ):
            doc = _render_mcp_services_doc()
        assert "**broken-service** (no tools advertised)" in doc

    def test_built_agent_instruction_contains_live_tool_names_and_guardrails(self):
        with (
            patch.object(agent_module, "_discover_mcp_toolsets", return_value=[]),
            patch.object(agent_module, "DISCOVERED_MCP_SERVERS", self._DISCOVERED),
        ):
            built = agent_module._build_agent()
        instruction = built.instruction
        # Concrete prefixed names present.
        assert "`legacy_dms_search_documents`" in instruction
        assert "`legacy_dms_get_document`" in instruction
        assert "`income_verification_verify_income`" in instruction
        # Wildcard form must NOT leak through when tools are known.
        assert "`legacy_dms_*`" not in instruction
        assert "`corporate_email_*`" not in instruction
        assert "`income_verification_*`" not in instruction
        # Anti-hallucination guardrails are in place.
        assert "Only call tools by the exact names listed below." in instruction
        assert "never use a colon (`:`)" in instruction
        assert "Never invent tool names." in instruction


class TestConnectionTimeoutNoMutation:
    """We rely on ADK's 5s default for fail-fast on denied calls; do not mutate it."""

    def test_discover_does_not_override_toolset_timeout(self, monkeypatch):
        monkeypatch.setenv("MCP_REGISTRY_PROJECT", "test-project")
        monkeypatch.setenv("MCP_REGISTRY_LOCATION", "us-central1")
        monkeypatch.delenv("MCP_REGISTRY_FILTER", raising=False)
        monkeypatch.delenv("MCP_REGISTRY_ENDPOINT", raising=False)

        conn_params = MagicMock()
        conn_params.timeout = 5.0  # ADK default
        conn_params.url = "https://x.example/mcp"

        toolset = MagicMock()
        toolset._connection_params = conn_params
        toolset.tool_name_prefix = "x"

        registry_instance = MagicMock()
        registry_instance.list_mcp_servers.return_value = {
            "mcpServers": [
                {
                    "name": "projects/p/locations/l/mcpServers/x",
                    "displayName": "x",
                    "tools": [{"name": "do_thing"}],
                }
            ]
        }
        registry_instance.get_mcp_toolset.return_value = toolset

        # Reset module-level cache so the discovery actually runs (other
        # tests in this file may have populated it via real or mocked calls).
        agent_module._CACHED_TOOLSETS = None
        agent_module._CACHED_DISCOVERED = None

        with patch(
            "google.adk.integrations.agent_registry.AgentRegistry",
            return_value=registry_instance,
        ):
            result = _discover_mcp_toolsets()

        assert result == [toolset]
        assert conn_params.timeout == 5.0
        # Unprefixed tool names from the registry payload land in
        # DISCOVERED_MCP_SERVERS so the instruction renderer can enumerate
        # exact names (preventing hallucination).
        assert agent_module.DISCOVERED_MCP_SERVERS[0]["tools"] == ["do_thing"]
