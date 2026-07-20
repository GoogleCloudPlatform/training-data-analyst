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

locals {
  # Strip a trailing dot so the URL matches what HTTP clients send in the Host header
  # (var.mcp_internal_dns_domain may be an FQDN like "mcp-server.internal.").
  mcp_internal_dns_domain_trimmed = (
    var.mcp_internal_dns_domain != null
    ? trimsuffix(var.mcp_internal_dns_domain, ".")
    : null
  )

  mcp_registrations = {
    for name, cfg in var.mcp_servers : name => {
      id             = name
      display_name   = coalesce(cfg.display_name, name)
      description    = cfg.description
      tool_spec_path = cfg.tool_spec_path
      # Both URL modes must include the /mcp path: FastMCP mounts the protocol
      # endpoint at /mcp (see src/*/main.py: mcp.http_app(path="/mcp", ...)),
      # and Cloud Run returns 404 for any other path, including /.
      url = (
        var.mcp_url_mode == "internal_lb"
        ? "https://${name}.${local.mcp_internal_dns_domain_trimmed}/mcp"
        : "${var.mcp_service_urls[name]}/mcp"
      )
    }
  }

  # Flatten each Google API into its five endpoint variants (global, mTLS,
  # locational, locational mTLS, and regional REP), keyed by service_id. IDs,
  # display names, and URLs mirror the variants the old registration script
  # produced 1:1.
  google_api_variants = merge([
    for id, name in var.google_apis : {
      # service_id must be 4-63 chars ([a-z][a-z0-9-]{2,61}[a-z0-9]); pad API
      # ids shorter than 4 chars (e.g. "iap") while keeping the real URL host.
      (length(id) >= 4 ? id : "${id}-endpoint") = {
        display_name = name
        url          = "https://${id}.googleapis.com"
      }
      "${id}-mtls" = {
        display_name = "${name} mTLS"
        url          = "https://${id}.mtls.googleapis.com"
      }
      "${var.location}-${id}" = {
        display_name = "${name} Locational"
        url          = "https://${var.location}-${id}.googleapis.com"
      }
      "${var.location}-${id}-mtls" = {
        display_name = "${name} Locational mTLS"
        url          = "https://${var.location}-${id}.mtls.googleapis.com"
      }
      "${id}-${var.location}-rep" = {
        display_name = "${name} Regional (REP)"
        url          = "https://${id}.${var.location}.rep.googleapis.com"
      }
    }
  ]...)
}

# Cross-variable input validation. Variable `validation` blocks can't reference
# other variables, so we surface the precondition failures via terraform_data.
resource "terraform_data" "mcp_input_check" {
  lifecycle {
    precondition {
      condition = (
        length(var.mcp_servers) == 0 ||
        var.mcp_url_mode != "internal_lb" ||
        var.mcp_internal_dns_domain != null
      )
      error_message = "mcp_internal_dns_domain is required when mcp_url_mode is 'internal_lb' and mcp_servers is non-empty."
    }
    precondition {
      condition = (
        var.mcp_url_mode != "cloud_run" ||
        length(setsubtract(keys(var.mcp_servers), keys(var.mcp_service_urls))) == 0
      )
      error_message = "mcp_service_urls must contain a URL for every key in mcp_servers when mcp_url_mode is 'cloud_run'."
    }
    precondition {
      condition = alltrue([
        for name, cfg in var.mcp_servers :
        cfg.tool_spec_path != null && fileexists(cfg.tool_spec_path)
      ])
      error_message = format(
        "Every MCP server in var.mcp_servers must set tool_spec_path to an existing file. Missing or unreadable: %s",
        join(", ", [
          for name, cfg in var.mcp_servers :
          "${name}=${coalesce(cfg.tool_spec_path, "<unset>")}"
          if cfg.tool_spec_path == null || !fileexists(cfg.tool_spec_path)
        ])
      )
    }
  }
}

# Google API endpoints (global, mTLS, locational, and REP variants). These are
# plain endpoints with no spec, exposed over JSON-RPC.
resource "google_agent_registry_service" "google_apis" {
  for_each = local.google_api_variants

  project      = var.project_id
  location     = var.location
  service_id   = each.key
  display_name = each.value.display_name

  interfaces {
    url              = each.value.url
    protocol_binding = "JSONRPC"
  }

  endpoint_spec {
    type = "NO_SPEC"
  }

  depends_on = [terraform_data.mcp_input_check]
}

# Custom (non-Google) service endpoints, e.g. GitHub. Also spec-less endpoints.
resource "google_agent_registry_service" "custom" {
  for_each = { for svc in var.custom_services : svc.id => svc }

  project      = var.project_id
  location     = var.location
  service_id   = each.key
  display_name = each.value.display_name
  description  = each.value.description

  interfaces {
    url              = each.value.url
    protocol_binding = "JSONRPC"
  }

  endpoint_spec {
    type = "NO_SPEC"
  }

  depends_on = [terraform_data.mcp_input_check]
}

# MCP servers. Registered as MCP Server services carrying an inline tool spec.
# The native resource takes the spec *content*, so read the toolspec.json file
# (existence is validated by terraform_data.mcp_input_check above).
resource "google_agent_registry_service" "mcp" {
  for_each = local.mcp_registrations

  project      = var.project_id
  location     = var.location
  service_id   = each.value.id
  display_name = each.value.display_name
  description  = each.value.description

  interfaces {
    url              = each.value.url
    protocol_binding = "JSONRPC"
  }

  mcp_server_spec {
    type    = "TOOL_SPEC"
    content = file(each.value.tool_spec_path)
  }

  depends_on = [terraform_data.mcp_input_check]
}
