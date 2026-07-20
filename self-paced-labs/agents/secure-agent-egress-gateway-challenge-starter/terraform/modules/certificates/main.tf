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



# Extract domain name without trailing dot for authorization names
locals {
  domain_name_clean = var.dns_zone_domain != null ? trimsuffix(var.dns_zone_domain, ".") : ""
  domain_auth_name  = var.dns_zone_domain != null ? replace(local.domain_name_clean, ".", "-") : ""
  wildcard_domain   = var.dns_zone_domain != null ? "*.${local.domain_name_clean}" : ""

  # Internal domain configuration - subdomain of dns_zone_domain for validation
  internal_domain        = var.dns_zone_domain != null ? "internal.${local.domain_name_clean}" : ""
  internal_wildcard      = var.dns_zone_domain != null ? "*.${local.internal_domain}" : ""
  internal_auth_name     = "internal-auth"
  internal_auth_regional = "${local.internal_auth_name}-regional"

  # MCP subdomain — covered by the same internal cert so the MCP internal LB
  # can serve TLS for <service>.mcp.<domain> hostnames.
  mcp_domain        = var.dns_zone_domain != null ? "mcp.${local.domain_name_clean}" : ""
  mcp_wildcard      = var.dns_zone_domain != null ? "*.${local.mcp_domain}" : ""
  mcp_auth_regional = "mcp-auth-regional"
}

# Regional DNS Authorizations (no map needed for regional gateways)
module "certificate_manager_regional" {
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/certificate-manager?ref=v55.3.0"
  project_id = var.project_id

  count = var.enable_certificate_manager && var.dns_zone_domain != null && var.gateway_scope == "regional" ? 1 : 0

  # No map needed for regional gateways
  map = null

  # Certificate is created directly as a resource below
  certificates = {}

  # DNS authorizations for public, internal, and MCP subdomains
  dns_authorizations = {
    "${local.domain_auth_name}-regional" = {
      location = var.region
      type     = "PER_PROJECT_RECORD"
      domain   = local.domain_name_clean
    }
    (local.internal_auth_regional) = {
      location = var.region
      type     = "PER_PROJECT_RECORD"
      domain   = local.internal_domain
    }
    (local.mcp_auth_regional) = {
      location = var.region
      type     = "PER_PROJECT_RECORD"
      domain   = local.mcp_domain
    }
  }
}

# Create the regional certificate directly for public domain
# Create the regional certificate directly for public domain
resource "google_certificate_manager_certificate" "regional" {
  count = var.enable_certificate_manager && var.dns_zone_domain != null && var.gateway_scope == "regional" ? 1 : 0

  name        = var.regional_certificate_name
  location    = var.region
  project     = var.project_id
  description = "Regional certificate for ${local.domain_name_clean} and subdomains"

  managed {
    domains = [local.domain_name_clean, local.wildcard_domain]
    dns_authorizations = [
      module.certificate_manager_regional[0].dns_authorizations["${local.domain_auth_name}-regional"].id
    ]
  }

  labels = var.labels
}

# Regional certificate for internal gateways and the MCP internal LB.
# Covers internal.{domain}, *.internal.{domain}, mcp.{domain}, *.mcp.{domain}.
#
# The name carries an 8-char hash of the SAN list so that a SAN change creates
# a new cert (different name) before the old one is destroyed. Without this,
# the cert is force-replaced in-place and Cert Manager refuses to delete it
# while the target HTTPS proxy still references it (RESOURCE_STILL_IN_USE).
locals {
  internal_regional_domains = [
    local.internal_domain,
    local.internal_wildcard,
    local.mcp_domain,
    local.mcp_wildcard,
  ]
  internal_regional_san_hash = substr(sha256(jsonencode(local.internal_regional_domains)), 0, 8)
}

resource "google_certificate_manager_certificate" "internal_regional" {
  count = var.enable_certificate_manager && var.dns_zone_domain != null && var.gateway_scope == "regional" ? 1 : 0

  name        = "${var.internal_certificate_name}-${local.internal_regional_san_hash}"
  location    = var.region
  project     = var.project_id
  description = "Regional certificate for ${join(", ", local.internal_regional_domains)}"

  managed {
    domains = local.internal_regional_domains
    dns_authorizations = [
      module.certificate_manager_regional[0].dns_authorizations[local.internal_auth_regional].id,
      module.certificate_manager_regional[0].dns_authorizations[local.mcp_auth_regional].id,
    ]
  }

  labels = var.labels

  lifecycle {
    create_before_destroy = true
  }
}
