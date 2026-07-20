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



# user_project_override + billing_project route quota/billing for every API
# call through var.project_id. Required for DLP — the API rejects requests
# made via Application Default Credentials when no quota project is supplied.
provider "google" {
  project               = var.project_id
  region                = var.region
  user_project_override = true
  billing_project       = var.project_id
}

provider "google-beta" {
  project                          = var.project_id
  region                           = var.region
  network_services_custom_endpoint = "https://networkservices.googleapis.com/v1beta1/"
  user_project_override            = true
  billing_project                  = var.project_id
}
