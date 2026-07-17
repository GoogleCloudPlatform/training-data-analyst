import os
import pathlib
from google.adk.agents import Agent
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset

MODEL = os.environ.get("MODEL", "gemini-3.5-flash")

# Load local skill folder
skill_dir = pathlib.Path(__file__).parent / "skills"
content_builder_skill = load_skill_from_dir(skill_dir)

# TODO: Wrap the skill in a SkillToolset
# content_builder_toolset = ...

# TODO: Define the content_builder agent using the Agent class.
# Pass the content_builder_toolset into the tools list and set name="content_builder".
content_builder = None

root_agent = content_builder
