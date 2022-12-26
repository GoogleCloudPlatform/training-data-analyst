resource "google_spanner_instance" "db-instance" {
  name             = "terraform-spanner-instance"
  config           = "regional-${var.region}"
  display_name     = "TF Spanner Instance"
  processing_units = var.processing_units
  force_destroy = var.force_destroy
}

resource "google_spanner_database" "test-database" {
  instance            = google_spanner_instance.db-instance.name
  name                = "pets-db"
  # Can't run destroy unless set to false
  deletion_protection = var.deletion_protection 

  ddl = [
    "CREATE TABLE Owners (OwnerID STRING(36) NOT NULL, OwnerName STRING(MAX) NOT NULL) PRIMARY KEY (OwnerID)",
    "CREATE TABLE Pets (PetID STRING(36) NOT NULL, OwnerID STRING(36) NOT NULL, PetType STRING(MAX) NOT NULL, PetName STRING(MAX) NOT NULL, Breed STRING(MAX) NOT NULL) PRIMARY KEY (PetID)",
  ]
}
