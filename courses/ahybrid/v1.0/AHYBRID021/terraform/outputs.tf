output "cluster_name" {
  description = "The automatically generated name of your aws GKE cluster"
  value       = local.name_prefix
}
output "message" {
  description = "Connect Instructions"
  value       = "To connect to your cluster issue the command: gcloud container hub memberships get-credentials ${local.name_prefix}"

}