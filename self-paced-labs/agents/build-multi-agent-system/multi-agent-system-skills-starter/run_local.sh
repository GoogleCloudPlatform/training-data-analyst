#!/bin/bash

# Create clean directories for local agent runtime configuration
# This prevents the local agent loader from scanning sibling folders as agents
mkdir -p local_run/researcher local_run/judge local_run/content_builder local_run/orchestrator

# Safe cleanup of ports 8080, 8001-8004
echo "Stopping any existing processes on ports 8080, 8001-8004..."
for port in 8080 8001 8002 8003 8004; do
  pid=$(lsof -t -i:$port 2>/dev/null)
  if [ ! -z "$pid" ]; then
    kill -9 $pid 2>/dev/null
  fi
done

# TODO 1: Set the GOOGLE_CLOUD_PROJECT environment variable using a gcloud command
# Tip: Use $(gcloud config get-value project) to retrieve your active Qwiklabs project
export GOOGLE_CLOUD_PROJECT="FILL_ME_IN"

# TODO 2: Set the GOOGLE_CLOUD_LOCATION environment variable to your assigned regional boundary variable
export GOOGLE_CLOUD_LOCATION="FILL_ME_IN"

export GOOGLE_GENAI_USE_VERTEXAI="True" 

echo "Starting Researcher Agent on port 8001..."
pushd agents/researcher
uv run adk_app.py --host 0.0.0.0 --port 8001 --a2a ../../local_run/researcher &
RESEARCHER_PID=$!
popd

echo "Starting Judge Agent on port 8002..."
pushd agents/judge
uv run adk_app.py --host 0.0.0.0 --port 8002 --a2a ../../local_run/judge &
JUDGE_PID=$!
popd

echo "Starting Content Builder Agent on port 8003..."
pushd agents/content_builder
uv run adk_app.py --host 0.0.0.0 --port 8003 --a2a ../../local_run/content_builder &
CONTENT_BUILDER_PID=$!
popd

# TODO 3: Configure remote connection URLs for the local agents
# These variables match the environment variables expected by the orchestrator agent.
# Specify the correct localhost endpoints pointing to the ports defined above.
export RESEARCHER_AGENT_CARD_URL=http://localhost:8001/a2a/agent/.well-known/agent-card.json
export JUDGE_AGENT_CARD_URL="FILL_ME_IN"
export CONTENT_BUILDER_AGENT_CARD_URL="FILL_ME_IN"

echo "Starting Orchestrator Agent on port 8004..."
pushd agents/orchestrator
uv run adk_app.py --host 0.0.0.0 --port 8004 ../../local_run/orchestrator &
ORCHESTRATOR_PID=$!
popd

# Wait a bit for them to start up and perform their startup cleanup
sleep 3
# Re-create the empty agent folders to satisfy the ADK AgentLoader check during requests
mkdir -p local_run/researcher/agent local_run/judge/agent local_run/content_builder/agent local_run/orchestrator/agent
sleep 2

echo "Starting Frontend App on port 8080..."
pushd app
export AGENT_SERVER_URL=http://localhost:8004

uv run uvicorn main:app --host 0.0.0.0 --port 8080 &
BACKEND_PID=$!
popd

echo "All agents started!"
echo "Researcher: http://localhost:8001"
echo "Judge: http://localhost:8002"
echo "Content Builder: http://localhost:8003"
echo "Orchestrator: http://localhost:8004"
echo "App Server (Frontend): http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop all agents."

# Wait for all processes
trap "kill $RESEARCHER_PID $JUDGE_PID $CONTENT_BUILDER_PID $ORCHESTRATOR_PID $BACKEND_PID 2>/dev/null; rm -rf local_run; exit" INT
wait
