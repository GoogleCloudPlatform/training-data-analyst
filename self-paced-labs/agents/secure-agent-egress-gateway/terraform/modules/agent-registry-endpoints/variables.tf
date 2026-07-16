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
  description = "The GCP project ID"
  type        = string
}

variable "location" {
  description = "The GCP location for the Agent Registry"
  type        = string
}

variable "google_apis" {
  description = "Map of Google API IDs to their display names to register with all regional/mtls variants"
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
    iamcredentials         = "IAM Credentials"
  }
}

variable "custom_services" {
  description = "List of custom services to register"
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

variable "mcp_servers" {
  description = "Map of MCP service name -> registration metadata. The map key becomes the Agent Registry service ID. Every entry must set tool_spec_path to an existing toolspec.json (validated at plan time); display_name defaults to the map key when null."
  type = map(object({
    display_name   = optional(string)
    description    = optional(string)
    tool_spec_path = optional(string)
  }))
  default = {}
}

variable "mcp_url_mode" {
  description = "URL strategy for MCP server registration. 'internal_lb' registers https://<key>.<mcp_internal_dns_domain> (the canonical private hostname fronted by the MCP internal LB). 'cloud_run' registers the *.run.app URL from mcp_service_urls."
  type        = string
  default     = "internal_lb"
  validation {
    condition     = contains(["internal_lb", "cloud_run"], var.mcp_url_mode)
    error_message = "mcp_url_mode must be 'internal_lb' or 'cloud_run'."
  }
}

variable "mcp_internal_dns_domain" {
  description = "Internal DNS domain for MCP services (e.g. 'mcp-server.internal.' or 'mcp-server.internal'). Trailing dot is stripped before constructing URLs. Required when mcp_url_mode = 'internal_lb'."
  type        = string
  default     = null
}

variable "mcp_service_urls" {
  description = "Map of MCP service name -> *.run.app URL. Pass module.mcp_services.service_urls. Required when mcp_url_mode = 'cloud_run'; must contain a URL for every key in mcp_servers."
  type        = map(string)
  default     = {}
}
