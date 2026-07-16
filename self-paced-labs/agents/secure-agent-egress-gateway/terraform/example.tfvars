# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# ##############################################################################
# # REQUIRED — edit these three values before `terraform apply`.               #
# # Every variable below this block has a sensible default tuned for the demo. #
# ##############################################################################

# GCP project ID where all resources will be created.
project_id = "my-gcp-project-id"

# GCP organization ID (numeric).
organization_id = "123456789012"

# Members granted demo-wide roles
platform_admin_members = ["user:admin@example.com"]

# IAP Enforcement Mode ("DRY_RUN" or null)
agent_gateway_iap_iam_enforcement_mode = "DRY_RUN"


# ##############################################################################
# # OPTIONAL — everything below this line has a default and is pre-tuned for   #
# # the demo. Override only when you know you need to.                         #
# ##############################################################################

# ==============================================================================
# CLOUD RUN PRIVATE NETWORKING — feature flag for the secure MCP path
# ==============================================================================
#
# false (default): MCP Cloud Run services run with `ingress = all` and the
#   Agent Registry registers each service at its literal *.run.app URL. No
#   internal LB, no MCP private DNS zone, no public DNS zone, no Certificate
#   Manager cert, no Agent Gateway peering for `mcp.<domain>.`. Simplest path
#   — works with no domain ownership.
#
# true: provisions all of the above so the agent reaches MCP via
#   `<service>.<mcp_internal_dns_zone.domain>` over an internal Application LB.
#   Requires you to own `dns_zone_domain` (so Certificate Manager can validate
#   the LB cert) and to set `mcp_internal_dns_zone` and `mcp_lb_protocol`.
#   See the "Secure path (opt-in)" section below.
enable_cloud_run_private_networking = false

# ==============================================================================
# DNS CONFIGURATION (secure path opt-in)
# ==============================================================================

# Public DNS zone domain (must end with a dot)
# A Cloud DNS managed zone must already exist for this domain.
# Only used when enable_cloud_run_private_networking = true.
dns_zone_domain = "demo.example.com."

# Enable Google Certificate Manager for automatic TLS certificates.
# Provisions managed certs matching *.internal.<dns_zone_domain>.
# Only takes effect when enable_cloud_run_private_networking = true.
enable_certificate_manager = true

# ==============================================================================
# MCP SERVICES (CLOUD RUN)
# ==============================================================================

# Private DNS zone hosting per-service A records, attached to the VPC so
# workloads (and Agent Engine via DNS peering) resolve internally.
# Only used when enable_cloud_run_private_networking = true.
#
# `domain` MUST be a real subdomain of dns_zone_domain (e.g.
# "mcp.${dns_zone_domain}") so Certificate Manager can issue a Google-managed
# regional cert. Agent Gateway does not currently validate self-signed certs,
# so values like "mcp-server.internal." (the legacy default) only work when
# enable_agent_gateway = false.
mcp_internal_dns_zone = {
  name   = "mcp-server-internal"
  domain = "mcp.demo.example.com."
}

# Front-end protocol for the MCP internal Application LB. HTTPS (default) uses
# the Google-managed regional cert covering *.mcp.<dns_zone_domain> when
# enable_certificate_manager = true; otherwise it falls back to a self-signed
# cert for *.<mcp_internal_dns_zone.domain>. Set "HTTP" for the simplest demo.
# Only used when enable_cloud_run_private_networking = true.
mcp_lb_protocol = "HTTPS"

# Map of MCP service name to deployment configuration. The map key becomes the
# Cloud Run service name AND the URL-mask token (e.g. legacy-dms ->
# legacy-dms.${mcp_internal_dns_zone.domain}). Adding a new service is a Cloud
# Run deploy plus one entry in this map (a DNS A record is added automatically).
# The `us-docker.pkg.dev/cloudrun/container/placeholder` image is a Google-
# provided stub; replace with your own image in Artifact Registry before the
# service handles real traffic (Skaffold deploys overwrite the image tag).
# min_instance_count = 1 keeps one warm instance per service. MCP tools/list
# runs at the start of every agent turn with a 5s initialize() timeout; a
# scale-to-zero cold start (~16-19s observed) trips that timeout and drops all
# MCP tools for the request. Set to 0 if you don't mind cold-start failures.
mcp_services = {
  legacy-dms = {
    image              = "us-docker.pkg.dev/cloudrun/container/placeholder"
    min_instance_count = 1
  }
  corporate-email = {
    image              = "us-docker.pkg.dev/cloudrun/container/placeholder"
    min_instance_count = 1
  }
  income-verification = {
    image              = "us-docker.pkg.dev/cloudrun/container/placeholder"
    min_instance_count = 1
  }
}

# Per-service toolspec paths (relative to terraform/ or absolute). Required for
# every active mcp_services key when enable_agent_registry_endpoints = true. The
# toolspec is uploaded as the MCP server spec on the Agent Registry entry so
# clients see the full tool catalogue.
mcp_tool_specs = {
  legacy-dms          = "../src/legacy-dms/toolspec.json"
  corporate-email     = "../src/corporate-email/toolspec.json"
  income-verification = "../src/income-verification-api/toolspec.json"
}

# ==============================================================================
# MODEL ARMOR - AI Safety Screening
# ==============================================================================

# Enable Model Armor templates for AI safety filtering on LB traffic
enable_model_armor = true

# Enable a multi-region template for Gemini Enterprise
enable_model_armor_gemini_enterprise = true

# Prompt injection / jailbreak detection confidence threshold
# Options: LOW_AND_ABOVE, MEDIUM_AND_ABOVE, HIGH
model_armor_pi_jailbreak_confidence = "MEDIUM_AND_ABOVE"

# Sensitive Data Protection enforcement (ENABLED or DISABLED).
# When ENABLED, the model-armor module also creates a DLP inspect template
# (US_SOCIAL_SECURITY_NUMBER), a DLP de-identify template (replace with
# infoType), and binds the Model Armor service agent to roles/dlp.{user,reader}.
# The response Model Armor template's sdp_settings.advanced_config is wired to
# those DLP templates so SSNs in MCP responses are redacted in flight.
model_armor_sdp_enforcement = "ENABLED"

# ==============================================================================
# AGENT ENGINE - Vertex AI Agent Engine
# ==============================================================================

# Enable Vertex AI Agent Engine infrastructure (IAM, networking)
enable_agent_engine = true

# ==============================================================================
# PSC INTERFACE - Private Service Connect for Agent Engine
# ==============================================================================

# Enable PSC Interface for Agent Engine to call back into the VPC.
# Creates network attachment, firewall rules, and IAM bindings. Independent
# of the master flag — leave true to give Agent Engine VPC reachability even
# when private networking is off.
enable_psc_interface = true

# Private DNS zone for Agent Engine to peer so it can resolve internal MCP
# hostnames. Only takes effect when `enable_cloud_run_private_networking = true`
# (with the master flag off there are no private hostnames to resolve, so the
# zone would be an orphan). `domain` MUST end with a trailing dot.
psc_interface_dns_zone = {
  name   = "mcp-server-internal"
  domain = "mcp.demo.example.com." # Must match mcp_internal_dns_zone.domain
}

# ==============================================================================
# AGENT GATEWAY - Governance plane in front of MCP services
# ==============================================================================

# Enable the Agent Gateway (AGENT_TO_ANYWHERE for MCP), its dedicated PSC-I
# subnet, IAP and Model Armor authz extensions/policies, and the IAP agent
# registry IAM grant for the project's Vertex AI agents. When enabled, the MCP
# internal LB VIP is relocated into the dedicated subnet so PSC-I and the LB
# share a subnet (forces an LB recreation; expected for the demo).
enable_agent_gateway = true

# Name of the Agent Gateway resource (also used as a prefix for the network
# attachment, authz extensions, and authz policies).
agent_gateway_name = "agent-gateway"

# Dedicated subnet for the Agent Gateway PSC-I network attachment AND the
# relocated MCP internal LB VIP. Min /28, RFC1918, must NOT overlap
# 10.0.0.0/24, 10.0.1.0/24, or 10.0.2.0/24 (Agent Gateway egress restrictions).
agent_gateway_subnet_cidr = "10.20.0.0/28"

# When true, allow traffic through the Agent Gateway if an authz extension
# fails. Set false in production to fail-closed.
agent_gateway_authz_fail_open = true

# DNS peering: lets the gateway resolve customer-VPC private DNS zones so it
# can reach upstream MCP servers by hostname. The `mcp.<domain>.` entry for
# the internal LB hostnames is auto-prepended when
# `enable_cloud_run_private_networking = true`, so this list only needs any
# extra domains. Each domain MUST end with a trailing dot. Set the whole var
# to null to skip entirely.
#
# `target_project` defaults to var.project_id and `target_network` defaults
# to the VPC this module creates — only set them to peer against a different
# project/network.
agent_gateway_dns_peering_config = {
  domains = [
    # "run.app.",   # uncomment when enable_run_app_psc = true
  ]
}

# Provision a private DNS zone for `run.app.` (attached to the gateway VPC)
# that overrides every Cloud Run hostname to the Private Service Connect for
# Google APIs VIP (`private.googleapis.com`, 199.36.153.8). Lets the agent
# reach Cloud Run MCP servers using their literal `*.run.app` URLs while
# Cloud Run keeps `ingress = internal-and-cloud-load-balancing`. Pair with
# adding `run.app.` to `agent_gateway_dns_peering_config.domains` above.
enable_run_app_psc = false

# Regional `run.app` subdomains to publish wildcard A records for. Cloud DNS
# wildcards bind to a single label position, so `*.run.app.` does NOT cover
# `<service>-<num>.<region>.run.app.` — every region the gateway needs to
# reach must be enumerated here. Defaults cover us-central1 plus the legacy
# `*.a.run.app.` form.
# run_app_psc_regions = ["us-central1", "a"]


# ==============================================================================
# AGENT REGISTRY ENDPOINTS
# ==============================================================================

# Enable the Agent Registry endpoint provisioner
enable_agent_registry_endpoints = true

# Optional: Override the default list of Google APIs to register. Map key is
# the service short name; value is the human-readable display name surfaced in
# the Agent Registry UI.
agent_registry_google_apis = {
  aiplatform           = "Vertex AI Platform"
  cloudresourcemanager = "Cloud Resource Manager"
  discoveryengine      = "Discovery Engine"
  logging              = "Logging"
  monitoring           = "Monitoring"
  oauth2               = "OAuth2"
  telemetry            = "Telemetry"
  trace                = "Trace"
  agentregistry        = "Agent Registry"
  iap                  = "Identity-Aware Proxy"
  modelarmor           = "Model Armor"
  iamcredentials       = "IAM Credentials"
}

# Optional: Override or add custom (non-Google) services to register
agent_registry_custom_services = [
  {
    id           = "github"
    display_name = "Github"
    url          = "https://github.com"
  }
]
