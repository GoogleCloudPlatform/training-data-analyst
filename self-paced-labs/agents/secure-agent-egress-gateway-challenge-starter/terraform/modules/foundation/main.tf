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



/**
 * Foundation Module
 *
 * Enables required Google Cloud APIs and sets quota preferences.
 * This module should be applied first before any other infrastructure.
 */

module "project" {
  source        = "github.com/GoogleCloudPlatform/cloud-foundation-fabric//modules/project?ref=v55.3.0"
  name          = var.project_id
  project_reuse = {} # Use existing project

  services = [for s in var.enabled_services : s if s != "aiplatform.googleapis.com"]

  logging_data_access = var.logging_data_access

  # NOTE: GPU quotas must be requested manually via GCP Console.
  # The Cloud Foundation Fabric quota feature requires the Service Usage Consumer
  # API which may not be available in all projects. Request quotas at:
  # https://console.cloud.google.com/iam-admin/quotas
}

# Ensure Service Extensions service identity exists
# This is required for IAM bindings in model-armor module
resource "google_project_service_identity" "network_services" {
  provider = google-beta
  project  = var.project_id
  service  = "networkservices.googleapis.com"

  depends_on = [module.project]
}

# Enable Vertex AI API explicitly to control order and avoid race conditions
# in the project module's IAM bindings
resource "google_project_service" "aiplatform" {
  project            = module.project.project_id
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

# Ensure Vertex AI service identity exists
# This must happen after the API is enabled
resource "google_project_service_identity" "aiplatform" {
  provider = google-beta
  project  = module.project.project_id
  service  = "aiplatform.googleapis.com"

  depends_on = [google_project_service.aiplatform]
}

resource "google_project_iam_member" "aiplatform_network_admin" {
  count   = var.enable_psc_interface ? 1 : 0
  project = module.project.project_id
  role    = "roles/compute.networkAdmin"
  member  = "serviceAccount:${google_project_service_identity.aiplatform.email}"
}

resource "google_project_iam_member" "aiplatform_dns_peer" {
  count   = var.enable_psc_interface ? 1 : 0
  project = module.project.project_id
  role    = "roles/dns.peer"
  member  = "serviceAccount:${google_project_service_identity.aiplatform.email}"
}

# Allow time for the AI Platform service identity to propagate before
# binding IAM roles to the Reasoning Engine service agent.
resource "time_sleep" "aiplatform_identity_propagation" {
  count           = var.enable_psc_interface ? 1 : 0
  depends_on      = [google_project_service_identity.aiplatform]
  create_duration = "30s"
}

# The Reasoning Engine service agent (gcp-sa-aiplatform-re) also needs
# network and DNS permissions to create PSC Interface NICs and DNS peering zones.
resource "google_project_iam_member" "aiplatform_re_network_admin" {
  count      = var.enable_psc_interface ? 1 : 0
  project    = module.project.project_id
  role       = "roles/compute.networkAdmin"
  member     = "serviceAccount:service-${module.project.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
  depends_on = [time_sleep.aiplatform_identity_propagation]
}

resource "google_project_iam_member" "aiplatform_re_dns_peer" {
  count      = var.enable_psc_interface ? 1 : 0
  project    = module.project.project_id
  role       = "roles/dns.peer"
  member     = "serviceAccount:service-${module.project.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
  depends_on = [time_sleep.aiplatform_identity_propagation]
}
