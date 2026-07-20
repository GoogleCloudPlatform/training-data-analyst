#!/usr/bin/env bash
#
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
#
# Grants `roles/iap.egressor` to an agent identity on each MCP server and/or
# endpoint registered in the project's Agent Registry. Per-resource bindings
# are documented at:
#   https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/policies/assign-identity-iam#agent-to-mcp-server
#   https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/policies/assign-identity-iam#agent-to-endpoint
#   https://docs.cloud.google.com/agent-registry/manage-endpoints
#
# Note: gcloud SDK 552 does NOT yet ship `gcloud beta iap web
# add-iam-policy-binding --mcpServer=...` / `--endpoint=...` (the docs page is
# ahead of the CLI). This script calls the REST endpoints directly and
# implements add-iam-policy-binding semantics on the client (get + merge + set):
#   - List mcpServers: https://agentregistry.googleapis.com/v1alpha/projects/{P}/locations/{R}/mcpServers
#   - List endpoints:  https://agentregistry.googleapis.com/v1alpha/projects/{P}/locations/{R}/endpoints
#   - Per-resource IAM: https://iap.googleapis.com/v1/projects/{P}/locations/{R}/iap_web/agentRegistry/{mcpServers,endpoints}/{ID}:{get,set}IamPolicy
#
# Resource IDs in the Agent Registry are auto-generated (e.g.
# `agentregistry-00000000-0000-0000-3626-b6e6cfd10681`), not friendly names.
# The script discovers them; you don't pass them in.
#
# Required env vars:
#   PROJECT_ID       e.g. duncanjames-agw-tf
#   PROJECT_NUMBER   numeric project number (used in the principal URI)
#   ORG_ID           12-digit GCP organization id (used in the principal URI)
#   REGION           e.g. us-central1
#
# Identity (one of the following — flag wins when both are set):
#   --agent-id <ID>               [env AGENT_ID]
#                                 Reasoning engine id (numeric, from
#                                 `gcloud beta ai reasoning-engines list` or
#                                 deploy_agent.py output). Not required when
#                                 --bind-all-agents is set.
#
# Resource-type selection flags (boolean — neither set means both):
#   --mcp                    Apply the binding to MCP servers in the registry.
#   --endpoints              Apply the binding to endpoints in the registry.
#
# Behavior flags (each has an env-var fallback — flag wins when both are set):
#   --bind-all-agents             [env BIND_ALL_AGENTS]
#                                 Bind the project's Agent Engine principalSet
#                                 (`principalSet://…/projects/${PROJECT_NUMBER}`)
#                                 instead of a single reasoning engine. AGENT_ID
#                                 is ignored. NOTE: the IAP API has historically
#                                 rejected principalSet at the per-mcpServer
#                                 scope (HTTP 400); per-endpoint is unverified.
#                                 The HTTP error capture surfaces any rejection
#                                 verbatim.
#   --mcp-filter <SUBSTR>         [env MCP_SERVERS]
#                                 Space-separated substring filter for MCP
#                                 servers. Only consulted with --mcp.
#   --endpoints-filter <SUBSTR>   [env ENDPOINTS_FILTER]
#                                 Space-separated substring filter for
#                                 endpoints. Only consulted with --endpoints.
#   --condition-expression <CEL>  [env CONDITION_EXPRESSION]
#                                 CEL expression to attach to the binding (e.g.
#                                 "api.getAttribute('iap.googleapis.com/mcp.tool.isReadOnly', false) == true").
#                                 When set, the policy is written at version 3
#                                 (required by IAM for conditional bindings)
#                                 and --condition-title must also be set.
#   --condition-title <TITLE>     [env CONDITION_TITLE]
#                                 Human-readable title for the condition.
#                                 Required when --condition-expression is set.
#   --condition-description <T>   [env CONDITION_DESCRIPTION]
#                                 Optional human-readable description.

set -euo pipefail

# Resource-type selection (CLI-only; default = both when neither is set).
DO_MCP=
DO_ENDPOINTS=

# value_for <flag-name> <candidate>: echo <candidate> if present and not
# itself a flag; error otherwise. Intended call:  value_for "$1" "${2:-}".
value_for() {
	local flag="$1" candidate="${2:-}"
	if [ -z "${candidate}" ] || [[ ${candidate} == --* ]]; then
		echo "${flag} requires a value" >&2
		exit 1
	fi
	printf '%s' "${candidate}"
}

while [ $# -gt 0 ]; do
	case "$1" in
	--mcp)
		DO_MCP=1
		shift
		;;
	--endpoints)
		DO_ENDPOINTS=1
		shift
		;;
	--bind-all-agents)
		BIND_ALL_AGENTS=1
		shift
		;;
	--agent-id)
		AGENT_ID="$(value_for "$1" "${2:-}")"
		shift 2
		;;
	--mcp-filter)
		MCP_SERVERS="$(value_for "$1" "${2:-}")"
		shift 2
		;;
	--endpoints-filter)
		ENDPOINTS_FILTER="$(value_for "$1" "${2:-}")"
		shift 2
		;;
	--condition-expression)
		CONDITION_EXPRESSION="$(value_for "$1" "${2:-}")"
		shift 2
		;;
	--condition-title)
		CONDITION_TITLE="$(value_for "$1" "${2:-}")"
		shift 2
		;;
	--condition-description)
		CONDITION_DESCRIPTION="$(value_for "$1" "${2:-}")"
		shift 2
		;;
	-h | --help)
		sed -n '17,79p' "$0"
		exit 0
		;;
	*)
		echo "Unknown flag: $1 (run with -h for usage)" >&2
		exit 1
		;;
	esac
done
if [ -z "${DO_MCP}" ] && [ -z "${DO_ENDPOINTS}" ]; then
	DO_MCP=1
	DO_ENDPOINTS=1
fi

: "${PROJECT_ID:?PROJECT_ID is required}"
: "${PROJECT_NUMBER:?PROJECT_NUMBER is required}"
: "${ORG_ID:?ORG_ID is required}"
: "${REGION:?REGION is required}"

# Behavior knobs default to whatever the flag parser or env var left them as,
# else empty. Flag wins; env is fallback.
BIND_ALL_AGENTS="${BIND_ALL_AGENTS:-}"
MCP_SERVERS="${MCP_SERVERS:-}"
ENDPOINTS_FILTER="${ENDPOINTS_FILTER:-}"
CONDITION_EXPRESSION="${CONDITION_EXPRESSION:-}"
CONDITION_TITLE="${CONDITION_TITLE:-}"
CONDITION_DESCRIPTION="${CONDITION_DESCRIPTION:-}"

if [ -z "${BIND_ALL_AGENTS}" ]; then
	: "${AGENT_ID:?--agent-id (or env AGENT_ID) is required \(numeric reasoning engine id\), or pass --bind-all-agents to bind the project-wide principalSet}"
fi

if [ -n "${CONDITION_EXPRESSION}" ] && [ -z "${CONDITION_TITLE}" ]; then
	echo "--condition-title (or env CONDITION_TITLE) is required when --condition-expression is set" >&2
	exit 1
fi

if [ -n "${BIND_ALL_AGENTS}" ]; then
	AGENT_PRINCIPAL="principalSet://agents.global.org-${ORG_ID}.system.id.goog/attribute.platformContainer/aiplatform/projects/${PROJECT_NUMBER}"
else
	AGENT_PRINCIPAL="principal://agents.global.org-${ORG_ID}.system.id.goog/resources/aiplatform/projects/${PROJECT_NUMBER}/locations/${REGION}/reasoningEngines/${AGENT_ID}"
fi
ROLE="roles/iap.egressor"

for cmd in curl jq gcloud; do
	command -v "$cmd" >/dev/null 2>&1 || {
		echo "Missing required command: $cmd" >&2
		exit 1
	}
done

TOKEN="$(gcloud auth print-access-token)"
AR_BASE="https://agentregistry.googleapis.com/v1alpha"
IAP_BASE="https://iap.googleapis.com/v1"

bind_to=()
[ -n "${DO_MCP}" ] && bind_to+=("mcpServers")
[ -n "${DO_ENDPOINTS}" ] && bind_to+=("endpoints")

echo "Granting ${ROLE} to:"
echo "  ${AGENT_PRINCIPAL}"
echo "Project: ${PROJECT_ID}  Region: ${REGION}"
echo "Bind to: ${bind_to[*]}"
[ -n "${DO_MCP}" ] && { [ -n "${MCP_SERVERS}" ] && echo "MCP_SERVERS filter: ${MCP_SERVERS}" || echo "MCP_SERVERS filter: (none — all)"; }
[ -n "${DO_ENDPOINTS}" ] && { [ -n "${ENDPOINTS_FILTER}" ] && echo "ENDPOINTS_FILTER:   ${ENDPOINTS_FILTER}" || echo "ENDPOINTS_FILTER:   (none — all)"; }
if [ -n "${CONDITION_EXPRESSION}" ]; then
	echo "Condition (${CONDITION_TITLE}): ${CONDITION_EXPRESSION}"
fi
echo

# http_request <output_file> <curl args…>
# Wraps curl so the response body is always written to <output_file> and the
# HTTP status is checked explicitly. On 4xx/5xx, prints "FAILED (HTTP <code>):"
# and the body to stderr, then returns non-zero. On success, returns 0.
http_request() {
	local out="$1"
	shift
	local code
	code="$(curl -sS -o "${out}" -w '%{http_code}' "$@")"
	if [ "${code}" -lt 200 ] || [ "${code}" -ge 300 ]; then
		echo "FAILED (HTTP ${code}):" >&2
		cat "${out}" >&2
		echo >&2
		return 1
	fi
}

# apply_policy <iam_url_base> <label>
# Merges (ROLE, AGENT_PRINCIPAL[, CONDITION_*]) into the existing IAM policy at
# <iam_url_base>:{get,set}IamPolicy, mirroring `gcloud add-iam-policy-binding`
# semantics: existing bindings are preserved, an existing binding with the same
# role+condition gets the member appended (de-duped), and otherwise a new
# binding is created. The GET requests version 3 so any conditional bindings
# round-trip intact, and the SET writes version 3 unconditionally.
apply_policy() {
	local iam_url="$1" label="$2"
	local resp="/tmp/iam_resp.$$"
	local body

	if ! http_request "${resp}" -X POST \
		-H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" \
		-d '{"options":{"requestedPolicyVersion":3}}' "${iam_url}:getIamPolicy"; then
		rm -f "${resp}"
		exit 1
	fi

	body="$(jq \
		--arg role "${ROLE}" \
		--arg member "${AGENT_PRINCIPAL}" \
		--arg expr "${CONDITION_EXPRESSION}" \
		--arg title "${CONDITION_TITLE}" \
		--arg desc "${CONDITION_DESCRIPTION}" '
    . as $cur
    | (if $expr == "" then null
       else {expression: $expr, title: $title}
            + (if $desc == "" then {} else {description: $desc} end)
       end) as $cond
    | ({role: $role, members: [$member]}
       + (if $cond == null then {} else {condition: $cond} end)) as $new
    | ($cur.bindings // []) as $bs
    | (if ($bs | any(.role == $new.role and ((.condition // null) == ($new.condition // null))))
       then $bs | map(
         if .role == $new.role and ((.condition // null) == ($new.condition // null))
         then .members = (if (.members // []) | any(. == $member)
                          then (.members // [])
                          else (.members // []) + [$member]
                          end)
         else .
         end)
       else $bs + [$new]
       end) as $merged
    | {policy: ({bindings: $merged, version: 3}
                + (if ($cur.etag // "") == "" then {} else {etag: $cur.etag} end))}
  ' <"${resp}")"

	echo "==>   ${label}"
	if ! http_request "${resp}" -X POST \
		-H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" \
		-d "${body}" "${iam_url}:setIamPolicy"; then
		rm -f "${resp}"
		exit 1
	fi
	jq -c '.bindings' "${resp}"
	rm -f "${resp}"
}

# matches_filter <display> <service> <filter>
# True when <filter> is empty OR any whitespace-separated needle in <filter> is
# a substring of either <display> or <service>.
matches_filter() {
	local display="$1" service="$2" filter="$3"
	[ -z "${filter}" ] && return 0
	for needle in ${filter}; do
		[[ ${display} == *"${needle}"* || ${service} == *"${needle}"* ]] && return 0
	done
	return 1
}

# process_resource_type <collection> <filter>
# <collection> is "mcpServers" or "endpoints" — used as both the list-URL leaf,
# the JSON top-level key, and the IAP IAM URL segment. <filter> is the value of
# MCP_SERVERS or ENDPOINTS_FILTER (substring filter).
# Lists every resource of that type, applies the binding to each match, prints
# a final count line, and returns non-zero when no resources match.
process_resource_type() {
	local collection="$1" filter="$2"
	local list_resp="/tmp/iam_resp.$$"

	echo "--- ${collection} ---"
	if ! http_request "${list_resp}" -H "Authorization: Bearer ${TOKEN}" \
		"${AR_BASE}/projects/${PROJECT_ID}/locations/${REGION}/${collection}"; then
		rm -f "${list_resp}"
		return 1
	fi

	local entries
	mapfile -t entries < <(jq -r --arg c "${collection}" '
    .[$c] // []
    | .[]
    | [
        (.name | split("/") | last),
        (.displayName // ""),
        ((.attributes["agentregistry.googleapis.com/system/RuntimeReference"].uri // "")
          | split("/") | last)
      ]
    | @tsv
  ' <"${list_resp}")
	rm -f "${list_resp}"

	if [ "${#entries[@]}" -eq 0 ]; then
		echo "No ${collection} found in ${PROJECT_ID}/${REGION}." >&2
		return 0
	fi

	local applied=0 line id display service
	for line in "${entries[@]}"; do
		IFS=$'\t' read -r id display service <<<"${line}"
		if ! matches_filter "${display}" "${service}" "${filter}"; then
			echo "skip:  ${display} (${service})"
			continue
		fi

		apply_policy \
			"${IAP_BASE}/projects/${PROJECT_ID}/locations/${REGION}/iap_web/agentRegistry/${collection}/${id}" \
			"${display} (${service})  [${id}]"
		applied=$((applied + 1))
	done

	echo "${collection}: granted on ${applied} resource(s)."
	echo
}

if [ -n "${DO_MCP}" ]; then
	process_resource_type "mcpServers" "${MCP_SERVERS}"
fi
if [ -n "${DO_ENDPOINTS}" ]; then
	process_resource_type "endpoints" "${ENDPOINTS_FILTER}"
fi

echo "Done."
