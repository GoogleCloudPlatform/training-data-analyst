# Field manual: Agent Gateway / Registry / Identity / IAP

Practical debugging knowledge for the GCP Gemini Enterprise Agent Platform, distilled from real incident triage. Read this *before* diving into the official docs — it covers the gotchas that the docs don't surface.

## The mental model

The Agent Platform runs as **default-deny egress**. An agent (typically a Vertex AI ReasoningEngine) cannot talk to *anything* outside itself unless every layer permits it:

1.  **Agent Registry** — the destination must be registered as an Endpoint, MCP Server, or Agent.
2.  **Agent Gateway** — intercepts the request (it sits in front of the agent's egress). Note: an `authz_policy` must explicitly target the gateway resource, otherwise the authz extension won't actually run.
3.  **Service-extension (delegated authz)** — the gateway calls IAP to make an allow/deny decision.
4.  **IAP / IAM** — the agent's identity must have the **IAP egressor role** (`roles/iap.egressor`, display name "IAP-secured Egressor") on the registered resource, or be in a principal set that does.
5.  **Principal Access Boundary (PAB)** — even with the IAM binding correct, a PAB policy on the principal set can restrict which resources it can reach. **PAB takes precedence over IAM Allow** — a correct egressor binding does nothing if a PAB scopes the principal away from the target.

**Implementation note.** Agent Gateway is built on a Google-managed Secure Web Proxy instance that provides the egress-proxy capabilities. Customers don't configure the proxy directly — its rules are derived from registry entries and authz policies. Denials *can* originate at this proxy layer before IAP runs (no IAP audit entry exists for those calls); those show up in load-balancer logs (see Step 3b).

**Proxy Routing & TLS SNI:** The proxy performs TLS inspection and looks inside the HTTPS call for the SNI hostname. In Private Service Connect (PSC) environments, the client resolves APIs to internal VIPs, so the outer tunnel request is naturally logged as `CONNECT 240.0.0.2:443`. This is expected. The proxy intercepts this and evaluates routing based on the inner SNI hostname. If the corresponding hostname (e.g., `us-central1-aiplatform.googleapis.com`) is NOT registered, the proxy cannot route the traffic, resulting in a `default_denied` action on the `CONNECT` request before IAP is ever reached.

### Don't confuse `roles/iap.egressor` with other IAP roles

The display name "IAP-secured Egressor" maps to **`roles/iap.egressor`** — that's the role for Agent Gateway egress. Other IAP roles exist that are easy to mistake for it but are unrelated:

| Role ID | Purpose | Use for Agent Gateway? |
| :--- | :--- | :--- |
| `roles/iap.egressor` | Agent egress through Agent Gateway | **Yes — this one** |
| `roles/iap.tunnelResourceAccessor` | TCP/SSH tunneling through IAP to a VM | No |
| `roles/iap.httpsResourceAccessor` | Access to IAP-protected web apps (ingress) | No |
| `roles/iap.tunnelDestGroupUser` | Member of an IAP tunnel destination group | No |

Don't substitute. The IAP authz check explicitly looks for `iap.webServiceVersions.egressViaIAP`, which only `roles/iap.egressor` grants for the Agent Gateway path.

If any layer says no, the agent gets back a 403:

```
{'code': 403, 'message': "403 Forbidden. {'message': 'Egress request is not authorized.', 'status': 'Forbidden'}"}
```

## The single biggest gotcha: hostname permutations

A Google API like `aiplatform.googleapis.com` is reachable through *many* hostnames. The agent might call any of them depending on the SDK version, regional client config, or whether mTLS is in play:

| Form | Example |
| :--- | :--- |
| Base | `aiplatform.googleapis.com` |
| Base + mTLS | `aiplatform.mtls.googleapis.com` |
| Locational | `us-central1-aiplatform.googleapis.com` |
| Locational + mTLS | `us-central1-aiplatform.mtls.googleapis.com` |
| Regional REP (public) | `aiplatform.us-central1.rep.googleapis.com` |
| Regional REP (private/PSC) | `aiplatform.us-central1.p.rep.googleapis.com` |

**The gateway matches hostnames exactly.** If you registered only `aiplatform.googleapis.com` but the SDK actually called `us-central1-aiplatform.googleapis.com`, the request gets denied — even though "the API is registered." When investigating a 403, *always* establish what hostname the agent actually called, then verify that *exact* hostname is in the registry.

A registration script typically looks like this (note all five permutations):

```bash
reg_svc "${id}"                   "${name}"                "https://${id}.googleapis.com"
reg_svc "${id}-mtls"              "${name} mTLS"           "https://${id}.mtls.googleapis.com"
reg_svc "${LOCATION}-${id}"       "${name} Locational"     "https://${LOCATION}-${id}.googleapis.com"
reg_svc "${LOCATION}-${id}-mtls"  "${name} Locational mTLS" "https://${LOCATION}-${id}.mtls.googleapis.com"
reg_svc "${id}-${LOCATION}-rep"   "${name} Regional (REP)" "https://${id}.${LOCATION}.rep.googleapis.com"
```

## Recommended Registry Structure: Consolidated Google APIs

To simplify management and reduce resource overhead, it is recommended to register all Google APIs under a single `googleapis` service entry in the Agent Registry using **multiple interfaces** (one for each required API hostname).

### Recommended Base Interfaces (Consolidated `googleapis` Service)

Your base `googleapis` service should include the following interfaces:

-   `https://agentregistry.googleapis.com`
-   `https://aiplatform.mtls.googleapis.com`
-   `https://cloudresourcemanager.mtls.googleapis.com`
-   `https://iamcredentials.mtls.googleapis.com`
-   `https://telemetry.mtls.googleapis.com`
-   `https://{region}-aiplatform.mtls.googleapis.com`
-   `https://{region}-aiplatform.googleapis.com`
-   `https://aiplatform.{region}.rep.googleapis.com`

*(Replace `{region}` with your actual region, e.g., `us-central1`)*

### Other Services

If you are not using the consolidated model, or are using additional services (like custom MCPs or separate engines), make sure they are registered:

-   `discoveryengine`
-   `logging`
-   `monitoring`
-   `oauth2`
-   `trace`
-   `iap`
-   `modelarmor`

Missing any required API hostnames is the most common "agent works in dev, fails in prod" cause.

## Metric Queries & Visualization

When diagnosing performance issues, latency spikes, or intermittent failures, you can query and visualize relevant time-series metrics if you have monitoring access.

If the user reports "slowness" or "intermittent errors", visualize the trend using a Mermaid `xychart-beta` chart in your diagnostic report.

### 1. Agent Gateway Egress QPS & Error Rate

Query the Secure Web Proxy metrics for the gateway to see traffic volume and error distribution:

-   **Metric**: `networkservices.googleapis.com/gateway/request_count`
-   **Breakby**: `response_code_class`, `gateway_name`

### 2. Reasoning Engine Latency (p50/p90/p99)

Query the Reasoning Engine latency to identify performance degradation:

-   **Metric**: `aiplatform.googleapis.com/reasoning_engine/query_latency`
-   **Breakby**: `reasoning_engine_id`, `location`

### 3. Visualizing with Mermaid

When presenting latency or error trends in the report, format them as a Mermaid chart:

```mermaid
xychart-beta
    title "Gateway Latency (p90) last 24h"
    x-axis [00:00, 04:00, 08:00, 12:00, 16:00, 20:00]
    y-axis "Latency (ms)" 0 --> 1000
    line [120, 150, 850, 900, 140, 130]
```

## Diagnostic playbook

### Step 1 — Confirm the symptom in agent logs

Check the ReasoningEngine logs for the error (403, SSL Handshake Timeout, or Connection Reset):

```
resource.type="aiplatform.googleapis.com/ReasoningEngine"
resource.labels.location=$LOCATION
resource.labels.reasoning_engine_id=$AGENT_ID
(textPayload:"403" OR textPayload:"handshake operation timed out" OR textPayload:"Connection reset by peer" OR textPayload:"Network is unreachable")
```

**Alternative (CLI Fallback):**

```bash
gcloud logging read 'resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.location="'$LOCATION'" AND resource.labels.reasoning_engine_id="'$AGENT_ID'" AND (textPayload:"403" OR textPayload:"handshake operation timed out" OR textPayload:"Connection reset by peer" OR textPayload:"Network is unreachable")' --project=$PROJECT_ID --limit=10
```

The error payload tells you *that* it failed.

-   If it is a **403**, continue with the standard Gateway/IAP flow (Step 2).
-   If it is an **SSL Handshake Timeout** or **Connection Reset/Network Unreachable**, suspect a PSC provisioning issue or subnet exhaustion. Skip to **Step 3c**.
-   If it is a **container crash**, **startup error**, or **Python exception**, proceed to **Step 1b**.

### Step 1b — Debugging Agent Runtime Crashes (Container Crashes & Python Exceptions)

If the agent logs (Step 1) show that the Reasoning Engine container failed to start or crashed during execution (instead of a 403 or network timeout), follow this checklist:

#### 1. Pull stderr logs for Python exceptions

Query the stderr logs specifically to find traceback info:

```
resource.type="aiplatform.googleapis.com/ReasoningEngine"
resource.labels.location=$LOCATION
resource.labels.reasoning_engine_id=$AGENT_ID
logName="projects/$PROJECT_ID/logs/aiplatform.googleapis.com%2Freasoning_engine_stderr"
```

**Alternative (CLI Fallback):**

```bash
gcloud logging read 'resource.type="aiplatform.googleapis.com/ReasoningEngine" AND resource.labels.location="'$LOCATION'" AND resource.labels.reasoning_engine_id="'$AGENT_ID'" AND logName="projects/'$PROJECT_ID'/logs/aiplatform.googleapis.com%2Freasoning_engine_stderr"' --project=$PROJECT_ID --limit=20
```

Look for common Python startup failures:

-   `ModuleNotFoundError` or `ImportError`: The uploaded agent code requires a package that was not specified in the deployment requirements.
-   `SyntaxError`: Syntax error in the uploaded Python files.
-   Initialization crashes in the `__init__` method of the agent class.

#### 2. Check for Resource Limit Exceeded (OOM)

If the container dies silently without a Python traceback, it may have been killed by the runtime due to Out of Memory (OOM) or CPU limits.

-   Check if the requested resource limits (CPU/Memory) in `DeploymentSpec` are sufficient.
-   Look for container termination status if visible in the logs (e.g., exit code `137` usually indicates OOMKilled).

### Step 2 — Find the failing hostname in gateway logs

```
resource.type="networkservices.googleapis.com/Gateway"
resource.labels.location="REGION"
resource.labels.gateway_name="AGENT_GATEWAY_NAME"
```

**Alternative (CLI Fallback):**

```bash
gcloud logging read 'resource.type="networkservices.googleapis.com/Gateway" AND resource.labels.location="REGION" AND resource.labels.gateway_name="AGENT_GATEWAY_NAME"' --project=PROJECT_ID --limit=50
```

The gateway log entry shows the actual hostname the request was for. Write it down — you'll need it in step 4.

**Model Armor Special Case (High-Confidence Indicator):** If the gateway log contains `serviceExtensionInfo` with `grpcStatus: "PERMISSION_DENIED"`, `backendTargetType: "BACKEND_SERVICE"`, and `backendTargetName` matching `modelarmor.*`, this is a definitive, high-confidence indicator of a Model Armor integration permission issue. Refer to **known-issues.md §13 (BKI 13)** immediately for the exact role requirements and fix commands.

### Step 3 — Check IAP allow/deny decision

> [!IMPORTANT] **Data Access Logs Prerequisite**: IAP authorization decisions for the data-plane are logged to **Data Access audit logs** (`DATA_READ` type), which are **disabled by default** in GCP. If the log query below returns **no results**, you must verify if IAP audit logging is enabled. Check with:
>
> ```bash
> gcloud projects get-iam-policy $PROJECT_ID \
>   --filter="auditConfigs.service:iap.googleapis.com" \
>   --format="yaml(auditConfigs)"
> ```
>
> If the output is empty or missing `DATA_READ` for `iap.googleapis.com`, you must enable it in the GCP Console under **IAM -> Audit Logs**.

Narrow the noise by scoping to the egress permission and excluding base-protocol MCP method noise:

```
protoPayload.serviceName="iap.googleapis.com"
protoPayload.authorizationInfo.permission="iap.webServiceVersions.egressViaIAP"
-protoPayload.metadata.mcp_attributes.base_protocol_method="true"
```

**Alternative (CLI Fallback):**

```bash
gcloud logging read 'protoPayload.serviceName="iap.googleapis.com" AND protoPayload.authorizationInfo.permission="iap.webServiceVersions.egressViaIAP" AND -protoPayload.metadata.mcp_attributes.base_protocol_method="true"' --project=PROJECT_ID --limit=50
```

What to read out of each entry:

-   **`protoPayload.authorizationInfo[].granted`** — `true` or `false`. The bottom-line allow/deny.
-   **`protoPayload.authenticationInfo.principalSubject`** — the SPIFFE / `principal://...` URI of the caller.
-   **`protoPayload.authorizationInfo[].resource`** — the registered resource the call resolved to.
-   **`labels."iap.googleapis.com/audited_resource_name"`** — if this is `unregisteredResource`, the destination hostname isn't in the registry. Go to Step 4.
-   **The enforcement mode** — is IAP in dry-run?

    ```yaml
    service: iap.googleapis.com
    failOpen: true
    timeout: 1s
    metadata:
      iamEnforcementMode: "DRY_RUN"
      iapPolicyVersion: "V1"
    ```

    In `DRY_RUN` mode, denials are logged but the request proceeds. If your agent is failing with a real 403 *and* IAP is in dry-run, the denial is coming from somewhere else — most often the gateway's underlying egress proxy (see Step 3b) or the destination service itself.

### Step 3b — If there's no IAP audit entry for the failing call, pull the gateway proxy load-balancer log

The gateway's underlying egress proxy can deny a request before IAP runs. The denial is in the proxy's load-balancer log. The `SECURE_WEB_GATEWAY` label here refers to the proxy implementation under the hood:

```
jsonPayload.@type="type.googleapis.com/google.cloud.loadbalancing.type.LoadBalancerLogEntry"
resource.labels.gateway_type="SECURE_WEB_GATEWAY"
```

**Alternative (CLI Fallback):**

```bash
gcloud logging read 'jsonPayload.@type="type.googleapis.com/google.cloud.loadbalancing.type.LoadBalancerLogEntry" AND resource.labels.gateway_type="SECURE_WEB_GATEWAY"' --project=PROJECT_ID --limit=50
```

Key fields to inspect:
- `httpRequest.status`: Look for `403`.
- `jsonPayload.enforcedGatewaySecurityPolicy.hostname`: Look for `240.0.0.2:443` (expected under PSC).
- `jsonPayload.enforcedGatewaySecurityPolicy.matchedRules`: Look for `default_denied`.
- `jsonPayload.mtls.clientCertChainVerified`: Often `false` if connection dropped early.

If you see `240.0.0.2:443` under `hostname` and `default_denied` under `matchedRules`, this is a routing drop. The proxy decrypted the tunnel but failed to match the *inner* SNI hostname against the Agent Registry. Make sure all required hostname permutations are registered.

### Step 3c — Diagnosing PSC Subnet Exhaustion

If you observe **SSL Handshake Timeouts** or **Connection Reset** in the agent logs, or if the Agent Gateway deployment is failing/stuck, the Private Service Connect (PSC) subnet might be out of IP addresses.

1.  **Identify the Network Attachment**:
    Describe the Agent Gateway to find the Network Attachment in use:
    ```bash
    gcloud alpha network-services agent-gateways describe AGENT_GATEWAY_NAME --location=$LOCATION --project=$PROJECT_ID
    ```
    Look for `networkConfig.egress.networkAttachment`.

2.  **Describe the Network Attachment**:
    ```bash
    gcloud compute network-attachments describe NETWORK_ATTACHMENT_NAME --region=$LOCATION --project=$PROJECT_ID
    ```
    Note the `subnetwork` field.

3.  **Inspect the Subnet**:
    Describe the subnetwork to check its IP range:
    ```bash
    gcloud compute networks subnetworks describe SUBNET_NAME --region=$LOCATION --project=$PROJECT_ID
    ```
    Check the `ipCidrRange` (e.g., a `/28` subnet only has 16 IP addresses, and GCP reserves 4, leaving only 12 for resources).

4.  **Check IP Usage**:
    Compare the subnet size with the number of resources deployed in it. A `/28` subnet is easily exhausted if shared. If exhausted, recommend the user to expand the subnet range or allocate a larger subnet (minimum `/26` recommended).

### Step 4 — Verify the hostname is registered (in the form the agent used)

List registry entries — pick the right resource type for the destination:

```bash
gcloud alpha agent-registry endpoints list      --project=$PROJECT_ID --location=$LOCATION
gcloud alpha agent-registry mcp-servers list    --project=$PROJECT_ID --location=$LOCATION
gcloud alpha agent-registry agents list         --project=$PROJECT_ID --location=$LOCATION
```

Grep the output for the exact hostname from step 2. If it's missing, that's the root cause.

### Step 5 — Verify IAM bindings on the registered resource

The agent's identity (or a principal set it belongs to) needs the IAP egressor role on the destination. Bindings can live at the **registry level** or on a **specific resource**.

#### Registry-level IAM policy

```bash
curl -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -d '{}' \
  -X POST "https://iap.googleapis.com/v1/projects/${PROJECT_NUMBER}/locations/${LOCATION}/iap_web/agentRegistry:getIamPolicy" \
  -H "Content-Type: application/json"
```

#### Per-endpoint IAM policy

```bash
curl -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -d '{}' \
  -X POST "https://iap.googleapis.com/v1/projects/${PROJECT_NUMBER}/locations/${LOCATION}/iap_web/agentRegistry/endpoints/${ENDPOINT_ID}:getIamPolicy" \
  -H "Content-Type: application/json"
```

#### Same call, but for global registry:

```bash
curl -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -d '{"options": {"requestedPolicyVersion": 3}}' \
  -X POST "https://iap.googleapis.com/v1/projects/${PROJECT_NUMBER}/locations/global/iap_web/agentRegistry:getIamPolicy" \
  -H "Content-Type: application/json"
```

When reading the returned policy, look for a binding that matches the agent's service account or principal set with role `roles/iap.egressor`.

### Step 6 — Inspect the gateway / authz extension wiring

#### List authz extensions

```bash
gcloud beta service-extensions authz-extensions list \
  --location=$LOCATION --project=$PROJECT_ID

gcloud beta service-extensions authz-extensions describe RESOURCE_NAME \
  --location=$LOCATION --project=$PROJECT_ID
```

#### List authz policies, agent gateways, and authz extensions via raw API

```bash
# authzPolicies
curl -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  "https://networksecurity.googleapis.com/v1alpha1/projects/${PROJECT_ID}/locations/${LOCATION}/authzPolicies"

# agentGateways
curl -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  "https://networkservices.googleapis.com/v1alpha1/projects/${PROJECT_ID}/locations/${LOCATION}/agentGateways"

# authzExtensions
curl -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  "https://serviceextensions.googleapis.com/v1alpha1/projects/${PROJECT_ID}/locations/${LOCATION}/authzExtensions"
```

### Step 7 — Verify the agent identity has the baseline roles

The agent identity itself needs enough permissions to function on the source side:

-   `roles/aiplatform.user` (Vertex AI User) — to run the ReasoningEngine
-   Agent Registry viewer role — to know what's registered
-   `roles/logging.logWriter`, `roles/monitoring.metricWriter`, telemetry roles — observability
-   `roles/browser` — needed for `resourcemanager.projects.get` during SDK init. Without it, the ReasoningEngine fails startup with `Failed to convert project number to project ID` (see known-issues §1).

### Step 7b — Check Principal Access Boundary (PAB) policies

A PAB policy can override IAM Allow and restrict the resources the principal set can reach.

```bash
# List org-wide PAB policies
gcloud iam principal-access-boundary-policies list \
  --organization="${ORGANIZATION_ID}" --location=global

# Find what's bound to the agent's principal set
gcloud iam policy-bindings search-target-policy-bindings \
  --project="${PROJECT_ID}" --target="${PRINCIPAL_SET}"
```

### Step 8 — PrincipalSet vs Principal

If permissions seem flaky, suspect the **PrincipalSet** binding. Move to a **1:1 Principal binding** (bind the specific service account directly) to verify.

## Quick reference: the checks in order

When triaging a 403 or connection failure, walk these in order:

1.  Confirm the error in the agent log (403 vs SSL Handshake Timeout vs Connection Reset).
2.  Find the *exact hostname* in the gateway log (if 403).
3.  Check IAP audit log: decision, principal, `iamEnforcementMode`, and watch for `unregisteredResource`.
3b. If no IAP audit entry, pull gateway proxy load-balancer log.
3c. If SSL Handshake Timeout or Connection Reset, run the PSC Subnet Exhaustion Check.
4.  Confirm hostname is registered.
5.  Check IAM on the registry/resource (`roles/iap.egressor`).
6.  Check authz extensions and policies.
7.  Confirm agent identity has baseline roles.
7b. Check PAB policies.
8.  If behavior is flaky, switch to direct Principal bindings.
