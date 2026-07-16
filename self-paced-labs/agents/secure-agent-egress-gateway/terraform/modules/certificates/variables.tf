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

variable "region" {
  description = "GCP region for regional certificates"
  type        = string
}

variable "dns_zone_domain" {
  description = "DNS zone domain (must end with dot, e.g., 'example.com.'). Set to null to skip certificate creation."
  type        = string
  default     = null
  validation {
    condition     = var.dns_zone_domain == null || can(regex("[.]$", var.dns_zone_domain))
    error_message = "dns_zone_domain must end with a dot (e.g., 'example.com.') or be null"
  }
}

variable "enable_certificate_manager" {
  description = "Enable Certificate Manager and create SSL certificates"
  type        = bool
  default     = false
}

variable "gateway_scope" {
  description = "Gateway scope: 'regional' for regional internal load balancers, or null to skip"
  type        = string
  default     = null
  validation {
    condition     = var.gateway_scope == null || contains(["regional"], var.gateway_scope)
    error_message = "gateway_scope must be 'regional' or null"
  }
}

variable "labels" {
  description = "Labels to apply to certificate resources"
  type        = map(string)
  default     = {}
}

# Regional Certificate Configuration
variable "regional_certificate_name" {
  description = "Name for the regional certificate (public domain)"
  type        = string
  default     = "main-certificate-regional"
}

variable "internal_certificate_name" {
  description = "Name for the internal certificate covering base domain and wildcard (private endpoints)"
  type        = string
  default     = "internal-certificate-regional"
}

# Global Certificate Configuration
