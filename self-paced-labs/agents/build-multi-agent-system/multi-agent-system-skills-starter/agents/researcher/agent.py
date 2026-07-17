import os
import pathlib
from google.adk.agents import Agent
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset

MODEL = os.environ.get("MODEL", "gemini-3.5-flash")

# Load local skill folder
skill_dir = pathlib.Path(__file__).parent / "skills"
researcher_skill = load_skill_from_dir(skill_dir)

# Wrap the local skill in a SkillToolset
researcher_toolset = SkillToolset(skills=[researcher_skill])

# TODO: Define the researcher agent using the Agent class.
# Pass the researcher_toolset in the tools list and set name to "researcher".
researcher = None

root_agent = researcher
