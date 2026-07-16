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

# --- Remote Agents ---

# TODO: Define connections to remote agents
# Connect to Researcher, Judge, and Content Builder using RemoteA2aAgent.
# Remember to use the environment variables for URLs (or localhost defaults).

# --- Escalation Checker ---

# TODO: Define EscalationChecker
# This agent should check the status of the judge's feedback.
# If status is "pass", it should escalate (break the loop).

# --- Orchestration ---

# TODO: Define the Research Loop
# Use LoopAgent to cycle through Researcher -> Judge -> EscalationChecker.

# TODO: Define the Root Agent (Pipeline)
# Use SequentialAgent to run the Research Loop followed by the Content Builder.

