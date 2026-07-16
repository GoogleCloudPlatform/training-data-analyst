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



# Regional Certificate Outputs
output "regional_certificate_id" {
  description = "ID of the regional certificate for public domain (null if not using regional scope)"
  value       = var.gateway_scope == "regional" && var.enable_certificate_manager && var.dns_zone_domain != null ? google_certificate_manager_certificate.regional[0].id : null
}

output "regional_certificate_name" {
  description = "Name of the regional certificate for public domain (null if not using regional scope)"
  value       = var.gateway_scope == "regional" && var.enable_certificate_manager && var.dns_zone_domain != null ? google_certificate_manager_certificate.regional[0].name : null
}

output "internal_certificate_id" {
  description = "ID of the internal certificate (null if not using regional scope)"
  value       = var.gateway_scope == "regional" && var.enable_certificate_manager && var.dns_zone_domain != null ? google_certificate_manager_certificate.internal_regional[0].id : null
}

output "internal_certificate_name" {
  description = "Name of the internal certificate (null if not using regional scope)"
  value       = var.gateway_scope == "regional" && var.enable_certificate_manager && var.dns_zone_domain != null ? google_certificate_manager_certificate.internal_regional[0].name : null
}

output "regional_dns_authorizations" {
  description = "Map of regional DNS authorizations for certificate validation (empty if not using regional scope)"
  value       = var.gateway_scope == "regional" && var.enable_certificate_manager && var.dns_zone_domain != null ? module.certificate_manager_regional[0].dns_authorizations : {}
}

# Global Certificate Outputs
output "global_certificate_id" {
  description = "ID of the global certificate for public domain (null if certificate manager is disabled)"
  value       = null
}

output "global_dns_authorizations" {
  description = "Map of global DNS authorizations for certificate validation (empty if certificate manager is disabled)"
  value       = {}
}

# Combined Outputs (for convenience)
output "dns_authorizations" {
  description = "All DNS authorizations (regional)"
  value       = var.enable_certificate_manager && var.dns_zone_domain != null && var.gateway_scope == "regional" ? module.certificate_manager_regional[0].dns_authorizations : {}
}

output "certificate_ids" {
  description = "All certificate IDs in a consistent format"
  value = var.enable_certificate_manager && var.dns_zone_domain != null && var.gateway_scope == "regional" ? {
    regional = google_certificate_manager_certificate.regional[0].id
    internal = google_certificate_manager_certificate.internal_regional[0].id
    } : {
    regional = null
    internal = null
  }
}

output "domains_covered" {
  description = "List of domains covered by the certificates"
  value = var.enable_certificate_manager && var.dns_zone_domain != null && var.gateway_scope == "regional" ? [
    trimsuffix(var.dns_zone_domain, "."),
    "*.${trimsuffix(var.dns_zone_domain, ".")}",
    local.internal_domain,
    local.internal_wildcard,
    local.mcp_domain,
    local.mcp_wildcard,
  ] : []
}
