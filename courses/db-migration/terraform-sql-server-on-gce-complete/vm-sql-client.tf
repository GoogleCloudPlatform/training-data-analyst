# Create VM SQL Client
resource "google_compute_instance" "sql-client" {
  name         = "sql-client-${random_id.instance_id.hex}"
  machine_type = "f1-micro"
  zone         = var.gcp_zone_1
  tags         = ["allow-ssh"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-1604-xenial-v20200429"
    }
  }

  metadata_startup_script = "sudo apt-get update;"

  network_interface {
    network       = google_compute_network.public-vpc.name
    subnetwork    = google_compute_subnetwork.public-subnet_1.name
    access_config { }
  }
} 

output "sql-client-name" {
  value = google_compute_instance.sql-client.name
}

output "sql-client-external-ip" {
  value = google_compute_instance.sql-client.network_interface.0.access_config.0.nat_ip
}

output "sql-client-internal-ip" {
  value = google_compute_instance.sql-client.network_interface.0.network_ip
}