"""Documentation Agent Implementation."""

from google.adk.agents import LlmAgent

# Import tools from the parent 'tools' module
from ...tools import codebase_search_tool
from ...tools.filesystem import edit_file_tool, list_dir_tool, read_file_tool
from ...tools.search import google_search_grounding
from ...tools.shell_command import ( # Modified block
    check_command_exists_tool,
    check_shell_command_safety_tool,
    configure_shell_approval_tool, # Added for completeness
    configure_shell_whitelist_tool, # Added for completeness
    execute_vetted_shell_command_tool,
)
from . import prompt

documentation_agent = LlmAgent(
    model="gemini-2.5-pro-preview-05-06",
    name="documentation_agent",
    description="Agent specialized in writing and updating documentation",
    instruction=prompt.DOCUMENTATION_AGENT_INSTR,
    tools=[
        read_file_tool,
        list_dir_tool,
        edit_file_tool,
        codebase_search_tool,
        google_search_grounding,
        # Shell tools
        check_command_exists_tool,  # Added
        check_shell_command_safety_tool,  # Added
        configure_shell_approval_tool, # Added
        configure_shell_whitelist_tool, # Added
        execute_vetted_shell_command_tool,
    ],
    output_key="documentation",
)

# Placeholder for actual tool implementation
