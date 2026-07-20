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

output "service_names" {
  description = "Map of MCP service key to Cloud Run service name"
  value       = { for k, v in google_cloud_run_v2_service.mcp : k => v.name }
}

output "service_urls" {
  description = "Map of MCP service key to Cloud Run *.run.app URL (only reachable via the internal LB)"
  value       = { for k, v in google_cloud_run_v2_service.mcp : k => v.uri }
}

output "service_url_list" {
  description = "Map of MCP service key to the full list of Cloud Run URLs (both the hash form `<svc>-<hash>-<region-abbrev>.a.run.app` and the project-number form `<svc>-<project-number>.<region>.run.app`). Use this when scoping authz/security policies to Host headers — agents may legitimately call either URL form."
  value       = { for k, v in google_cloud_run_v2_service.mcp : k => v.urls }
}

output "service_account_emails" {
  description = "Map of MCP service key to runtime service account email"
  value       = { for k, v in google_service_account.mcp : k => v.email }
}
