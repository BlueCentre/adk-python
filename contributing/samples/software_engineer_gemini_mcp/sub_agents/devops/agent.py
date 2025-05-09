"""DevOps Agent Implementation."""

import logging  # Ensure logging is imported
import os
from dotenv import load_dotenv

from google.adk.agents.llm_agent import Agent, LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import built_in_code_execution
from google.adk.tools.google_search_tool import google_search
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_toolset import StdioServerParameters
from google.genai.types import GenerateContentConfig

# Import codebase search tool from the tools module
from ...tools import codebase_search_tool
from ...tools.filesystem import edit_file_tool, list_dir_tool, read_file_tool
from ...tools.shell_command import (
    check_command_exists_tool,
    execute_vetted_shell_command_tool,
)

# Import from the prompt module in the current directory
from . import prompt

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Load .env file - Added
load_dotenv()

# Get allowed directories from environment variable - Added logic
mcp_allowed_dirs_str = os.getenv("MCP_ALLOWED_DIRECTORIES")
mcp_allowed_dirs = []
if mcp_allowed_dirs_str:
    mcp_allowed_dirs = [d.strip() for d in mcp_allowed_dirs_str.split(",") if d.strip()]
if not mcp_allowed_dirs:  # Fallback if not set or empty after stripping
    mcp_allowed_dirs = [os.path.dirname(os.path.abspath(__file__))]

# Instruction for _search_agent (google_search_grounding):
# The prompt below was revised based on findings in IMPROVEMENTS.md (DevOps Agent - Item 3)
# and subsequent analysis (see TMP.md for discussion).
# The original prompt, while emphasizing brevity, was found to be too restrictive for
# complex research tasks the devops_agent might undertake (e.g., comparing technologies,
# understanding multifaceted concepts).
#
# The revised prompt aims to:
#   - Maintain conciseness for simple, direct queries.
#   - Explicitly request more comprehensive summaries (multiple sentences or bullet points)
#     when the devops_agent's query implies a need for deeper explanation, comparison, or
#     a list of factors.
#   - Guide the _search_agent to avoid superficial answers for complex topics, thereby
#     better equipping the devops_agent.
#
# Future Consideration (More Advanced Control):
# A potential future enhancement could involve the devops_agent explicitly hinting at the
# desired level of detail in its queries to the _search_agent (e.g., requesting
# 'actionable_step' vs. 'detailed_summary'). This would offer more granular control but
# requires investigation into how parameters or contextual hints can be passed effectively
# through the AgentTool mechanism when invoking a sub-agent.
_search_agent = Agent(
    model="gemini-2.0-flash",
    name="google_search_grounding",
    description="An agent providing Google-search grounding capability",
    instruction="""Answer the user's (the devops_agent's) question using the google_search grounding tool.
Be concise, but prioritize completeness when the query suggests a need for detailed explanation, comparison, or a list of factors.

*   For simple, direct questions, a single actionable sentence is ideal.
*   For more complex research questions (e.g., understanding concepts, comparing technologies, identifying best practices), provide a summary of the most important information, even if it requires multiple sentences or bullet points.
*   Your goal is to equip the devops_agent with the necessary information to proceed effectively. Avoid superficial answers for complex topics.
*   Do not ask the devops_agent to look up information independently.
""",
    tools=[google_search],
)

_code_execution_agent = Agent(
    model="gemini-2.5-pro-preview-05-06",
    name="code_execution",
    description="Agent specialized in code execution",
    instruction=prompt.CODE_EXECUTION_AGENT_INSTR,
    tools=[built_in_code_execution],
)


# --- Dynamically build the tools list for devops_agent ---
devops_core_tools = [
    read_file_tool,
    list_dir_tool,
    edit_file_tool,
    codebase_search_tool,
    execute_vetted_shell_command_tool,
    check_command_exists_tool,
    AgentTool(agent=_code_execution_agent),
    AgentTool(agent=_search_agent),
]

try:
    # Attempt to initialize MCPToolset
    mcp_toolset_instance = MCPToolset(
        connection_params=StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "@modelcontextprotocol/server-filesystem",
                *mcp_allowed_dirs,
            ],
        ),
        # Using confirmed MCP tool names for write-like operations
        # tool_predicate=lambda tool, ctx=None: tool.name
        # not in ("write_file", "edit_file", "create_directory", "move_file"),
    )
    devops_core_tools.append(mcp_toolset_instance)
    logger.info("MCPToolset loaded successfully and added to DevOps agent tools.")
except Exception as e:
    logger.warning(
        f"Failed to load MCPToolset: {e}. "
        "DevOps agent will operate without MCP file tools. "
        "Custom file tools remain available."
    )
# --- End of dynamic tool building ---

devops_agent = LlmAgent(
    model="gemini-2.5-pro-preview-05-06",
    name="devops_agent",
    description="Agent specialized in DevOps, CI/CD, deployment, and infrastructure",
    instruction=prompt.DEVOPS_AGENT_INSTR,
    tools=devops_core_tools,  # Use the dynamically constructed list
    output_key="devops",
    generate_content_config=GenerateContentConfig(
        temperature=0.3,
        # top_p=0.95,
        max_output_tokens=8000,
    ),
)
