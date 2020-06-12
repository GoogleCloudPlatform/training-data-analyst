# Create Test Server in Private VPC
resource "google_compute_instance" "private-test-server-linux" {
  name         = "private-test-server-linux-${random_id.instance_id.hex}"
  machine_type = "f1-micro"
  zone         = var.gcp_zone_1
  tags         = ["allow-ssh"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-9"
    }
  }

  metadata_startup_script = "sudo apt-get update;"

  network_interface {
    network        = google_compute_network.private-vpc.name
    subnetwork     = google_compute_subnetwork.private-subnet_1.name
    access_config { }  # Comment out this line to remove external IP address
  }
} 


output "private-test-server-linux" {
  value = google_compute_instance.private-test-server-linux.name
}

output "private-test-server-linux-external-ip" {
  value = google_compute_instance.private-test-server-linux.network_interface.0.access_config.0.nat_ip
}

output "private-test-server-linux-internal-ip" {
  value = google_compute_instance.private-test-server-linux.network_interface.0.network_ip
}