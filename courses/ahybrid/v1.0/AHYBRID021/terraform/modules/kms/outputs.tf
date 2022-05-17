output "database_encryption_kms_key_arn" {
  description = "ARN of the actuated KMS key resource for cluster secret encryption"
  value       = aws_kms_key.database_encryption_kms_key.arn
}