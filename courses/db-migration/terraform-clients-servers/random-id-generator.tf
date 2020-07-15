# Terraform plugin for creating random ids
resource "random_id" "instance_id" {
 byte_length = 4
}