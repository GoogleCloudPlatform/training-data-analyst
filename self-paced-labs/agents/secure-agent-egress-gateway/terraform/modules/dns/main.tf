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




# Local variables for domain configuration
locals {
  # Derive internal domain from dns_zone_domain if not explicitly provided
  internal_dns_domain_computed = var.internal_dns_domain != null ? var.internal_dns_domain : (
    var.dns_zone_domain != null ? "internal.${var.dns_zone_domain}" : null
  )
}

# Data source to reference existing DNS zone
data "google_dns_managed_zone" "dns_zone" {
  count   = var.dns_zone_domain != null ? 1 : 0
  project = var.project_id
  name    = var.dns_zone_name != null ? var.dns_zone_name : replace(trimsuffix(var.dns_zone_domain, "."), ".", "-")
}

# Certificate validation DNS records for regional certificates
resource "google_dns_record_set" "certificate_validation_regional" {
  for_each = var.enable_certificate_manager && var.dns_zone_domain != null && var.certificate_dns_authorizations_regional != null ? var.certificate_dns_authorizations_regional : {}

  project      = var.project_id
  name         = each.value.dns_resource_record[0].name
  managed_zone = data.google_dns_managed_zone.dns_zone[0].name
  type         = each.value.dns_resource_record[0].type
  ttl          = var.certificate_validation_ttl
  rrdatas      = [each.value.dns_resource_record[0].data]

  depends_on = [data.google_dns_managed_zone.dns_zone]
}


# Private DNS Zone for internal gateways
module "internal_dns_zone" {
  count      = var.dns_zone_domain != null ? 1 : 0
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/dns?ref=v55.3.0"
  project_id = var.project_id
  name       = var.internal_dns_zone_name
  zone_config = {
    domain = local.internal_dns_domain_computed
    private = {
      client_networks = var.vpc_self_links
    }
  }
}

# ==============================================================================
# PHASE 11: SELF MANAGED GATEWAY DNS RECORD
# ==============================================================================

# DNS A record for self managed gateway
# Only created if self managed gateway is enabled and has an IP address
resource "google_dns_record_set" "self_managed_gateway" {
  count = var.enable_self_managed_gateway_dns && var.dns_zone_domain != null ? 1 : 0

  project      = var.project_id
  name         = "${var.self_managed_gateway_subdomain}.${var.dns_zone_domain}"
  managed_zone = data.google_dns_managed_zone.dns_zone[0].name
  type         = "A"
  ttl          = var.gateway_dns_ttl
  rrdatas      = [var.self_managed_gateway_ip]

  depends_on = [module.internal_dns_zone]
}

# DNS A record for self managed gateway in internal zone
# Enables pods within the VPC to resolve the self managed gateway hostname
resource "google_dns_record_set" "self_managed_gateway_internal" {
  count = var.enable_self_managed_internal_dns && var.dns_zone_domain != null ? 1 : 0

  project      = var.project_id
  name         = "${var.self_managed_internal_subdomain}.${local.internal_dns_domain_computed}"
  managed_zone = module.internal_dns_zone[0].name
  type         = "A"
  ttl          = var.internal_dns_ttl
  rrdatas      = [var.self_managed_gateway_ip]

  depends_on = [module.internal_dns_zone]
}

# ==============================================================================
# PHASE 12: GKE GATEWAY DNS RECORD
# ==============================================================================

# DNS A record for GKE gateway
# Only created if GKE gateway is enabled and has an IP address
resource "google_dns_record_set" "gke_gateway" {
  count = var.enable_gke_gateway_dns && var.dns_zone_domain != null ? 1 : 0

  project      = var.project_id
  name         = "${var.gke_gateway_subdomain}.${var.dns_zone_domain}"
  managed_zone = data.google_dns_managed_zone.dns_zone[0].name
  type         = "A"
  ttl          = var.gateway_dns_ttl
  rrdatas      = [var.gke_gateway_ip]

  depends_on = [data.google_dns_managed_zone.dns_zone]
}
