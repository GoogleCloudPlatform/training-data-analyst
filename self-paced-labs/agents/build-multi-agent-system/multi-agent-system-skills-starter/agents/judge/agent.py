import os
from typing import Literal
from google.adk.agents import Agent
from google.adk.apps.app import App
from pydantic import BaseModel, Field


MODEL = os.environ.get("MODEL", "gemini-3.5-flash")

# TODO 1: Define the JudgeFeedback schema class extending BaseModel
class JudgeFeedback(BaseModel):
    status: Literal["pass", "fail"] = Field(
        description="Whether the research is sufficient ('pass') or needs more work ('fail')."
    )
    feedback: str = Field(
        description="Detailed feedback on what is missing. If 'pass', a brief confirmation."
    )


# TODO 2: Complete the judge Agent definition below
# Set the output_schema and disallow transfer behaviors to prevent the agent from delegation.
judge = Agent(
    name="judge",
    model=MODEL,
    instruction="""
    You are a strict editor.
    Evaluate the 'research_findings' against the user's original request.
    If the findings are missing key info, return status='fail'.
    If they are comprehensive, return status='pass'.
    """,
    output_schema=None,                # TODO: Replace None with the feedback schema class
    disallow_transfer_to_parent=False, # TODO: Set to True to prevent parent delegation
    disallow_transfer_to_peers=False,  # TODO: Set to True to prevent peer delegation
)

root_agent = judge
