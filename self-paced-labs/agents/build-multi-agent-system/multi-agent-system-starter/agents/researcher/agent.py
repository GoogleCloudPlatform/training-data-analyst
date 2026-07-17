import os
from google.adk.agents import Agent
from google.adk.tools.google_search_tool import google_search

MODEL = os.environ.get("MODEL", "gemini-3.5-flash")

# TODO: Define the researcher agent using the Agent class (replacing the placeholder below).
# Make sure to set name="researcher", pass google_search in the tools list, and write appropriate instructions.
# researcher = None

root_agent = researcher
