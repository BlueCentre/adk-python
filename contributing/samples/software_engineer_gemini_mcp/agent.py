"""
Implementation of the Software Engineer Agent with knowledge and experience of sub-agents.

This is the main entry point for the software engineer agent.

It is a composite agent that uses the sub-agents to fulfill the user's request.
"""
import logging

from google.adk.agents import Agent
from google.adk.tools import load_memory
from google.genai.types import GenerateContentConfig

from . import prompt

# Use relative imports from the 'software_engineer' sibling directory
from .sub_agents.code_quality.agent import code_quality_agent
from .sub_agents.code_review.agent import code_review_agent
from .sub_agents.debugging.agent import debugging_agent
from .sub_agents.design_pattern.agent import design_pattern_agent
from .sub_agents.devops.agent import devops_agent
from .sub_agents.documentation.agent import documentation_agent
from .sub_agents.testing.agent import testing_agent
from .sub_agents.task_management.agent import task_management_agent
from .sub_agents.code_developer.agent import code_developer_agent
from .tools import (
    google_search_grounding,
    list_dir_tool,
    read_file_tool,
)

from .tools.memory_tools import add_memory_fact, search_memory_facts
from .tools.project_context import load_project_context

logger = logging.getLogger(__name__)


# --- Memory Initialization ---
def initialize_session_memory(tool_context):
    """Initializes the session memory in tool_context if it doesn't exist."""
    if not hasattr(tool_context, "session_state"):
        logger.warning("Tool context does not have session_state. Cannot initialize memory.")
        # In a real scenario, might need to initialize session_state itself
        # For now, we assume session_state exists but memory might not.
        return

    if "memory" not in tool_context.session_state:
        logger.info("Initializing agent session memory.")
        tool_context.session_state["memory"] = {
            "context": {
                "project_path": None,  # Will be populated by load_project_context
                "current_file": None,
            },
            "tasks": {
                "active_task": None,
                "completed_tasks": [],
            },
            "history": {
                "last_read_file": None,
                "last_search_query": None,
                "last_error": None,
            },
            "user_preferences": {},
            # Add other relevant fields as needed based on agent interactions
        }
    # else: memory already exists, do nothing


# --- Agent Definition ---

# Note: Using custom ripgrep-based codebase search in tools/code_search.py

# REF: https://ai.google.dev/gemini-api/docs/rate-limits
root_agent = Agent(
    model="gemini-2.5-flash-preview-04-17",
    name="root_agent",
    description="An AI software engineer assistant that helps with various software development tasks",
    instruction=prompt.ROOT_AGENT_INSTR,
    sub_agents=[
        design_pattern_agent,
        documentation_agent,
        code_review_agent,
        code_quality_agent,
        testing_agent,
        debugging_agent,
        devops_agent, # devops_agent now handles all shell command execution
        task_management_agent, # Agent for managing tasks
        code_developer_agent,
    ],
    tools=[
        read_file_tool,
        list_dir_tool,
        # edit_file_tool, # Removed - delegate to sub-agents
        # configure_edit_approval_tool, # Removed - delegate to sub-agents
        google_search_grounding,
        # codebase_search_tool, # Removed - delegate to sub-agents
        # get_os_info_tool, # Removed - delegate to sub-agents
        # Memory Tools:
        load_memory,  # Keep for transcript search
        add_memory_fact,  # Use wrapped tool variable name
        search_memory_facts,  # Use wrapped tool variable name
    ],
    # Pass the function directly, not as a list
    before_agent_callback=load_project_context,
    output_key="software_engineer",
    generate_content_config=GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=4096,
    ),
)
