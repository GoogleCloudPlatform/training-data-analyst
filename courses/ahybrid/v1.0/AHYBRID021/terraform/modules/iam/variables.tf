variable "gcp_project_number" {
  description = "GCP project Number of project to host cluster"
  type        = string
}

variable "anthos_prefix" {
  description = "Prefix to apply to Anthos AWS Policy & Network names"
  type        = string
}

variable "db_kms_arn" {
  description = "DB KMS ARN"
  type        = string
}