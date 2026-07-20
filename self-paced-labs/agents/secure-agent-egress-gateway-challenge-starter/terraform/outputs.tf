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

# Foundation Module Outputs

output "foundation_project_id" {
  description = "The GCP project ID from the foundation module"
  value       = module.foundation.project_id
}

output "foundation_project_number" {
  description = "The GCP project number from the foundation module"
  value       = module.foundation.project_number
}

# Networking Module Outputs

output "vpc_id" {
  description = "The ID of the VPC network"
  value       = module.networking.network_id
}

output "vpc_name" {
  description = "The name of the VPC network"
  value       = module.networking.network_name
}

output "subnet_id" {
  description = "The ID of the primary subnet"
  value       = module.networking.subnet_id
}

output "subnet_name" {
  description = "Name of the primary subnet"
  value       = module.networking.subnet_name
}

output "subnet_self_link" {
  description = "The self-link of the primary subnet"
  value       = module.networking.subnet_self_link
}

output "network_self_link" {
  description = "The self-link of the VPC network"
  value       = module.networking.network_self_link
}

output "gateway_scope" {
  description = "The configured gateway scope (regional or null)"
  value       = var.gateway_scope
}

output "psc_subnet_id" {
  description = "The ID of the Private Service Connect subnet"
  value       = module.networking.psc_subnet_id
}

output "psc_subnet_self_link" {
  description = "The self-link of the Private Service Connect subnet"
  value       = module.networking.psc_subnet_self_link
}

# MCP Services (Cloud Run) Outputs

output "mcp_service_names" {
  description = "Map of MCP service key to Cloud Run service name"
  value       = module.mcp_services.service_names
}

output "mcp_service_urls" {
  description = "Map of MCP service key to Cloud Run *.run.app URL (only reachable via the internal LB)"
  value       = module.mcp_services.service_urls
}

output "mcp_service_account_emails" {
  description = "Map of MCP service key to runtime service account email"
  value       = module.mcp_services.service_account_emails
}

output "agent_mcp_invoker_email" {
  description = "Email of the SA agents impersonate when invoking MCP Cloud Run services. Pass to deploy_agent.py via --mcp-invoker-sa or $MCP_INVOKER_SA_EMAIL. Null when enable_agent_engine is false."
  value       = var.enable_agent_engine ? module.agent_engine[0].agent_mcp_invoker_email : null
}

output "mcp_internal_dns_names" {
  description = "Map of MCP service key to its private DNS name (<service>.<domain>). Null when enable_cloud_run_private_networking = false (no MCP private zone is provisioned)."
  value = (
    var.enable_cloud_run_private_networking && var.mcp_internal_dns_zone != null
    ? { for k, _ in var.mcp_services : k => trimsuffix("${k}.${var.mcp_internal_dns_zone.domain}", ".") }
    : null
  )
}

output "mcp_internal_lb_ip" {
  description = "Internal IP address of the MCP services Application LB. Null when enable_cloud_run_private_networking = false."
  value       = var.enable_cloud_run_private_networking ? module.mcp_internal_lb[0].ip_address : null
}

output "mcp_internal_dns_zone_name" {
  description = "Cloud DNS managed zone name for the MCP servers private DNS"
  value       = module.networking.mcp_internal_dns_zone_name
}

output "mcp_internal_dns_domain" {
  description = "Domain name (with trailing dot) of the MCP servers private DNS zone"
  value       = module.networking.mcp_internal_dns_domain
}

output "mcp_cloud_run_ingress_annotation" {
  description = "Cloud Run v1 ingress annotation value to use when rendering cloudrun/*.yaml.tmpl. Mirrors the ingress chosen by the mcp-cloud-run module based on enable_cloud_run_private_networking, so skaffold-rendered manifests stay in sync with terraform state."
  value       = var.enable_cloud_run_private_networking ? "internal-and-cloud-load-balancing" : "all"
}

# Artifact Registry Outputs

output "artifact_registry_id" {
  description = "The Artifact Registry repository ID"
  value       = google_artifact_registry_repository.registry.id
}

output "artifact_registry_url" {
  description = "The Artifact Registry repository URL for docker push/pull"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.registry.repository_id}"
}

# Certificate Outputs

output "regional_certificate_name" {
  description = "Name of the regional Google-managed certificate. Null unless both enable_cloud_run_private_networking and enable_certificate_manager are true."
  value       = var.enable_cloud_run_private_networking && var.enable_certificate_manager ? module.certificates[0].regional_certificate_name : null
}

# Model Armor Outputs

output "model_armor_request_template_id" {
  description = "Request-side Model Armor template ID"
  value       = var.enable_model_armor ? module.model_armor[0].request_template_id : null
}

output "model_armor_request_template_name" {
  description = "Request-side Model Armor template full resource name"
  value       = var.enable_model_armor ? module.model_armor[0].request_template_name : null
}

output "model_armor_response_template_id" {
  description = "Response-side Model Armor template ID"
  value       = var.enable_model_armor ? module.model_armor[0].response_template_id : null
}

output "model_armor_response_template_name" {
  description = "Response-side Model Armor template full resource name"
  value       = var.enable_model_armor ? module.model_armor[0].response_template_name : null
}

output "model_armor_inspect_template_id" {
  description = "DLP inspect template ID referenced by the response template's advanced SDP config (null when model_armor_sdp_enforcement = DISABLED)"
  value       = var.enable_model_armor ? module.model_armor[0].inspect_template_id : null
}

output "model_armor_deidentify_template_id" {
  description = "DLP de-identify template ID referenced by the response template's advanced SDP config (null when model_armor_sdp_enforcement = DISABLED)"
  value       = var.enable_model_armor ? module.model_armor[0].deidentify_template_id : null
}

output "model_armor_service_account" {
  description = "Service Extensions service account (gcp-sa-dep) used by the Agent Gateway to call Model Armor"
  value       = var.enable_model_armor ? module.model_armor[0].service_account_email : null
}

output "model_armor_service_agent_email" {
  description = "Model Armor service agent (gcp-sa-modelarmor) granted DLP read access (null when model_armor_sdp_enforcement = DISABLED)"
  value       = var.enable_model_armor ? module.model_armor[0].model_armor_service_agent_email : null
}

output "model_armor_gemini_enterprise_template_name" {
  description = "Full resource name of the Gemini Enterprise Model Armor template (for Discovery Engine REST API)"
  value       = var.enable_model_armor && var.enable_model_armor_gemini_enterprise ? module.model_armor[0].gemini_enterprise_template_name : null
}

output "model_armor_vertex_ai_service_account" {
  description = "AI Platform service agent email granted Model Armor access"
  value       = var.enable_model_armor && var.enable_model_armor_vertex_ai ? module.model_armor[0].vertex_ai_service_account_email : null
}


/*
# Apigee Outputs

output "apigee_org_id" {
  description = "Apigee organization ID"
  value       = var.enable_apigee ? module.apigee[0].org_id : null
}

output "apigee_org_name" {
  description = "Apigee organization name"
  value       = var.enable_apigee ? module.apigee[0].org_name : null
}

output "apigee_tenant_project_id" {
  description = "Apigee tenant project ID"
  value       = var.enable_apigee ? module.apigee[0].tenant_project_id : null
}

output "apigee_envgroups" {
  description = "Map of Apigee environment groups"
  value       = var.enable_apigee ? module.apigee[0].envgroups : {}
}

output "apigee_environments" {
  description = "Map of Apigee environments"
  value       = var.enable_apigee ? module.apigee[0].environments : {}
}

output "apigee_instances" {
  description = "Map of Apigee instances"
  value       = var.enable_apigee ? module.apigee[0].instances : {}
}

output "apigee_proxy_runtime_sa_email" {
  description = "Apigee proxy runtime service account email"
  value       = var.enable_apigee ? module.apigee[0].proxy_runtime_sa_email : null
}

output "apigee_apim_operator_sa_email" {
  description = "Apigee APIM Operator service account email"
  value       = var.enable_apigee ? module.apigee[0].apim_operator_sa_email : null
}

output "apigee_endpoint_attachment_hosts" {
  description = "Map of Apigee endpoint attachment hosts"
  value       = var.enable_apigee ? module.apigee[0].endpoint_attachment_hosts : {}
}

output "apigee_northbound_lb_ip" {
  description = "Apigee northbound load balancer internal IP"
  value       = var.enable_apigee && var.apigee_enable_northbound_lb ? module.apigee[0].northbound_lb_ip : null
}

output "apigee_dns_peering_zones" {
  description = "Apigee DNS peering zones"
  value       = var.enable_apigee ? module.apigee[0].dns_peering_zones : {}
}
*/

# PSC Interface Outputs

output "psc_interface_network_attachment_id" {
  description = "Network attachment ID for PSC Interface (pass to deploy_agent.py --network-attachment)"
  value       = var.enable_psc_interface ? module.networking.psc_interface_network_attachment_id : null
}

output "psc_interface_network_attachment_name" {
  description = "Network attachment name for PSC Interface"
  value       = var.enable_psc_interface ? module.networking.psc_interface_network_attachment_name : null
}

output "psc_interface_dns_zone_name" {
  description = "DNS zone name for PSC Interface DNS peering"
  value       = var.enable_psc_interface ? module.networking.psc_interface_dns_zone_name : null
}

output "psc_interface_dns_domain" {
  description = "Domain name for PSC Interface DNS peering (ends with a dot)"
  value       = var.enable_psc_interface ? module.networking.psc_interface_dns_domain : null
}

output "psc_interface_dns_peering_domain" {
  description = "DNS domain for PSC Interface DNS peering (pass to deploy_agent.py --dns-peering-domain)"
  value       = var.enable_psc_interface && var.psc_interface_dns_zone != null ? var.psc_interface_dns_zone.domain : null
}

# Agent Gateway Outputs

output "agent_gateway_id" {
  description = "Full resource ID of the Agent Gateway"
  value       = var.enable_agent_gateway ? module.agent_gateway[0].agent_gateway_id : null
}

output "agent_gateway_mtls_endpoint" {
  description = "mTLS endpoint clients use to reach the Agent Gateway"
  value       = var.enable_agent_gateway ? module.agent_gateway[0].mtls_endpoint : null
}

output "agent_gateway_root_certificates" {
  description = "Root certificates clients use to validate the Agent Gateway mTLS endpoint"
  value       = var.enable_agent_gateway ? module.agent_gateway[0].root_certificates : null
  sensitive   = true
}

output "agent_gateway_service_extensions_service_account" {
  description = "Service account the Agent Gateway uses to call out to authz extensions"
  value       = var.enable_agent_gateway ? module.agent_gateway[0].service_extensions_service_account : null
}

output "agent_gateway_registry_uri" {
  description = "URI of the project-local agent registry the gateway is bound to"
  value       = var.enable_agent_gateway ? module.agent_gateway[0].registry_uri : null
}

output "agent_gateway_subnet_self_link" {
  description = "Self link of the Agent Gateway dedicated co-location subnet"
  value       = var.enable_agent_gateway ? module.networking.agent_gateway_subnet_self_link : null
}

# Agent Registry Endpoints Outputs

output "agent_registry_service_ids" {
  description = "Map of registered Agent Registry service resource IDs, keyed by service_id"
  value       = var.enable_agent_registry_endpoints ? module.agent_registry_endpoints[0].service_ids : null
}
