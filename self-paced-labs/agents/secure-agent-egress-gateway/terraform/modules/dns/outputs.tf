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



# Public DNS Zone Outputs
output "dns_zone_name" {
  description = "Name of the public DNS zone"
  value       = var.dns_zone_domain != null ? data.google_dns_managed_zone.dns_zone[0].name : null
}

output "dns_zone_id" {
  description = "ID of the public DNS zone"
  value       = var.dns_zone_domain != null ? data.google_dns_managed_zone.dns_zone[0].id : null
}

output "dns_zone_name_servers" {
  description = "Name servers for the public DNS zone"
  value       = var.dns_zone_domain != null ? data.google_dns_managed_zone.dns_zone[0].name_servers : []
}

# Internal DNS Zone Outputs
output "internal_dns_zone_name" {
  description = "Name of the internal DNS zone"
  value       = var.dns_zone_domain != null ? module.internal_dns_zone[0].name : null
}

output "internal_dns_zone_id" {
  description = "ID of the internal DNS zone"
  value       = var.dns_zone_domain != null ? module.internal_dns_zone[0].id : null
}

output "internal_dns_domain" {
  description = "Domain for the internal DNS zone"
  value       = var.dns_zone_domain != null ? local.internal_dns_domain_computed : null
}

# Certificate Validation Records
output "certificate_validation_records_count" {
  description = "Number of certificate validation DNS records created"
  value       = length(var.certificate_dns_authorizations_regional != null ? var.certificate_dns_authorizations_regional : {})
}

# Summary Output
output "dns_records_summary" {
  description = "Summary of all DNS records created by this module"
  value = {
    public_zone = var.dns_zone_domain != null ? {
      zone_name = data.google_dns_managed_zone.dns_zone[0].name
      domain    = var.dns_zone_domain
      records = {
        cert_validations = length(var.certificate_dns_authorizations_regional != null ? var.certificate_dns_authorizations_regional : {})
      }
    } : null
    internal_zone = var.dns_zone_domain != null ? {
      zone_name = module.internal_dns_zone[0].name
      domain    = local.internal_dns_domain_computed
      records   = {}
    } : null
  }
}
