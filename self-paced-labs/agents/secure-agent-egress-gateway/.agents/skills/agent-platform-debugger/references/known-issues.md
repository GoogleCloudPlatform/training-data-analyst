# Best Known Issues (BKIs) and limitations

Concrete failure modes that come up repeatedly with the Agent Platform — symptoms and fixes. Read this when the symptom in front of you matches one of these patterns; it's faster than walking the full diagnostic flow.

--------------------------------------------------------------------------------

## 1. ReasoningEngine startup: "Failed to convert project number to project ID"

**Symptom:**
- Log name: `aiplatform.googleapis.com/reasoning_engine_stderr`
- Error text: `google.api_core.exceptions.Unknown: None` or `Failed to convert project number to project ID.`
- Happens during ReasoningEngine startup, before any user code runs.

**Cause:** The ReasoningEngine's system identity (the principal set it runs under) lacks `resourcemanager.projects.get`, which the Vertex AI SDK needs to resolve the project name during init.

**Fix:** Grant `roles/browser` to the ReasoningEngine principal set:

```bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="principalSet://agents.global.org-${ORG_ID}.system.id.goog/attribute.platformContainer/aiplatform/projects/${PROJECT_NUMBER}" \
  --role="roles/browser"
```

--------------------------------------------------------------------------------

## 2. ReasoningEngine startup: "Assembly Service failed to initialize"

**Symptom:** `[1099] ERROR: Assembly Service failed to initialize.` in `reasoning_engine_stderr`.

**Cause:** Generic "init failed" — usually a downstream symptom of either #1 (project-number resolution) or a runtime error in the agent's `set_up()` method.

**Investigation:** Pull all `severity=ERROR` from `reasoning_engine_stderr` around the same timestamp; the actual root cause is in the same window.

--------------------------------------------------------------------------------

## 3. Private-preview limit: one Reasoning Engine per project bonded to an Agent Gateway

**Symptom:** Updating a Reasoning Engine to use an Agent Gateway fails with `Internal error encountered` or `The specified parameters are invalid.`

**Cause:** During the private preview, a project can have only one active ReasoningEngine ↔ AgentGateway bonding. A second bonding attempt fails.

**Fix:** Either delete the existing bonded RE / AGW, or reuse the existing AGW for any new REs.

--------------------------------------------------------------------------------

## 4. 403 / "Egress request is not authorized" — missing `authz_policy` targeting the gateway

**Symptom:** Audit logs show `GatekeeperAuthorizer.AuthorizeUser` returning `Permission Denied` for `iap.webServiceVersions.egressViaIAP`.

**Cause:** The IAP authz extension exists but no `authz_policy` actually attaches it to the specific Agent Gateway. The extension is configured but the policy that targets the gateway resource is missing.

**Fix:** Verify there's an `authz_policy` in the consumer project that targets the specific `agentGateway` resource. Check with:

```bash
curl -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  "https://networksecurity.googleapis.com/v1alpha1/projects/${PROJECT_ID}/locations/${LOCATION}/authzPolicies"
```

Look for a policy whose `target.resources[]` includes the gateway's full resource name.

--------------------------------------------------------------------------------

## 5. IAP `ENFORCE` mode blocks Agent Engine startup

**Symptom:** Agent Engine instances fail to deploy or start, with 403s in startup logs.

**Cause:** With IAP in `ENFORCE` mode on the Agent Gateway, all egress is denied by default — including the bootstrap calls the agent runtime makes to `cloudresourcemanager`, `aiplatform`, `logging`, `monitoring`, etc. If those endpoints aren't registered AND the agent identity isn't granted `roles/iap.egressor` on them, startup never completes.

**Fix:** Make sure the bootstrap service set is registered in the Agent Registry (see field-manual's "Recommended Registry Structure: Consolidated Google APIs" section) and the agent identity has `roles/iap.egressor` on them. While debugging, flipping IAP to `DRY_RUN` lets you observe the failing destinations without blocking startup.

--------------------------------------------------------------------------------

## 6. Self-signed / Private CA destinations not supported (early versions)

**Symptom:** Agent fails to connect to internal MCP servers or tools that present self-signed or Private CA-issued certificates.

**Cause:** In private-preview / early Agent Gateway, the gateway's egress proxy can't validate self-signed cert chains.

**Mitigation:** Use publicly-trusted CA certificates for internal MCP servers, or wait for the platform enhancement that adds Private CA trust-anchor support.

--------------------------------------------------------------------------------

## 7. Principal Access Boundary (PAB) policies overriding IAM Allow

**Symptom:** Agent identity has the right roles bound (`roles/iap.egressor`, `roles/aiplatform.user`, etc.) and the resource is registered correctly, but calls still 403.

**Cause:** A Principal Access Boundary policy is restricting the scope of resources the principal can access. **PAB policies take precedence over IAM Allow policies** — even a correct binding does nothing if a PAB blocks the target resource.

**Investigation:** List PAB policies and their bindings for the agent identity:

```bash
# List org-wide PAB policies
gcloud iam principal-access-boundary-policies list \
  --organization="${ORGANIZATION_ID}" --location=global

# Find what's bound to a specific principal set / agent identity
gcloud iam policy-bindings search-target-policy-bindings \
  --project="${PROJECT_ID}" --target="${PRINCIPAL_SET}"

# Inspect a specific PAB
gcloud iam principal-access-boundary-policies search-policy-bindings "${PAB_POLICY_ID}" \
  --organization="${ORGANIZATION_ID}" --location=global
```

**Fix:** Either widen the PAB to include the destination resource, or remove the PAB binding from the agent's principal set if it shouldn't apply.

--------------------------------------------------------------------------------

## 8. Gateway proxy denies the request before IAP runs

**Symptom:** Requests fail with no IAP audit log entry — IAP never saw them.

**Cause:** The gateway's underlying egress proxy (a Google-managed Secure Web Proxy instance) enforces a deny-by-default posture *before* IAP authz runs. When the proxy itself denies a call, IAP doesn't get a chance to evaluate, so no IAP audit-log entry is produced for that call.

**Specific Case: CONNECT to PSC VIP (`240.0.0.2:443`) with Default Denied** In environments using Private Service Connect (PSC), clients resolve Google APIs to internal VIPs (e.g., `240.0.0.2:443`). Consequently, the outer tunnel request is logged as `CONNECT 240.0.0.2:443` in the proxy logs. **This is expected behavior.** Because TLS inspection is enabled on the Secure Web Proxy (SWP), the proxy intercepts this CONNECT tunnel and inspects the TLS handshake to extract the actual SNI hostname (e.g., `us-central1-aiplatform.googleapis.com`) for routing and policy evaluation. If the extracted SNI hostname is **not** registered in the Agent Registry, the proxy cannot match the route. The proxy then denies the connection, logging a `403` on the `CONNECT` request with `hostname: 240.0.0.2:443` and matching the `default_denied` rule.

**Investigation:** Pull the gateway proxy load-balancer logs:

```
jsonPayload.@type="type.googleapis.com/google.cloud.loadbalancing.type.LoadBalancerLogEntry"
resource.labels.gateway_type="SECURE_WEB_GATEWAY"
```

**Alternative (CLI Fallback):**

```bash
gcloud logging read 'jsonPayload.@type="type.googleapis.com/google.cloud.loadbalancing.type.LoadBalancerLogEntry" AND resource.labels.gateway_type="SECURE_WEB_GATEWAY"' --project=PROJECT_ID --limit=50
```

Key fields to inspect in the match:
- `httpRequest.status`: Look for `403`.
- `jsonPayload.enforcedGatewaySecurityPolicy.hostname`: Look for `240.0.0.2:443` (expected PSC CONNECT target).
- `jsonPayload.enforcedGatewaySecurityPolicy.matchedRules`: Look for `default_denied`.
- `jsonPayload.mtls.clientCertChainVerified`: Often `false` because the handshake was interrupted on route match failure.

**Fix:** Identify the inner hostname the agent was attempting to reach (e.g. `us-central1-aiplatform.googleapis.com`) and ensure ALL required hostname permutations are registered in the Agent Registry. The proxy relies on these registry entries to dynamically build its routing table.

--------------------------------------------------------------------------------

## 9. Cross-Project Agent Gateway import / creation failing (Code 13 Internal Error)

**Symptom:**
- Happening during `gcloud alpha network-services agent-gateways import` or creation.
- CLI rejects the command with a synchronous error: `ERROR: (gcloud.alpha.network-services.agent-gateways.import) { "code": 13, "message": "an internal error has occurred" }`
- Gateway YAML specifies **cross-project** infrastructure targets (e.g. a PSC network attachment or target DNS peering network residing inside another network host project, e.g., Project B).

**Cause:** To satisfy GCP's cross-project resource isolation controls, the API control-plane must validate that the gateway's billing project is authorized to map the target resource. The validation is executed under the **Agent Gateway Control Plane Service Agent** identity: `service-GATEWAY_PROJECT_NUMBER@gcp-sa-agentgateway.iam.gserviceaccount.com`

If this service agent lacks read permissions on the target network project, the validation fails, causing the import command to exit with a synchronous `Code 13` internal error.

**Investigation:**
1. Verify the caller has full Owner/Editor rights on both projects.
2. Check if the network attachment `connectionPreference` is set to `ACCEPT_AUTOMATIC`.
3. Check the IAM policy in the target network project. Verify if the gateway's **control-plane service agent** is missing: `service-GATEWAY_PROJECT_NUMBER@gcp-sa-agentgateway.iam.gserviceaccount.com`
4. Confirm if the **egress proxy service agent** (`service-GATEWAY_PROJECT_NUMBER@gcp-sa-dep.iam.gserviceaccount.com`) is present (typically holds `roles/compute.networkUser` and `roles/dns.peer`).

**Fix:** You must grant the control-plane service agent the required validation permissions inside the target network host project:

1.  Grant `roles/compute.networkUser` to validate the PSC network attachment:
    ```bash
    gcloud projects add-iam-policy-binding TARGET_NETWORK_PROJECT_ID \
      --member="serviceAccount:service-GATEWAY_PROJECT_NUMBER@gcp-sa-agentgateway.iam.gserviceaccount.com" \
      --role="roles/compute.networkUser"
    ```
2.  Grant `roles/dns.peer` to validate the DNS peering target:
    ```bash
    gcloud projects add-iam-policy-binding TARGET_NETWORK_PROJECT_ID \
      --member="serviceAccount:service-GATEWAY_PROJECT_NUMBER@gcp-sa-agentgateway.iam.gserviceaccount.com" \
      --role="roles/dns.peer"
    ```

--------------------------------------------------------------------------------

## 11. Reasoning Engine Container Crash: Python Dependency Mismatch / Startup Exceptions

**Symptom:**
- Log name: `aiplatform.googleapis.com/reasoning_engine_stderr`
- Error text: `ModuleNotFoundError: No module named '...'` or `ImportError: cannot import name '...'` or Python tracebacks.
- The Reasoning Engine fails to deploy or dies immediately after creation.

**Cause:** The Python code uploaded for the Reasoning Engine depends on external packages that were not specified or incorrectly specified during deployment.

**Fix:**
1.  Identify the missing or mismatched package from the traceback in `reasoning_engine_stderr`.
2.  Update your `requirements.txt` file or the `requirements` parameter in your deployment script (e.g. `deploy_agent.py`) to include the correct package and version constraint.
3.  Re-deploy the Reasoning Engine.

--------------------------------------------------------------------------------

## 12. mTLS Egress Failure: Invalid or Expired Client Certificate

**Symptom:**
- Gateway proxy load-balancer logs show connection drops or `403` errors.
- Logs contain `jsonPayload.mtls.clientCertChainVerified: false` or handshake failures.
- The agent fails to reach the destination MCP server when using mTLS.

**Cause:** The client certificate used by the Agent Gateway is expired, not yet valid, or not trusted by the destination server (CA mismatch).

**Fix:**
1.  Verify the certificate validity dates and CA chain.
2.  If expired or invalid, upload a new certificate to Certificate Manager and update the corresponding `ClientTlsPolicy` resource.
3.  Ensure the destination server trusts the CA that signed the gateway's client certificate.

--------------------------------------------------------------------------------

## 13. Model Armor integration on Agent Gateway fails with 500 / PERMISSION_DENIED

**Symptom:**
- Calling `remote_agent.async_stream_query` returns `500 Internal Server Error`.
- Gateway Request Logs show `grpcStatus: "PERMISSION_DENIED"` for the Model Armor backend and `authzPolicyInfo.result: DENIED`.

**How to Identify:** Search in Cloud Logging in the consumer project using the following query:

```
resource.type="networkservices.googleapis.com/Gateway"
jsonPayload.serviceExtensionInfo.backendTargetName : "modelarmor"
jsonPayload.serviceExtensionInfo.backendTargetType="BACKEND_SERVICE"
jsonPayload.serviceExtensionInfo.grpcStatus="PERMISSION_DENIED"
```

**Cause:** The gateway proxy (Secure Web Proxy) executing the inline Model Armor scan lacks the necessary permissions in the consumer project to call the Model Armor service. The callout runs under the Consumer's Service Extensions Service Agent (`gcp-sa-dep`).

> [!WARNING]
> Granting the legacy basic `roles/owner` or `roles/editor` roles to the Service Extensions Service Agent is **insufficient**. Granular data-plane permissions must be explicitly granted via specialized roles.

The required roles are:
1.  `roles/modelarmor.user`: Required to read and apply the template.
2.  `roles/modelarmor.calloutUser`: Required to initiate the egress gRPC callout.
3.  `roles/serviceusage.serviceUsageConsumer`: Required to consume quota and bill it.

**Fix:** Grant all three required roles to the **consumer-side delegated Service Extensions Service Agent** (`gcp-sa-dep`) in the consumer project.

```bash
gcloud projects add-iam-policy-binding CONSUMER_PROJECT_ID \
    --member="serviceAccount:service-CONSUMER_PROJECT_NUMBER@gcp-sa-dep.iam.gserviceaccount.com" \
    --role="roles/modelarmor.user"

gcloud projects add-iam-policy-binding CONSUMER_PROJECT_ID \
    --member="serviceAccount:service-CONSUMER_PROJECT_NUMBER@gcp-sa-dep.iam.gserviceaccount.com" \
    --role="roles/modelarmor.calloutUser"

gcloud projects add-iam-policy-binding CONSUMER_PROJECT_ID \
    --member="serviceAccount:service-CONSUMER_PROJECT_NUMBER@gcp-sa-dep.iam.gserviceaccount.com" \
    --role="roles/serviceusage.serviceUsageConsumer"
```

--------------------------------------------------------------------------------

## 15. Egress Blocked: Empty Agent Registry IAM Policy (403 Forbidden)

**Symptom:** All egress attempts through the gateway fail with a `403 Permission Denied` (logged as `Egress request is not authorized`).

**Cause:** The IAM policy on the `agent-registry` resource in the consumer project is empty or lacks bindings for the agent. The agent's service account must be explicitly granted the `roles/iap.egressor` role.

**Fix:** Grant the `roles/iap.egressor` role to the agent's service account at the registry level.

1.  Create a `policy.json` file:
    ```json
    {
      "bindings": [
        {
          "role": "roles/iap.egressor",
          "members": [
            "serviceAccount:YOUR_AGENT_SERVICE_ACCOUNT_EMAIL"
          ]
        }
      ]
    }
    ```
2.  Apply the policy to the Agent Registry:
    ```bash
    gcloud alpha iap web set-iam-policy policy.json \
        --resource-type=agent-registry \
        --project=YOUR_PROJECT_ID
    ```

--------------------------------------------------------------------------------

## 16. Reasoning Engine deployment fails with Code 13 (Internal Error)

**Symptom:**
- Vertex AI Reasoning Engine deployment fails with generic Code 13: `Failed to deploy to Agent Platform: Failed to update Agent Engine: {'code': 13, 'message': 'Please refer to our troubleshooting pages...'}`.
- The instance is immediately cleaned up.

### Root Cause A: Route Conflict in Shared Tenant Project (Wildcard Route Collision)
-   **Underlying Cause:** Vertex AI allocates a single, shared tenant project per customer project and region to host Reasoning Engines. If a customer already has a Reasoning Engine bonded to one Agent Gateway (`gateway-A`), the tenant project contains wildcard routes pointing to `gateway-A`. Trying to deploy another Reasoning Engine bonded to `gateway-B` in the same region fails due to route conflict.
-   **Fix:** A project/location can only support one active Agent Gateway bonding for Reasoning Engines.
    1.  Delete any active Reasoning Engines in the region bonded to the old gateway.
        ```bash
        gcloud beta ai reasoning-engines delete <REASONING_ENGINE_ID> --region=LOCATION
        ```
    2.  If the old Reasoning Engines are already deleted but routes are stuck, delete the old gateway resource to force cleanup:
        ```bash
        gcloud alpha network-services agent-gateways delete OLD_GATEWAY_NAME --location=LOCATION --project=PROJECT_ID
        ```
    3.  Retry deployment bonded to the new gateway.

### Root Cause B: Container Startup Timeout or Initialization Failure
-   **Underlying Cause:** The container fails to complete initialization within the startup timeout limit (due to syntax errors, missing dependencies, slow network calls, or permission denials).
-   **Fix:**
    1.  Verify the container can start locally.
    2.  Check Cloud Logging at the time of deployment for Python tracebacks.
    3.  De-risk initialization code by lazy loading heavy dependencies.

--------------------------------------------------------------------------------

## 17. Reasoning Engine outbound SSL handshake failure (CERTIFICATE_VERIFY_FAILED) with Egress Agent Gateway

**Symptom:**
- Log show: `CERTIFICATE_VERIFY_FAILED: self signed certificate in certificate chain`
- Occurs when a Reasoning Engine makes outbound calls while bound to an Egress Agent Gateway with `AGENT_IDENTITY` enabled.

**Cause:**
When outgoing connections pass through Secure Web Proxy (SWG) on the Agent Gateway, SWG performs TLS decryption and inspection using a dynamic certificate signed by its custom root CA. If the Reasoning Engine trust store does not contain these root certificates, outbound handshakes fail.

For custom container or prebuilt image deployments, the automated trust certificate injection is skipped, so the gateway's root certificates are not baked into the container.

**Fix / Workaround:**
-   **For Source/Config-based Deployments (Vertex AI SDK):** Create the Agent Gateway first and wait until provisioning completes. Verify root certificates are ready:
    ```bash
    gcloud alpha network-services agent-gateways describe GATEWAY_NAME \
        --location=LOCATION \
        --format="value(agentGatewayCard.rootCertificates)"
    ```
    Once this returns PEM certificates, deploy/update the Reasoning Engine. The pipeline will automatically bake them in.
-   **For Custom Container / Prebuilt Image Deployments:** Export the gateway's root certificates using the command above and manually copy/bake them into your Dockerfile:
    ```dockerfile
    COPY agw_root.crt /usr/local/share/ca-certificates/agw-gateway.crt
    RUN chmod 644 /usr/local/share/ca-certificates/agw-gateway.crt && update-ca-certificates
    ENV GRPC_DEFAULT_SSL_ROOTS_FILE_PATH=/etc/ssl/certs/ca-certificates.crt
    ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
    ```

--------------------------------------------------------------------------------

## 18. VPC Service Controls (VPC-SC) Perimeter Blocks Agent Gateway Provisioning

**Symptom:**
- Deployment of Agent Gateway fails when the project is inside a VPC-SC perimeter.
- Violation logs show `NETWORK_NOT_IN_SAME_SERVICE_PERIMETER` or similar VPC-SC blocks for calls between the consumer project and Google-managed projects.

**Cause:**
The Agent Gateway provisioning workflow uses Google-managed infrastructure outside the customer's VPC-SC perimeter. Because the calls target resources inside the perimeter using Google-managed service accounts, VPC-SC blocks them as unauthorized ingress.

**Fix:**
Configure ingress policies in your VPC-SC perimeter to allow the actuation identities. Two ingress rules are required:

### Rule 1: Gateway Control Plane Actuation
Allows the control plane service agent to manage gateway resources.

-   **From**:
    -   Identities: `serviceAccount:actuation-a@networkservices-prod.iam.gserviceaccount.com`
    -   Sources: Access Level `*`
-   **To**:
    -   Operations:
        -   Service: `compute.googleapis.com`
            -   Methods:
                -   `FirewallsService.Delete`, `FirewallsService.Get`
                -   `GlobalOperationsService.Get`
                -   `HealthChecksService.Delete`, `HealthChecksService.Get`
                -   `InstanceTemplatesService.Delete`, `InstanceTemplatesService.Get`
                -   `NetworksService.Delete`, `NetworksService.Get`
                -   `RegionAddressesService.Delete`
                -   `RegionBackendServicesService.Delete`, `RegionBackendServicesService.Get`
                -   `RegionForwardingRulesService.Delete`, `RegionForwardingRulesService.Get`
                -   `RegionInstanceGroupManagersService.Delete`, `RegionInstanceGroupManagersService.Get`
                -   `RegionOperationsService.Get`
                -   `RegionRoutersService.Delete`, `RegionRoutersService.Get`
                -   `RoutesService.Delete`, `RoutesService.Get`
                -   `ServiceAttachmentsService.Delete`, `ServiceAttachmentsService.Get`
                -   `SubnetworksService.Delete`, `SubnetworksService.Get`, `SubnetworksService.List`
                -   `ZonesService.List`
        -   Service: `cloudresourcemanager.googleapis.com`
            -   Methods: `Projects.SetIamPolicy`
        -   Service: `networkservices.googleapis.com` (Methods: `*`)
        -   Service: `networksecurity.googleapis.com` (Methods: `*`)
        -   Service: `serviceusage.googleapis.com` (Methods: `*`)
        -   Service: `certificatemanager.googleapis.com` (Methods: `*`)
        -   Service: `privateca.googleapis.com` (Methods: `*`)
    -   Resources: `projects/CUSTOMER_PROJECT_NUMBER`

### Rule 2: Agent Runtime
Allows the Vertex AI pipeline agent to access security resources.

-   **From**:
    -   Identities: `serviceAccount:cloud-aiplatform-pipeline-robot-prod@system.gserviceaccount.com`
    -   Sources: Access Level `*`
-   **To**:
    -   Operations:
        -   Service: `networksecurity.googleapis.com` (Methods: `*`)
    -   Resources: `projects/CUSTOMER_PROJECT_NUMBER`

Replace `CUSTOMER_PROJECT_NUMBER` with your actual project number.

--------------------------------------------------------------------------------

## 19. PSC Subnet Exhaustion Fails Agent Gateway Deployment

**Symptom:**
- Agent Gateway deployment fails or gets stuck during provisioning.
- Resource allocation errors related to IP addresses in GCE logs.

**Cause:**
The Private Service Connect (PSC) Network Attachment requires free IP addresses in its allocated subnet to establish connections. If the subnet (especially if it is small, like `/28`) runs out of free IP addresses, the gateway cannot allocate the necessary interfaces and deployment fails.

**Fix:**
Verify and expand the PSC subnet.

1.  Identify the subnetwork used by the gateway's Network Attachment:
    ```bash
    gcloud alpha network-services agent-gateways describe AGENT_GATEWAY_NAME --location=$LOCATION --project=$PROJECT_ID
    ```
    Look for `networkConfig.egress.networkAttachment`.
2.  Describe the Network Attachment to find the subnet name:
    ```bash
    gcloud compute network-attachments describe <ATTACHMENT_NAME> --region=$LOCATION
    ```
3.  Describe the subnetwork to check the CIDR range:
    ```bash
    gcloud compute networks subnetworks describe <SUBNET_NAME> --region=$LOCATION
    ```
4.  If the subnet is small (e.g. `/28` or `/29`), it may be exhausted. Allocate a larger subnet (minimum `/26` recommended) or expand the existing one, and recreate the network attachment and gateway if necessary.
