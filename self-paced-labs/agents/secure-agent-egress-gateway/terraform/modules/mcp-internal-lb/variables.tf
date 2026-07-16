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
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for the regional internal Application LB"
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "network_self_link" {
  description = "Self link of the VPC network"
  type        = string
}

variable "subnet_self_link" {
  description = "Self link of the subnet that hosts the LB internal IP. Also used as the forwarding rule's subnetwork unless forwarding_rule_subnet_self_link is set."
  type        = string
}

variable "internal_ip_address" {
  description = "Existing internal IP address to use as the LB VIP. If null a new one is allocated in subnet_self_link."
  type        = string
  default     = null
}

variable "create_address" {
  description = "Whether to create a new internal IP address for the LB. Set to false if internal_ip_address is provided."
  type        = bool
  default     = true
}

variable "forwarding_rule_subnet_self_link" {
  description = "Self link of the subnet to bind the forwarding rule to. Defaults to subnet_self_link. Override when the LB VIP is allocated from a different subnet (e.g. an Agent Gateway co-location subnet)."
  type        = string
  default     = null
}

variable "dns_domain" {
  description = "Private DNS domain (with trailing dot) hosting the per-service A records, e.g. 'mcp-server.internal.'. The URL mask uses '<service>.<dns_domain_no_dot>'."
  type        = string
  validation {
    condition     = endswith(var.dns_domain, ".")
    error_message = "dns_domain must end with a trailing dot."
  }
}

variable "protocol" {
  description = "LB front-end protocol: HTTP or HTTPS. HTTPS auto-generates a self-signed cert for *.<dns_domain>."
  type        = string
  default     = "HTTPS"
  validation {
    condition     = contains(["HTTP", "HTTPS"], var.protocol)
    error_message = "protocol must be HTTP or HTTPS."
  }
}

variable "labels" {
  description = "Labels to apply to LB resources that support them"
  type        = map(string)
  default     = {}
}

variable "ssl_certificate_id" {
  description = "Existing SSL certificate ID to use for the HTTPS proxy. If provided, self-signed cert generation is skipped."
  type        = string
  default     = null
}
