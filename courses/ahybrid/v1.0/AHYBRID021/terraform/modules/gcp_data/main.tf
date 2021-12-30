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