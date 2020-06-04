# Create a MySQL Server in Private VPC
resource "google_compute_instance" "mysql-server" {
  name         = "mysql-server-${random_id.instance_id.hex}"
  machine_type = "f1-micro"
  zone         = var.gcp_zone_1
  tags         = ["allow-ssh", "allow-mysql"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-9"
    }
  }

  network_interface {
    network        = google_compute_network.private-vpc.name
    subnetwork     = google_compute_subnetwork.private-subnet_1.name
  #  access_config { } 
  }
} 

output "mysql-server" {
  value = google_compute_instance.mysql-server.name
}

output "mysql-server-external-ip" {
  value = "NONE"
}

output "mysql-server-internal-ip" {
  value = google_compute_instance.mysql-server.network_interface.0.network_ip
}