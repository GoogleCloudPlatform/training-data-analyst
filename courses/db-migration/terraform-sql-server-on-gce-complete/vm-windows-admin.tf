# Create VM Windows Admin
resource "google_compute_instance" "windows-admin" {
  name         = "windows-admin-${random_id.instance_id.hex}"
  machine_type = "n1-standard-2"
  zone         = var.gcp_zone_1
  tags         = ["allow-rdp"]

  boot_disk {
    initialize_params {
      image = "windows-cloud/windows-server-2016-dc-v20200424"
    }
  }

  network_interface {
    network       = google_compute_network.public-vpc.name
    subnetwork    = google_compute_subnetwork.public-subnet_1.name
    access_config { }
  }
} 

output "windows-admin-name" {
  value = google_compute_instance.windows-admin.name
}

output "windows-admin-external-ip" {
  value = google_compute_instance.windows-admin.network_interface.0.access_config.0.nat_ip
}

output "windows-admin-internal-ip" {
  value = google_compute_instance.windows-admin.network_interface.0.network_ip
}