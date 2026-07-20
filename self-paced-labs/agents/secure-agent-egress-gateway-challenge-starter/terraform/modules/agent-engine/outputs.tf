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



output "agent_identity_principal" {
  description = "The Agent Identity principalSet for all Agent Engine agents in this project"
  value       = "principalSet://agents.global.org-${var.organization_id}.system.id.goog/attribute.platformContainer/aiplatform/projects/${var.project_number}"
}

output "agent_mcp_invoker_email" {
  description = "Email of the SA agents impersonate when invoking MCP Cloud Run services. Pass this to the mcp-cloud-run module's invoker_sa_email and to the agent runtime as MCP_INVOKER_SA_EMAIL."
  value       = google_service_account.agent_mcp_invoker.email
}
