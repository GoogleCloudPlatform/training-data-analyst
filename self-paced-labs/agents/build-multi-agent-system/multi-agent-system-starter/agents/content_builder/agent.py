import os
from google.adk.agents import Agent

MODEL = os.environ.get("MODEL", "gemini-1.5-flash")

# TODO: Define the content_builder agent using the Agent class (replacing the placeholder below).
# Make sure to set name="content_builder" and add appropriate instructions for module structuring.
# content_builder = None

root_agent = content_builder
