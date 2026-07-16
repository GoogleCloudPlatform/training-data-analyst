# Model Armor Module

This module creates a Google Cloud Model Armor template to provide multi-layer content filtering and security for LLMs. It also configures the necessary IAM permissions for the Model Armor service account.

## Features

- **Responsible AI (RAI) Filters:** Filter content for hate speech, harassment, sexually explicit material, and dangerous content.
- **PII Detection:** Use Sensitive Data Protection (SDP) to detect and block personally identifiable information.
- **Jailbreak Protection:** Detect and block malicious prompts that attempt to bypass safety controls.
- **URI Filtering:** Block requests that contain malicious URIs.
- **Custom Error Handling:** Configure user-friendly error codes and messages for blocked requests.
- **Automated IAM:** Manage role bindings for the Model Armor service account automatically.

---

## Architecture

1.  **Request Filtering:** Model Armor evaluates incoming prompts for harmful content or security threats before they reach the LLM.
2.  **LLM Processing:** If the prompt is safe, it is forwarded to the backend.
3.  **Response Filtering:** Model Armor inspects the LLM's response to ensure it complies with your safety standards before returning it to the user.

---

## Usage Guide

### Basic Usage

```hcl
module "model_armor" {
  source = "./modules/model-armor"

  project_id = "YOUR_PROJECT_ID"
  region     = "YOUR_REGION"
}
```

This creates a request-side template (`agw-request-template`) and a response-side template (`agw-response-template`). With the default `sdp_enforcement = "ENABLED"`, it also creates DLP inspect/de-identify templates and wires them into the response template's `sdp_settings.advanced_config`.

### Production Configuration

```hcl
module "model_armor" {
  source = "./modules/model-armor"

  project_id = "YOUR_PROJECT_ID"
  region     = "YOUR_REGION"

  request_template_id    = "prod-request-template"
  response_template_id   = "prod-response-template"
  inspect_template_id    = "prod-ssn-inspect-template"
  deidentify_template_id = "prod-ssn-redaction-template"

  # RAI Filters - Block harmful content
  rai_filters = [
    {
      filter_type      = "HATE_SPEECH"
      confidence_level = "MEDIUM_AND_ABOVE"
    },
    {
      filter_type      = "DANGEROUS"
      confidence_level = "LOW_AND_ABOVE"
    }
  ]

  # PII info types fed into the DLP inspect template
  pii_types = [
    "US_SOCIAL_SECURITY_NUMBER",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER"
  ]

  # Custom Error Messages
  prompt_error_message = "Your request was blocked by our content filter. Please rephrase and try again."
}
```

---

## Variables

### Core
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `project_id` | The Google Cloud project ID. | `string` | - | Yes |
| `region` | The region for resource deployment. | `string` | - | Yes |
| `enable_model_armor` | Set to `true` to enable Model Armor template creation. | `bool` | `true` | No |
| `enable_iam_bindings` | Enable IAM role bindings for Model Armor service account. | `bool` | `true` | No |
| `enable_mcp_floor_setting` | Enable Model Armor floor setting for MCP server protection. | `bool` | `true` | No |
| `request_template_id` | ID for the request-side Model Armor template. | `string` | `"agw-request-template"` | No |
| `response_template_id` | ID for the response-side Model Armor template. | `string` | `"agw-response-template"` | No |
| `inspect_template_id` | ID for the DLP inspect template wired into the response template's `sdp_settings.advanced_config` (only created when `sdp_enforcement = ENABLED`). | `string` | `"agw-ssn-inspect-template"` | No |
| `deidentify_template_id` | ID for the DLP de-identify template wired into the response template's `sdp_settings.advanced_config` (only created when `sdp_enforcement = ENABLED`). | `string` | `"agw-ssn-redaction-template"` | No |

### RAI Filters
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `rai_filters` | A list of RAI filter configurations. | `list(object)` | See below | No |

Each RAI filter object has:
- `filter_type`: One of `SEXUALLY_EXPLICIT`, `HATE_SPEECH`, `HARASSMENT`, `DANGEROUS`
- `confidence_level`: One of `LOW_AND_ABOVE`, `MEDIUM_AND_ABOVE`, `HIGH`

Default RAI filters: `HATE_SPEECH` (MEDIUM_AND_ABOVE), `HARASSMENT` (MEDIUM_AND_ABOVE), `SEXUALLY_EXPLICIT` (MEDIUM_AND_ABOVE).

### Sensitive Data Protection (SDP)
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `sdp_enforcement` | When `ENABLED`, the module provisions DLP inspect/de-identify templates and layers them into the response template's `sdp_settings.advanced_config`. When `DISABLED`, no DLP/SDP resources are created. | `string` | `"ENABLED"` | No |
| `pii_types` | PII info types fed into the DLP inspect template's `info_types` (only consulted when `sdp_enforcement = ENABLED`). | `list(string)` | See below | No |

Default PII types: `US_SOCIAL_SECURITY_NUMBER`, `CREDIT_CARD_NUMBER`, `PHONE_NUMBER`, `EMAIL_ADDRESS`, `PASSPORT`, `DATE_OF_BIRTH`, `MEDICAL_RECORD_NUMBER`.

Additional supported PII types include: `IP_ADDRESS`, `STREET_ADDRESS`, `PERSON_NAME`.

### Security Filters
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `pi_jailbreak_enforcement` | Prompt injection and jailbreak filter enforcement (`ENABLED` or `DISABLED`). | `string` | `"ENABLED"` | No |
| `pi_jailbreak_confidence_level` | Jailbreak filter confidence level (`LOW_AND_ABOVE`, `MEDIUM_AND_ABOVE`, `HIGH`). | `string` | `"LOW_AND_ABOVE"` | No |
| `malicious_uri_enforcement` | Malicious URI filter enforcement (`ENABLED` or `DISABLED`). | `string` | `"ENABLED"` | No |

### Custom Error Messages
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `llm_response_error_code` | Custom error code for LLM response safety evaluation failures. | `number` | `798` | No |
| `llm_response_error_message` | Custom error message for LLM response failures. | `string` | `"LLM response blocked by content filter"` | No |
| `prompt_error_code` | Custom error code for prompt safety evaluation failures. | `number` | `799` | No |
| `prompt_error_message` | Custom error message for prompt failures. | `string` | `"Your request was blocked..."` | No |

### Logging
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `ignore_partial_failures` | Whether to ignore partial invocation failures. | `bool` | `true` | No |
| `log_template_operations` | Whether to log template CRUD operations. | `bool` | `true` | No |
| `log_sanitize_operations` | Whether to log sanitize operations. | `bool` | `true` | No |

---

## Outputs

| Name | Description |
|------|-------------|
| `request_template_id` | ID of the request-side Model Armor template. |
| `request_template_name` | Full resource name of the request-side Model Armor template. |
| `response_template_id` | ID of the response-side Model Armor template. |
| `response_template_name` | Full resource name of the response-side Model Armor template. |
| `template_location` | Location of the Model Armor templates. |
| `inspect_template_id` | ID of the DLP inspect template (null when `sdp_enforcement = DISABLED`). |
| `deidentify_template_id` | ID of the DLP de-identify template (null when `sdp_enforcement = DISABLED`). |
| `model_armor_service_agent_email` | Email of the Model Armor service agent (`gcp-sa-modelarmor`) granted DLP read access (null when advanced SDP is `DISABLED`). |
| `service_account_email` | Email of the Service Extensions service account (`gcp-sa-dep`) used for Model Armor. |

---

## Integration with GKE

Model Armor requires specific IAM permissions to access GKE clusters, which this module handles automatically. To use the template in your Kubernetes deployment, reference its ID in your HTTPRoute annotations:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: llm-gateway
  annotations:
    modelarmor.google.com/template: "projects/YOUR_PROJECT_ID/locations/YOUR_REGION/modelArmorTemplates/YOUR_TEMPLATE_ID"
```

---

## Troubleshooting

- **Template Not Found:** Verify that the template ID and region match your deployment.
- **Permission Errors:** Ensure the Model Armor service account (`service-YOUR_PROJECT_NUMBER@gcp-sa-dep.iam.gserviceaccount.com`) has the required IAM roles.
- **Incorrect Blocking:** Review your logs to identify which filter triggered the block and adjust the confidence levels if they are too strict.

---

## License
Copyright 2026 Google LLC. Licensed under the Apache License, Version 2.0.
