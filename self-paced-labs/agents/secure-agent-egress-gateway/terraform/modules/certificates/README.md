# Certificates Module

This module manages SSL/TLS certificates using Google Cloud Certificate Manager for both global and regional load balancers.

## Features

- **Global Certificates:** Use Certificate Manager with certificate maps for your global load balancers.
- **Regional Certificates:** Deploy regional managed certificates for your regional load balancers.
- **DNS Authorizations:** Automatically handle DNS challenge authorizations using the PER_PROJECT_RECORD type.
- **Wildcard Support:** Provide coverage for both base domains and wildcard subdomains.
- **Internal Certificates:** Manage separate wildcard certificates for your internal VPC endpoints.

---

## Architecture

### Global Scope
- **Certificate Map:** Creates a map with a PRIMARY matcher.
- **Managed Certificate:** Covers your domain and its wildcard.
- **DNS Authorization:** Provides validation for the certificate.

### Regional Scope
- **Public Certificate:** Covers your public base domain and wildcard.
- **Internal Certificate:** Covers your internal domain (e.g., `*.internal.example.com`).
- **DNS Authorizations:** Handles validation for both public and internal domains.

---

## Usage Guide

### Basic Regional Configuration

```hcl
module "certificates" {
  source = "./modules/certificates"

  project_id                 = "YOUR_PROJECT_ID"
  region                     = "YOUR_REGION"
  dns_zone_domain            = "example.com."
  enable_certificate_manager = true
  gateway_scope              = "regional"
}
```

### Global Configuration

```hcl
module "certificates" {
  source = "./modules/certificates"

  project_id                 = "YOUR_PROJECT_ID"
  region                     = "YOUR_REGION"
  dns_zone_domain            = "example.com."
  enable_certificate_manager = true
  gateway_scope              = "global"
}
```

---

## Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `project_id` | The Google Cloud project ID. | `string` | - | Yes |
| `region` | The region for regional certificates. | `string` | - | Yes |
| `dns_zone_domain` | DNS zone domain (must end with a dot). | `string` | `null` | No |
| `enable_certificate_manager` | Set to `true` to enable Certificate Manager. | `bool` | `false` | No |
| `gateway_scope` | The scope of the gateway: `"regional"`, `"global"`, or `null`. | `string` | `null` | No |
| `labels` | Labels to apply to certificate resources. | `map(string)` | `{}` | No |
| `global_certificate_map_name` | Name for the global certificate map. | `string` | `"main-certificate-map-global"` | No |
| `global_certificate_name` | Name for the global certificate. | `string` | `"main-certificate-global"` | No |
| `regional_certificate_name` | Name for the regional certificate (public domain). | `string` | `"main-certificate-regional"` | No |
| `internal_certificate_name` | Name for the internal certificate (private endpoints). | `string` | `"internal-certificate-regional"` | No |

---

## Outputs

| Name | Description |
|------|-------------|
| `global_certificate_map_id` | The ID of the global certificate map. |
| `regional_certificate_id` | The ID of the regional certificate. |
| `internal_certificate_id` | The ID of the internal certificate. |
| `dns_authorizations` | A list of all created DNS authorizations. |

---

## Certificate Lifecycle

1.  **DNS Authorizations:** The module creates authorizations containing CNAME records for ACME challenges.
2.  **Record Creation:** Your DNS module uses this data to create the necessary records.
3.  **Validation:** Certificate Manager checks for the DNS records, which typically takes 10 to 30 minutes.
4.  **Activation:** The certificate becomes ACTIVE and ready for use by your load balancers.
5.  **Auto-renewal:** Certificate Manager automatically handles renewals before expiration.

---

## Troubleshooting

### Certificate stuck in PROVISIONING state
Check that your DNS records are correctly created:
```bash
# Verify the CNAME record
dig _acme-challenge.example.com CNAME
```

### Internal certificate not validating
Ensure that your private DNS zone exists, the VPC is attached to it, and the DNS record is correctly created within that zone.

---

## License
Copyright 2026 Google LLC. Licensed under the Apache License, Version 2.0.
