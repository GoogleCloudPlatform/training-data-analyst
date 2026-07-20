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

# One dedicated runtime service account per MCP service. Replaces the prior
# Workload Identity binding per K8s service account.
resource "google_service_account" "mcp" {
  for_each = var.services

  project      = var.project_id
  account_id   = "mcp-${each.key}"
  display_name = "MCP server runtime SA: ${each.key}"
  description  = "Runtime service account for the ${each.key} MCP Cloud Run service"
}

# Project-level IAM roles required by every MCP service (OTel exporters, logging,
# Cloud Trace, telemetry writer, service usage). Flattened so for_each gets a
# single map keyed by "<service>/<role>".
locals {
  service_account_role_bindings = {
    for pair in flatten([
      for svc_name, _ in var.services : [
        for role in var.service_account_roles : {
          key  = "${svc_name}/${role}"
          svc  = svc_name
          role = role
        }
      ]
    ]) : pair.key => pair
  }
}

resource "google_project_iam_member" "mcp_runtime" {
  for_each = local.service_account_role_bindings

  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.mcp[each.value.svc].email}"
}

# Cloud Run v2 services. Ingress depends on var.private_networking: when true,
# restricted to the internal Application LB so the *.run.app URL is unreachable
# from outside the VPC; when false, INGRESS_TRAFFIC_ALL so callers can hit the
# *.run.app URL directly (typical for the simple demo path).
resource "google_cloud_run_v2_service" "mcp" {
  for_each = var.services

  project  = var.project_id
  name     = each.key
  location = var.region

  ingress             = var.private_networking ? "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER" : "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  # On the private path the agent reaches each service via the internal LB at
  # `https://<name>.<domain>` and mints an OIDC token scoped to that origin.
  # Cloud Run only accepts tokens whose `aud` matches a *.run.app URL unless
  # the custom host is registered here, so without this the LB-fronted calls
  # return 401. Null on the public path leaves the default *.run.app audience.
  custom_audiences = var.private_networking && var.mcp_internal_dns_domain != null ? [
    "https://${each.key}.${trimsuffix(var.mcp_internal_dns_domain, ".")}"
  ] : null

  template {
    service_account = google_service_account.mcp[each.key].email

    scaling {
      min_instance_count = each.value.min_instance_count
      max_instance_count = each.value.max_instance_count
    }

    containers {
      image = each.value.image

      ports {
        container_port = each.value.container_port
      }

      env {
        name  = "OTEL_SERVICE_NAME"
        value = coalesce(each.value.otel_service_name, each.key)
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      dynamic "env" {
        for_each = each.value.env
        content {
          name  = env.key
          value = env.value
        }
      }

      resources {
        limits = {
          cpu    = each.value.cpu
          memory = each.value.memory
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  # Skaffold (and the underlying gcloud/Cloud Run client) owns deploy-time
  # mutations after the initial apply: container image tags, the per-revision
  # `run-id` label that Cloud Run auto-injects into template[0].labels, and
  # client identity annotations (run.googleapis.com/client-name, /client-version).
  # Ignoring these prevents Terraform from reverting Skaffold's deploys.
  lifecycle {
    ignore_changes = [
      client,
      client_version,
      template[0].containers[0].image,
      template[0].labels,
      template[0].annotations,
    ]
  }
}

# Grant `roles/run.invoker` only to the agent invoker SA (created in the
# agent-engine module). Agents impersonate this SA at runtime and present its
# OIDC ID token to Cloud Run, so Cloud Run sees the impersonated SA as the
# caller. `allUsers` is intentionally not granted: MCP services are unreachable
# except by holders of an OIDC token for the invoker SA, regardless of
# `private_networking`. Per-agent authorization is still enforced upstream at
# the Agent Gateway via `roles/iap.egressor` (see scripts/grant_agent_mcp_egress.sh).
#
# When `invoker_sa_email` is null (e.g. the agent-engine module is disabled),
# no binding is created and Cloud Run is unreachable until invoker is granted
# out-of-band. There is no `allUsers` fallback by design.
moved {
  from = google_cloud_run_v2_service_iam_member.internal_lb_invoker
  to   = google_cloud_run_v2_service_iam_member.agent_invoker
}

resource "google_cloud_run_v2_service_iam_member" "agent_invoker" {
  for_each = var.invoker_sa_email != null ? var.services : {}

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.mcp[each.key].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.invoker_sa_email}"
}
