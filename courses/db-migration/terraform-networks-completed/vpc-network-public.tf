resource "google_compute_network" "public-vpc" {
  name                    = "public-vpc"
  auto_create_subnetworks = "false"
  routing_mode            = "GLOBAL"
}

resource "google_compute_subnetwork" "public-subnet_1" {
  name          = "public-subnet-1"
  ip_cidr_range = var.subnet_cidr_public
  network       = google_compute_network.public-vpc.name
  region        = var.gcp_region_1
}