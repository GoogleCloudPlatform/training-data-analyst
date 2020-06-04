# Create Windows SLQ Server in Private VPC
resource "google_compute_instance" "sql-server-windows" {
  name         = "sql-server-windows-${random_id.instance_id.hex}"
  machine_type = "n1-standard-2"
  zone         = var.gcp_zone_1
  tags         = ["allow-rdp", "allow-sql"]

  boot_disk {
    initialize_params {
      image = "windows-sql-cloud/sql-2017-express-windows-2016-dc-v20200414"
    }
  }

  network_interface {
    network        = google_compute_network.private-vpc.name
    subnetwork     = google_compute_subnetwork.private-subnet_1.name
    # access_config { } - Remove access_config for no External IP
  }
} 

output "sql-server-windows" {
  value = google_compute_instance.sql-server-windows.name
}

output "sql-server-windows-external-ip" {
  value = "NONE"
}

output "tsql-server-windows-internal-ip" {
  value = google_compute_instance.sql-server-windows.network_interface.0.network_ip
}