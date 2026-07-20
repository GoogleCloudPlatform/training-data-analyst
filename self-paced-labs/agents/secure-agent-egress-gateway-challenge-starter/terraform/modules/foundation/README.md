# Foundation Module

This module enables required Google Cloud APIs and configures GPU quota preferences. You should apply this module before any other infrastructure components.

## Overview

The Foundation module manages the following core setup tasks:

- **API Enablement:** Enables all necessary Google Cloud APIs for the gateway infrastructure.
- **GPU Quotas:** Configures quota preferences for high-performance GPUs, including H100 and A100 models.
- **CPU Quotas:** Sets regional CPU quota preferences required to support GPU-equipped instances.

---

## Usage Guide

### Basic Configuration

```hcl
module "foundation" {
  source = "./modules/foundation"

  project_id          = "YOUR_PROJECT_ID"
  region              = "YOUR_REGION"
  quota_contact_email = "admin@example.com"

  # Optional: GPU quota configuration
  enable_gpu_quotas = true
  h100_quota        = 8
  a100_quota        = 8
  cpu_quota         = 3000
}
```

---

## Variables

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| `project_id` | The Google Cloud project ID. | `string` | - | Yes |
| `region` | The region for regional quota preferences. | `string` | - | Yes |
| `quota_contact_email` | Contact email for quota increase notifications and requests. | `string` | - | Yes |
| `enabled_services` | List of Google Cloud APIs to enable. | `list(string)` | See default list | No |
| `enable_gpu_quotas` | Set to `true` to request GPU and regional CPU quota increases. | `bool` | `true` | No |
| `h100_quota` | The preferred number of H100 GPUs for the region. | `number` | `8` | No |
| `a100_quota` | The preferred number of A100 GPUs for the region. | `number` | `8` | No |
| `cpu_quota` | The preferred number of regional CPUs. | `number` | `3000` | No |

---

## Default Enabled Services

The module enables the following critical APIs by default:

- **Core Infrastructure:** `compute.googleapis.com`, `storage.googleapis.com`, `dns.googleapis.com`.
- **Containers:** `container.googleapis.com`, `artifactregistry.googleapis.com`.
- **AI and ML:** `aiplatform.googleapis.com`, `apigee.googleapis.com`, `modelarmor.googleapis.com`.
- **Serverless and Security:** `run.googleapis.com`, `secretmanager.googleapis.com`, `iap.googleapis.com`.
- **Management:** `certificatemanager.googleapis.com`, `cloudquotas.googleapis.com`.

---

## Outputs

| Name | Description |
|------|-------------|
| `project_id` | The Google Cloud project ID. |
| `project_number` | The unique project number. |
| `enabled_services` | A list of all enabled Google Cloud APIs. |

---

## Important Considerations

- **Manual Approval:** Quota requests are preferences. Google Cloud may require manual review and approval, which can take 24 to 48 hours.
- **Propagation Delay:** API enablement can take several minutes to propagate across Google's infrastructure. Ensure APIs are fully active before deploying dependent resources.

---

## License
Copyright 2026 Google LLC. Licensed under the Apache License, Version 2.0.
