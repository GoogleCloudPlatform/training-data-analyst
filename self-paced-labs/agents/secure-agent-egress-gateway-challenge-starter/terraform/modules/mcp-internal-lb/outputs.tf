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

output "ip_address" {
  description = "Internal IP address that fronts the MCP services LB"
  value       = google_compute_forwarding_rule.mcp.ip_address
}

output "forwarding_rule_id" {
  description = "ID of the LB forwarding rule"
  value       = google_compute_forwarding_rule.mcp.id
}

output "url_mask" {
  description = "URL mask configured on the Serverless NEG"
  value       = google_compute_region_network_endpoint_group.mcp.cloud_run[0].url_mask
}
