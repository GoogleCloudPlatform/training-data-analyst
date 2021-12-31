data "google_project" "project" {
}

output "project_number" {
  value = data.google_project.project.number
}

data "google_container_azure_versions" "this" {
  location = var.gcp_location
  project  = var.gcp_project
}

output "latest_version" {
  value = data.google_container_azure_versions.this.valid_versions[0]
}

# Enable services in newly created GCP Project.
resource "google_project_service" "gcp_services" {
  count   = length(var.gcp_service_list)
  project = google_project.demo_project.project_id
  service = var.gcp_service_list[count.index]

  disable_dependent_services = true
}