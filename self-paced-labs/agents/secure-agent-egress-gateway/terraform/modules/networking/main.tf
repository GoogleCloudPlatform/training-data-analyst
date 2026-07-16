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
 * Networking Module
 *
 * Creates VPC network, subnets, Cloud NAT, and static IP addresses for gateways.
 * Supports regional internal gateway configuration.
 */

# Get available zones in the region
data "google_compute_zones" "available" {
  project = var.project_id
  region  = var.region
}

# VPC Network
module "vpc" {
  source       = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/net-vpc?ref=v55.3.0"
  project_id   = var.project_id
  name         = var.vpc_name
  routing_mode = "REGIONAL"
  description  = ""

  subnets = [
    {
      name          = var.subnet_name
      region        = var.region
      ip_cidr_range = var.primary_subnet_cidr
    }
  ]

  subnets_proxy_only = [
    {
      name          = "${var.name_prefix}-proxy-subnet"
      region        = var.region
      ip_cidr_range = var.proxy_subnet_cidr
      active        = true
    }
  ]

  subnets_psc = [
    {
      name          = "${var.name_prefix}-psc-subnet"
      region        = var.region
      ip_cidr_range = var.psc_subnet_cidr
    }
  ]
}

# Cloud Router for NAT
resource "google_compute_router" "nat_router" {
  name    = "${var.name_prefix}-nat-router"
  project = var.project_id
  network = module.vpc.self_link
  region  = var.region
}

# Cloud NAT for outbound internet access from private nodes
resource "google_compute_router_nat" "nat_gateway" {
  name                               = "${var.name_prefix}-nat-gateway"
  project                            = var.project_id
  router                             = google_compute_router.nat_router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# Private DNS zone for Apigee internal resolution (no VPC attachment)
# This zone is consumed by Apigee via DNS peering, not by VPC workloads
module "apigee_internal_dns_zone" {
  count      = var.apigee_internal_dns_zone != null ? 1 : 0
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/dns?ref=v55.3.0"
  project_id = var.project_id
  name       = var.apigee_internal_dns_zone.name
  zone_config = {
    domain = var.apigee_internal_dns_zone.domain
    private = {
      client_networks = []
    }
  }
}

# Combined MCP and PSC Interface private DNS zone — attached to the VPC so
# workloads resolve internally, and also available for DNS peering (e.g. for
# Agent Engine) if needed.
module "mcp_internal_dns_zone" {
  count      = var.mcp_internal_dns_zone != null ? 1 : 0
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/dns?ref=v55.3.0"
  project_id = var.project_id
  name       = var.mcp_internal_dns_zone.name
  zone_config = {
    domain = var.mcp_internal_dns_zone.domain
    private = {
      client_networks = [module.vpc.self_link]
    }
  }
}

# PSC Interface — dedicated regular subnet for network attachment
resource "google_compute_subnetwork" "psc_interface" {
  count                    = var.enable_psc_interface ? 1 : 0
  project                  = var.project_id
  name                     = "${var.name_prefix}-psc-interface-subnet"
  region                   = var.region
  network                  = module.vpc.self_link
  ip_cidr_range            = var.psc_interface_subnet_cidr
  private_ip_google_access = true
}

# PSC Interface — network attachment with automatic acceptance
resource "google_compute_network_attachment" "psc_interface" {
  count                 = var.enable_psc_interface ? 1 : 0
  project               = var.project_id
  name                  = "${var.name_prefix}-psc-interface-attachment"
  region                = var.region
  connection_preference = "ACCEPT_AUTOMATIC"
  subnetworks           = [google_compute_subnetwork.psc_interface[0].self_link]
}

# PSC Interface — firewall rule allowing ingress from PSC-I subnet
resource "google_compute_firewall" "psc_interface_allow" {
  count         = var.enable_psc_interface ? 1 : 0
  project       = var.project_id
  name          = "${var.name_prefix}-allow-psc-interface"
  network       = module.vpc.self_link
  direction     = "INGRESS"
  priority      = 1000
  source_ranges = [var.psc_interface_subnet_cidr]

  allow {
    protocol = "tcp"
    ports    = ["22", "443"]
  }
  allow {
    protocol = "icmp"
  }
}

# Agent Gateway — dedicated regular subnet that hosts both the Agent Gateway
# PSC-Interface network attachment and the relocated MCP internal LB VIP.
# Co-locating them satisfies the demo's "same subnet" requirement and keeps the
# PSC-I egress range outside the documented Agent Gateway exclusions.
resource "google_compute_subnetwork" "agent_gateway" {
  count         = var.enable_agent_gateway ? 1 : 0
  project       = var.project_id
  name          = "${var.name_prefix}-agent-gateway-subnet"
  region        = var.region
  network       = module.vpc.self_link
  ip_cidr_range = var.agent_gateway_subnet_cidr
}

# PSC Interface — private DNS zone for DNS peering (only if different from MCP zone)
module "psc_interface_dns_zone" {
  count      = var.enable_psc_interface && var.psc_interface_dns_zone != null && (var.mcp_internal_dns_zone == null || var.psc_interface_dns_zone.name != var.mcp_internal_dns_zone.name) ? 1 : 0
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/dns?ref=v55.3.0"
  project_id = var.project_id
  name       = var.psc_interface_dns_zone.name
  zone_config = {
    domain = var.psc_interface_dns_zone.domain
    private = {
      client_networks = []
    }
  }
}

# Private DNS zone for `run.app.` — overrides every Cloud Run hostname to the
# Private Service Connect for Google APIs VIP (`private.googleapis.com`,
# 199.36.153.8). Cloud Run with `ingress = internal-and-cloud-load-balancing`
# treats PSC-sourced traffic as internal, so the agent can reach Cloud Run MCP
# servers using their literal `*.run.app` URLs without opening the services to
# the public internet. The zone must be paired with `run.app.` in
# `agent_gateway_dns_peering_config.domains` so the Agent Gateway resolves the
# override on the egress path.
module "run_app_private_zone" {
  count      = var.enable_run_app_psc ? 1 : 0
  source     = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/dns?ref=v55.3.0"
  project_id = var.project_id
  name       = "run-app-internal"
  zone_config = {
    domain = "run.app."
    private = {
      client_networks = [module.vpc.self_link]
    }
  }
}

# Wildcard A records for every Cloud Run URL form. DNS wildcards bind to a
# single label position, so `*.run.app.` only matches `<thing>.run.app.` —
# regional URLs like `<service>-<num>.us-central1.run.app.` need their own
# `*.us-central1.run.app.` record. `*.a.run.app.` covers the legacy
# `<service>-<hash>-<region-short>.a.run.app` format.
resource "google_dns_record_set" "run_app_wildcards" {
  for_each = var.enable_run_app_psc ? toset(concat(
    ["*.run.app."],
    [for r in var.run_app_psc_regions : "*.${r}.run.app."]
  )) : []
  project      = var.project_id
  managed_zone = module.run_app_private_zone[0].name
  name         = each.value
  type         = "A"
  ttl          = 300
  rrdatas      = ["199.36.153.8"]
}
