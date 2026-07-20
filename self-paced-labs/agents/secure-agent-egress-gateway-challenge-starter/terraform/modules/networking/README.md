# Networking Module

This module creates the VPC network infrastructure including subnets, Cloud NAT, and static IP addresses for gateway load balancers.

## Overview

The Networking module provisions:

- A VPC network with primary and secondary subnets for GKE.
- A proxy-only subnet for internal application load balancers.
- A Cloud Router and Cloud NAT for outbound internet access.
- Static IP addresses for external and internal gateways.
- Support for both regional and global gateway configurations.

---

## Architecture

1.  **VPC Network:** The core network hosting your infrastructure.
2.  **Primary Subnet:** Hosts your node IPs and contains secondary ranges for Pods and Services.
3.  **Proxy-Only Subnet:** Reserved for Google Cloud Envoy-based load balancers.
4.  **Cloud NAT:** Provides your private instances with outbound internet access.
5.  **Static IPs:** Reserved addresses for your gateway and model endpoints.

---

## Usage Guide

### Basic Configuration

```hcl
module "networking" {
  source = "./modules/networking"

  project_id  = "YOUR_PROJECT_ID"
  region      = "YOUR_REGION"
  name_prefix = "ai-gateway"
  vpc_name    = "ai-gateway-vpc"
  subnet_name = "ai-gateway-subnet"

  # Optional: Custom CIDR ranges
  primary_subnet_cidr = "10.0.0.0/20"
  pods_cidr           = "10.4.0.0/14"
  services_cidr       = "10.8.0.0/20"
  proxy_subnet_cidr   = "10.9.0.0/24"

  # Gateway scope: "regional", "global", or null
  gateway_scope = "regional"
}
```

---

## Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `project_id` | The Google Cloud project ID. | `string` | - | Yes |
| `region` | The region for resource deployment. | `string` | - | Yes |
| `vpc_name` | The name of the VPC network. | `string` | - | Yes |
| `subnet_name` | The name of the primary subnet. | `string` | - | Yes |
| `name_prefix` | Prefix to use for naming resources. | `string` | - | Yes |
| `gateway_scope` | The scope of the gateway: `"regional"`, `"global"`, or `null`. | `string` | `"regional"` | No |

---

## Outputs

| Name | Description |
|------|-------------|
| `network_id` | The ID of the VPC network. |
| `network_self_link` | The self-link of the VPC network. |
| `subnet_id` | The ID of the primary subnet. |
| `subnet_self_link` | The self-link of the primary subnet. |
| `nat_router_name` | The name of the Cloud Router. |
| `available_zones` | A list of available zones in the specified region. |

### Regional Gateway IP Outputs
| Name | Description |
|------|-------------|
| `gateway_ip_regional_address` | Regional static IP address for the gateway. |
| `internal_gateway_ip` | Internal static IP address for the gateway. |

---

## Gateway Scope Options

| Scope | Description | Static IPs Created |
|-------|-------------|-------------------|
| `"regional"` | Regional load balancer with standard tier networking. | Regional external IPs and internal IPs. |
| `"global"` | Global load balancer with premium tier networking. | Global external IPs only (no internal IPs). |
| `null` | Disables gateway IP provisioning entirely. | None. |

**Key differences:**
- **Regional IPs** are created with `google_compute_address` and are tied to a specific region. They support both `EXTERNAL` and `INTERNAL` address types, making them suitable for internal load balancers with body-based routing.
- **Global IPs** are created with `google_compute_global_address` and use Premium Tier networking. They only support `EXTERNAL` address type and cannot be used for internal load balancers. Internal IPs are not provisioned in global scope.

---

## CIDR Range Planning

By default, the module allocates the following ranges:

| Range | CIDR | Purpose |
|-------|------|---------|
| Primary Subnet | 10.0.0.0/20 | Node IPs. |
| Pods | 10.4.0.0/14 | Kubernetes Pod IPs. |
| Services | 10.8.0.0/20 | Kubernetes Service IPs. |
| Proxy-Only | 10.9.0.0/24 | Envoy proxy instances. |

Ensure these CIDR ranges do not overlap with other networks if you plan to use VPC peering.

---

## License
Copyright 2026 Google LLC. Licensed under the Apache License, Version 2.0.
