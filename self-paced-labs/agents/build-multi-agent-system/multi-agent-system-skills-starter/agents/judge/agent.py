from typing import Literal
from google.adk.agents import Agent
from google.adk.apps.app import App
from pydantic import BaseModel, Field


MODEL = "gemini-3.5-flash"

# TODO 1: Define the JudgeFeedback schema class extending BaseModel
# Ensure it defines status (Literal["pass", "fail"]) and feedback (str) fields.


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
    # Add output_schema and disallow transfer properties here
)

root_agent = judge
