"""
Implementation of the Task Management Agent.

This agent is responsible for:
- Managing a list of tasks (TODO, IN_PROGRESS, DONE, etc.).
- Prioritizing tasks.
- Delegating tasks to appropriate sub-agents.
- Tracking task progress and receiving updates.
"""
import logging
import os
from dotenv import load_dotenv
from typing import Any, Dict, Optional

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_toolset import StdioServerParameters
from google.genai.types import GenerateContentConfig

# Import task types from shared_libraries
# Assuming 'types.py' is in '.../shared_libraries/' relative to this agent's location
# Adjust path if necessary based on actual project structure when ADK resolves it
# from ...shared_libraries.types import (
#     Task,
#     TaskListResponse,
#     TaskPriority,
#     TaskStatus,
#     TaskUpdateRequest,
# )

from . import prompt

# Load .env file
load_dotenv()

# Placeholder for memory tools - to be refined
# from ....tools.memory_tools import add_memory_fact, search_memory_facts, update_memory_fact

logger = logging.getLogger(__name__)

# Default tasks file if none is specified by the user/LLM
DEFAULT_TASKS_MARKDOWN_FILE = "TASKS.md"

MAX_CONSECUTIVE_PARSING_ERRORS = 5

class TaskManagementTools(BaseTool):
    """Tools for the Task Management Agent that operate on raw markdown task files,
    allowing specification of the target file."""

    def __init__(self):
        super().__init__(
            name="TaskManagementTools",
            description="Tools for reading and writing the entire content of a user-specified or default markdown task file."
        )

    def _resolve_file_path(self, tasks_file_path: Optional[str] = None) -> str:
        """Resolves the file path to be used, defaulting if None is provided."""
        path_to_use = tasks_file_path if tasks_file_path else DEFAULT_TASKS_MARKDOWN_FILE
        logger.debug(f"Resolved task file path to: {path_to_use}")
        return path_to_use

    def _read_tasks_markdown_file(self, tool_context: ToolContext, file_path: str) -> str:
        """Reads the entire content of the specified markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Successfully read {len(content)} characters from '{file_path}'.")
            return content
        except FileNotFoundError:
            logger.info(f"Tasks file '{file_path}' not found. Returning empty string.")
            return ""
        except IOError as e:
            logger.error(f"IOError reading tasks file '{file_path}': {e}. Returning empty string.")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error reading tasks file '{file_path}': {e}. Returning empty string.")
            return ""

    def _save_tasks_markdown_file(self, tool_context: ToolContext, file_path: str, markdown_content: str) -> bool:
        """Saves the provided markdown content to the specified file, overwriting it.
        Returns True on success, False on failure.
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            logger.info(f"Successfully wrote {len(markdown_content)} characters to '{file_path}'.")
            return True
        except IOError as e:
            logger.critical(f"CRITICAL: IOError writing tasks file '{file_path}': {e}. Content NOT saved.")
            return False
        except Exception as e:
            logger.error(f"Unexpected error writing tasks file '{file_path}': {e}. Content NOT saved.")
            return False

    def list_all_tasks_markdown(self, tool_context: ToolContext, tasks_file_path: Optional[str] = None) -> str:
        """Reads and returns the entire markdown content from a specified task file (default TASKS.md). Use `tasks_file_path` to specify a file."""
        file_to_read = self._resolve_file_path(tasks_file_path)
        logger.info(f"Executing list_all_tasks_markdown tool for file: {file_to_read}.")
        return self._read_tasks_markdown_file(tool_context, file_to_read)

    def get_specific_task_markdown(self, tool_context: ToolContext, task_identifier: str, tasks_file_path: Optional[str] = None) -> str:
        """Reads and returns the entire markdown content from a specified task file (default TASKS.md), used when focusing on a `task_identifier`. Use `tasks_file_path` to specify a file."""
        file_to_read = self._resolve_file_path(tasks_file_path)
        logger.info(f"Executing get_specific_task_markdown for identifier: '{task_identifier}' from file: {file_to_read}. Returning all tasks from this file.")
        return self._read_tasks_markdown_file(tool_context, file_to_read)

    def save_tasks_markdown(
        self,
        tool_context: ToolContext,
        full_updated_markdown_content: str,
        tasks_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Saves/overwrites the 'full_updated_markdown_content' to a specified task file (default TASKS.md). Use `tasks_file_path` to specify."""
        file_to_write = self._resolve_file_path(tasks_file_path)
        logger.info(f"Executing save_tasks_markdown tool for file: {file_to_write} with content length {len(full_updated_markdown_content)}.")
        success = self._save_tasks_markdown_file(tool_context, file_to_write, full_updated_markdown_content)
        if success:
            return {"status": "success", "message": f"Tasks markdown file '{file_to_write}' was successfully updated. Length: {len(full_updated_markdown_content)}."}
        else:
            return {"status": "error", "message": f"Failed to save tasks markdown file '{file_to_write}' due to a persistence error."}

    def prepare_delegation_and_save_tasks(
        self,
        tool_context: ToolContext,
        task_identifier_for_message: str,
        target_agent_name: str,
        delegation_instructions_for_message: str,
        full_updated_markdown_content: str,
        tasks_file_path: Optional[str] = None
    ) -> Dict[str, str]:
        """Saves 'full_updated_markdown_content' (reflecting a task prepared for delegation) to a task file (default TASKS.md). Use `tasks_file_path`. Returns details for instructing root_agent."""
        file_to_write = self._resolve_file_path(tasks_file_path)
        logger.info(f"Executing prepare_delegation_and_save_tasks for task '{task_identifier_for_message}' to agent '{target_agent_name}', saving to file: {file_to_write}.")
        
        save_success = self._save_tasks_markdown_file(tool_context, file_to_write, full_updated_markdown_content)

        if not save_success:
            logger.error(f"Persistence failed for file '{file_to_write}' during delegation preparation for task '{task_identifier_for_message}'.")
            return {
                "status": "error",
                "message": f"Persistence failed for '{file_to_write}' when preparing delegation for task '{task_identifier_for_message}'.",
                "task_identifier": task_identifier_for_message,
                "target_agent": target_agent_name,
                "delegation_instructions": delegation_instructions_for_message
            }
        
        logger.info(f"Task '{task_identifier_for_message}' delegation info saved to '{file_to_write}'. Ready for root_agent instruction.")
        return {
            "status": "delegation_prepared",
            "message": f"Markdown in '{file_to_write}' updated for task '{task_identifier_for_message}' for delegation to {target_agent_name}.",
            "task_identifier": task_identifier_for_message,
            "target_agent": target_agent_name,
            "delegation_instructions": delegation_instructions_for_message
        }

    def receive_task_update(
        self,
        tool_context: ToolContext,
        task_identifier: str,
        new_status_description: str,
        update_message: Optional[str] = None,
        tasks_file_path: Optional[str] = None
    ) -> Dict[str, str]:
        """Receives a task update (identifier, new status, message) from another agent for a task in a specified file (default TASKS.md). Triggers this agent's LLM to process and save the update. Use `tasks_file_path`."""
        file_path_context = tasks_file_path if tasks_file_path else DEFAULT_TASKS_MARKDOWN_FILE
        logger.info(f"Executing receive_task_update tool for task_identifier: '{task_identifier}' in file context: '{file_path_context}'. New status: '{new_status_description}', Message: '{update_message}'.")
        # Basic validation of inputs
        if not task_identifier or not new_status_description:
            logger.warning("receive_task_update called with missing task_identifier or new_status_description.")
            return {
                "status": "error",
                "message": "Task identifier and new status description are required.",
                "task_identifier": task_identifier or "MISSING"
            }

        # The actual work of reading, modifying, and saving the markdown
        # will be done by the LLM of this (TaskManagement) agent, guided by its instructions,
        # using list_all_tasks_markdown and save_tasks_markdown tools internally.
        # This tool call serves as the trigger and data provider for that LLM workflow.
        return {
            "status": "received",
            "message": f"Update for task '{task_identifier}' (new status: '{new_status_description}') received. LLM will process and save to '{file_path_context}'.",
            "task_identifier": task_identifier,
            "new_status_description": new_status_description,
            "update_message": update_message or "",
            "tasks_file_path_context": file_path_context # Pass back for LLM context
        }

# Initialize tools
task_tools = TaskManagementTools()

# Define the default set of tools (custom markdown tools)
default_agent_tools = [
    FunctionTool(task_tools.list_all_tasks_markdown),
    FunctionTool(task_tools.get_specific_task_markdown),
    FunctionTool(task_tools.save_tasks_markdown),
    FunctionTool(task_tools.prepare_delegation_and_save_tasks),
    FunctionTool(task_tools.receive_task_update),
]

mcp_task_tools = []
agent_tools_to_use = default_agent_tools # Default to custom tools

try:
    # Attempt to initialize MCPToolset
    mcp_toolset_instance = MCPToolset(
        connection_params=StdioServerParameters(
            command="uvx",
            args=[
                "mcp-atlassian",
                "--confluence-url=" + os.getenv('CONFLUENCE_URL'),
                "--confluence-username=" + os.getenv('CONFLUENCE_USERNAME'),
                "--confluence-token=" + os.getenv('CONFLUENCE_TOKEN'),
                "--jira-url=" + os.getenv('JIRA_URL'),
                "--jira-username=" + os.getenv('JIRA_USERNAME'),
                "--jira-token=" + os.getenv('JIRA_TOKEN'),
            ],
        ),
    )
    # If MCPToolset loads, add its tools. ADK documentation suggests a Toolset is a list of tools.
    # If mcp_toolset_instance is a single tool, wrap it in a list.
    # If it's already a list of tools, it can be assigned directly or extended.
    # Assuming mcp_toolset_instance itself can be used as the list of tools if it's a ToolSet.
    # Or, if MCPToolset is expected to *provide* a list of tools, that method should be called.
    # For now, let's assume mcp_toolset_instance can be directly used or is a list of tools.
    if mcp_toolset_instance: # Check if it loaded successfully
        mcp_task_tools.append(mcp_toolset_instance) # Assuming it's a tool or a list of tools
        agent_tools_to_use = mcp_task_tools # Prioritize MCP tools if loaded
        logger.info("MCPToolset loaded successfully. Task Management agent will use MCP tools.")
    else:
        logger.warning(
            "MCPToolset initialization did not return a tool instance, though no exception was raised. "
            "Falling back to default task management tools."
        )
        # agent_tools_to_use remains default_agent_tools
except Exception as e:
    logger.warning(
        f"Failed to load MCPToolset: {e}. "
        "Task Management agent will operate without MCP task management tools, using default custom tools. "
        "Custom task management tools remain available."
    )
    # agent_tools_to_use remains default_agent_tools

task_management_agent = LlmAgent(
    model="gemini-2.5-pro-preview-05-06",
    name="task_management_agent",
    description=(
        "Manages tasks by reading and writing to a user-specified or default TASKS.md file in markdown format, "
        "or via MCP tools if available. " # Updated description
        "Can list, create, update, and prepare tasks for delegation."
    ),
    instruction=prompt.TASK_MANAGEMENT_AGENT_INSTR, # Ensure this prompt guides LLM on which tools might be present
    tools=agent_tools_to_use, # Use the conditionally assigned tools
    output_key="task_management",
    generate_content_config=GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=8000,
    ),
)
