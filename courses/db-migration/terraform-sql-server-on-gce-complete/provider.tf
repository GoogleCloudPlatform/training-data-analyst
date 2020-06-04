terraform {
  required_version = ">= 0.12"
}

provider "google" {
  project = var.project_id
  region  = var.gcp_region_1
  zone    = var.gcp_zone_1
}