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



output "request_template_id" {
  description = "ID of the request-side Model Armor template"
  value       = var.enable_model_armor ? google_model_armor_template.request[0].template_id : null
}

output "request_template_name" {
  description = "Full resource name of the request-side Model Armor template"
  value       = var.enable_model_armor ? google_model_armor_template.request[0].name : null
}

output "response_template_id" {
  description = "ID of the response-side Model Armor template"
  value       = var.enable_model_armor ? google_model_armor_template.response[0].template_id : null
}

output "response_template_name" {
  description = "Full resource name of the response-side Model Armor template"
  value       = var.enable_model_armor ? google_model_armor_template.response[0].name : null
}

output "template_location" {
  description = "Location of the Model Armor templates"
  value       = var.enable_model_armor ? google_model_armor_template.request[0].location : null
}

output "inspect_template_id" {
  description = "ID of the DLP inspect template referenced by the response template's advanced SDP config (null when sdp_enforcement = DISABLED)"
  value       = local.enable_sdp_advanced ? google_data_loss_prevention_inspect_template.ssn[0].template_id : null
}

output "deidentify_template_id" {
  description = "ID of the DLP de-identify template referenced by the response template's advanced SDP config (null when sdp_enforcement = DISABLED)"
  value       = local.enable_sdp_advanced ? google_data_loss_prevention_deidentify_template.ssn[0].template_id : null
}

output "model_armor_service_agent_email" {
  description = "Email of the Model Armor service agent (gcp-sa-modelarmor) granted DLP read access (null when advanced SDP is DISABLED)"
  value       = local.enable_sdp_advanced ? google_project_service_identity.model_armor[0].email : null
}

output "service_account_email" {
  description = "Email of the Service Extensions service account (gcp-sa-dep) used for Model Armor"
  value       = local.service_extensions_sa_email
}

output "rai_filters" {
  description = "Configured RAI filters"
  value       = var.rai_filters
}

output "filter_configuration" {
  description = "Summary of filter configuration"
  value = var.enable_model_armor ? {
    rai_filters = {
      count   = length(var.rai_filters)
      filters = var.rai_filters
    }
    sdp_settings = {
      enforcement = var.sdp_enforcement
      pii_types   = var.pii_types
    }
    pi_jailbreak = {
      enforcement      = var.pi_jailbreak_enforcement
      confidence_level = var.pi_jailbreak_confidence_level
    }
    malicious_uri = {
      enforcement = var.malicious_uri_enforcement
    }
  } : null
}

output "error_configuration" {
  description = "Custom error codes and messages"
  value = var.enable_model_armor ? {
    llm_response = {
      code    = var.llm_response_error_code
      message = var.llm_response_error_message
    }
    prompt = {
      code    = var.prompt_error_code
      message = var.prompt_error_message
    }
  } : null
}

output "logging_configuration" {
  description = "Logging and operation settings"
  value = var.enable_model_armor ? {
    log_template_operations = var.log_template_operations
    log_sanitize_operations = var.log_sanitize_operations
    ignore_partial_failures = var.ignore_partial_failures
  } : null
}

output "iam_roles_granted" {
  description = "List of IAM roles granted to Service Extensions service account (gcp-sa-dep) for Model Armor"
  value = var.enable_model_armor && var.enable_iam_bindings ? [
    "roles/container.admin",
    "roles/modelarmor.calloutUser",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/modelarmor.user"
  ] : []
}

output "mcp_floor_setting_name" {
  description = "Name of the MCP floor setting"
  value       = var.enable_model_armor && (var.enable_mcp_floor_setting || var.enable_vertex_ai_integration) ? google_model_armor_floorsetting.mcp_floor_setting[0].name : null
}

output "gemini_enterprise_template_name" {
  description = "Full resource name of the Gemini Enterprise Model Armor template (use for Discovery Engine REST API)"
  value       = var.enable_model_armor && var.enable_gemini_enterprise_template ? google_model_armor_template.gemini_enterprise_template[0].name : null
}

output "gemini_enterprise_template_id" {
  description = "ID of the Gemini Enterprise Model Armor template"
  value       = var.enable_model_armor && var.enable_gemini_enterprise_template ? google_model_armor_template.gemini_enterprise_template[0].template_id : null
}

output "vertex_ai_service_account_email" {
  description = "Email of the AI Platform service agent granted Model Armor access"
  value       = var.enable_model_armor && var.enable_vertex_ai_integration ? "service-${data.google_project.project.number}@gcp-sa-aiplatform.iam.gserviceaccount.com" : null
}
