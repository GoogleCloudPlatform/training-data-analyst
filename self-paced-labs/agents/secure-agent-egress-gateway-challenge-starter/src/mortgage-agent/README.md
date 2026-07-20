# Mortgage Assistant Agent

ADK mortgage assistant agent deployed to Agent Runtime. Connects to
legacy DMS, income verification, and corporate email MCP servers running in GKE
via PSC Interface.

## Prerequisites

- Terraform infrastructure deployed (VPC, GKE, PSC Interface, DNS zones)
- MCP servers deployed to GKE and reachable via the internal gateway
- `uv` installed for Python dependency management

## Deploy

### Get values from Terraform

From the `terraform/` directory, retrieve the required outputs:

```bash
cd ../../terraform

export PROJECT_ID=$(terraform output -raw foundation_project_id)
export VPC_NAME=$(terraform output -raw vpc_name)
export PSC_ATTACHMENT=$(terraform output -raw psc_interface_network_attachment_id)
export DNS_PEERING_DOMAIN=$(terraform output -raw psc_interface_dns_peering_domain)
```

### Create a new agent

```bash
cd ../src/mortgage-agent

uv run python deploy_agent.py \
  --project=$PROJECT_ID \
  --dms-mcp-url=https://dms.${DNS_PEERING_DOMAIN%%.}/mcp \
  --income-verification-url=https://income-verification.${DNS_PEERING_DOMAIN%%.} \
  --email-mcp-url=https://email.${DNS_PEERING_DOMAIN%%.}/mcp \
  --network-attachment=$PSC_ATTACHMENT \
  --dns-peering-domain=$DNS_PEERING_DOMAIN \
  --dns-peering-target-project=$PROJECT_ID \
  --dns-peering-target-network=$VPC_NAME \
  --enable-agent-identity
```

### Update an existing agent

```bash
uv run python deploy_agent.py \
  --project=$PROJECT_ID \
  --dms-mcp-url=https://dms.${DNS_PEERING_DOMAIN%%.}/mcp \
  --income-verification-url=https://income-verification.${DNS_PEERING_DOMAIN%%.} \
  --email-mcp-url=https://email.${DNS_PEERING_DOMAIN%%.}/mcp \
  --network-attachment=$PSC_ATTACHMENT \
  --dns-peering-domain=$DNS_PEERING_DOMAIN \
  --dns-peering-target-project=$PROJECT_ID \
  --dns-peering-target-network=$VPC_NAME \
  --enable-agent-identity \
  --update=projects/PROJECT_NUMBER/locations/us-central1/reasoningEngines/ENGINE_ID
```

### Register in Gemini Enterprise

Add `--ge-deploy` with the required OAuth and Gemini Enterprise flags:

```bash
export OAUTH_CLIENT_SECRET=<your-oauth-client-secret>

uv run python deploy_agent.py \
  --project=$PROJECT_ID \
  --dms-mcp-url=https://dms.${DNS_PEERING_DOMAIN%%.}/mcp \
  --income-verification-url=https://income-verification.${DNS_PEERING_DOMAIN%%.} \
  --email-mcp-url=https://email.${DNS_PEERING_DOMAIN%%.}/mcp \
  --network-attachment=$PSC_ATTACHMENT \
  --dns-peering-domain=$DNS_PEERING_DOMAIN \
  --dns-peering-target-project=$PROJECT_ID \
  --dns-peering-target-network=$VPC_NAME \
  --enable-agent-identity \
  --ge-deploy \
  --app-id=<gemini-enterprise-engine-id> \
  --oauth-client-id=<oauth-client-id>
```

## Architecture

```
Agent Runtime (Reasoning Engine)
  |
  |-- PSC Interface NIC (10.11.0.0/28 subnet)
  |     |
  |     |-- DNS Peering → inference-vpc → internal DNS zone
  |     |
  |     └── TCP/443 → Internal Gateway (10.0.0.2)
  |                       |
  |                       ├── dms.internal.demo.sc-ccn.xyz
  |                       ├── income-verification.internal.demo.sc-ccn.xyz
  |                       └── corporate-email.internal.demo.sc-ccn.xyz
  |
  └── Agent Platform APIs (Gemini models, session management)
```

## Terraform Outputs Reference

| Output | Description | deploy_agent.py flag |
|--------|-------------|---------------------|
| `foundation_project_id` | GCP project ID | `--project` |
| `vpc_name` | VPC network name | `--dns-peering-target-network` |
| `psc_interface_network_attachment_id` | PSC Interface network attachment | `--network-attachment` |
| `psc_interface_dns_peering_domain` | DNS domain for peering | `--dns-peering-domain` |

## Local Testing

```bash
uv sync
adk web
```
