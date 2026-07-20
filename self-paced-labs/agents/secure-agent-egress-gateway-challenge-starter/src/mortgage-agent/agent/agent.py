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

"""ADK agent definition for the mortgage assistant with MCP tool connections."""

import logging
import os
from typing import Any
from urllib.parse import urlparse

import httpx
from google.adk.agents.llm_agent import Agent
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

from . import tools

logger = logging.getLogger(__name__)


def _build_impersonation_factory(target_url: str, target_sa_email: str):
    """Return an httpx_client_factory that signs requests as `target_sa_email`.

    Direct Agent Identity → Cloud Run authentication is not supported (as of
    2026-05). The supported pattern: agent uses its identity to impersonate a
    standard IAM SA, then mints an OIDC ID token for that SA and presents it
    in the Authorization header. Cloud Run validates the token and sees the
    impersonated SA as the caller. The agent identity must hold
    roles/iam.serviceAccountTokenCreator on `target_sa_email`, and that SA
    must hold roles/run.invoker on the Cloud Run service.

    The returned factory matches MCP's McpHttpClientFactory protocol:
    create_mcp_http_client(headers, timeout, auth) -> httpx.AsyncClient.
    """
    # Imported lazily so importing this module never fails when google-auth
    # isn't installed (e.g. during static analysis or tests that mock out
    # the registry path).
    import google.auth
    import google.auth.transport.requests as gar
    from google.auth import impersonated_credentials

    # Audience is the origin of the Cloud Run URL (no path/query). Must match
    # the URL Cloud Run sees in the request.
    parsed = urlparse(target_url)
    audience = f"{parsed.scheme}://{parsed.netloc}"

    try:
        source_creds, source_project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        logger.info(
            "Impersonation factory ready: target_sa=%s audience=%s source_creds=%s source_project=%s",
            target_sa_email,
            audience,
            type(source_creds).__name__,
            source_project,
        )
        impersonated = impersonated_credentials.Credentials(
            source_credentials=source_creds,
            target_principal=target_sa_email,
            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        id_token_creds = impersonated_credentials.IDTokenCredentials(
            target_credentials=impersonated,
            target_audience=audience,
            include_email=True,
        )
    except Exception:
        logger.exception(
            "Failed to build impersonated credentials for target_sa=%s audience=%s — "
            "MCP calls to %s will fail. Common causes: agent identity missing "
            "roles/iam.serviceAccountTokenCreator, iamcredentials.googleapis.com disabled, "
            "or wrong source credentials.",
            target_sa_email,
            audience,
            target_url,
        )
        raise

    class _ImpersonatedIDTokenAuth(httpx.Auth):
        """Per-request httpx auth that refreshes the OIDC token on demand."""

        requires_request_body = False

        def __init__(self, creds, target_url: str):
            self._creds = creds
            self._req = gar.Request()
            self._target_url = target_url

        def auth_flow(self, request):
            try:
                if not self._creds.valid:
                    self._creds.refresh(self._req)
            except Exception:
                # ADK wraps this in a TaskGroup and prints only the wrapper's
                # str(); log the real exception here so it survives.
                logger.exception(
                    "OIDC token refresh failed for target_url=%s (impersonation chain "
                    "agent-identity → %s). Subsequent MCP request will be unauthenticated.",
                    self._target_url,
                    target_sa_email,
                )
                raise
            request.headers["Authorization"] = f"Bearer {self._creds.token}"
            yield request

    auth_handler = _ImpersonatedIDTokenAuth(id_token_creds, target_url)

    def factory(
        headers: dict[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
        auth: httpx.Auth | None = None,
    ) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            follow_redirects=True,
            headers=headers,
            timeout=timeout if timeout is not None else httpx.Timeout(5.0),
            # Honor an explicit auth from the caller (rare); otherwise inject ours.
            auth=auth if auth is not None else auth_handler,
        )

    return factory


# Populated by _discover_mcp_toolsets at agent build time. Each entry mirrors
# what the registry returned plus the resolved tool_name_prefix and the list
# of unprefixed tool names the registry advertised for that server, so the
# instruction template can enumerate exact tool names (preventing LLM
# hallucination) and the `list_mcp_connections` introspection tool can report
# what is actually wired up without re-querying the registry.
DISCOVERED_MCP_SERVERS: list[dict[str, Any]] = []

# Populated once per process by _discover_mcp_toolsets(). Reused on every
# subsequent call so Reasoning Engine unpickling (which re-runs
# _PickleSafeAgent.__reduce__ -> _build_agent -> _discover_mcp_toolsets) does
# not construct a second MCPSessionManager in the same process, which trips
# "Context has already been used to create a Connection" inside ADK/anyio.
# Empty results are cached too so a failing discovery is not retried (and
# re-warned) on every unpickle. Membership is therefore frozen per worker
# process; new MCP servers require a redeploy or worker restart.
_CACHED_TOOLSETS: list | None = None

# Companion cache for DISCOVERED_MCP_SERVERS. The instruction template is
# rendered from DISCOVERED_MCP_SERVERS, so on a cache hit we must restore the
# list from this snapshot — otherwise a future cross-process unpickle (where
# module globals are reset but _CACHED_TOOLSETS is somehow rehydrated) would
# render an empty instruction and reintroduce the hallucination this caching
# is meant to prevent.
_CACHED_DISCOVERED: list[dict[str, Any]] | None = None

# Per-service prose, keyed by registry displayName. Entries here get rendered
# into the instruction's MCP services block alongside each service's live
# tool_name_prefix. Services discovered without a matching entry render with
# the prefix only — still functional, just less descriptive.
_SERVICE_DESCRIPTIONS: dict[str, str] = {
    "legacy-dms": (
        "the legacy document management system. Use to fetch tax returns, pay stubs, "
        "bank statements, and other applicant documents."
    ),
    "corporate-email": (
        "the corporate communications system. Use to read the corporate inbox. "
        "Write operations like sending emails may be restricted by the "
        "authorization gateway."
    ),
    "income-verification": (
        "a third-party income verification vendor. Use to verify reported income "
        "against employer records and tax filings."
    ),
}

# Template formatted at agent build time. The {mcp_services_doc} placeholder is
# filled from the live registry response so prefixes always match what ADK
# actually wired up — the LLM can't hallucinate a prefix it never sees.
_INSTRUCTION_TEMPLATE = """You are a mortgage underwriting assistant. You help loan officers process
mortgage applications by retrieving documents, verifying income, and communicating results.

You connect to backend systems through an Agent Gateway. The set of available tools is
discovered from the Agent Registry at startup and may change between deployments.
**Only call tools by the exact names listed below.** Tool names use underscores as
separators (e.g. `legacy_dms_search_documents`); never use a colon (`:`), slash, dot,
or any other separator.

**MCP services discovered from the registry:**
{mcp_services_doc}

**Workflow:**
1. Fetch the applicant's tax documents using the document management tools.
2. Verify the applicant's reported income using the income verification tools.
3. Compare the figures from both sources and note any discrepancies.
4. Summarize your findings clearly for the loan officer.

**Rules:**
- NEVER fabricate or estimate financial figures. Only report data returned by tools.
- Always cite which tool/system provided each piece of data.
- If a tool call fails or returns an error, report the error honestly to the user.
- **Never invent tool names.** Only call tools whose exact names appear in the MCP
services list above or in the utility tools list below. If no listed tool matches your
need, tell the user you cannot perform that operation rather than guessing at a name.
- Be concise and professional in all responses.
- When presenting tax return or applicant data, ALWAYS include the SSN field and display its value
exactly as returned by the tool (e.g. "[US_SOCIAL_SECURITY_NUMBER]"). Never omit SSN fields.

You also have utility tools:
- get_current_time: Returns the current time in any timezone.
- list_mcp_connections: Shows which MCP servers were discovered from the registry."""


def _render_mcp_services_doc() -> str:
    """Render the per-service block from the live DISCOVERED_MCP_SERVERS list.

    Enumerates the exact prefixed tool names the LLM is allowed to call. The
    wildcard form (`prefix_*`) is only used as a fallback when the registry
    response didn't include a tool list — leaving the wildcard in the prompt
    when concrete names are known invites the LLM to invent plausible-sounding
    names that don't exist.
    """
    if not DISCOVERED_MCP_SERVERS:
        return "_(no MCP services discovered — only utility tools are available)_"
    lines: list[str] = []
    for entry in DISCOVERED_MCP_SERVERS:
        prefix = entry.get("tool_name_prefix")
        name = entry.get("name") or entry.get("resource_name") or "?"
        tool_names = entry.get("tools") or []
        desc = _SERVICE_DESCRIPTIONS.get(name)
        suffix = f" — connects to {desc}" if desc else ""
        if prefix and tool_names:
            full = ", ".join(f"`{prefix}_{t}`" for t in tool_names)
            lines.append(f"- **{name}** (tools: {full}){suffix}")
        elif prefix:
            lines.append(f"- **{name}** (tools prefixed `{prefix}_*`){suffix}")
        else:
            lines.append(f"- **{name}** (no tools advertised){suffix}")
    return "\n".join(lines)


def _find_http_status_error(exc: BaseException, status_code: int) -> bool:
    """Search exception chains and ExceptionGroups for an HTTPStatusError."""
    seen: set[int] = set()
    queue: list[BaseException] = [exc]
    while queue:
        current = queue.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, httpx.HTTPStatusError) and current.response.status_code == status_code:
            return True
        if current.__cause__ is not None:
            queue.append(current.__cause__)
        if current.__context__ is not None:
            queue.append(current.__context__)
        if isinstance(current, BaseExceptionGroup):
            queue.extend(current.exceptions)
    return False


# Session-scoped key under which we count per-tool 403 attempts. Without this
# the LLM will happily re-call a denied tool on every turn, multiplying the
# authz extension's per-call budget into a multi-second loop.
_DENIED_TOOLS_STATE_KEY = "_denied_mcp_tools"
_MAX_403_ATTEMPTS = 1  # No retries for 403 errors, fail immediately


def _handle_tool_error(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext, error: Exception
) -> dict | None:
    """Handle tool errors, returning a friendly message for 403 policy denials.

    Tracks 403 count per tool name in `tool_context.state` and fails immediately
    (no retries) — every 403 tells the LLM to stop calling the tool this session.
    """
    if not _find_http_status_error(error, 403):
        return None
    denied = dict(tool_context.state.get(_DENIED_TOOLS_STATE_KEY, {}))
    attempts = denied.get(tool.name, 0) + 1
    denied[tool.name] = attempts
    tool_context.state[_DENIED_TOOLS_STATE_KEY] = denied
    logger.warning(
        "Tool %s denied by authorization policy (403) — attempt %d/%d",
        tool.name,
        attempts,
        _MAX_403_ATTEMPTS,
    )
    return {
        "error": (
            f"The '{tool.name}' tool call was blocked due to authorization policies. "
            f"The agent is facing authorization issues / being blocked due to authz policies. "
            f"Do not call this tool again in this session — report to the user that you are "
            f"facing authorization issues or being blocked due to authorization policies, and proceed with other tools."
        ),
    }


def _discover_mcp_toolsets() -> list:
    """Discover MCP servers from the Agent Registry and return ADK toolsets.

    Project, location, and an optional server-name filter come from env vars
    set by deploy_agent.py:
      - MCP_REGISTRY_PROJECT  (falls back to GOOGLE_CLOUD_PROJECT)
      - MCP_REGISTRY_LOCATION (falls back to GOOGLE_CLOUD_LOCATION; rejected if "global")
      - MCP_REGISTRY_FILTER   (optional; passed through to list_mcp_servers as the
                               Google API list-filter expression)
      - MCP_REGISTRY_ENDPOINT (optional; full base URL override. When unset we
                               leave ADK's built-in default in place — currently
                               https://agentregistry.googleapis.com/v1alpha, the
                               only endpoint actually serving mcpServers today.
                               Set this to a regional URL once those endpoints
                               exist.)

    Discovery failures are logged and produce an empty list rather than
    aborting agent startup, so the agent still boots (with utility tools only)
    if the registry is unreachable.
    """
    global _CACHED_TOOLSETS, _CACHED_DISCOVERED
    if _CACHED_TOOLSETS is not None:
        logger.debug(
            "Reusing %d cached MCP toolset(s); skipping registry discovery.",
            len(_CACHED_TOOLSETS),
        )
        # Keep DISCOVERED_MCP_SERVERS in sync with the cached toolsets so the
        # instruction renderer always sees the same view as the toolset list.
        DISCOVERED_MCP_SERVERS.clear()
        DISCOVERED_MCP_SERVERS.extend(_CACHED_DISCOVERED or [])
        return _CACHED_TOOLSETS

    DISCOVERED_MCP_SERVERS.clear()

    project = os.environ.get("MCP_REGISTRY_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("MCP_REGISTRY_LOCATION")
    if not location:
        env_location = os.environ.get("GOOGLE_CLOUD_LOCATION")
        # GOOGLE_CLOUD_LOCATION may legitimately be "global" for the model
        # endpoint; the registry needs a real region.
        if env_location and env_location != "global":
            location = env_location

    if not project or not location:
        logger.warning(
            "MCP registry discovery skipped: project=%r location=%r "
            "(set MCP_REGISTRY_PROJECT and MCP_REGISTRY_LOCATION).",
            project,
            location,
        )
        _CACHED_TOOLSETS = []
        _CACHED_DISCOVERED = []
        return _CACHED_TOOLSETS

    filter_str = os.environ.get("MCP_REGISTRY_FILTER")
    endpoint = os.environ.get("MCP_REGISTRY_ENDPOINT")
    invoker_sa_email = os.environ.get("MCP_INVOKER_SA_EMAIL")
    if not invoker_sa_email:
        logger.warning(
            "MCP_INVOKER_SA_EMAIL is not set. MCP calls will use the agent's default "
            "credentials, which Cloud Run does not accept for IAM-protected services. "
            "Set MCP_INVOKER_SA_EMAIL to the SA the agent should impersonate."
        )

    try:
        # Imported lazily so the agent module loads even when ADK's optional
        # dependency chain is not satisfied locally. The deployed image must
        # pin a2a-sdk in deploy_agent.py's requirements list, otherwise this
        # import fails with `No module named 'a2a'` and discovery is skipped.
        from google.adk.integrations import agent_registry as _ar_module
        from google.adk.integrations.agent_registry import AgentRegistry
    except ImportError as e:
        logger.warning(
            "MCP registry discovery skipped: ADK agent_registry import failed (%s). "
            "On a deployed agent this means the requirements list in deploy_agent.py "
            "is missing a transitive dep (typically a2a-sdk).",
            e,
        )
        _CACHED_TOOLSETS = []
        _CACHED_DISCOVERED = []
        return _CACHED_TOOLSETS

    try:
        if endpoint:
            # Override ADK's hardcoded module-level endpoint constant. Remove
            # this patch if ADK starts accepting an explicit endpoint argument.
            _ar_module.AGENT_REGISTRY_BASE_URL = endpoint

        registry = AgentRegistry(project_id=project, location=location)
        response = registry.list_mcp_servers(filter_str=filter_str)
    except Exception:
        effective_endpoint = endpoint or getattr(_ar_module, "AGENT_REGISTRY_BASE_URL", "<adk-default>")
        logger.exception(
            "Failed to list MCP servers from registry %s/%s (endpoint=%s)",
            project,
            location,
            effective_endpoint,
        )
        _CACHED_TOOLSETS = []
        _CACHED_DISCOVERED = []
        return _CACHED_TOOLSETS

    raw_servers = response.get("mcpServers", [])
    effective_endpoint = endpoint or getattr(_ar_module, "AGENT_REGISTRY_BASE_URL", "<adk-default>")
    logger.info(
        "Registry %s/%s returned %d mcpServer(s) (endpoint=%s, filter=%r)",
        project,
        location,
        len(raw_servers),
        effective_endpoint,
        filter_str,
    )
    for s in raw_servers:
        logger.info(
            "  registry entry: name=%s displayName=%r interfaces=%s tools=%s",
            s.get("name"),
            s.get("displayName"),
            [(i.get("protocolBinding"), i.get("url")) for i in s.get("interfaces", [])],
            [t.get("name") for t in s.get("tools", [])],
        )

    toolsets = []
    for server in raw_servers:
        name = server.get("name")
        if not name:
            continue
        try:
            toolset = registry.get_mcp_toolset(mcp_server_name=name)
        except Exception:
            logger.exception("Failed to build toolset for MCP server %s", name)
            continue
        # Use ADK's 5s StreamableHTTPConnectionParams default so denied calls
        # fail fast. Cold-start tolerance is handled by keeping >=1 warm
        # instance per MCP backend (terraform/example.tfvars), not by stretching
        # the per-call budget.
        conn_params = getattr(toolset, "_connection_params", None)
        resolved_url = getattr(conn_params, "url", None)
        # Inject SA-impersonation auth so each MCP HTTP call carries an OIDC
        # ID token for the invoker SA. Cloud Run validates the token and sees
        # the invoker SA as the caller (the agent identity is not propagated
        # to Cloud Run; principalSet members are not accepted as run.invoker).
        if (
            invoker_sa_email
            and conn_params is not None
            and resolved_url
            and hasattr(conn_params, "httpx_client_factory")
        ):
            conn_params.httpx_client_factory = _build_impersonation_factory(
                target_url=resolved_url,
                target_sa_email=invoker_sa_email,
            )
        logger.info(
            "  built toolset: server=%s displayName=%r prefix=%s resolved_url=%s",
            name,
            server.get("displayName"),
            getattr(toolset, "tool_name_prefix", None),
            resolved_url,
        )
        toolsets.append(toolset)
        DISCOVERED_MCP_SERVERS.append(
            {
                "name": server.get("displayName") or name,
                "resource_name": name,
                "tool_name_prefix": getattr(toolset, "tool_name_prefix", None),
                "resolved_url": resolved_url,
                # Unprefixed tool names from the registry payload. The
                # instruction renderer prefixes them at render time so the
                # LLM sees the exact names ADK will accept.
                "tools": [t.get("name") for t in server.get("tools", []) if t.get("name")],
            }
        )

    if not toolsets:
        logger.warning(
            "MCP registry discovery returned no servers in %s/%s (filter=%r, endpoint=%s).",
            project,
            location,
            filter_str,
            effective_endpoint,
        )
    else:
        logger.info(
            "Discovered %d MCP server(s) from registry %s/%s via %s",
            len(toolsets),
            project,
            location,
            effective_endpoint,
        )

    _CACHED_TOOLSETS = toolsets
    _CACHED_DISCOVERED = list(DISCOVERED_MCP_SERVERS)
    return _CACHED_TOOLSETS


class _PickleSafeAgent(Agent):
    """Agent that rebuilds with MCP tools when unpickled or deep-copied."""

    def __reduce__(self):
        return (_build_agent, ())

    def __deepcopy__(self, memo):
        return _build_agent()


def _build_agent():
    """Build the agent with utility tools plus discovered MCP toolsets.

    Called at import time for local dev, and at unpickle time on Agent Engine.
    """
    _tools: list = [
        tools.get_current_time,
        tools.list_mcp_connections,
    ]
    _tools.extend(_discover_mcp_toolsets())

    instruction = _INSTRUCTION_TEMPLATE.format(mcp_services_doc=_render_mcp_services_doc())

    return _PickleSafeAgent(
        model=os.environ.get("MODEL_NAME", "gemini-3.1-flash-lite-preview"),
        name="mortgage_assistant_agent",
        description=(
            "A mortgage underwriting assistant that connects to legacy document management, "
            "income verification, and corporate email systems through an Agent Gateway."
        ),
        instruction=instruction,
        tools=_tools,
        on_tool_error_callback=_handle_tool_error,
    )


root_agent = _build_agent()
