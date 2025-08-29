"""Implementation of the Code Developer Agent."""
import logging
import os
from dotenv import load_dotenv

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_toolset import StdioServerParameters
from google.genai.types import GenerateContentConfig

from ...tools.filesystem import read_file_tool, list_dir_tool, edit_file_tool
from ...tools.code_search import codebase_search_tool
from ...tools.project_context import load_project_context

from .prompt import CODE_DEVELOPER_AGENT_INSTR

logger = logging.getLogger(__name__)
load_dotenv() # Load .env file for potential MCP configurations

# MCP Configuration for Filesystem (similar to devops_agent)
mcp_allowed_dirs_str = os.getenv("MCP_ALLOWED_DIRECTORIES")
mcp_allowed_dirs = []
if mcp_allowed_dirs_str:
    mcp_allowed_dirs = [d.strip() for d in mcp_allowed_dirs_str.split(",") if d.strip()]
if not mcp_allowed_dirs:  # Fallback if not set or empty
    # Defaulting to a safer, more generic fallback if needed, or consider erroring
    # For now, let's use a placeholder. This should be configured appropriately for security.
    logger.warning("MCP_ALLOWED_DIRECTORIES not set; MCP filesystem tool might have restricted access or fail.")
    # mcp_allowed_dirs = [os.path.dirname(os.path.abspath(__file__))] # Example, might not be ideal

# --- Dynamically build the tools list for code_developer_agent ---
code_developer_core_tools = [
    read_file_tool,
    list_dir_tool,
    edit_file_tool,
    codebase_search_tool, # Added as per prompt indication of its utility
]

# Attempt to initialize MCP Filesystem Toolset
if mcp_allowed_dirs: # Only attempt if allowed directories are configured
    try:
        mcp_filesystem_toolset = MCPToolset(
            connection_params=StdioServerParameters(
                command="npx", # Assuming same command as devops_agent for filesystem MCP server
                args=[
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    *mcp_allowed_dirs,
                ],
            ),
        )
        code_developer_core_tools.append(mcp_filesystem_toolset)
        logger.info("MCP Filesystem Toolset loaded successfully for Code Developer agent.")
    except Exception as e:
        logger.warning(
            f"Failed to load MCP Filesystem Toolset for Code Developer agent: {e}. "
            "Agent will use standard filesystem tools."
        )
else:
    logger.info("MCP_ALLOWED_DIRECTORIES not configured. Code Developer agent will use standard filesystem tools.")

code_developer_agent = LlmAgent(
    model="gemini-2.5-pro-preview-05-06",
    name="code_developer_agent",
    description=(
        "Writes and modifies code based on specifications using available filesystem tools (preferring MCP tools if available)."
    ),
    instruction=CODE_DEVELOPER_AGENT_INSTR,
    tools=code_developer_core_tools,
    output_key="code_developer",
    generate_content_config=GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=8000,
    ),
)
