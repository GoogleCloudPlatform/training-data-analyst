# Create MySQL Client in Public VPC
resource "google_compute_instance" "mysql-client" {
  name         = "mysql-client-${random_id.instance_id.hex}"
  machine_type = "f1-micro"
  zone         = var.gcp_zone_1
  tags         = ["allow-ssh"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-9"
    }
  }

  network_interface {
    network        = google_compute_network.public-vpc.name
    subnetwork     = google_compute_subnetwork.public-subnet_1.name
    access_config { } 
  }
} 


output "mysql-client" {
  value = google_compute_instance.mysql-client.name
}

output "mysql-client-external-ip" {
  value = google_compute_instance.mysql-client.network_interface.0.access_config.0.nat_ip
}

output "mysql-client-internal-ip" {
  value = google_compute_instance.mysql-client.network_interface.0.network_ip
}