# allow ssh
resource "google_compute_firewall" "public-allow-ssh" {
  name    = "${google_compute_network.public-vpc.name}-allow-ssh"
  network = google_compute_network.public-vpc.name
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = [
    "0.0.0.0/0"
  ]
  target_tags = ["allow-ssh"] 
}

# allow rdp
resource "google_compute_firewall" "public-allow-rdp" {
  name    = "${google_compute_network.public-vpc.name}-allow-rdp"
  network = google_compute_network.public-vpc.name
  allow {
    protocol = "tcp"
    ports    = ["3389"]
  }
  source_ranges = [
    "0.0.0.0/0"
  ]
  target_tags = ["allow-rdp"] 
}

# allow ping only from everywhere
resource "google_compute_firewall" "public-allow-ping" {
  name    = "${google_compute_network.public-vpc.name}-allow-ping"
  network = google_compute_network.public-vpc.name
  allow {
    protocol = "icmp"
  }
  source_ranges = [
    "0.0.0.0/0"
  ]
}