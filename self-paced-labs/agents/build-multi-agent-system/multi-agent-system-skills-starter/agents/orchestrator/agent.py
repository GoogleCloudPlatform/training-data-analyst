import os
import json
from typing import AsyncGenerator
from google.adk.agents import BaseAgent, LoopAgent, SequentialAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.events import Event, EventActions
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext

from authenticated_httpx import create_authenticated_client

# --- Callbacks ---
def create_save_output_callback(key: str):
    """Creates a callback to save the agent's final response to session state."""
    def callback(callback_context: CallbackContext, **kwargs) -> None:
        ctx = callback_context
        # Find the last event from this agent that has content
        for event in reversed(ctx.session.events):
            if event.author == ctx.agent_name and event.content and event.content.parts:
                text = event.content.parts[0].text
                if text:
                    # Try to parse as JSON if it looks like it, for judge_feedback
                    if key == "judge_feedback" and text.strip().startswith("{"):
                        try:
                            ctx.state[key] = json.loads(text)
                        except json.JSONDecodeError:
                            ctx.state[key] = text
                    else:
                        ctx.state[key] = text
                    print(f"[{ctx.agent_name}] Saved output to state['{key}']")
                    return
    return callback

# Remote Agent Addresses
RESEARCHER_URL = os.environ.get(
    "RESEARCHER_AGENT_CARD_URL", "http://localhost:8001/a2a/agent/.well-known/agent-card.json"
)
JUDGE_URL = os.environ.get(
    "JUDGE_AGENT_CARD_URL", "http://localhost:8002/a2a/agent/.well-known/agent-card.json"
)
CONTENT_BUILDER_URL = os.environ.get(
    "CONTENT_BUILDER_AGENT_CARD_URL", "http://localhost:8003/a2a/agent/.well-known/agent-card.json"
)

# Connect to Researcher (Port 8001)
researcher = RemoteA2aAgent(
    agent_card=RESEARCHER_URL,
    httpx_client=create_authenticated_client(RESEARCHER_URL),
    after_agent_callback=create_save_output_callback("research_findings"),
)

# TODO 1: Define remote connection to the Judge Agent (Port 8002)
# Attach create_save_output_callback("judge_feedback") and create_authenticated_client(JUDGE_URL).
judge = None

# Connect to Content Builder (Port 8003)
content_builder = RemoteA2aAgent(
    agent_card=CONTENT_BUILDER_URL,
    httpx_client=create_authenticated_client(CONTENT_BUILDER_URL),
)

# --- Escalation Checker ---

class EscalationChecker(BaseAgent):
    name = "escalation_checker"
    description = "Escalates workflow when judge passes findings."

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        feedback = ctx.session.state.get("judge_feedback")
        print(f"[EscalationChecker] Feedback: {feedback}")

        is_pass = False
        if isinstance(feedback, dict) and feedback.get("status") == "pass":
            is_pass = True
        elif isinstance(feedback, str) and '"status": "pass"' in feedback:
            is_pass = True

        # TODO 2: Complete the escalation logic below.
        # If is_pass is True, yield an Event with EventActions(escalate=True) to break the loop.
        # Otherwise, yield a default empty Event.
        pass

escalation_checker = EscalationChecker()

# --- Orchestration ---

# TODO 3: Construct the orchestration loop and sequential pipeline agents.
# 1. Define 'research_loop' as a LoopAgent cycling: researcher -> judge -> escalation_checker. Set max_iterations to 3.
# 2. Define 'root_agent' as a SequentialAgent running 'research_loop' followed by 'content_builder'.
research_loop = None
root_agent = None

