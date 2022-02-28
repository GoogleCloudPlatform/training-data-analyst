data "google_project" "project" {
}

output "project_number" {
  value = data.google_project.project.number
}
