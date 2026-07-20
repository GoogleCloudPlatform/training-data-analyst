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
 * Observability Module
 *
 * Enables Log Analytics on the auto-created `_Default` log bucket so audit
 * and platform logs are queryable as `<project>.global._Default._AllLogs`,
 * and provisions the authorization-debugging Cloud Monitoring dashboard
 * whose widgets run opsAnalyticsQuery against that view.
 *
 * The provider adopts the existing `_Default` bucket — no creation, no
 * import. `terraform destroy` removes the bucket config from state but
 * leaves the bucket and its log entries intact (provider semantics for
 * `_Default` / `_Required` buckets).
 */

resource "google_logging_project_bucket_config" "default_analytics" {
  project          = var.project_id
  location         = "global"
  bucket_id        = "_Default"
  enable_analytics = true
}

# The dashboard JSON ships with the `PROJECT_ID` placeholder in BigQuery-
# style table refs (`<project>.global._Default._AllLogs`); rewrite it to the
# caller's project. For a manual import via the GCP console, substitute
# `PROJECT_ID` with a real project ID first.
resource "google_monitoring_dashboard" "authorization_debugging" {
  project = var.project_id
  dashboard_json = replace(
    file("${path.module}/authorization-debugging.json"),
    "PROJECT_ID",
    var.project_id,
  )

  depends_on = [google_logging_project_bucket_config.default_analytics]
}
