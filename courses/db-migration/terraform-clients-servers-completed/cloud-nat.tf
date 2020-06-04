resource "google_compute_router" "nat-router" {
  name    = "nat-router"
  region  = google_compute_subnetwork.private-subnet_1.region
  network = google_compute_network.private-vpc.id

  bgp {
    asn = 64514
  }
}

resource "google_compute_router_nat" "private-nat" {
  name                               = "private-nat"
  router                             = google_compute_router.nat-router.name
  region                             = google_compute_router.nat-router.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}