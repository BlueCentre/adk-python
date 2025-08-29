"""Testing Agent Implementation."""

from google.adk.agents import LlmAgent

# Import tools from the parent 'tools' module
from ...tools import codebase_search_tool
from ...tools.filesystem import edit_file_tool, list_dir_tool, read_file_tool
from ...tools.search import google_search_grounding
from ...tools.shell_command import ( # Modified block
    check_command_exists_tool,
    check_shell_command_safety_tool,
    configure_shell_approval_tool,
    configure_shell_whitelist_tool,
    execute_vetted_shell_command_tool,
)
from . import prompt

testing_agent = LlmAgent(
    model="gemini-1.5-pro-001",
    name="testing_agent",
    description="Agent specialized in writing and running tests",
    instruction=prompt.TESTING_AGENT_INSTR,
    tools=[
        read_file_tool,
        list_dir_tool,
        edit_file_tool,
        codebase_search_tool,
        google_search_grounding,
        # Shell tools
        check_command_exists_tool,  # Added
        check_shell_command_safety_tool,  # Added
        configure_shell_approval_tool,  # Added
        configure_shell_whitelist_tool,  # Added
        execute_vetted_shell_command_tool,
    ],
    output_key="testing",
)

# Placeholder for actual tool implementation
