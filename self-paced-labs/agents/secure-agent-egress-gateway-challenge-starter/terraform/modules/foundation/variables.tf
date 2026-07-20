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

variable "enabled_services" {
  description = "List of Google Cloud APIs to enable"
  type        = list(string)
  default = [
    # Core GCP services
    "compute.googleapis.com",
    "storage.googleapis.com",
    "storage-api.googleapis.com",
    "storage-component.googleapis.com",
    "dns.googleapis.com",

    # GKE and container services
    # "container.googleapis.com",
    "containerregistry.googleapis.com",
    "artifactregistry.googleapis.com",
    # "containerfilesystem.googleapis.com",
    # "containersecurity.googleapis.com",

    # Cloud Run services
    "run.googleapis.com",

    # Monitoring and logging
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudtrace.googleapis.com",
    "cloudprofiler.googleapis.com",

    # Networking & Security
    "servicenetworking.googleapis.com",
    "networkmanagement.googleapis.com",
    "networkservices.googleapis.com",
    "modelarmor.googleapis.com",
    "networksecurity.googleapis.com",

    # Security and IAM
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "cloudkms.googleapis.com",
    "binaryauthorization.googleapis.com",
    "secretmanager.googleapis.com",
    "iap.googleapis.com",

    # Other essential services
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "stackdriver.googleapis.com",
    "autoscaling.googleapis.com",
    "cloudbuild.googleapis.com",

    # Certificate Manager
    "certificatemanager.googleapis.com",

    # Quota management
    "cloudquotas.googleapis.com",

    # Apigee services
    # "apigee.googleapis.com",

    # Vertex AI services
    "aiplatform.googleapis.com",

    # BigQuery
    # "bigquery.googleapis.com",

    # Cloud DLP
    "dlp.googleapis.com",

    # Telemetry (OTLP endpoint for metrics and traces)
    "telemetry.googleapis.com",

    # Agent Registry
    "apphub.googleapis.com",
    "agentregistry.googleapis.com"
  ]
}

variable "enable_psc_interface" {
  description = "Enable IAM grants for PSC Interface (compute.networkAdmin, dns.peer for Vertex AI service agent)"
  type        = bool
  default     = false
}

variable "logging_data_access" {
  description = "Data access audit log configuration. Map of service name to a map of log type (ADMIN_READ|DATA_READ|DATA_WRITE) to optional exempted_members. Use the special 'allServices' key to apply project-wide across every API."
  type = map(object({
    ADMIN_READ = optional(object({ exempted_members = optional(list(string), []) }))
    DATA_READ  = optional(object({ exempted_members = optional(list(string), []) }))
    DATA_WRITE = optional(object({ exempted_members = optional(list(string), []) }))
  }))
  default = {
    "allServices" = {
      ADMIN_READ = {}
      DATA_READ  = {}
      DATA_WRITE = {}
    }
  }
  nullable = false
}
