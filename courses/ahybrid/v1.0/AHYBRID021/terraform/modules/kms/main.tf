terraform {
  required_version = ">= 0.12.23"
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

data "aws_caller_identity" "current" {}
#Create KMS
# https://cloud.google.com/anthos/clusters/docs/multi-cloud/aws/how-to/create-aws-kms-key

resource "aws_kms_key" "database_encryption_kms_key" {
  description = "${var.anthos_prefix} AWS Database Encryption KMS Key"

}

resource "aws_kms_alias" "database_encryption_kms_key_alias" {
  target_key_id = aws_kms_key.database_encryption_kms_key.arn
  name          = "alias/${var.anthos_prefix}-database-encryption-key"
}
