---
name: agent-platform-debugger
description: "Debug GCP Gemini Enterprise Agent Platform issues: Agent Gateway 403s, Agent Registry failures, Agent Identity/IAM denials, IAP egressor authz, service-extensions delegated authz, Model Armor integration failures (500s/denials), hostname mismatches, authzPolicies/authzExtensions misconfig. Use whenever the user mentions agent gateway, agent registry, agent identity, IAP authz, ReasoningEngine 403s/500s, 'Egress request is not authorized', authzPolicies, authzExtensions, Model Armor, MCP server registration, gateway import failures. Also triggers on terse symptoms like 'agent returning 403', 'MCP tool not reachable', 'authz extension denying', 'Model Armor blocking' if there is any Agent Platform context."
---

# Agent Platform Debugger

Diagnose issues across the GCP Gemini Enterprise Agent Platform: Agent Gateway, Agent Registry (Agents / MCP Servers / Endpoints), Agent Identity, Policies, IAP-delegated authorization, and service extensions.

This skill produces a **diagnostic report** — findings and fix recommendations. It does not apply fixes. The user owns the change.

## When to use this skill

Trigger when symptoms involve:

-   Agent → external API requests failing with 403, especially `Egress request is not authorized`
-   ReasoningEngine queries returning `500 Internal Server Error` (especially when Model Armor is enabled)
-   ReasoningEngine logs showing authz errors or container crashes
-   Gateway logs showing `PERMISSION_DENIED` for Model Armor backend callouts
-   Newly-registered endpoints / MCP servers / agents that "should work" but don't
-   Suspected IAP / IAM / IAM-principal-set issues for agent identities
-   Authz extension or authz policy debugging
-   Gateway routing / monitoring confusion
-   Anything where the user mentions Agent Gateway, Agent Registry, Agent Identity, Model Armor integration, or the Gemini Enterprise Agent Platform

When *not* to use:

-   General GCP IAM debugging unrelated to the Agent Platform (use direct gcloud / IAM inspection)
-   Networking issues that don't involve the Agent Platform stack (e.g., raw VPC SC, plain Cloud Run auth)

## Required context (gather first)

Before doing anything else, pin down the basics. If the user hasn't supplied them, ask. Don't guess.

| Item | Why it's needed |
| :--- | :--- |
| `PROJECT_ID` and `PROJECT_NUMBER` | Most API calls take one or the other; some take both |
| `LOCATION` (region) | Registry, gateway, and IAM scope are regional. `global` is also valid for some resources |
| `AGENT_ID` (ReasoningEngine ID) or runtime identifier | To filter agent logs |
| `AGENT_GATEWAY_NAME` | To filter gateway logs |
| Agent identity (service account email or principal-set ID) | To check IAM bindings |
| Symptom: exact error text + when it started | Anchors hypothesis; "started after Terraform apply X" is gold |
| The destination the agent was trying to reach | E.g. `aiplatform`, `discoveryengine`, an MCP server, another agent |

If only some are known, proceed but call out the unknowns in the report.

## Hypothesis Generation Rules

Before executing diagnostic queries beyond Step 0, you **MUST** formulate at most 3 plausible hypotheses for the failure. For each hypothesis, explicitly correlate it with recent changes (e.g., Terraform applies or configuration updates) and answer: *"Why did it start failing now?"*

Limit your diagnostics to validating these hypotheses. Do not execute random queries.

## Diagnostic flow

This is a **process skill** — follow the steps in order. Most 403s resolve at step 2 or 4. Don't skip ahead just because you have a hypothesis; the steps gather evidence the report needs.

```
        ┌─────────────────────────────────────┐
        │ 0. Establish context & Verify access│
        └────────────────┬────────────────────┘
                         │
                         ▼
        ┌─────────────────────────────────────┐
        │ 1. Pull agent logs — confirm error  │
        │    (403 vs Connection vs Crash)     │
        └────────────────┬────────────────────┘
                         │
        ┌────────────────┴────────────────────┐
        │ Is it a Connection / Network error? │
        └───────┬──────────────────────┬──────┘
            no  │                  yes │
                │                      ▼
                │             ┌────────────────────────────────┐
                │             │ 3c. PSC Subnet Exhaustion Check│
                │             └────────────────────────────────┘
                ▼
        ┌─────────────────────────────────────┐
        │ Is it a Container Crash / Python    │
        │ Exception?                          │
        └───────┬──────────────────────┬──────┘
            no  │                  yes │
            (403)                      ▼
                │             ┌────────────────────────────────┐
                │             │ 1b. Runtime Health Check       │
                │             │     (Python dependencies,      │
                │             │      stderr logs, crash codes) │
                │             └────────────────────────────────┘
                ▼
        ┌─────────────────────────────────────┐
        │ 2. Pull gateway logs — find the     │
        │    EXACT hostname being called      │
        └────────────────┬────────────────────┘
                         │
                         ▼
        ┌─────────────────────────────────────┐
        │ 3. Pull IAP logs — DRY_RUN or       │
        │    enforced? Allow or deny?         │
        └────────────────┬────────────────────┘
                         │
                         ▼
        ┌─────────────────────────────────────┐
        │ 4. Is the EXACT hostname in the     │
        │    registry (any of agents /        │
        │    mcp-servers / endpoints)?        │
        └────────┬────────────────────┬───────┘
            no   │                yes │
                 ▼                    ▼
       ┌──────────────────┐   ┌─────────────────────────────┐
       │ Root cause:      │   │ 5. Does the agent identity  │
       │ unregistered     │   │    (or its principal set)   │
       │ hostname permu-  │   │    have IAP egressor on     │
       │ term. Recommend  │   │    the registered resource? │
       │ registering all  │   └────────┬────────────────────┘
       │ five forms.      │            │
       └──────────────────┘            ▼
                            ┌─────────────────────────────┐
                            │ 6. Authz extension wired to │
                            │    the gateway? Pointing at │
                            │    IAP?                     │
                            └────────┬────────────────────┘
                                     ▼
                            ┌─────────────────────────────┐
                            │ 7. Agent identity baseline  │
                            │    roles (Vertex User,      │
                            │    Registry Viewer, logs)   │
                            └────────┬────────────────────┘
                                     ▼
                            ┌─────────────────────────────┐
                            │ 8. PrincipalSet flakiness?  │
                            │    Recommend 1:1 binding    │
                            │    test                     │
                            └─────────────────────────────┘
```

The exact log queries, gcloud commands, and curl invocations live in `references/field-manual.md`. Read that file when you reach each step — it has the copy-pasteable commands and explains what each output means.

### Step 0: Establish context & Verify access

Before running any operational diagnostics, perform the following baseline checks to verify project access:

1.  **Verify Target Project Access**: Verify if you have direct ambient permissions on the target GCP project:
    ```bash
    gcloud projects describe $PROJECT_ID
    ```
    If this fails, you cannot proceed with log gathering. Prompt the user for correct permissions or coordinates.

## Tools to use

The skill assumes the agent has access to:

-   **`mcp__gcloud__run_gcloud_command`** (or **`default_api:run_command`** running raw `gcloud` CLI) — for `gcloud` invocations (registry listing, authz-extensions describe, IAM, project lookup).
-   **`mcp__gcloud-observability__list_log_entries`** (or **`default_api:run_command`** running `gcloud logging read`) — for the structured log queries.
-   **`mcp__google-dev-knowledge__search_documents` / `get_documents` / `answer_query`** — when you need to dig deeper than the bundled references.
-   **`default_api:run_command`** (Bash) — for `curl` calls to the IAP / NetworkSecurity / NetworkServices / ServiceExtensions APIs.

Run independent log queries in parallel if supported.

## How to use the references

The `references/` folder is layered:

-   **`field-manual.md`** — read this first on every invocation. It's the operational core.
-   **`known-issues.md`** — read when the symptom matches a recurring pattern.
-   **`agent-gateway.md`** — when the gateway itself is the suspect.
-   **`policies.md`** — when the question is about IAM modeling.
-   **`agent-registry.md`** — when registration mechanics are unclear.
-   **`agent-identity.md`** — when the question is about *who* the agent is.

Read the smallest set that answers the question. Don't preload everything.

## Output report

Always produce a structured report. Use this template exactly.

```markdown
# Agent Platform Diagnostic — <one-line summary>

## Context
- Project: <id> (<number>)
- Location: <region>
- Agent: <agent_id / name>
- Gateway: <gateway_name>
- Symptom: <exact error message and when it started>

## Evidence gathered
- Agent log query: <filter, brief summary of matches>
- Gateway log query: <filter, exact failing hostname found>
- IAP log query: <filter, decision + enforcement mode>
- Registry state: <relevant entries, IAM bindings>
- (any other tool output that mattered)

## Root cause hypothesis
<single most likely cause, stated plainly. If multiple, rank them.>

## Why this fits the evidence
<brief — connect the dots. Show which evidence rules in / rules out the hypothesis.>

## Recommended fix
<concrete actions in order. Show exact gcloud / curl / Terraform changes the user can run. If the fix is in the user's repo (Terraform), point at file:line.>

## What to verify after the fix
<the queries to re-run to confirm resolution.>

## Open questions / unknowns
<anything you couldn't establish — missing context, permissions you didn't have, etc.>

## Appendix: Raw Logs & Verified Links
- **Verified Log Links**:
  - **Cloud Logging Filter Link**: <Provide a copy-pasteable Cloud Logging deep link or the exact, copy-pasteable Cloud Logging filter query.>
- **Raw Logs**:
  - **Agent Raw Logs**:
    [Insert the full, untruncated raw logs from the ReasoningEngine here]
  - **Gateway Raw Logs**:
    [Insert the full, untruncated raw logs from the Gateway here]
  - **IAP Raw Logs**:
    [Insert the full, untruncated raw logs from IAP here]
```

## Principles

-   **Hostname mismatch is the #1 cause.** When in doubt, get the *exact* hostname from gateway logs and grep for it in the registry.
-   **Default-deny is the model with multiple layers.** Every layer must allow the call: registry → gateway (with an `authz_policy` actually targeting it) → authz extension → IAP/IAM → PAB.
-   **PAB beats IAM Allow.** A correct `roles/iap.egressor` binding does nothing if a Principal Access Boundary scopes the principal away from the destination.
-   **DRY_RUN changes everything.** If IAP is in dry-run, denials are logged but not enforced.
-   **The role is `roles/iap.egressor`.**
-   **Read evidence, don't assume.** Pull logs first.
-   **Cite exact resource names in the report.**
-   **Stay in diagnosis mode.** Don't apply Terraform changes or run destructive gcloud commands. Read-only inspection only.
