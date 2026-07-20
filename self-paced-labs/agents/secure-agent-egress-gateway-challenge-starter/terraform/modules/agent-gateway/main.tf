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
 * Agent Gateway Module
 *
 * Provisions a Google-managed Agent Gateway in AGENT_TO_ANYWHERE mode for MCP,
 * a PSC-Interface network attachment in the dedicated co-location subnet, two
 * authz service extensions (IAP REQUEST_AUTHZ and Model Armor CONTENT_AUTHZ),
 * and the authz policies that bind those extensions to the gateway.
 *
 * Per-MCP-server `roles/iap.egressor` bindings (the grants IAP REQUEST_AUTHZ
 * actually evaluates) are issued out-of-band by `scripts/grant_agent_mcp_egress.sh`
 * after each agent deploy.
 *
 * The Agent Gateway resource is GA (uses the default google provider). The authz
 * service extensions and policies remain beta — pinned via the google-beta provider.
 */

locals {
  registry_uri = "//agentregistry.googleapis.com/projects/${var.project_id}/locations/${var.region}"
}

# PSC-Interface network attachment in the dedicated co-location subnet. This is
# what the Agent Gateway egresses through to reach the customer VPC (and from
# there the MCP internal LB).
resource "google_compute_network_attachment" "agent_gateway" {
  project               = var.project_id
  name                  = "${var.name}-na"
  region                = var.region
  connection_preference = "ACCEPT_AUTOMATIC"
  subnetworks           = [var.agent_gateway_subnet_self_link]
}

# Allow the gateway tenant's PSC-I NIC (sourcing from the dedicated subnet) to
# reach the MCP internal LB on its front-end port.
resource "google_compute_firewall" "agent_gateway_psc_i" {
  project       = var.project_id
  name          = "${var.name}-allow-psc-i"
  network       = var.network_self_link
  direction     = "INGRESS"
  priority      = 1000
  source_ranges = [var.agent_gateway_subnet_cidr]

  allow {
    protocol = "tcp"
    ports    = [tostring(var.mcp_lb_target_port)]
  }
}

# The Agent Gateway itself. Google-managed, AGENT_TO_ANYWHERE.
resource "google_network_services_agent_gateway" "this" {
  project  = var.project_id
  name     = var.name
  location = var.region

  google_managed {
    governed_access_path = "AGENT_TO_ANYWHERE"
  }

  registries = [local.registry_uri]

  network_config {
    egress {
      network_attachment = google_compute_network_attachment.agent_gateway.id
    }

    # DNS peering lets the gateway resolve customer-VPC private DNS zones (e.g.
    # mcp.agent-gateway.sc-ccn.xyz.) so it can reach upstream MCP servers by
    # hostname.
    dynamic "dns_peering_config" {
      # Only emit the block when there is at least one domain — the API rejects
      # a dns_peering_config with an empty domains list.
      for_each = try(length(var.dns_peering_config.domains), 0) > 0 ? [var.dns_peering_config] : []
      content {
        domains        = dns_peering_config.value.domains
        target_project = dns_peering_config.value.target_project
        target_network = dns_peering_config.value.target_network
      }
    }
  }
}

# Allow the Agent Gateway control plane / tenant project to stabilize before
# attaching authz policies. Without this, the backend may return a 400/409
# 'resource is being created and therefore can not be updated' error.
resource "time_sleep" "wait_for_gateway" {
  depends_on      = [google_network_services_agent_gateway.this]
  create_duration = "30s"
}

# IAP REQUEST_AUTHZ service extension. The Agent Gateway calls IAP per request
# to evaluate the agent identity's IAM allow policy on the target.
resource "google_network_services_authz_extension" "iap" {
  provider  = google-beta
  project   = var.project_id
  name      = "${var.name}-iap-authz"
  location  = var.region
  service   = "iap.googleapis.com"
  timeout   = var.authz_extension_timeout
  fail_open = var.authz_extension_fail_open

  # iapPolicyVersion is required by IAP on the authz extension (GA-era rollout);
  # without it the per-request IAP authorization path is misconfigured. "V1" is
  # currently the only valid value. iamEnforcementMode is merged in only for the
  # DRY_RUN case.
  metadata = merge(
    {
      iapPolicyVersion = "V1"
    },
    var.iap_iam_enforcement_mode != null ? {
      iamEnforcementMode = var.iap_iam_enforcement_mode
    } : {}
  )
}

# Model Armor CONTENT_AUTHZ service extension. Regional REP endpoint —
# constructed from var.region. The extension passes the request/response
# templates as opaque metadata that Model Armor's callout reads at evaluation
# time.
resource "google_network_services_authz_extension" "model_armor" {
  count    = var.enable_model_armor ? 1 : 0
  provider = google-beta
  project  = var.project_id
  name     = "${var.name}-ma-authz"
  location = var.region
  service  = "modelarmor.${var.region}.rep.googleapis.com"
  timeout  = var.authz_extension_timeout

  metadata = {
    "model_armor_settings" = jsonencode([{
      request_template_id  = "projects/${var.project_id}/locations/${var.region}/templates/${var.model_armor_request_template_id}"
      response_template_id = "projects/${var.project_id}/locations/${var.region}/templates/${var.model_armor_response_template_id}"
    }])
  }

  fail_open = var.authz_extension_fail_open

  lifecycle {
    precondition {
      condition     = var.model_armor_request_template_id != null && var.model_armor_response_template_id != null
      error_message = "Both model_armor_request_template_id and model_armor_response_template_id are required when enable_model_armor is true."
    }
  }
}

# Bind the IAP authz extension to the Agent Gateway. REQUEST_AUTHZ profile
# evaluates once per request at the headers stage. target.load_balancing_scheme
# must be omitted when targeting an Agent Gateway.
resource "google_network_security_authz_policy" "iap" {
  depends_on     = [time_sleep.wait_for_gateway]
  provider       = google-beta
  project        = var.project_id
  name           = "${var.name}-iap-policy"
  location       = var.region
  policy_profile = "REQUEST_AUTHZ"
  action         = "CUSTOM"

  target {
    resources = [google_network_services_agent_gateway.this.id]
  }

  custom_provider {
    authz_extension {
      resources = [google_network_services_authz_extension.iap.id]
    }
  }
}

# Bind the Model Armor authz extension to the Agent Gateway. CONTENT_AUTHZ
# profile streams body events to the extension for content sanitization.
# When model_armor_authz_hosts is non-empty, scope the policy to the listed
# Host header values via http_rules; otherwise the policy applies to all
# gateway traffic.
resource "google_network_security_authz_policy" "model_armor" {
  depends_on     = [time_sleep.wait_for_gateway]
  count          = var.enable_model_armor ? 1 : 0
  provider       = google-beta
  project        = var.project_id
  name           = "${var.name}-ma-policy"
  location       = var.region
  policy_profile = "CONTENT_AUTHZ"
  action         = "CUSTOM"

  target {
    resources = [google_network_services_agent_gateway.this.id]
  }

  custom_provider {
    authz_extension {
      resources = [google_network_services_authz_extension.model_armor[0].id]
    }
  }

  dynamic "http_rules" {
    for_each = length(var.model_armor_authz_hosts) > 0 ? [1] : []
    content {
      to {
        operations {
          dynamic "hosts" {
            for_each = var.model_armor_authz_hosts
            content {
              exact = hosts.value
            }
          }
        }
      }
    }
  }
}

# IAM for the gateway's service-extensions service account (Model Armor path
# only — IAP doesn't require additional grants per the delegate-authorization
# docs). The SA is output-only on the gateway resource.
locals {
  service_extensions_sa_member = "serviceAccount:${google_network_services_agent_gateway.this.agent_gateway_card[0].service_extensions_service_account}"

  model_armor_sa_roles = var.enable_model_armor ? [
    "roles/modelarmor.calloutUser",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/modelarmor.user",
  ] : []
}

resource "google_project_iam_member" "service_extensions_sa" {
  for_each = toset(local.model_armor_sa_roles)
  project  = var.project_id
  role     = each.value
  member   = local.service_extensions_sa_member
}
