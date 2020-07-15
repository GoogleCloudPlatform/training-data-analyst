# create the Private VPC
resource "google_compute_network" "private-vpc" {
  name                    = "private-vpc"
  auto_create_subnetworks = "false"
  routing_mode            = "GLOBAL"
}

# create the private subnet
resource "google_compute_subnetwork" "private-subnet_1" {
  name          = "private-subnet-1"
  ip_cidr_range = var.subnet_cidr_private
  network       = google_compute_network.private-vpc.name
  region        = var.gcp_region_1
}