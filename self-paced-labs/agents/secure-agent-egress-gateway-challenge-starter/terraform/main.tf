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
 * Root Terraform Configuration
 *
 * Orchestrates deployment of modular infrastructure for MCP gateway services:
 * 1. Foundation: API enablement and quotas
 * 2. Networking: VPC, NAT, static IPs, private DNS zones
 * 3. MCP Cloud Run services + per-service runtime SAs
 * 4. MCP internal Application LB with URL-mask Serverless NEG
 * 5. Public DNS zone and certs (optional)
 */

# Provider configuration lives in providers.tf.

# Derived values controlled by `enable_cloud_run_private_networking`. Folded
# into a `locals` block so the gating logic lives in one place rather than
# scattered across every consumer.
data "google_project" "project" {
  project_id = var.project_id
}

locals {
  # MCP private zone domain only exists when the master flag is on AND the
  # operator has supplied a zone. Used by anything that needs the LB-fronted
  # MCP hostname (Agent Gateway DNS peering, Model Armor authz hosts, agent
  # registry URL construction).
  mcp_internal_dns_domain_or_null = (
    var.enable_cloud_run_private_networking && var.mcp_internal_dns_zone != null
    ? var.mcp_internal_dns_zone.domain
    : null
  )

  # Agent Gateway DNS peering: auto-prepend the MCP private zone when private
  # networking is on, so the user only declares non-MCP entries (e.g.
  # `run.app.`) in agent_gateway_dns_peering_config. When the master flag is
  # off the MCP zone doesn't exist and is omitted from the peered domains.
  _agent_gateway_dns_peering_domains = distinct(compact(concat(
    local.mcp_internal_dns_domain_or_null != null ? [local.mcp_internal_dns_domain_or_null] : [],
    try(var.agent_gateway_dns_peering_config.domains, []),
  )))

  # Collapse to null whenever there are no domains to peer — the Agent Gateway
  # API rejects a dns_peering_config with an empty domains list. This covers the
  # case where the input var is set but resolves to zero effective domains (e.g.
  # private networking off, so no MCP zone, and no user-supplied domains).
  agent_gateway_dns_peering_config_effective = (
    length(local._agent_gateway_dns_peering_domains) == 0
    ? null
    : {
      domains        = local._agent_gateway_dns_peering_domains
      target_project = coalesce(try(var.agent_gateway_dns_peering_config.target_project, null), var.project_id)
      target_network = coalesce(try(var.agent_gateway_dns_peering_config.target_network, null), module.networking.network_self_link)
    }
  )
}

# Phase 1: Foundation - API Enablement and Quotas
module "foundation" {
  source = "./modules/foundation"

  providers = {
    google-beta = google-beta
  }

  project_id           = var.project_id
  enable_psc_interface = var.enable_psc_interface
  logging_data_access  = var.logging_data_access
}

# Phase 1.5: Observability - Log Analytics on _Default + authorization
# debugging dashboard.
module "observability" {
  source = "./modules/observability"

  project_id = var.project_id

  depends_on = [module.foundation]
}

# Phase 2: Networking - VPC, Subnets, NAT, Static IPs, private DNS zones
module "networking" {
  source = "./modules/networking"

  project_id  = var.project_id
  region      = var.region
  name_prefix = var.name_prefix
  vpc_name    = var.vpc_name
  subnet_name = var.subnet_name

  # Customizable CIDR ranges
  primary_subnet_cidr = var.primary_subnet_cidr
  proxy_subnet_cidr   = var.proxy_subnet_cidr
  psc_subnet_cidr     = var.psc_subnet_cidr

  # MCP servers internal DNS zone (attached to the VPC). Only created when
  # the master flag is on; otherwise the networking module skips the zone via
  # its existing `count = var.mcp_internal_dns_zone != null ? 1 : 0` guard.
  mcp_internal_dns_zone = var.enable_cloud_run_private_networking ? var.mcp_internal_dns_zone : null

  # PSC Interface (network attachment, firewall, DNS zone). The DNS zone is
  # only useful when there are private hostnames to resolve via Agent Engine
  # peering — i.e. when private networking is on. With the master flag off,
  # the agent reaches Cloud Run via *.run.app (public DNS), so the zone would
  # be an orphan (no records, no VPC attachment). Gate it on both flags.
  enable_psc_interface      = var.enable_psc_interface
  psc_interface_subnet_cidr = var.psc_interface_subnet_cidr
  psc_interface_dns_zone    = var.enable_psc_interface && var.enable_cloud_run_private_networking ? var.psc_interface_dns_zone : null

  # Private DNS zone for `run.app.` that resolves every Cloud Run URL to the
  # PSC for Google APIs VIP, so Cloud Run services with internal-only ingress
  # are reachable from the gateway without opening them to the public internet.
  enable_run_app_psc  = var.enable_run_app_psc
  run_app_psc_regions = var.run_app_psc_regions

  # Agent Gateway dedicated subnet (hosts both the new PSC-I network attachment
  # and the relocated MCP internal LB VIP when enable_agent_gateway = true).
  enable_agent_gateway      = var.enable_agent_gateway
  agent_gateway_subnet_cidr = var.agent_gateway_subnet_cidr

  depends_on = [module.foundation]
}

# Artifact Registry — Regional Docker repository for container images
resource "google_artifact_registry_repository" "registry" {
  project       = var.project_id
  location      = var.region
  repository_id = "${var.name_prefix}-docker"
  format        = "DOCKER"
  description   = "Regional Docker repository for container images"

  depends_on = [module.foundation]
}

# Cloud Build — Source bucket for regional Cloud Build submissions
resource "google_storage_bucket" "cloudbuild" {
  project                     = var.project_id
  name                        = coalesce(var.cloudbuild_bucket_name, "${var.project_id}_cloudbuild")
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [module.foundation]
}

# Grant Compute Engine default SA full bucket access for Cloud Build source
# uploads. roles/storage.admin (scoped to the bucket) is required because
# Cloud Build's build-creation step calls storage.buckets.get to validate the
# source bucket — a permission not included in roles/storage.objectAdmin.
resource "google_storage_bucket_iam_member" "cloudbuild_compute_sa" {
  bucket = google_storage_bucket.cloudbuild.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${module.foundation.project_number}-compute@developer.gserviceaccount.com"
}

# Grant Compute Engine default SA artifact registry access for Cloud Build
resource "google_project_iam_member" "cloudbuild_registry" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${module.foundation.project_number}-compute@developer.gserviceaccount.com"
}

# Grant Cloud Build service agent storage access for source tarballs
resource "google_storage_bucket_iam_member" "cloudbuild_service_agent" {
  bucket = google_storage_bucket.cloudbuild.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:service-${module.foundation.project_number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"
}

# Phase 5: Certificates — Google-managed TLS via Certificate Manager
# Gated by both the master `enable_cloud_run_private_networking` flag (the
# cert is only meaningful when the MCP internal LB is provisioned) and the
# `enable_certificate_manager` sub-flag.
module "certificates" {
  count  = var.enable_cloud_run_private_networking && var.enable_certificate_manager ? 1 : 0
  source = "./modules/certificates"

  project_id                 = var.project_id
  region                     = var.region
  dns_zone_domain            = var.dns_zone_domain
  enable_certificate_manager = var.enable_certificate_manager
  gateway_scope              = var.gateway_scope

  depends_on = [module.foundation]
}

# Phase 6: DNS - DNS Zones and Records
# Gated by both the master `enable_cloud_run_private_networking` flag and the
# presence of `dns_zone_domain`. The public zone is only needed to host the
# Certificate Manager DNS authorizations for the MCP LB cert.
module "dns" {
  count  = var.enable_cloud_run_private_networking && var.dns_zone_domain != null ? 1 : 0
  source = "./modules/dns"

  project_id      = var.project_id
  dns_zone_domain = var.dns_zone_domain
  dns_zone_name   = var.dns_zone_name

  enable_certificate_manager              = var.enable_certificate_manager
  certificate_dns_authorizations_regional = var.enable_certificate_manager && var.gateway_scope == "regional" ? module.certificates[0].regional_dns_authorizations : null

  enable_self_managed_gateway_dns  = false
  enable_self_managed_internal_dns = false

  vpc_self_links = [module.networking.network_self_link]

  depends_on = [module.networking, module.certificates]
}

module "model_armor" {
  count  = var.enable_model_armor ? 1 : 0
  source = "./modules/model-armor"

  project_id = var.project_id
  region     = var.region

  enable_model_armor   = var.enable_model_armor
  request_template_id  = var.model_armor_request_template_id
  response_template_id = var.model_armor_response_template_id

  # Admin IAM
  platform_admin_members = var.platform_admin_members

  # RAI filters
  rai_filters = var.model_armor_rai_filters

  # Sensitive Data Protection
  sdp_enforcement = var.model_armor_sdp_enforcement
  pii_types       = var.model_armor_pii_types

  # Prompt Injection & Jailbreak
  pi_jailbreak_enforcement      = var.model_armor_pi_jailbreak_enforcement
  pi_jailbreak_confidence_level = var.model_armor_pi_jailbreak_confidence

  # Malicious URI
  malicious_uri_enforcement = var.model_armor_malicious_uri_enforcement

  # MCP Floor Setting
  enable_mcp_floor_setting = var.enable_model_armor_mcp_floor_setting

  # Vertex AI Integration
  enable_vertex_ai_integration   = var.enable_model_armor_vertex_ai
  vertex_ai_inspect_only         = var.model_armor_vertex_ai_inspect_only
  vertex_ai_enable_cloud_logging = var.model_armor_vertex_ai_cloud_logging

  # Gemini Enterprise Template
  enable_gemini_enterprise_template   = var.enable_model_armor_gemini_enterprise
  gemini_enterprise_template_id       = var.model_armor_gemini_enterprise_template_id
  gemini_enterprise_template_location = var.model_armor_gemini_enterprise_location

  depends_on = [module.foundation]
}


# Phase 10: Agent Engine — Agent Identity IAM bindings
module "agent_engine" {
  count  = var.enable_agent_engine ? 1 : 0
  source = "./modules/agent-engine"

  project_id     = var.project_id
  project_number = module.foundation.project_number

  organization_id        = var.organization_id
  platform_admin_members = var.platform_admin_members

  depends_on = [module.foundation]
}

/*
# Phase 11: Apigee — API Management Platform
module "apigee" {
  count  = var.enable_apigee ? 1 : 0
  source = "./modules/apigee"

  project_id     = var.project_id
  project_number = module.foundation.project_number
  region         = var.region

  organization         = var.apigee_organization
  vpc_id               = var.apigee_vpc_id
  envgroups            = var.apigee_envgroups
  environments         = var.apigee_environments
  instances            = var.apigee_instances
  endpoint_attachments = var.apigee_endpoint_attachments

  create_service_accounts       = var.apigee_create_service_accounts
  service_account_prefix        = var.apigee_service_account_prefix
  create_apim_operator_iam      = var.apigee_create_apim_operator_iam
  enable_apim_workload_identity = var.apigee_enable_apim_workload_identity
  apim_operator_namespace       = var.apigee_apim_operator_namespace
  apim_operator_ksa             = var.apigee_apim_operator_ksa

  # Northbound LB (PSC)
  northbound_lb = var.apigee_enable_northbound_lb ? {
    network_self_link  = module.networking.network_self_link
    subnet_self_link   = module.networking.subnet_self_link
    ssl_certificate_id = module.certificates[0].internal_certificate_id
    instances = {
      for k, v in var.apigee_instances : k => {}
    }
  } : null

  # Southbound DNS peering
  dns_peering_zones = {
    for k, v in var.apigee_dns_peering_zones : k => {
      domain            = v.domain
      description       = v.description
      target_project_id = var.project_id
      target_network_id = module.networking.network_name
    }
  }

  # Southbound wildcard DNS record
  internal_dns_wildcard = var.apigee_internal_dns_zone != null && var.apigee_internal_dns_wildcard_endpoint_attachment != null ? {
    managed_zone        = module.networking.apigee_internal_dns_zone_name
    domain              = var.apigee_internal_dns_zone.domain
    endpoint_attachment = var.apigee_internal_dns_wildcard_endpoint_attachment
  } : null

  depends_on = [module.foundation]
}

# DNS A record for Apigee northbound LB (api.internal.ai-demo.gcp.sc-ccn.xyz → LB IP)
resource "google_dns_record_set" "apigee_northbound" {
  count = var.enable_apigee && var.apigee_enable_northbound_lb && var.dns_zone_domain != null ? 1 : 0

  project      = var.project_id
  name         = "api.${module.dns[0].internal_dns_domain}"
  managed_zone = module.dns[0].internal_dns_zone_name
  type         = "A"
  ttl          = 300
  rrdatas      = [module.apigee[0].northbound_lb_ip]

  depends_on = [module.dns, module.apigee]
}
*/

# Phase 12: MCP Cloud Run services + per-service runtime SAs
# `private_networking = false` (the default) leaves Cloud Run with
# `INGRESS_TRAFFIC_ALL` so callers can hit the *.run.app URL directly. Set the
# master flag to true to restrict ingress to the internal LB.
module "mcp_services" {
  source = "./modules/mcp-cloud-run"

  project_id              = var.project_id
  region                  = var.region
  services                = var.mcp_services
  private_networking      = var.enable_cloud_run_private_networking
  mcp_internal_dns_domain = local.mcp_internal_dns_domain_or_null
  # Restricts roles/run.invoker to the agent-mcp-invoker SA. Null when
  # agent_engine is disabled, in which case mcp-cloud-run skips the binding
  # and Cloud Run is unreachable until invoker is granted out-of-band.
  invoker_sa_email = var.enable_agent_engine ? module.agent_engine[0].agent_mcp_invoker_email : null

  depends_on = [module.foundation, google_artifact_registry_repository.registry]
}

# When the Agent Gateway is enabled, allocate the MCP internal LB VIP from the
# dedicated co-location subnet so PSC-I and the LB front-end share a subnet
# (the demo's same-subnet requirement). When disabled, the LB falls back to
# allocating from the primary subnet via mcp-internal-lb's default behavior.
resource "google_compute_address" "mcp_lb_in_agent_gw_subnet" {
  count        = var.enable_cloud_run_private_networking && var.enable_agent_gateway ? 1 : 0
  project      = var.project_id
  name         = "${var.name_prefix}-mcp-ilb-ip-agw"
  region       = var.region
  subnetwork   = module.networking.agent_gateway_subnet_self_link
  address_type = "INTERNAL"
  description  = "MCP internal LB VIP relocated to the Agent Gateway co-location subnet"
}

# Agent Gateway can't validate the self-signed cert the MCP LB falls back to
# when mcp_internal_dns_zone.domain isn't a real, Certificate-Manager-issuable
# subdomain. Catch the misconfiguration at plan time rather than during the
# first agent → MCP HTTPS call.
#
# Only enforced when the master flag is on — otherwise there's no LB and no
# cert to validate; the agent reaches Cloud Run via the *.run.app URL directly.
check "agent_gateway_mcp_cert_prereqs" {
  assert {
    condition     = !var.enable_cloud_run_private_networking || !var.enable_agent_gateway || var.enable_certificate_manager
    error_message = "enable_agent_gateway = true (with enable_cloud_run_private_networking = true) requires enable_certificate_manager = true so the MCP internal LB serves a Google-managed cert (Agent Gateway does not currently validate self-signed certs)."
  }
  assert {
    condition = !var.enable_cloud_run_private_networking || !var.enable_agent_gateway || (
      var.mcp_internal_dns_zone != null &&
      var.dns_zone_domain != null &&
      endswith(
        trimsuffix(var.mcp_internal_dns_zone.domain, "."),
        ".${trimsuffix(var.dns_zone_domain, ".")}"
      )
    )
    error_message = "enable_agent_gateway = true (with enable_cloud_run_private_networking = true) requires mcp_internal_dns_zone.domain to be a subdomain of dns_zone_domain (e.g. dns_zone_domain = \"agw.example.com.\" + mcp_internal_dns_zone.domain = \"mcp.agw.example.com.\") so Certificate Manager can issue the cert."
  }
}

# Phase 13: Internal Application LB with URL-mask Serverless NEG fronting all
# MCP Cloud Run services. The LB extracts <service> from the Host header and
# routes to the Cloud Run service of the same name.
#
# Gated by `enable_cloud_run_private_networking`. When the master flag is off
# the LB is not provisioned and the agent talks to Cloud Run via *.run.app.
moved {
  from = module.mcp_internal_lb
  to   = module.mcp_internal_lb[0]
}
module "mcp_internal_lb" {
  count  = var.enable_cloud_run_private_networking ? 1 : 0
  source = "./modules/mcp-internal-lb"

  project_id         = var.project_id
  region             = var.region
  name_prefix        = var.name_prefix
  network_self_link  = module.networking.network_self_link
  subnet_self_link   = module.networking.subnet_self_link
  dns_domain         = var.mcp_internal_dns_zone.domain
  protocol           = var.mcp_lb_protocol
  ssl_certificate_id = var.enable_certificate_manager && var.gateway_scope == "regional" ? module.certificates[0].internal_certificate_id : null

  # When the Agent Gateway is enabled, both the LB VIP and the forwarding rule
  # bind to the dedicated co-location subnet instead of the primary subnet.
  create_address                   = !var.enable_agent_gateway
  internal_ip_address              = var.enable_agent_gateway ? google_compute_address.mcp_lb_in_agent_gw_subnet[0].address : null
  forwarding_rule_subnet_self_link = var.enable_agent_gateway ? module.networking.agent_gateway_subnet_self_link : null

  labels = {
    managed-by = "terraform"
    component  = "mcp-server"
  }

  depends_on = [module.mcp_services]
}

# Phase 14: Agent Gateway — governance plane fronting the MCP services.
# Provisions the gateway in AGENT_TO_ANYWHERE mode with PSC-I egress and IAP
# and Model Armor authz extensions. Per-MCP-server `roles/iap.egressor`
# bindings are issued out-of-band by `scripts/grant_agent_mcp_egress.sh`.
module "agent_gateway" {
  count  = var.enable_agent_gateway ? 1 : 0
  source = "./modules/agent-gateway"

  providers = {
    google      = google
    google-beta = google-beta
  }

  project_id = var.project_id
  region     = var.region

  name                           = var.agent_gateway_name
  network_self_link              = module.networking.network_self_link
  agent_gateway_subnet_self_link = module.networking.agent_gateway_subnet_self_link
  agent_gateway_subnet_cidr      = var.agent_gateway_subnet_cidr

  mcp_lb_target_port = var.mcp_lb_protocol == "HTTPS" ? 443 : 80

  enable_model_armor               = var.enable_model_armor
  model_armor_request_template_id  = var.enable_model_armor ? module.model_armor[0].request_template_id : null
  model_armor_response_template_id = var.enable_model_armor ? module.model_armor[0].response_template_id : null

  # Scope the Model Armor CONTENT_AUTHZ policy to the per-MCP-service Host
  # values: when private networking is on, that's `<svc>.<mcp domain>` (the
  # internal LB hostname). When private networking is off, the agent reaches
  # Cloud Run via *.run.app, so flatten over every URL form Cloud Run exposes
  # for each service (both the hash form `<svc>-<hash>-<region>.a.run.app`
  # AND the project-number form `<svc>-<project-number>.<region>.run.app`) —
  # an agent may legitimately call either, and Model Armor host matching is
  # exact-string. The trailing dot on the private zone domain is stripped so
  # the value matches what HTTP clients actually send in the Host header.
  model_armor_authz_hosts = var.enable_model_armor ? (
    var.enable_cloud_run_private_networking
    ? [for svc in keys(var.mcp_services) :
    "${svc}.${trimsuffix(var.mcp_internal_dns_zone.domain, ".")}"]
    : flatten([for svc in keys(var.mcp_services) :
      [for u in module.mcp_services.service_url_list[svc] :
    replace(replace(u, "https://", ""), "/", "")]])
  ) : []

  authz_extension_fail_open = var.agent_gateway_authz_fail_open
  iap_iam_enforcement_mode  = var.agent_gateway_iap_iam_enforcement_mode

  # Auto-merge the MCP private zone with any user-supplied domains (e.g.
  # `run.app.`). Computed in main.tf locals so the user only declares the
  # extras they need.
  dns_peering_config = local.agent_gateway_dns_peering_config_effective

  depends_on = [module.foundation, module.networking, module.mcp_internal_lb]
}

# Per-service A record in the MCP private zone (var.mcp_internal_dns_zone),
# all pointing at the LB VIP. The URL mask on the Serverless NEG demuxes by
# hostname so adding a new MCP service is one Cloud Run deploy + one map entry
# (no LB changes). Only created when the master flag is on; the LB and
# private zone don't exist otherwise.
resource "google_dns_record_set" "mcp_service" {
  for_each = var.enable_cloud_run_private_networking ? var.mcp_services : {}

  project      = var.project_id
  managed_zone = module.networking.mcp_internal_dns_zone_name
  name         = "${each.key}.${module.networking.mcp_internal_dns_domain}"
  type         = "A"
  ttl          = 60
  rrdatas      = [module.mcp_internal_lb[0].ip_address]
}

# Discovery Engine Admin — Allow user to manage Gemini Enterprise / Discovery Engine
resource "google_project_iam_member" "discoveryengine_admin" {
  for_each = toset(var.platform_admin_members)
  project  = var.project_id
  role     = "roles/discoveryengine.admin"
  member   = each.key
}

# Cloud Run Admin — Allow platform admins to manage Cloud Run services
resource "google_project_iam_member" "run_admin" {
  for_each = toset(var.platform_admin_members)
  project  = var.project_id
  role     = "roles/run.admin"
  member   = each.key
}

# Phase 15: Agent Registry Endpoints — governance plane fronting the Google API
# services AND the MCP Cloud Run services. Registers all regional, mTLS, and REP
# variants of the specified Google APIs, plus one entry per MCP Cloud Run service
# (URL = https://<service>.<mcp_internal_dns_zone.domain>).
module "agent_registry_endpoints" {
  count  = var.enable_agent_registry_endpoints ? 1 : 0
  source = "./modules/agent-registry-endpoints"

  project_id = var.project_id
  location   = var.region

  google_apis     = var.agent_registry_google_apis
  custom_services = var.agent_registry_custom_services

  mcp_servers = {
    for name in keys(var.mcp_services) : name => {
      tool_spec_path = lookup(var.mcp_tool_specs, name, null) != null ? abspath("${path.root}/${var.mcp_tool_specs[name]}") : null
    }
  }
  # Master flag flips the URL mode: `internal_lb` registers each service at
  # `https://<svc>.<mcp_internal_dns_zone.domain>/mcp`; `cloud_run` registers
  # the literal *.run.app URL from module.mcp_services.service_urls.
  mcp_url_mode            = var.enable_cloud_run_private_networking ? "internal_lb" : "cloud_run"
  mcp_internal_dns_domain = local.mcp_internal_dns_domain_or_null
  mcp_service_urls        = module.mcp_services.service_urls

  depends_on = [module.foundation, module.mcp_services, module.mcp_internal_lb]
}

###############################################################################
# CHALLENGE LAB: SECURE AGENT EGRESS (TODOs)
###############################################################################

# Task 2: Provision Egress Agent Gateway
# TODO: Declare the google_network_services_agent_gateway resource block.
# Use name = "agent-egress-gateway" and set the governed access path mode to AGENT_TO_ANYWHERE.
resource "google_network_services_agent_gateway" "agent-egress-gateway" {
  name     = "agent-egress-gateway"
  location = var.region
  google_managed {
    # TODO: Set the governed access path mode to route traffic correctly
    governed_access_path = "FILL_ME_IN"
  }
}

# Task 3: Deploy Model Armor Guardrails
# TODO: Define a google_model_armor_template named "agent-safety-template".
# Enable prompt injection filtering (ENABLED).
resource "google_model_armor_template" "agent-safety-template" {
  template_id = "agent-safety-template"
  location    = var.region
  filter_config {
    pi_and_jailbreak_filter_settings {
      # TODO: Enable the prompt injection filter
      filter_enforcement = "FILL_ME_IN"
    }
  }
}

# TODO: Define a google_network_services_authz_extension named "model-armor-extension".
# Reference the Model Armor template path.
resource "google_network_services_authz_extension" "model-armor-extension" {
  provider = google-beta
  name     = "model-armor-extension"
  location = var.region
  service  = format("modelarmor.%s.rep.googleapis.com", var.region)
  timeout  = "3s"
  metadata = {
    # TODO: Encode the model armor settings with project and template references.
    # Look at the template_id 'agent-safety-template' you defined above.
    "model_armor_settings" = jsonencode([{
      request_template_id  = "FILL_ME_IN"
      response_template_id = "FILL_ME_IN"
    }])
  }
}

# TODO: Define a google_network_security_authz_policy named "model-armor-policy".
# Map the service extension to the agent-egress-gateway.
resource "google_network_security_authz_policy" "model-armor-policy" {
  provider       = google-beta
  name           = "model-armor-policy"
  location       = var.region
  policy_profile = "CONTENT_AUTHZ"
  action         = "CUSTOM"
  target {
    # TODO: Bind this policy to the agent-egress-gateway resource ID
    resources = ["FILL_ME_IN"]
  }
  custom_provider {
    authz_extension {
      # TODO: Link the model-armor-extension resource ID
      resources = ["FILL_ME_IN"]
    }
  }
}

# Task 4: Configure Agentic IAM and Auth Manager
# TODO: Grant the correct role to the Agent Principal URN.
# Bind the custom agent role `roles/aiplatform.user` to the mortgage-assistant principal.
resource "google_project_iam_member" "agent-iam-binding" {
  project = var.project_id
  # TODO: Grant the correct role
  role    = "FILL_ME_IN"
  member  = format("principal://agents.global.org-%s/agents/mortgage-assistant", coalesce(var.organization_id, data.google_project.project.org_id, "123456789012"))
}

# TODO: Grant the correct role to allow the gateway service extensions SA to call Model Armor
# Bind `roles/modelarmor.user` to the gateway's service extensions service account.
resource "google_project_iam_member" "gateway-extensions-sa-model-armor-user" {
  project = var.project_id
  # TODO: Grant the correct role
  role    = "FILL_ME_IN"
  member  = format("serviceAccount:%s", google_network_services_agent_gateway.agent-egress-gateway.agent_gateway_card[0].service_extensions_service_account)
}

# Configure Token Injection extension
resource "google_network_services_authz_extension" "iap-extension" {
  provider  = google-beta
  name      = "iap-extension"
  location  = var.region
  service   = "iap.googleapis.com"
  timeout   = "3s"

  metadata = {
    iapPolicyVersion = "V1"
  }
}

# Configure Token Injection policy
resource "google_network_security_authz_policy" "iap-policy" {
  provider       = google-beta
  name           = "iap-policy"
  location       = var.region
  policy_profile = "REQUEST_AUTHZ"
  action         = "CUSTOM"
  target {
    # TODO: Bind this policy to the agent-egress-gateway resource ID
    resources = ["FILL_ME_IN"]
  }
  custom_provider {
    authz_extension {
      resources = [google_network_services_authz_extension.iap-extension.id]
    }
  }
}
