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

variable "region" {
  description = "The GCP region for the Cloud Run services"
  type        = string
}

variable "services" {
  description = "Map of MCP service name to deployment configuration. Service name is used as the Cloud Run service name and as the URL-mask token (e.g. <name>.mcp-server.internal)."
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
}

variable "service_account_roles" {
  description = "IAM roles granted at the project level to each per-service GSA"
  type        = list(string)
  default = [
    "roles/cloudtrace.agent",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/telemetry.writer",
  ]
}

variable "private_networking" {
  description = "When true, restrict each Cloud Run service to `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` so the *.run.app URL is unreachable from outside the VPC and traffic must arrive via the internal Application LB. When false, set ingress to `INGRESS_TRAFFIC_ALL` so callers can hit the *.run.app URL directly. Defaults to true to preserve historical behavior for module-only callers; the agent-gateway demo wires this to its `enable_cloud_run_private_networking` master flag."
  type        = bool
  default     = true
}

variable "invoker_sa_email" {
  description = "Email of the service account granted `roles/run.invoker` on every MCP Cloud Run service. Agents impersonate this SA (using `roles/iam.serviceAccountTokenCreator` granted on the agent identity in the agent-engine module) and present its OIDC ID token in the Authorization header. When null, no invoker binding is created and the services are unreachable until invoker is granted manually — this is the intended behavior when the agent-gateway demo is disabled."
  type        = string
  default     = null
}

variable "mcp_internal_dns_domain" {
  description = "Internal DNS domain fronting the MCP services behind the internal LB (e.g. \"mcp.example.com.\"). When set and private_networking is true, each service registers `https://<name>.<domain>` as a Cloud Run custom audience so it accepts the OIDC token the agent mints for the LB-fronted host (the agent's audience is the request origin, not the *.run.app URL). Null on the public *.run.app path."
  type        = string
  default     = null
}
