"""Code quality agent implementation."""

import logging
import os
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.genai.types import GenerateContentConfig
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

from ...tools.code_analysis import (
    analyze_code_tool,
    get_analysis_issues_by_severity_tool,
    suggest_code_fixes_tool,
)
from ...tools.filesystem import list_dir_tool, read_file_tool, edit_file_tool, configure_approval_tool # Added edit_file_tool, configure_approval_tool
from . import prompt

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()

# Get allowed directories from environment variable
mcp_allowed_dirs_str = os.getenv("MCP_ALLOWED_DIRECTORIES")
mcp_allowed_dirs = []
if mcp_allowed_dirs_str:
    mcp_allowed_dirs = [d.strip() for d in mcp_allowed_dirs_str.split(",") if d.strip()]
if not mcp_allowed_dirs:  # Fallback if not set or empty after stripping
    # Fallback to a sensible default, e.g., the parent directory of the agent's location or project root
    # For this example, let's assume the project root is two levels up from this agent's directory.
    # Adjust this path as necessary for your project structure.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    mcp_allowed_dirs = [project_root]
    logger.info(f"MCP_ALLOWED_DIRECTORIES not set or empty, falling back to: {project_root}")


# --- Dynamically build the tools list for code_quality_agent ---
core_tools = [
    analyze_code_tool,
    get_analysis_issues_by_severity_tool,
    suggest_code_fixes_tool,
    read_file_tool,
    list_dir_tool,
    edit_file_tool,
    configure_approval_tool,
]

try:
    # Attempt to initialize MCPToolset
    mcp_toolset_instance = MCPToolset(
        connection_params=StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "@modelcontextprotocol/server-filesystem",
                *mcp_allowed_dirs, # Pass the determined allowed directories
            ],
        ),
        # Example: tool_predicate=lambda tool, ctx=None: tool.name not in ("write_file"), # If you want to restrict some MCP tools
    )
    core_tools.append(mcp_toolset_instance)
    logger.info("MCPToolset loaded successfully and added to code_quality_agent tools.")
except Exception as e:
    logger.warning(
        f"Failed to load MCPToolset: {e}. "
        "Code Quality agent will operate without MCP file tools. "
        "Standard ADK file tools remain available."
    )
# --- End of dynamic tool building ---

code_quality_agent = Agent(
    model="gemini-2.5-flash-preview-04-17", # Consider updating model if Pro is better for this
    name="code_quality_agent",
    description="Analyzes code for quality issues, suggests improvements, and can optionally apply safe fixes with approval.",
    instruction=prompt.CODE_QUALITY_AGENT_INSTR,
    tools=core_tools, # Use the dynamically constructed list
    generate_content_config=GenerateContentConfig(
        temperature=0.1, # Keep low for factual analysis and precise code edits
        top_p=0.95,
        max_output_tokens=4096, # Ensure sufficient for detailed explanations and proposed code
    ),
)
