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

variable "dns_zone_domain" {
  description = "DNS zone domain (must end with dot, e.g., 'example.com.'). Set to null to skip DNS configuration."
  type        = string
  default     = null
  validation {
    condition     = var.dns_zone_domain == null || can(regex("[.]$", var.dns_zone_domain))
    error_message = "dns_zone_domain must end with a dot (e.g., 'example.com.') or be null"
  }
}

variable "dns_zone_name" {
  description = "The name of the existing Cloud DNS managed zone. If null, derived from dns_zone_domain."
  type        = string
  default     = null
}

variable "enable_certificate_manager" {
  description = "Enable Certificate Manager DNS validation records"
  type        = bool
  default     = false
}

# Certificate DNS Authorizations (from certificates module)
variable "certificate_dns_authorizations_regional" {
  description = "DNS authorizations from regional certificates module (output from module.certificates.regional_dns_authorizations)"
  type = map(object({
    id     = string
    domain = string
    dns_resource_record = list(object({
      name = string
      type = string
      data = string
    }))
  }))
  default = null
}

# VPC Configuration (for private DNS zone)
variable "vpc_self_links" {
  description = "List of VPC self links to attach to the private DNS zone"
  type        = list(string)
  default     = []
}

# DNS Record Configuration
variable "certificate_validation_ttl" {
  description = "TTL for certificate validation DNS records (in seconds)"
  type        = number
  default     = 300
}

variable "gateway_dns_ttl" {
  description = "TTL for gateway DNS A records (in seconds)"
  type        = number
  default     = 300
}

variable "internal_dns_ttl" {
  description = "TTL for internal DNS A records (in seconds)"
  type        = number
  default     = 300
}

# Internal DNS Configuration
variable "internal_dns_zone_name" {
  description = "Name of the internal DNS zone"
  type        = string
  default     = "internal-zone"
}

variable "internal_dns_domain" {
  description = "Domain for internal DNS zone (must end with dot). If null, will be derived from dns_zone_domain as 'internal.{dns_zone_domain}'"
  type        = string
  default     = null
  validation {
    condition     = var.internal_dns_domain == null || can(regex("[.]$", var.internal_dns_domain))
    error_message = "internal_dns_domain must end with a dot or be null"
  }
}

# Self Managed Gateway (Phase 11)
variable "enable_self_managed_gateway_dns" {
  description = "Enable DNS record creation for self managed gateway"
  type        = bool
  default     = false
}

variable "self_managed_gateway_ip" {
  description = "IP address for the self managed gateway"
  type        = string
  default     = null
}

variable "self_managed_gateway_subdomain" {
  description = "Subdomain for the self managed gateway (e.g., 'smg' creates smg.gateway.example.com)"
  type        = string
  default     = "smg"
}

# Self Managed Gateway Internal DNS (Phase 11)
variable "enable_self_managed_internal_dns" {
  description = "Enable internal DNS record for self managed gateway"
  type        = bool
  default     = false
}

variable "self_managed_internal_subdomain" {
  description = "Subdomain in the internal zone for the self managed gateway (e.g., 'diy' creates diy.internal.example.com)"
  type        = string
  default     = "diy"
}

# GKE Gateway (Phase 12)
variable "enable_gke_gateway_dns" {
  description = "Enable DNS record creation for GKE gateway"
  type        = bool
  default     = false
}

variable "gke_gateway_ip" {
  description = "IP address for the GKE gateway (from networking module)"
  type        = string
  default     = null
}

variable "gke_gateway_subdomain" {
  description = "Subdomain for the GKE gateway (e.g., 'gateway' creates gateway.example.com)"
  type        = string
  default     = "gateway"
}
