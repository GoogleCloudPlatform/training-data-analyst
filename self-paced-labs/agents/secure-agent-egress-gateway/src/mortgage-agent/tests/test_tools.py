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

"""Tests for mortgage agent utility tools."""

from __future__ import annotations

from unittest import mock

from agent.tools import get_current_time, list_mcp_connections


class TestGetCurrentTime:
    def test_utc_default(self):
        result = get_current_time()
        assert result["timezone"] == "UTC"
        assert "datetime" in result
        assert result["utc_offset"] == "+0000"

    def test_valid_timezone(self):
        result = get_current_time("US/Eastern")
        assert result["timezone"] == "US/Eastern"
        assert "datetime" in result
        assert "utc_offset" in result

    def test_invalid_timezone_falls_back_to_utc(self):
        result = get_current_time("Not/A/Timezone")
        assert result["timezone"] == "UTC"
        assert "note" in result
        assert "Not/A/Timezone" in result["note"]


class TestListMcpConnections:
    _MOCK_DISCOVERED = [
        {
            "name": "legacy-dms",
            "tool_name_prefix": "dms_",
            "resolved_url": "https://dms.internal/mcp",
            "tools": ["search_documents", "get_document"],
        },
        {
            "name": "income-verification",
            "tool_name_prefix": "income_",
            "resolved_url": "https://income.internal/mcp",
            "tools": ["verify_income"],
        },
        {
            "name": "corporate-email",
            "tool_name_prefix": "email_",
            "resolved_url": "https://email.internal/mcp",
            "tools": ["list_messages", "get_message"],
        },
    ]

    def test_default_urls(self):
        from agent import agent as agent_module

        with mock.patch.object(agent_module, "DISCOVERED_MCP_SERVERS", self._MOCK_DISCOVERED):
            result = list_mcp_connections()
            assert result["count"] == 3
            connections = result["connections"]
            assert connections[0]["tool_name_prefix"] == "dms_"
            assert connections[1]["tool_name_prefix"] == "income_"
            assert connections[2]["tool_name_prefix"] == "email_"
            assert connections[0]["resolved_url"] == "https://dms.internal/mcp"

    def test_custom_discovered_servers(self):
        from agent import agent as agent_module

        custom_servers = [
            {
                "name": "custom-dms",
                "tool_name_prefix": "custom_dms_",
                "resolved_url": "https://custom-dms/mcp",
                "tools": ["get_custom"],
            }
        ]
        with mock.patch.object(agent_module, "DISCOVERED_MCP_SERVERS", custom_servers):
            result = list_mcp_connections()
            assert result["count"] == 1
            connections = result["connections"]
            assert connections[0]["name"] == "custom-dms"
            assert connections[0]["tool_name_prefix"] == "custom_dms_"
            assert connections[0]["resolved_url"] == "https://custom-dms/mcp"
