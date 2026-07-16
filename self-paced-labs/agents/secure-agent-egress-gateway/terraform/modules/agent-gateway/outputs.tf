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

output "agent_gateway_id" {
  description = "Full resource ID of the Agent Gateway"
  value       = google_network_services_agent_gateway.this.id
}

output "agent_gateway_name" {
  description = "Short name of the Agent Gateway"
  value       = google_network_services_agent_gateway.this.name
}

output "mtls_endpoint" {
  description = "mTLS endpoint clients use to reach the Agent Gateway"
  value       = try(google_network_services_agent_gateway.this.agent_gateway_card[0].mtls_endpoint, null)
}

output "root_certificates" {
  description = "Root certificates clients use to validate the Agent Gateway mTLS endpoint"
  value       = try(google_network_services_agent_gateway.this.agent_gateway_card[0].root_certificates, null)
}

output "service_extensions_service_account" {
  description = "Service account the Agent Gateway uses to call out to authz extensions. Grant additional invoker permissions to this SA on backend services as needed."
  value       = try(google_network_services_agent_gateway.this.agent_gateway_card[0].service_extensions_service_account, null)
}

output "registry_uri" {
  description = "URI of the project-local agent registry the gateway is bound to"
  value       = local.registry_uri
}

output "network_attachment_id" {
  description = "Full resource ID of the PSC-Interface network attachment created for the gateway"
  value       = google_compute_network_attachment.agent_gateway.id
}

output "iap_authz_extension_id" {
  description = "ID of the IAP authz service extension"
  value       = google_network_services_authz_extension.iap.id
}

output "model_armor_authz_extension_id" {
  description = "ID of the Model Armor authz service extension (null when enable_model_armor is false)"
  value       = var.enable_model_armor ? google_network_services_authz_extension.model_armor[0].id : null
}
