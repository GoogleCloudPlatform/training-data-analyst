terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.5.0"
    }
  }
}

provider "aws" {
  profile = "default"
  region  = "us-east-1"
}
provider "google" {
  project = var.gcp_project_id
}
