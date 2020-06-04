# GCP Project ID 
variable "project_id" {
  type = string
  description = "GCP Project ID"
}

# Region to use for Subnet 1
variable "gcp_region_1" {
  type = string
  description = "GCP Region"
}

# Zone used for VMs
variable "gcp_zone_1" {
  type = string
  description = "GCP Zone"
}

# Define subnet for public network
variable "subnet_cidr_public" {
  type = string
  description = "Subnet CIDR for Public Network"
}

# define subnet for private network
variable "subnet_cidr_private" {
  type = string
  description = "Subnet CIDR for Private Network"
}