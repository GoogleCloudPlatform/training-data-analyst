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



variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "project_number" {
  description = "GCP project number (for Agent Identity IAM bindings)"
  type        = string
}

variable "organization_id" {
  description = "GCP organization ID (numeric). Required for Agent Identity IAM bindings."
  type        = string
}

variable "platform_admin_members" {
  description = "List of IAM members granted roles/aiplatform.user for Agent Engine access"
  type        = list(string)
  default     = []
}
