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

variable "project_id" {
  description = "GCP project ID hosting the Agent Gateway, registry IAM, and authz extensions"
  type        = string
}

variable "region" {
  description = "Region for the Agent Gateway, agent registry, network attachment, authz extensions, and authz policies. The regional Model Armor endpoint is derived from this."
  type        = string
}

variable "name" {
  description = "Name of the Agent Gateway resource. Also used as a prefix for the network attachment, authz extensions, and authz policies."
  type        = string
  default     = "agent-gateway"
}

variable "network_self_link" {
  description = "Self link of the VPC network where the PSC-Interface network attachment lives"
  type        = string
}

variable "agent_gateway_subnet_self_link" {
  description = "Self link of the dedicated subnet that hosts the Agent Gateway PSC-I network attachment (and the relocated MCP internal LB VIP)"
  type        = string
}

variable "agent_gateway_subnet_cidr" {
  description = "CIDR of the dedicated subnet — used to scope the inbound firewall rule"
  type        = string
}

variable "mcp_lb_target_port" {
  description = "TCP port on the MCP internal LB that the Agent Gateway PSC-I needs to reach"
  type        = number
  default     = 443
}

variable "enable_model_armor" {
  description = "When true, also create the Model Armor CONTENT_AUTHZ extension and policy. Requires both model_armor_request_template_id and model_armor_response_template_id."
  type        = bool
  default     = false
}

variable "model_armor_request_template_id" {
  description = "Model Armor request-side template ID (regional, in this project + region). Required when enable_model_armor = true."
  type        = string
  default     = null
}

variable "model_armor_response_template_id" {
  description = "Model Armor response-side template ID (regional, in this project + region). Required when enable_model_armor = true."
  type        = string
  default     = null
}

variable "model_armor_authz_hosts" {
  description = "Optional list of Host header values to scope the Model Armor CONTENT_AUTHZ policy to. Hosts match exact strings, so callers must include every Host value the agent might send — including BOTH Cloud Run URL forms when targeting Cloud Run services directly: the hash form `<svc>-<hash>-<region-abbrev>.a.run.app` AND the project-number form `<svc>-<project-number>.<region>.run.app`. Either URL routes to the same service, but a host missing from this list bypasses Model Armor / SDP. When empty, the policy applies to all gateway traffic. When non-empty, http_rules.to.operations.hosts is generated with one exact-match entry per element."
  type        = list(string)
  default     = []
}

variable "authz_extension_timeout" {
  description = "gRPC call timeout for the authz extensions (string format e.g. \"1s\")"
  type        = string
  default     = "2s"
}

variable "authz_extension_fail_open" {
  description = "If true, allow traffic through when an authz extension call fails. Set false in production to fail-closed."
  type        = bool
  default     = true
}

variable "iap_iam_enforcement_mode" {
  description = "Set to \"DRY_RUN\" to write metadata.iamEnforcementMode = DRY_RUN on the IAP authz extension — IAP evaluates IAM allow policies and emits decision logs but does not block. Leave null (the default) to omit iamEnforcementMode, which matches the IAP default of enforcing. Independent of this setting, the extension always sends metadata.iapPolicyVersion = \"V1\", which IAP now requires."
  type        = string
  default     = null
  validation {
    condition     = var.iap_iam_enforcement_mode == null || var.iap_iam_enforcement_mode == "DRY_RUN"
    error_message = "iap_iam_enforcement_mode must be null or \"DRY_RUN\" (the only non-default value the IAP authz extension accepts here)."
  }
}

variable "dns_peering_config" {
  description = "Optional DNS peering for the Agent Gateway. When set, the gateway resolves the listed `domains` (must end with a dot) against the target VPC's private Cloud DNS zones — required for the gateway to reach upstream MCP servers by hostname. Typical entries: the LB-fronted MCP zone (e.g. `mcp.<your-domain>.`) and `run.app.` when MCP servers are registered with their literal Cloud Run URLs and the networking module is provisioning the `enable_run_app_psc` private zone. Applied natively via `network_config.dns_peering_config` on the Agent Gateway resource."
  type = object({
    domains        = list(string)
    target_project = string
    target_network = string
  })
  default  = null
  nullable = true

  validation {
    condition     = var.dns_peering_config == null || alltrue([for d in coalesce(var.dns_peering_config.domains, []) : endswith(d, ".")])
    error_message = "Every entry in dns_peering_config.domains must end with a trailing dot (e.g. \"mcp.agent-gateway.sc-ccn.xyz.\")."
  }
}
