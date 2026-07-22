import os
import pathlib
from google.adk.agents import Agent
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

# Load local skill folder
skill_dir = pathlib.Path(__file__).parent / "skills"
content_builder_skill = load_skill_from_dir(skill_dir)

# Wrap the local skill in a SkillToolset
content_builder_toolset = SkillToolset(skills=[content_builder_skill])

# TODO: Complete the content_builder agent definition below by passing the loaded skill toolset
content_builder = Agent(
    name="content_builder",
    model=MODEL,
    tools=[None], # TODO: Replace None with content_builder_toolset
)

root_agent = content_builder
