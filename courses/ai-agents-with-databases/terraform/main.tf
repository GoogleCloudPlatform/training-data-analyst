terraform {
  required_providers {
    google = {
      source  = "hashicorp/google-beta"
      version = ">= 5.35.0" # Using google-beta as per the requirement
    }
    local = {
      source  = "hashicorp/local"
      version = ">= 2.1"
    }
    null = {
      source  = "hashicorp/null"
      version = ">= 3.1"
    }
  }
}

# Configure the Google Cloud provider
provider "google" {
  project = var.gcp_project_id
  region  = var.region
}

# Get authentication token for the local-exec provisioner
data "google_client_config" "current" {}

# Enable the required Google Cloud APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "sqladmin.googleapis.com",
    "alloydb.googleapis.com",
    "logging.googleapis.com",
    "storage-component.googleapis.com",
    "serviceusage.googleapis.com",
    "networkmanagement.googleapis.com",
    "servicenetworking.googleapis.com",
    "dns.googleapis.com",
    "vpcaccess.googleapis.com",
    "spanner.googleapis.com",
    "iam.googleapis.com",
    "compute.googleapis.com",
    "networkconnectivity.googleapis.com",
    "notebooks.googleapis.com",
    "dataform.googleapis.com",
    "datacatalog.googleapis.com",
    "dataproc.googleapis.com",
    "dataflow.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudtrace.googleapis.com",
    "monitoring.googleapis.com",
    "iap.googleapis.com",
    "datastream.googleapis.com"
  ])
  service                    = each.key
  disable_dependent_services = true
}

# Create a custom VPC
resource "google_compute_network" "demo_vpc" {
  name                    = "demo-vpc"
  auto_create_subnetworks = true
  mtu                     = 1460
  routing_mode            = "REGIONAL"
  depends_on              = [google_project_service.apis]
}

# Create a Cloud Router
resource "google_compute_router" "router" {
  name    = "nat-router"
  network = google_compute_network.demo_vpc.id
  region  = var.region
}

# Create a Cloud NAT Gateway
resource "google_compute_router_nat" "nat" {
  name                               = "managed-nat-gateway"
  router                             = google_compute_router.router.name
  region                             = google_compute_router.router.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

resource "google_compute_firewall" "dataflow_internal_communication" {
  name    = "allow-dataflow-internal"
  network = google_compute_network.demo_vpc.name
  project = var.gcp_project_id

  allow {
    protocol = "tcp"
    ports    = ["12345-12346"]
  }

  source_tags = ["dataflow"]
  target_tags = ["dataflow"]
  direction   = "INGRESS"
  priority    = 1000 # You can adjust the priority if needed. Lower numbers have higher precedence.
  description = "Allows internal TCP communication between Dataflow workers on ports 12345-12346."
}

resource "google_compute_firewall" "iap_internal_communication" {
  name    = "allow-iap-internal"
  network = google_compute_network.demo_vpc.name
  project = var.gcp_project_id

  allow {
    protocol = "all"
  }

  source_ranges = ["35.235.240.0/20"]
  direction   = "INGRESS"
  priority    = 1000 # You can adjust the priority if needed. Lower numbers have higher precedence.
  description = "Allows internal TCP communication for IAP."
}

# Reserve a private IP range for service networking
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "private-ip-alloc"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.demo_vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.demo_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}

# Create an AlloyDB cluster with PSA
resource "google_alloydb_cluster" "default" {
  cluster_id = "my-alloydb-cluster"
  location   = var.region
  deletion_policy = "FORCE"
  network_config {
    network = google_compute_network.demo_vpc.id
    allocated_ip_range = google_compute_global_address.private_ip_alloc.name
  }
  initial_user {
    password = var.alloydb_password
  }
  depends_on = [
    google_project_service.apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Create a single-zone AlloyDB instance with PSA
resource "google_alloydb_instance" "default" {
  cluster         = google_alloydb_cluster.default.name
  instance_id     = "my-alloydb-instance"
  instance_type   = "PRIMARY"
  availability_type = "ZONAL"
  client_connection_config {
    ssl_config {
        ssl_mode = "ALLOW_UNENCRYPTED_AND_ENCRYPTED"
    }
  }
  machine_config {
    cpu_count = 2
  }
  database_flags = {
    "google_ml_integration.enable_model_support" = "on"
    "password.enforce_complexity"                = "on"
    "password.min_uppercase_letters"             = "1"
    "password.min_numerical_chars"               = "1"
    "password.min_pass_length"                   = "10"
  }
  # Optional Public IP configuration
  #network_config {
  #  enable_public_ip = true
  #  authorized_external_networks {
  #      cidr_range = "1.2.3.4/32" # Replace with your IP address
  #  }
  #}
  
}

# Create a single-zone Cloud SQL instance with PSC
resource "google_sql_database_instance" "postgres" {
  name                 = "my-postgres-instance"
  database_version    = "POSTGRES_17"
  region              = var.region
  deletion_protection = false
  root_password       = var.cloud_sql_password

  settings {
    tier              = "db-custom-2-7680"
    availability_type = "ZONAL"
    edition           = "ENTERPRISE"
    ip_configuration {
      psc_config {
        psc_enabled = true
        allowed_consumer_projects = [var.gcp_project_id]
        psc_auto_connections {
          consumer_network = google_compute_network.demo_vpc.id
          consumer_service_project_id = var.gcp_project_id
        }
      }
      ipv4_enabled = false
    }

  }
  depends_on = [
    google_project_service.apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Create a PSC endpoint to connect to Cloud SQL from the VPC
resource "google_compute_address" "default" {
  name         = "psc-compute-address"
  region       = var.region
  address_type = "INTERNAL"
  subnetwork   = google_compute_network.demo_vpc.name
}

# Create a forwarding rule for the Cloud SQL PSC endpoint
resource "google_compute_forwarding_rule" "default" {
  name                  = "psc-forwarding-rule-${google_sql_database_instance.postgres.name}"
  region                = var.region
  network               = google_compute_network.demo_vpc.name
  ip_address            = google_compute_address.default.self_link
  load_balancing_scheme = ""
  target                = google_sql_database_instance.postgres.psc_service_attachment_link
}

# Create a DNS private zone for PSC connectivity
# This resource only needs to be created once per VPC.
resource "google_dns_managed_zone" "psc_private_zone" {
  project     = var.gcp_project_id
  name        = "${var.region}-sql-goog"
  dns_name    = "${var.region}.sql.goog."
  description = "Private zone for PSC created by Terraform"

  visibility = "private"
  private_visibility_config {
    networks {
      network_url = google_compute_network.demo_vpc.id
    }
  }
}

# Create an 'A' record to map the instance's DNS name to the PSC endpoint IP.
resource "google_dns_record_set" "psc_instance_record" {
  project      = var.gcp_project_id
  type         = "A"
  rrdatas      = [google_compute_address.default.address]
  name         = google_sql_database_instance.postgres.dns_name
  managed_zone = google_dns_managed_zone.psc_private_zone.name
  ttl          = 300
  
}

# Create a Spanner instance
resource "google_spanner_instance" "default" {
  name              = "my-spanner-instance"
  config            = "regional-${var.region}"
  display_name      = "Financial Graph Database"
  processing_units  = 100
  edition           = "ENTERPRISE"
  depends_on = [google_project_service.apis]
}

# Create the Spanner database and schema
resource "google_spanner_database" "database" {
  instance = google_spanner_instance.default.name
  name     = "finance-graph"
  version_retention_period = "3d"
  default_time_zone = "UTC"
  ddl = [<<-EOT

    CREATE TABLE Person (
    id                  INT64 NOT NULL,
    name                STRING(MAX),
    ) PRIMARY KEY (id)

    EOT
    ,
    <<-EOT

    CREATE TABLE Account (
    id                  INT64 NOT NULL,
    create_time         TIMESTAMP,
    is_blocked          BOOL,
    type                STRING(MAX),
    ) PRIMARY KEY (id)

    EOT
    ,

    <<-EOT

    CREATE TABLE Loan (
    id                  INT64 NOT NULL,
    loan_amount         FLOAT64,
    balance             FLOAT64,
    create_time         TIMESTAMP,
    interest_rate       FLOAT64,
    ) PRIMARY KEY (id)

    EOT
    ,

    <<-EOT

    CREATE TABLE AccountTransferAccount (
    id                  INT64 NOT NULL,
    to_id               INT64 NOT NULL,
    amount              FLOAT64,
    create_time         TIMESTAMP NOT NULL,
    ) PRIMARY KEY (id, to_id, create_time),
    INTERLEAVE IN PARENT Account ON DELETE CASCADE

    EOT
    ,

    <<-EOT

    CREATE TABLE AccountRepayLoan (
    id                  INT64 NOT NULL,
    loan_id             INT64 NOT NULL,
    amount              FLOAT64,
    create_time         TIMESTAMP NOT NULL,
    ) PRIMARY KEY (id, loan_id, create_time),
    INTERLEAVE IN PARENT Account ON DELETE CASCADE

    EOT
    ,

    <<-EOT

    CREATE TABLE PersonOwnAccount (
    id                  INT64 NOT NULL,
    account_id          INT64 NOT NULL,
    create_time         TIMESTAMP,
    ) PRIMARY KEY (id, account_id),
    INTERLEAVE IN PARENT Person ON DELETE CASCADE

    EOT
    ,

    <<-EOT

    CREATE TABLE AccountAudits (
    id                  INT64 NOT NULL,
    audit_timestamp     TIMESTAMP,
    audit_details       STRING(MAX),
    ) PRIMARY KEY (id, audit_timestamp),
    INTERLEAVE IN PARENT Account ON DELETE CASCADE

    EOT
    ,

    <<-EOT

    CREATE PROPERTY GRAPH FinGraph
    NODE TABLES (
        Person,
        Account,
        Loan
    )
    EDGE TABLES (
        AccountTransferAccount
        SOURCE KEY (id) REFERENCES Account
        DESTINATION KEY (to_id) REFERENCES Account
        LABEL Transfers,
        AccountRepayLoan
        SOURCE KEY (id) REFERENCES Account
        DESTINATION KEY (loan_id) REFERENCES Loan
        LABEL Repays,
        PersonOwnAccount
        SOURCE KEY (id) REFERENCES Person
        DESTINATION KEY (account_id) REFERENCES Account
        LABEL Owns
    )

    EOT
  ]
  deletion_protection = false
  depends_on = [ 
    google_spanner_instance.default 
  ]
}

# This resource runs the Spanner data import job only once (determined by existence of the local .dataflow_spanner_load_completed file)
resource "null_resource" "trigger_spanner_data_load" {
  depends_on = [
    google_spanner_database.database,
    google_storage_bucket.notebook_bucket,
    google_project_iam_member.project_compute_sa_roles
  ]

  # The triggers block ensures this null_resource runs only when the Spanner
  # database or the input directory changes. In this case, we only want it
  # to run once, so we'll use a local file as a flag.
  triggers = {
    # This trigger relies on the existence of a local file.
    # If the file doesn't exist, the null_resource will run.
    # After it runs and the Dataflow job is initiated, the file is created.
    # Subsequent applies will see the file, and thus not re-run.
    dataflow_job_ran_flag = !fileexists("${path.cwd}/.dataflow_spanner_load_completed") ? "completed" : "pending"
    spanner_instance_id = google_spanner_instance.default.id
    spanner_database_id = google_spanner_database.database.id
  }

  # Use a local-exec provisioner to execute a command on the machine
  # where Terraform is being run.
  provisioner "local-exec" {
    # Check if the flag file exists. If it does, skip the Dataflow job.
    # This ensures that even if a trigger changes (e.g., you update a tag on Spanner),
    # the Dataflow job itself won't re-run if it has already been initiated successfully.
    # The `|| true` is to prevent `terraform apply` from failing if the file exists and `grep` exits with 1.
    when    = create
    command = <<-EOT
      if [ -f "${path.cwd}/.dataflow_spanner_load_completed" ]; then
        echo "Dataflow Spanner data load already initiated. Skipping."
      else
        echo "Initiating Dataflow Spanner data load..."
        gcloud dataflow jobs run import-spanner \
          --gcs-location="gs://dataflow-templates-${var.region}/latest/GCS_Avro_to_Cloud_Spanner" \
          --region="${var.region}" \
          --staging-location="gs://${google_storage_bucket.notebook_bucket.name}/dataflow_temp" \
          --parameters="instanceId=${google_spanner_instance.default.name},databaseId=${google_spanner_database.database.name},inputDir=gs://pr-public-demo-data/adk-toolbox-demo/data/spanner-finance-graph/" \
          --network="${google_compute_network.demo_vpc.name}"

        # Create a flag file to indicate the job has been initiated.
        touch "${path.cwd}/.dataflow_spanner_load_completed"
        echo "Dataflow Spanner data load initiated and flag file created."
      fi
    EOT
  }
}

# --- START: Section for assigning permissions to the default compute service account ---

# Define lists of roles to assign to the default compute service account
locals {
  # Roles to be applied ONLY to the GCS notebook bucket
  compute_sa_bucket_roles = [
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
    # Add any other bucket-specific roles here
  ]

  # Roles to be applied to the ENTIRE GCP project
  compute_sa_project_roles = [
    "roles/dataflow.worker",
    "roles/dataflow.admin",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/logging.logWriter",
    "roles/spanner.viewer",
    "roles/spanner.databaseReader",
    "roles/spanner.databaseAdmin",
    "roles/storage.admin",
    "roles/iam.serviceAccountUser",
    "roles/browser",
    "roles/viewer",
    "roles/iam.serviceAccountTokenCreator",
    "roles/monitoring.metricWriter",
    "roles/artifactregistry.admin",
    "roles/artifactregistry.writer",
    "roles/run.admin",
    "roles/run.invoker",
    "roles/run.builder",
    "roles/run.developer"
    # Add any other project-wide roles here
  ]
}

# Access the project data object
data "google_project" "project" {}

# Define the service account name once to keep the code DRY (Don't Repeat Yourself)
locals {
  compute_service_account_member = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Loop 1: Create multiple IAM role bindings for the GCS BUCKET
resource "google_storage_bucket_iam_member" "gcs_compute_sa_roles" {
  # This for_each creates a resource instance for each role in the list
  for_each = toset(local.compute_sa_bucket_roles)

  bucket = google_storage_bucket.notebook_bucket.name
  role   = each.key # 'each.key' refers to the current role in the loop
  member = local.compute_service_account_member
}

# Loop 2: Create multiple IAM role bindings for the GCP PROJECT
resource "google_project_iam_member" "project_compute_sa_roles" {
  # This for_each creates a resource instance for each role in the list
  for_each = toset(local.compute_sa_project_roles)

  project = data.google_project.project.id
  role    = each.key # 'each.key' refers to the current role in the loop
  member  = local.compute_service_account_member
}

# --- END: Section for assigning permissions to the default compute service account ---

# --- START: Section for assigning permissions to the default AlloyDB service account ---

# Define the service account name once to keep the code DRY (Don't Repeat Yourself)
locals {
  alloydb_service_account_member = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-alloydb.iam.gserviceaccount.com"

  alloydb_sa_bucket_roles = [
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
    # Add any other bucket-specific roles here
  ]

  alloydb_sa_project_roles = [
    "roles/aiplatform.user",
    # Add any other project-specific roles here
  ]
}

# Loop 1: Create multiple IAM role bindings for the GCS BUCKET
resource "google_storage_bucket_iam_member" "alloydb_gcs_sa_roles" {
  # This for_each creates a resource instance for each role in the list
  for_each = toset(local.alloydb_sa_bucket_roles)

  bucket = google_storage_bucket.notebook_bucket.name
  role   = each.key # 'each.key' refers to the current role in the loop
  member = local.alloydb_service_account_member

  depends_on = [ google_alloydb_instance.default ]
}

# Loop 2: Create multiple IAM role bindings for the GCP PROJECT
resource "google_project_iam_member" "project_alloydb_sa_roles" {
  # This for_each creates a resource instance for each role in the list
  for_each = toset(local.alloydb_sa_project_roles)

  project = data.google_project.project.id
  role    = each.key # 'each.key' refers to the current role in the loop
  member  = local.alloydb_service_account_member

  depends_on = [ google_alloydb_instance.default ]
}

# --- END: Section for assigning permissions to the default AlloyDB service account ---

# --- START: Section for creating a Vertex AI Workbench service account and assigning roles ---
# This service account will be creating and testing a large number of services in this
# lab, which is why there are so many roles assigned to it. In the real world, you would
# provision the resources shown in the notebooks with a dedicated platform admin user or
# CI/CD pipeline service account.

# Create service account for Vertex AI Workbench
resource "google_service_account" "notebook_service_account" {
  account_id   = "notebook-service-account" 
  display_name = "Vertex AI Workbench Notebook Service Account" 
  description  = "Service account for Vertex AI Workbench Notebooks."
  project      = var.gcp_project_id
}

# Define lists of roles to assign to the default compute service account
locals {
  # Roles to be applied ONLY to the GCS notebook bucket
  notebook_sa_bucket_roles = [
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
    # Add any other bucket-specific roles here
  ]

  # Roles to be applied at the project level
  notebook_sa_project_roles = [
    "roles/viewer",
    "roles/browser",
    "roles/aiplatform.user",
    "roles/iam.serviceAccountAdmin",
    "roles/iam.securityAdmin",
    "roles/iam.serviceAccountOpenIdTokenCreator",
    "roles/iam.workloadIdentityUser",
    "roles/iam.serviceAccountKeyAdmin",
    "roles/iam.serviceAccountUser",
    "roles/iam.serviceAccountTokenCreator",
    "roles/iam.serviceAccountCreator",
    "roles/iam.roleAdmin",
    "roles/run.invoker",
    "roles/run.admin",
    "roles/run.developer",
    "roles/run.builder",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/serviceusage.serviceUsageViewer",
    "roles/logging.logWriter",
    "roles/alloydb.client",
    "roles/alloydb.admin",
    "roles/cloudsql.client",
    "roles/spanner.viewer",
    "roles/spanner.databaseReader",
    "roles/spanner.databaseAdmin",
    "roles/dataflow.worker",
    "roles/dataflow.admin",
    "roles/storage.admin",
    "roles/secretmanager.admin",
    "roles/artifactregistry.writer",
    "roles/artifactregistry.admin",
    "roles/vpcaccess.admin",
    "roles/compute.networkAdmin",
    "roles/compute.admin",
    "roles/compute.securityAdmin",
    "roles/dns.admin",
    "roles/dns.peer",
    "roles/cloudtrace.admin",
    "roles/cloudtrace.user",
    "roles/monitoring.metricWriter",
    "roles/resourcemanager.projectIamAdmin",
    "roles/iap.admin",
    "roles/iap.settingsAdmin"
    # Add any other project-wide roles here
  ]
}

# Loop 1: Create multiple IAM role bindings for the GCS BUCKET
resource "google_storage_bucket_iam_member" "notebook_sa_roles_gcs" {
  # This for_each creates a resource instance for each role in the list
  for_each = toset(local.notebook_sa_bucket_roles)

  bucket = google_storage_bucket.notebook_bucket.name
  role   = each.key # 'each.key' refers to the current role in the loop
  member = "serviceAccount:${google_service_account.notebook_service_account.email}"

  depends_on = [ google_service_account.notebook_service_account ]
}

# Loop 2: Create multiple IAM role bindings for the GCP PROJECT
resource "google_project_iam_member" "notebook_sa_roles_project" {
  # This for_each creates a resource instance for each role in the list
  for_each = toset(local.notebook_sa_project_roles)

  project = data.google_project.project.id
  role    = each.key # 'each.key' refers to the current role in the loop
  member = "serviceAccount:${google_service_account.notebook_service_account.email}"

  depends_on = [ google_service_account.notebook_service_account ]
}

# --- End: Section for creating a Vertex AI Workbench service account and assigning roles ---

# --- START: Section for creating a Toolbox IAM service account and assigning roles ---

# Create service account for MCP Toolbox
resource "google_service_account" "toolbox_service_account" {
  account_id   = "toolbox-service-account" 
  display_name = "MCP Toolbox Service Account" 
  description  = "Service account for MCP Toolbox."
  project      = var.gcp_project_id
}

locals {

  toolbox_sa_bucket_roles = [
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
    # Add any other bucket-specific roles here
  ]

  toolbox_sa_project_roles = [
    "roles/secretmanager.secretAccessor",
    "roles/alloydb.client",
    "roles/alloydb.databaseUser",
    "roles/spanner.viewer",
    "roles/spanner.databaseUser",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/serviceusage.serviceUsageViewer",
    "roles/storage.objectAdmin",
    "roles/logging.viewer",
    "roles/logging.logWriter",
    "roles/cloudtrace.admin",
    "roles/cloudtrace.user",
    "roles/monitoring.metricWriter"
    # Add any other project-specific roles here
  ]
}

# Loop 1: Create multiple IAM role bindings for the GCS BUCKET
resource "google_storage_bucket_iam_member" "toolbox_sa_gcs_roles" {
  # This for_each creates a resource instance for each role in the list
  for_each = toset(local.toolbox_sa_bucket_roles)

  bucket = google_storage_bucket.notebook_bucket.name
  role   = each.key # 'each.key' refers to the current role in the loop
  member = "serviceAccount:${google_service_account.toolbox_service_account.email}"

  depends_on = [ google_service_account.toolbox_service_account ]
}

# Loop 2: Create multiple IAM role bindings for the GCP PROJECT
resource "google_project_iam_member" "toolbox_sa_project_roles" {
  # This for_each creates a resource instance for each role in the list
  for_each = toset(local.toolbox_sa_project_roles)

  project = data.google_project.project.id
  role    = each.key # 'each.key' refers to the current role in the loop
  member  = "serviceAccount:${google_service_account.toolbox_service_account.email}"

  depends_on = [ google_service_account.toolbox_service_account ]
}

# --- END: Section for creating a Toolbox IAM user and assigning roles ---

# --- START: Section for creating an ADK IAM service account and assigning roles ---

# Create service account for MCP Toolbox
resource "google_service_account" "adk_service_account" {
  account_id   = "adk-service-account" 
  display_name = "ADK Agent Service Account" 
  description  = "Service account for ADK Agent."
  project      = var.gcp_project_id
}

locals {

  adk_sa_bucket_roles = [
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
    # Add any other bucket-specific roles here
  ]

  adk_sa_project_roles = [
    "roles/aiplatform.user",
    "roles/run.viewer",
    "roles/run.invoker",
    "roles/run.serviceAgent",
    "roles/iam.serviceAccountTokenCreator",
    "roles/iam.serviceAccountUser",
    "roles/iam.serviceAccountOpenIdTokenCreator",
    "roles/iam.workloadIdentityUser",
    "roles/serviceusage.serviceUsageConsumer",
    "roles/serviceusage.serviceUsageViewer",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
    "roles/logging.viewer",
    "roles/logging.logWriter",
    "roles/cloudsql.viewer",
    "roles/cloudsql.schemaViewer",
    "roles/cloudsql.client",
    "roles/cloudsql.instanceUser",
    "roles/cloudtrace.user",
    "roles/cloudtrace.agent",
    "roles/monitoring.viewer",
    "roles/monitoring.metricWriter",
    "roles/logging.viewer",
    "roles/logging.viewAccessor",
    "roles/logging.logWriter",
    "roles/logging.serviceAgent",
    "roles/logging.linkViewer",
    "roles/logging.sqlAlertWriter",
    "roles/logging.fieldAccessor",
    "roles/logging.configWriter",
    "roles/logging.bucketWriter",
    # Add any other project-specific roles here
  ]
}

# Loop 1: Create multiple IAM role bindings for the GCS BUCKET
resource "google_storage_bucket_iam_member" "adk_sa_roles_gcs" {
  # This for_each creates a resource instance for each role in the list
  for_each = toset(local.adk_sa_bucket_roles)

  bucket = google_storage_bucket.notebook_bucket.name
  role   = each.key # 'each.key' refers to the current role in the loop
  member = "serviceAccount:${google_service_account.adk_service_account.email}"

  depends_on = [ google_service_account.adk_service_account ]
}

# Loop 2: Create multiple IAM role bindings for the GCP PROJECT
resource "google_project_iam_member" "adk_sa_roles_project" {
  # This for_each creates a resource instance for each role in the list
  for_each = toset(local.adk_sa_project_roles)

  project = data.google_project.project.id
  role    = each.key # 'each.key' refers to the current role in the loop
  member  = "serviceAccount:${google_service_account.adk_service_account.email}"

  depends_on = [ google_service_account.adk_service_account ]
}

# --- END: Section for creating an ADK IAM service account and assigning roles ---

# Create a GCS bucket
resource "google_storage_bucket" "notebook_bucket" {
  name                        = "project-files-${var.gcp_project_id}"
  location                    = "US"
  force_destroy               = true
  uniform_bucket_level_access = true
}

# Get all files ending with .ipynb in the specified directory
locals {
  notebook_files = fileset("${path.module}/../notebooks", "**/*")
}

# Loop through the fileset and create a GCS object for each one
resource "google_storage_bucket_object" "notebooks" {
  for_each = local.notebook_files

  name   = "notebooks/${each.key}" # Creates objects like "notebooks/01-data-exploration.ipynb"
  source = "${path.module}/../notebooks/${each.key}"
  bucket = google_storage_bucket.notebook_bucket.name

}

# Create a Vertex AI Workbench instance in the demo-vpc
resource "google_workbench_instance" "google_workbench" {
  name     = "vertex-ai-workbench"
  location = "${var.region}-a"

  lifecycle {
    replace_triggered_by = [
      google_storage_bucket_object.notebooks
    ]
  }

  gce_setup {
    machine_type = "n1-standard-2"

    # Connect to the demo-vpc
    network_interfaces {
      network    = google_compute_network.demo_vpc.id
      # The subnet will be chosen automatically from the auto-mode VPC.
    }
    
    # Enable public IP address
    disable_public_ip = true

    service_accounts {
      email = google_service_account.notebook_service_account.email
    }

    # Shielded VM Configuration
    shielded_instance_config {
      enable_secure_boot          = true
      enable_vtpm                 = true
      enable_integrity_monitoring = true
    }

    metadata = {
      # This script runs automatically when the instance starts
      "startup-script" = <<-EOF
        #!/bin/bash
        echo "Starting file download"
        
        # Define the target directory for the notebooks
        TARGET_DIR="/home/jupyter/"

        # Create the target directory, -p ensures it doesn't fail if it exists
        mkdir -p $${TARGET_DIR}

        # Recursively copy all notebooks from the GCS bucket to the instance
        # The -n flag prevents overwriting existing files, making the script safer to re-run
        gsutil -m cp -r gs://${google_storage_bucket.notebook_bucket.name}/notebooks/ $${TARGET_DIR}/

        # Change the ownership of all downloaded files and directories to the jupyter user
        # This is CRITICAL for the files to be accessible in the JupyterLab UI
        chown -R jupyter:jupyter /home/jupyter

        # Remove the sample notebook to avoid confusion
        rm -f /home/jupyter/notebook_template.ipynb

      EOF
    }

  }

  depends_on = [
    google_project_service.apis, 
    google_compute_router_nat.nat,
    google_storage_bucket_object.notebooks,
    google_service_account.notebook_service_account
  ]
}


