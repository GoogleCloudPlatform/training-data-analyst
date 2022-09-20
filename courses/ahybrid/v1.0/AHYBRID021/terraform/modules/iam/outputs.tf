output "api_role_arn" {
  description = "ARN of the actuated IAM role resource"
  value       = aws_iam_role.api_role.arn
}

output "cp_instance_profile_id" {
  description = "IAM instance profile of controlplane"
  value       = aws_iam_instance_profile.cp_instance_profile.id
}

output "np_instance_profile_id" {
  description = "IAM instance profile of nodepool"
  value       = aws_iam_instance_profile.np_instance_profile.id
}