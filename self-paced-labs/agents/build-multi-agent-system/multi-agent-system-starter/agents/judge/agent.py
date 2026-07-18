import os
from typing import Literal
from pydantic import BaseModel, Field
from google.adk.agents import Agent

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

# TODO 1: Define the JudgeFeedback schema extending BaseModel.
# It should contain two required fields: status (Literal["pass", "fail"]) and feedback (str).


# TODO 2: Define the judge agent using the Agent class (replacing the placeholder below).
# Attach the output_schema and set disallow_transfer_to_parent and disallow_transfer_to_peers to True.
# Make sure to set name="judge".
# judge = None

root_agent = judge
