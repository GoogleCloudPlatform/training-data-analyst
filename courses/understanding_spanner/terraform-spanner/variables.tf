variable "deletion_protection" {
  description = "If set to true, you cannot run terraform destroy if there are databases created."
  type        = bool
  default     = false
}

variable "force_destroy" {
    description = "If set to true, running terraform destroy will delete all backups."
  type    = bool
  default = true
}

variable "processing_units" {
  type    = number
  default = 100
}

variable "project_id" {
  description = "The GCP Project ID."
  type        = string
}

variable "region" {
  type = string
}
