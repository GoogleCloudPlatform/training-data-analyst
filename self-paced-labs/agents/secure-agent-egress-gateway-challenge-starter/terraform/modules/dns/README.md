# DNS Module

This module manages Cloud DNS zones and records for both public and internal endpoints, including validation records for SSL certificates.

## Features

- **Public DNS Management:** Create A records for your public gateways using an existing DNS zone.
- **Certificate Validation:** Automatically generate DNS records for SSL certificate validation (ACME challenges).
- **Internal DNS Zone:** Deploy a private DNS zone for VPC-internal endpoints (regional scope only).
- **Customizable TTLs:** Independently configure Time-to-Live (TTL) settings for different record types.

---

## Architecture

### Public DNS
- **A Records:** Maps `gateway` subdomain to its IP address.
- **Validation Records:** CNAME records used by Certificate Manager to verify domain ownership.

### Private DNS
- **Internal Zone:** Provides resolution for `internal.example.com` within your VPC.
- **Internal Records:** Maps internal gateway endpoints to private IPs.

---

## Usage Guide

### Regional Configuration

```hcl
module "dns" {
  source = "./modules/dns"

  project_id      = "YOUR_PROJECT_ID"
  dns_zone_domain = "example.com."
  gateway_scope   = "regional"

  # Gateway IPs from networking module
  gateway_ip = module.networking.gateway_regional_ip

  # Internal IPs for private DNS
  internal_gateway_ip = module.networking.internal_gateway_ip

  # VPC attachment for private zone
  vpc_self_links = [module.networking.network_self_link]

  # Certificate validation
  enable_certificate_manager              = true
  certificate_dns_authorizations_regional = module.certificates.regional_dns_authorizations
}
```

---

## Zone Creation vs Zone Reference

This module uses an **existing public DNS managed zone** for public records. It derives the zone name from the `dns_zone_domain` variable (e.g., `gateway.example.com.` becomes `gateway-example-com`), or you can override this with the `dns_zone_name` variable.

For **internal (private) DNS**, the module **creates** a new private DNS zone (named via `internal_dns_zone_name`) and attaches it to the VPCs specified in `vpc_self_links`.

## Variables

### Core
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `project_id` | The Google Cloud project ID. | `string` | - | Yes |
| `dns_zone_domain` | The DNS zone domain name (must end with a dot). | `string` | `null` | No |
| `dns_zone_name` | The name of the existing Cloud DNS managed zone. If null, derived from `dns_zone_domain`. | `string` | `null` | No |
| `gateway_scope` | The gateway scope: `"regional"`, `"global"`, or `null`. | `string` | `null` | No |
| `enable_certificate_manager` | Set to `true` to enable certificate validation records. | `bool` | `false` | No |

### Public Gateway IPs
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `gateway_ip` | IP address for the main gateway. | `string` | `null` | No |

### Internal Gateway IPs
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `internal_gateway_ip` | Internal IP address for the main gateway. | `string` | `null` | No |

### Private DNS and VPC
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `vpc_self_links` | A list of VPC self-links for private DNS zone visibility. | `list(string)` | `[]` | No |
| `internal_dns_zone_name` | Name of the internal DNS zone. | `string` | `"internal-zone"` | No |
| `internal_dns_domain` | Domain for internal DNS zone (must end with dot). Derived from `dns_zone_domain` if null. | `string` | `null` | No |

### Self Managed and GKE Gateway DNS
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `enable_self_managed_gateway_dns` | Enable DNS record for Self Managed Gateway. | `bool` | `false` | No |
| `self_managed_gateway_ip` | IP address for the Self Managed Gateway. | `string` | `null` | No |
| `self_managed_gateway_subdomain` | Subdomain for the Self Managed Gateway (e.g., `smg`). | `string` | `"smg"` | No |
| `enable_gke_gateway_dns` | Enable DNS record for GKE Gateway. | `bool` | `false` | No |
| `gke_gateway_ip` | IP address for the GKE Gateway. | `string` | `null` | No |
| `gke_gateway_subdomain` | Subdomain for the GKE Gateway (e.g., `inference`). | `string` | `"inference"` | No |

### TTL Configuration
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `gateway_dns_ttl` | TTL for public gateway A records (in seconds). | `number` | `300` | No |
| `internal_dns_ttl` | TTL for internal DNS A records (in seconds). | `number` | `300` | No |
| `certificate_validation_ttl` | TTL for certificate validation DNS records (in seconds). | `number` | `300` | No |

---

## Outputs

| Name | Description |
|------|-------------|
| `dns_zone_name` | The name of the public DNS zone. |
| `gateway_fqdn` | The fully qualified domain name of the main gateway. |
| `internal_gateway_fqdn` | The internal FQDN for the gateway (VPC-only). |
| `dns_zone_name_servers` | The name servers for the public DNS zone. |

---

## Prerequisites

1.  **Existing Public Zone:** You must have an existing public DNS managed zone in your project.
2.  **VPC Network:** A VPC network is required if you are creating a private DNS zone.
3.  **IP Addresses:** You must provision static IP addresses (e.g., via the networking module) before configuring DNS records.

---

## Troubleshooting

### DNS Name Not Found
Ensure your managed zone name matches your domain name (e.g., `example.com` domain often uses `example-com` as the zone name). Verify the zone exists using `gcloud dns managed-zones list`.

### Internal Resolution Failing
- Confirm the VPC is correctly attached to the private DNS zone.
- Verify that your resources (e.g., GKE nodes or Cloud Run services) are in the attached VPC.
- Test resolution from within a pod using `nslookup YOUR_INTERNAL_FQDN`.

---

## License
Copyright 2026 Google LLC. Licensed under the Apache License, Version 2.0.
