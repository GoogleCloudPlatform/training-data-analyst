
locals {
  name_prefix = "aws-cluster"
}

module "kms" {
  source        = "./modules/kms"
  anthos_prefix = local.name_prefix
}

module "iam" {
  source             = "./modules/iam"
  gcp_project_number = module.gcp_data.project_number
  anthos_prefix      = local.name_prefix
  db_kms_arn         = module.kms.database_encryption_kms_key_arn
}

module "vpc" {
  source                        = "./modules/vpc"
  aws_region                    = var.aws_region
  vpc_cidr_block                = var.vpc_cidr_block
  anthos_prefix                 = local.name_prefix
  subnet_availability_zones     = var.subnet_availability_zones
  public_subnet_cidr_block      = var.public_subnet_cidr_block
  cp_private_subnet_cidr_blocks = var.cp_private_subnet_cidr_blocks
  np_private_subnet_cidr_blocks = var.np_private_subnet_cidr_blocks
}

module "gcp_data" {
  source       = "./modules/gcp_data"
  gcp_location = var.gcp_location
  gcp_project  = var.gcp_project_id
}

module "create_vars" {
  source                = "terraform-google-modules/gcloud/google"
  platform              = "linux"
  create_cmd_entrypoint = "./modules/scripts/create_vars.sh"
  create_cmd_body       = "\"${local.name_prefix}\" \"${var.gcp_location}\" \"${var.aws_region}\" \"${var.cluster_version}\" \"${module.kms.database_encryption_kms_key_arn}\" \"${module.iam.cp_instance_profile_id}\" \"${module.iam.api_role_arn}\" \"${module.vpc.aws_cp_subnet_id_1},${module.vpc.aws_cp_subnet_id_2},${module.vpc.aws_cp_subnet_id_3}\" \"${module.vpc.aws_vpc_id}\" \"${var.gcp_project_id}\" \"${var.pod_address_cidr_blocks}\" \"${var.service_address_cidr_blocks}\" \"${module.iam.np_instance_profile_id}\" \"${var.node_pool_instance_type}\""
  module_depends_on     = [module.kms, module.iam, module.vpc]
}


