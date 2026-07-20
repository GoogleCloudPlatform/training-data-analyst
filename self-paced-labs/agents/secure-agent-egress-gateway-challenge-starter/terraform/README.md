# Terraform Infrastructure

This directory contains the Terraform configuration for the MCP Gateway demo infrastructure on GCP.

## Architecture

The three MCP services (`legacy-dms`, `corporate-email`, `income-verification`) are deployed as **Cloud Run v2** services with `ingress = INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` — they cannot be reached from the public internet.

A regional **Internal Application Load Balancer** with a single **Serverless NEG using a URL mask** (`<service>.<mcp_internal_dns_zone.domain>`) fronts all three services. The LB extracts the `<service>` token from the request `Host` header and routes to the Cloud Run service of the same name; adding a new MCP service later is one Cloud Run deploy + one DNS A record, with no LB changes.

A Cloud DNS **private zone** (configured via `var.mcp_internal_dns_zone`, typically `mcp.<dns_zone_domain>.`) is attached to the VPC and holds one A record per service pointing at the LB VIP. This eliminates any external DNS dependency for service-to-service traffic and provides a clean target for **Agent Runtime DNS peering** through the existing PSC Interface (`enable_psc_interface = true`). When `enable_agent_gateway = true`, the domain MUST be a real subdomain of `dns_zone_domain` so Certificate Manager can issue a Google-managed cert — Agent Gateway does not currently validate the self-signed cert that the LB falls back to for unrouteable suffixes like the legacy `mcp-server.internal.`.

## Prerequisites

- Terraform >= 1.12.2
- Google Cloud SDK (`gcloud`) authenticated with appropriate permissions
- A GCP project with billing enabled
- Container images for the three MCP services pushed to the project's Artifact Registry (`<region>-docker.pkg.dev/<project>/<name_prefix>-docker/<service>:<tag>`)

## Quick Start

```bash
# Copy example configuration
cp example.tfvars terraform.tfvars
# Edit terraform.tfvars with your project details and image URIs

# Copy example backend configuration
cp example.backend.conf backend.conf
# Edit backend.conf with your GCS bucket details

# Initialize Terraform
terraform init -backend-config=backend.conf

# Preview changes
terraform plan -var-file=terraform.tfvars

# Apply
terraform apply -var-file=terraform.tfvars
```

## Verifying internal routing

After `terraform apply`, from a VM in the VPC:

```bash
# DNS resolves to the internal LB VIP
dig +short legacy-dms.mcp.demo.example.com

# LB routes by Host header to the matching Cloud Run service
curl https://legacy-dms.mcp.demo.example.com/mcp
curl https://corporate-email.mcp.demo.example.com/mcp
curl https://income-verification.mcp.demo.example.com/mcp

# *.run.app URLs are blocked from the public internet
curl https://<service>-<hash>-uc.a.run.app/mcp   # 403 from outside the VPC
```

The default LB front-end is HTTPS. When `enable_certificate_manager = true` and `gateway_scope = "regional"` (the demo's defaults), the LB serves a Google-managed regional cert covering `*.mcp.<dns_zone_domain>`. Otherwise the LB falls back to an auto-generated self-signed cert for `*.<mcp_internal_dns_zone.domain>` (use `curl -k` and note that Agent Gateway can't validate this today). Set `mcp_lb_protocol = "HTTP"` for an even simpler demo path.

## Known `gcloud` Exceptions

The project convention is to manage all infrastructure via Terraform. The following exceptions use `gcloud` via `null_resource` local-exec because no native Terraform resource exists:

- **Model Armor MCP Content Security** (`modules/model-armor/main.tf`): Uses `gcloud beta services mcp content-security add` to configure MCP floor settings. There is no Terraform resource for this API as of the current provider version.
