resource "google_compute_network_peering" "public-private" {
  name         = "peering1"
  network      = google_compute_network.public-vpc.self_link
  peer_network = google_compute_network.private-vpc.self_link
}

resource "google_compute_network_peering" "private-public" {
  name         = "peering2"
  network      = google_compute_network.private-vpc.self_link
  peer_network = google_compute_network.public-vpc.self_link
}