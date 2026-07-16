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

"""Utility tool functions for the mortgage assistant agent."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def get_current_time(timezone_name: str = "UTC") -> dict:
    """Return the current time in the specified timezone.

    Args:
        timezone_name: IANA timezone name (e.g. 'US/Eastern', 'Europe/London', 'UTC').

    Returns:
        Dictionary with the current time and timezone info.
    """
    try:
        tz = ZoneInfo(timezone_name)
        now = datetime.now(tz)
        return {
            "timezone": timezone_name,
            "datetime": now.isoformat(),
            "utc_offset": now.strftime("%z"),
        }
    except KeyError:
        now = datetime.now(timezone.utc)
        return {
            "timezone": "UTC",
            "datetime": now.isoformat(),
            "utc_offset": "+0000",
            "note": f"Unknown timezone '{timezone_name}', using UTC",
        }


def list_mcp_connections() -> dict:
    """List MCP servers discovered from the Agent Registry at startup.

    Returns:
        Dictionary with the list of discovered server descriptors and a count.
    """
    # Lazy import to avoid a circular dependency: agent.agent imports this module.
    from . import agent as _agent

    servers = list(_agent.DISCOVERED_MCP_SERVERS)
    return {"connections": servers, "count": len(servers)}
