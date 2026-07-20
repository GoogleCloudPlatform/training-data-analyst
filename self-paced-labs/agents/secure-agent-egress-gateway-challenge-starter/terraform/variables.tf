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



/**
 * Root Terraform Variables
 *
 * Input variables for the gateway infrastructure.
 * Covers foundation, networking, MCP Cloud Run services, internal LB, and DNS.
 */

# ==============================================================================
# CORE PROJECT CONFIGURATION
# ==============================================================================

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "gateway"
}

variable "organization_id" {
  description = "GCP organization ID (numeric). Required when agent engine is enabled."
  type        = string
  default     = null
}

variable "platform_admin_members" {
  description = "List of IAM members granted demo-wide roles: discoveryengine.admin always; modelarmor.admin and modelarmor.floorSettingsAdmin when enable_model_armor; aiplatform.user when enable_agent_engine (e.g. [\"user:admin@example.com\"])"
  type        = list(string)
  default     = []
}

variable "cloudbuild_bucket_name" {
  description = "Override the Cloud Build source bucket name. Defaults to <project_id>_cloudbuild, which matches the bucket gcloud/Cloud Build SDKs auto-pick when no --gcs-source-staging-dir is passed; overriding the name breaks that convenience."
  type        = string
  default     = null
}

# ==============================================================================
# NETWORKING CONFIGURATION
# ==============================================================================

variable "vpc_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "gateway-vpc"
}

variable "subnet_name" {
  description = "Name of the primary subnet"
  type        = string
  default     = "mcp-subnet-us-central1"
}

variable "primary_subnet_cidr" {
  description = "CIDR range for the primary subnet"
  type        = string
  default     = "10.0.0.0/20"
}

variable "proxy_subnet_cidr" {
  description = "CIDR range for the proxy-only subnet"
  type        = string
  default     = "10.9.0.0/24"
}

variable "psc_subnet_cidr" {
  description = "CIDR range for the Private Service Connect subnet"
  type        = string
  default     = "10.10.0.0/24"
}

variable "gateway_scope" {
  description = "Gateway scope: 'regional' for regional internal gateway, or null to skip gateway provisioning"
  type        = string
  default     = "regional"
  validation {
    condition     = var.gateway_scope == null || contains(["regional"], var.gateway_scope)
    error_message = "gateway_scope must be 'regional' or null"
  }
}

# ==============================================================================
# DNS CONFIGURATION
# ==============================================================================

variable "dns_zone_domain" {
  description = "The domain name for the public DNS zone (must end with a dot, e.g., 'example.com.'). Only used when `enable_cloud_run_private_networking = true` (Certificate Manager validates the MCP LB cert against this zone)."
  type        = string
  default     = null
}

variable "dns_zone_name" {
  description = "The name of the existing Cloud DNS managed zone. If not provided, derived from dns_zone_domain."
  type        = string
  default     = null
}

variable "enable_certificate_manager" {
  description = "Enable Certificate Manager to create managed certificates for the DNS domain. Only takes effect when `enable_cloud_run_private_networking = true` (the cert is only needed by the MCP internal Application LB, which the master flag also gates)."
  type        = bool
  default     = false
}

# ==============================================================================
# CLOUD RUN PRIVATE NETWORKING — master switch for the secure MCP path
# ==============================================================================

variable "enable_cloud_run_private_networking" {
  description = "Master switch for the secure MCP networking path. When true, MCP Cloud Run services run with `ingress = INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` behind a Google-managed internal Application LB at `<service>.<mcp_internal_dns_zone.domain>`, and the Agent Registry registers each MCP service at the LB-fronted URL. The internal LB, MCP private DNS zone, public DNS zone, Certificate Manager cert (when `enable_certificate_manager = true`), and Agent Gateway peering for `mcp.<domain>.` are all gated on this flag. When false (default), Cloud Run runs with `ingress = INGRESS_TRAFFIC_ALL`, the registry uses the literal `*.run.app` URLs, and none of the above private-network infra is created — the simplest path for new users who don't own a DNS zone."
  type        = bool
  default     = false
}

# ==============================================================================
# MCP SERVICES (CLOUD RUN) CONFIGURATION
# ==============================================================================

variable "mcp_internal_dns_zone" {
  description = <<-EOT
    Private DNS zone hosting <service>.<domain> A records for the MCP Cloud Run
    services. Attached to the VPC so workloads (and Agent Engine via DNS
    peering) resolve internally.

    Only used when `enable_cloud_run_private_networking = true` (the zone
    fronts the MCP internal Application LB, which the master flag also gates).
    Required when the master flag is true; ignored otherwise.

    `domain` MUST be a real subdomain (typically "mcp.<dns_zone_domain>") so
    Certificate Manager can issue a Google-managed regional cert that the
    Agent Gateway will validate. Agent Gateway does NOT currently accept the
    self-signed cert that the LB falls back to when the domain is unrouteable
    (e.g. the legacy "mcp-server.internal."). The self-signed / mcp-server.internal
    code path is retained for future use once Agent Gateway gains self-signed
    cert support.
  EOT
  type = object({
    name   = optional(string, "mcp-server-internal")
    domain = string
  })
  # null on the simple path (`enable_cloud_run_private_networking = false`); the
  # cross-variable validation below promotes it to required when the master flag
  # flips on. Every consumer in main.tf/outputs.tf already guards for null.
  default = null
  validation {
    condition     = var.mcp_internal_dns_zone == null || endswith(var.mcp_internal_dns_zone.domain, ".")
    error_message = "mcp_internal_dns_zone.domain must end with a trailing dot (e.g. \"mcp.example.com.\")."
  }
  validation {
    condition     = !var.enable_cloud_run_private_networking || var.mcp_internal_dns_zone != null
    error_message = "mcp_internal_dns_zone is required when enable_cloud_run_private_networking = true (it supplies the per-service domain fronting the MCP internal Application LB). Set it in your tfvars (typically mcp_internal_dns_zone = { domain = \"mcp.<dns_zone_domain>\" }), or leave enable_cloud_run_private_networking = false to use the *.run.app simple path."
  }
}

variable "mcp_services" {
  description = "Map of MCP service name to deployment configuration. The map key becomes the Cloud Run service name AND the URL-mask token (e.g. legacy-dms.<mcp_internal_dns_zone.domain> -> Cloud Run service 'legacy-dms')."
  type = map(object({
    image              = string
    container_port     = optional(number, 8080)
    otel_service_name  = optional(string)
    min_instance_count = optional(number, 0)
    max_instance_count = optional(number, 3)
    cpu                = optional(string, "1")
    memory             = optional(string, "512Mi")
    env                = optional(map(string), {})
  }))
  default = {}
}

variable "mcp_tool_specs" {
  description = "Map of MCP service name -> path to its toolspec.json (relative to the terraform/ directory or absolute). Required for every key in var.mcp_services when enable_agent_registry_endpoints = true; the toolspec is uploaded into the Agent Registry entry as the MCP server spec. Note: the var.mcp_services key (which becomes the Agent Registry service ID and the LB hostname) does not need to match the source directory name (e.g. income-verification -> ../src/income-verification-api/toolspec.json)."
  type        = map(string)
  default     = {}
}

variable "mcp_lb_protocol" {
  description = <<-EOT
    Front-end protocol for the MCP internal Application LB. With HTTPS, the LB
    serves a Google-managed regional cert for *.mcp.<dns_zone_domain> when
    enable_certificate_manager = true and gateway_scope = "regional"; otherwise
    it falls back to an auto-generated self-signed cert for *.<mcp_internal_dns_zone.domain>
    (note: not validatable by Agent Gateway today).

    Only used when `enable_cloud_run_private_networking = true` (the LB itself
    is gated by that flag).
  EOT
  type        = string
  default     = "HTTPS"
  validation {
    condition     = contains(["HTTP", "HTTPS"], var.mcp_lb_protocol)
    error_message = "mcp_lb_protocol must be HTTP or HTTPS."
  }
}

# ==============================================================================
# MODEL ARMOR CONFIGURATION
# ==============================================================================

variable "enable_model_armor" {
  description = "Enable Model Armor template and IAM bindings"
  type        = bool
  default     = false
}

variable "model_armor_request_template_id" {
  description = "ID for the request-side Model Armor template (RAI + PI/jailbreak; no SDP). Wired into the Agent Gateway CONTENT_AUTHZ extension as request_template_id."
  type        = string
  default     = "agw-request-template"
}

variable "model_armor_response_template_id" {
  description = "ID for the response-side Model Armor template (RAI; SDP advanced_config when model_armor_sdp_enforcement = ENABLED). Wired into the Agent Gateway CONTENT_AUTHZ extension as response_template_id."
  type        = string
  default     = "agw-response-template"
}

variable "model_armor_rai_filters" {
  description = "RAI (Responsible AI) filter configurations. filter_type can be: SEXUALLY_EXPLICIT, HATE_SPEECH, HARASSMENT, DANGEROUS. confidence_level can be: LOW_AND_ABOVE, MEDIUM_AND_ABOVE, HIGH"
  type = list(object({
    filter_type      = string
    confidence_level = string
  }))
  default = [
    {
      filter_type      = "HATE_SPEECH"
      confidence_level = "MEDIUM_AND_ABOVE"
    },
    {
      filter_type      = "HARASSMENT"
      confidence_level = "MEDIUM_AND_ABOVE"
    },
    {
      filter_type      = "SEXUALLY_EXPLICIT"
      confidence_level = "MEDIUM_AND_ABOVE"
    }
  ]
}

variable "model_armor_sdp_enforcement" {
  description = "Sensitive Data Protection filter enforcement setting (ENABLED or DISABLED)"
  type        = string
  default     = "ENABLED"
  validation {
    condition     = contains(["ENABLED", "DISABLED"], var.model_armor_sdp_enforcement)
    error_message = "model_armor_sdp_enforcement must be ENABLED or DISABLED"
  }
}

variable "model_armor_pii_types" {
  description = "Info types whose findings the response Model Armor template's deidentify transformation replaces with the type-name placeholder. Model Armor's SDP filter still runs Google's built-in detectors (including PERSON_NAME) regardless of this list, but only findings whose info type appears here are transformed — anything else is passed through to the agent unchanged. Keep identity fields the agent needs for downstream reasoning (e.g. PERSON_NAME) OUT of this list."
  type        = list(string)
  default = [
    "US_SOCIAL_SECURITY_NUMBER",
    "CREDIT_CARD_NUMBER",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "PASSPORT",
    "DATE_OF_BIRTH",
    "MEDICAL_RECORD_NUMBER",
    "IP_ADDRESS",
    "STREET_ADDRESS",
  ]
}

variable "model_armor_pi_jailbreak_enforcement" {
  description = "PI and jailbreak filter enforcement setting (ENABLED or DISABLED)"
  type        = string
  default     = "ENABLED"
}

variable "model_armor_pi_jailbreak_confidence" {
  description = "PI and jailbreak filter confidence level (LOW_AND_ABOVE, MEDIUM_AND_ABOVE, or HIGH)"
  type        = string
  default     = "LOW_AND_ABOVE"
  validation {
    condition     = contains(["LOW_AND_ABOVE", "MEDIUM_AND_ABOVE", "HIGH"], var.model_armor_pi_jailbreak_confidence)
    error_message = "model_armor_pi_jailbreak_confidence must be one of: LOW_AND_ABOVE, MEDIUM_AND_ABOVE, HIGH"
  }
}

variable "model_armor_malicious_uri_enforcement" {
  description = "Malicious URI filter enforcement setting (ENABLED or DISABLED)"
  type        = string
  default     = "ENABLED"
}

variable "enable_model_armor_mcp_floor_setting" {
  description = "Enable Model Armor floor setting for MCP server protection (BigQuery MCP)"
  type        = bool
  default     = true
}

variable "enable_model_armor_vertex_ai" {
  description = "Enable Model Armor integration with Vertex AI (floor setting + IAM)"
  type        = bool
  default     = false
}

variable "model_armor_vertex_ai_inspect_only" {
  description = "When true, Vertex AI uses INSPECT_ONLY mode; when false, uses INSPECT_AND_BLOCK"
  type        = bool
  default     = false
}

variable "model_armor_vertex_ai_cloud_logging" {
  description = "Enable Cloud Logging for Vertex AI Model Armor sanitization"
  type        = bool
  default     = true
}

variable "enable_model_armor_gemini_enterprise" {
  description = "Enable a multi-region Model Armor template for Gemini Enterprise"
  type        = bool
  default     = false
}

variable "model_armor_gemini_enterprise_template_id" {
  description = "ID for the Gemini Enterprise Model Armor template"
  type        = string
  default     = "gemini-enterprise-safety-template"
}

variable "model_armor_gemini_enterprise_location" {
  description = "Multi-region location for the Gemini Enterprise template"
  type        = string
  default     = "us"
  validation {
    condition     = contains(["us", "eu"], var.model_armor_gemini_enterprise_location)
    error_message = "model_armor_gemini_enterprise_location must be 'us' or 'eu'"
  }
}


# ==============================================================================
# AGENT ENGINE DEMO CONFIGURATION
# ==============================================================================

variable "enable_agent_engine" {
  description = "Enable the Agent Engine demo (chat API + LB for token exchange)"
  type        = bool
  default     = false
}

# ==============================================================================
# PSC INTERFACE CONFIGURATION
# ==============================================================================

variable "enable_psc_interface" {
  description = "Enable PSC Interface for Vertex AI Agent Engine (network attachment, firewall, IAM)"
  type        = bool
  default     = false
}

variable "psc_interface_subnet_cidr" {
  description = "CIDR for the PSC Interface subnet (min /28, must not overlap with psc_subnet_cidr)"
  type        = string
  default     = "10.11.0.0/28"
}

variable "psc_interface_dns_zone" {
  description = "Private DNS zone for PSC Interface DNS peering. `domain` MUST end with a trailing dot."
  type = object({
    name   = optional(string, "psc-interface-dns-zone")
    domain = string
  })
  default = null
  validation {
    condition     = var.psc_interface_dns_zone == null || endswith(var.psc_interface_dns_zone.domain, ".")
    error_message = "psc_interface_dns_zone.domain must end with a trailing dot (e.g. \"mcp.example.com.\")."
  }
}

variable "enable_run_app_psc" {
  description = "Provision a private Cloud DNS zone for `run.app.` (attached to the VPC) that overrides every Cloud Run hostname to the Private Service Connect for Google APIs VIP (`private.googleapis.com`, 199.36.153.8). Lets the agent reach Cloud Run services with `ingress = internal-and-cloud-load-balancing` using their literal `*.run.app` URLs without opening them to the public internet. Pair with adding `run.app.` to `agent_gateway_dns_peering_config.domains` so the Agent Gateway resolves the override."
  type        = bool
  default     = false
}

variable "run_app_psc_regions" {
  description = "Regional `run.app` subdomains to publish wildcard A records for when `enable_run_app_psc = true`. Cloud DNS wildcards bind to a single label position, so `*.run.app.` does NOT cover `<service>-<num>.<region>.run.app.` — every region the gateway needs to reach must be enumerated here."
  type        = list(string)
  default = [
    "us-central1",
    "a",
  ]
}

# ==============================================================================
# AGENT GATEWAY CONFIGURATION
# ==============================================================================

variable "enable_agent_gateway" {
  description = "Provision the Agent Gateway, its dedicated PSC-I subnet, the IAP/Model Armor authz extensions and policies, and the IAP agent registry IAM grant. Also relocates the MCP internal LB VIP into the dedicated subnet."
  type        = bool
  default     = false
}

variable "agent_gateway_name" {
  description = "Name of the Agent Gateway resource (and prefix for its network attachment, authz extensions, and authz policies)"
  type        = string
  default     = "agent-gateway"
}

variable "agent_gateway_subnet_cidr" {
  description = "CIDR for the Agent Gateway dedicated subnet. Min /28, RFC1918, must not overlap 10.0.0.0/24, 10.0.1.0/24, or 10.0.2.0/24 (Agent Gateway egress restrictions)."
  type        = string
  default     = "10.20.0.0/28"
}

variable "agent_gateway_authz_fail_open" {
  description = "If true, allow traffic through the Agent Gateway when an authz extension call fails. Set false in production."
  type        = bool
  default     = true
}

variable "agent_gateway_iap_iam_enforcement_mode" {
  description = "Set to \"DRY_RUN\" to put the Agent Gateway IAP authz extension into dry-run mode (IAM allow policies evaluated and logged but not blocking). Leave null (the default) to omit the metadata key, which matches the IAP default of enforcing."
  type        = string
  default     = null
  validation {
    condition     = var.agent_gateway_iap_iam_enforcement_mode == null || var.agent_gateway_iap_iam_enforcement_mode == "DRY_RUN"
    error_message = "agent_gateway_iap_iam_enforcement_mode must be null or \"DRY_RUN\"."
  }
}

variable "agent_gateway_dns_peering_config" {
  description = "Optional DNS peering for the Agent Gateway. Lets the gateway resolve the listed `domains` (each must end with a dot) against the target VPC's private Cloud DNS zones — required for the gateway to reach upstream MCP servers by hostname (e.g. `mcp.agent-gateway.sc-ccn.xyz.` records that point at the MCP internal LB). `target_project` defaults to `var.project_id` and `target_network` defaults to the self-link of the VPC this module creates; override only when peering against a VPC in a different project or network. Applied natively via `network_config.dns_peering_config` on the Agent Gateway resource."
  type = object({
    domains        = list(string)
    target_project = optional(string)
    target_network = optional(string)
  })
  default  = null
  nullable = true
}

# ==============================================================================
# AGENT REGISTRY ENDPOINT CONFIGURATION
# ==============================================================================

variable "enable_agent_registry_endpoints" {
  description = "Enable the Agent Registry endpoint provisioner (registers Google API and custom service endpoints)"
  type        = bool
  default     = false
}

variable "agent_registry_google_apis" {
  description = "Map of Google API IDs to their display names to register in Agent Registry"
  type        = map(string)
  default = {
    aiplatform             = "Vertex AI Platform"
    cloudresourcemanager   = "Cloud Resource Manager"
    global-discoveryengine = "Global Discovery Engine"
    discoveryengine        = "Discovery Engine"
    logging                = "Logging"
    monitoring             = "Monitoring"
    oauth2                 = "OAuth2"
    telemetry              = "Telemetry"
    trace                  = "Trace"
    agentregistry          = "Agent Registry"
    iap                    = "Identity-Aware Proxy"
  }
}

variable "agent_registry_custom_services" {
  description = "List of custom services to register in Agent Registry"
  type = list(object({
    id           = string
    display_name = string
    url          = string
    description  = optional(string)
  }))
  default = [
    {
      id           = "github"
      display_name = "Github"
      url          = "https://github.com"
    }
  ]
}

# ==============================================================================
# AUDIT LOGGING
# ==============================================================================

variable "logging_data_access" {
  description = "Data access audit log configuration passed to the foundation module. Defaults to ADMIN_READ + DATA_READ + DATA_WRITE for the special 'allServices' key (project-wide audit logging across every API). Override per-service to scope down or to exempt members."
  type = map(object({
    ADMIN_READ = optional(object({ exempted_members = optional(list(string), []) }))
    DATA_READ  = optional(object({ exempted_members = optional(list(string), []) }))
    DATA_WRITE = optional(object({ exempted_members = optional(list(string), []) }))
  }))
  default = {
    "allServices" = {
      ADMIN_READ = {}
      DATA_READ  = {}
      DATA_WRITE = {}
    }
  }
  nullable = false
}
