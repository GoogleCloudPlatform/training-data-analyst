# course-creation-agent (Distributed)

A multi-agent system built with Google's Agent Development Kit (ADK) and Agent-to-Agent (A2A) protocol. It features a team of microservice agents that research, judge, and build content, orchestrated to deliver high-quality results.

## Architecture

This project uses a distributed microservices architecture where each agent runs in its own container and communicates via A2A:

*   **Orchestrator Service (`orchestrator`):** The main entry point. It manages the workflow using `LoopAgent` and `SequentialAgent`, and connects to other agents using `RemoteA2aAgent`.
*   **Researcher Service (`researcher`):** A standalone agent that gathers information using Google Search.
*   **Judge Service (`judge`):** A standalone agent that evaluates research quality.
*   **Content Builder Service (`content_builder`):** A standalone agent that compiles the final course.
*   **Agent App (`app`):** A web application that queries the Orchestrator agent, displays progress and results.

## Project Structure

```
course-creation-agent/
├── agents/
    ├── orchestrator/        # Main Orchestrator agent, ADK API Service
    ├── researcher/          # Researcher agent, A2A microservice
    ├── judge/               # Judge agent, A2A microservice
    └── content_builder/     # Content Builder agent, A2A microservice
├── app/                     # Web App service application
    └── frontend/            # Frontend application
├── shared/                  # Files used by all agents
└── ...
```

### Shared files

There are some files in `shared` directory that are shared across all agents and the web app.
To avoid duplication, these files are linked into respective subdirectories as [**symlinks**](https://en.wikipedia.org/wiki/Symbolic_link).

* `a2a_utils.py` - contains code for rewriting agent URLs in A2A AgentCard when deployed in Cloud Run.
* `adk_app.py` - ADK API Service implementation with additional A2A functionality.
* `authenticated_httpx.py` - [httpx](https://www.python-httpx.org/) client extension for [service-to-service requests](https://docs.cloud.google.com/run/docs/authenticating/service-to-service).

## Requirements

*   **uv**: Python package manager (required for local development).
*   **Google Cloud SDK**: For GCP services and authentication.

## Quick Start

1.  **Install Dependencies:**
    ```bash
    uv sync
    ```

2.  **Set up credentials:**
    Ensure you have Google Cloud credentials available. You might need to run:
    ```bash
    gcloud auth application-default login
    ```
    And ensure your `GOOGLE_CLOUD_PROJECT` environment variable is set.

3.  **Run Locally:**
    ```bash
    ./run_local.sh
    ```
    This will start all 4 agents and the web app in background processes

4.  **Access the App:**
    Open **http://localhost:8000** in your browser.

## Deployment

To deploy to Google Cloud Run, you need to deploy each service individually and then configure the Orchestrator with the URLs of the other services.

1.  **Deploy Researcher, Judge, Content Builder, and Orchestrator:**
    Deploy each of these folders as a separate Cloud Run service. Note down their URLs (e.g., `https://researcher-xyz.a.run.app`).

2.  **Deploy Agent App:**
    Deploy the `app/` folder to Cloud Run.
    Set the following environment variables on the Agent App service:
    *   `RESEARCHER_AGENT_CARD_URL`: `https://<researcher-url>/a2a/agent/.well-known/agent.json`
    *   `JUDGE_AGENT_CARD_URL`: `https://<judge-url>/a2a/agent/.well-known/agent.json`
    *   `CONTENT_BUILDER_AGENT_CARD_URL`: `https://<content-builder-url>/a2a/agent/.well-known/agent.json`
    *   `AGENT_URL`: `https://<orchestrator-url>`

3.  **Access:**
    Open the App's URL in your browser.
