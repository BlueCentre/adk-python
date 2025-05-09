"""Code review agent implementation."""

from google.adk.agents import Agent
from google.genai.types import GenerateContentConfig

# Import tools from the parent 'tools' module
from ...tools import codebase_search_tool # Added
from ...tools.code_analysis import analyze_code_tool
from ...tools.filesystem import list_dir_tool, read_file_tool
from ...tools.shell_command import ( # Added block
    check_command_exists_tool,
    check_shell_command_safety_tool,
    configure_shell_approval_tool,
    configure_shell_whitelist_tool,
    execute_vetted_shell_command_tool,
)
from . import prompt

# from software_engineer.sub_agents.code_review.shared_libraries.types import CodeReviewResponse


code_review_agent = Agent(
    model="gemini-2.5-flash-preview-04-17",
    name="code_review_agent",
    description="Analyzes code for issues and suggests improvements",
    instruction=prompt.CODE_REVIEW_AGENT_INSTR,
    tools=[
        analyze_code_tool,
        read_file_tool,
        list_dir_tool,
        codebase_search_tool,  # Added
        check_command_exists_tool,  # Added
        check_shell_command_safety_tool,  # Added
        configure_shell_approval_tool, # Added
        configure_shell_whitelist_tool, # Added
        execute_vetted_shell_command_tool,  # Added
    ],
    generate_content_config=GenerateContentConfig(
        temperature=0.1,
        top_p=0.95,
        max_output_tokens=1000, # Consider increasing this later as noted in IMPROVEMENTS.md
    ),
)
