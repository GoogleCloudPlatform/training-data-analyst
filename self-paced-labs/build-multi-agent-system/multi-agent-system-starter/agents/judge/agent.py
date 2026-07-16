from typing import Literal
from google.adk.agents import Agent
from google.adk.apps.app import App
from pydantic import BaseModel, Field


MODEL = "gemini-3-flash-preview"

# TODO: Define the JudgeFeedback schema
# It should extend BaseModel and define 'status' ("pass" or "fail") and 'feedback'.

# TODO: Define the Judge Agent
# The judge should accept research findings, evaluate them, and output the JudgeFeedback schema.
