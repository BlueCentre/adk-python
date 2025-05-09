"""Implementation of the Software Engineer Agent with knowledge and experience of sub-agents."""

import logging

import os

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_toolset import StdioServerParameters

# from . import prompt

# Use relative imports from the 'software_engineer' sibling directory
# from .sub_agents.code_quality.agent import code_quality_agent
# from .sub_agents.code_review.agent import code_review_agent
# from .sub_agents.debugging.agent import debugging_agent
# from .sub_agents.design_pattern.agent import design_pattern_agent
# from .sub_agents.devops.agent import devops_agent
# from .sub_agents.documentation.agent import documentation_agent
# from .sub_agents.testing.agent import testing_agent
# from .tools import (
#     available_tools_tool,
#     check_command_exists_tool,
#     check_shell_command_safety_tool,
#     codebase_search_tool,
#     configure_shell_approval_tool,
#     configure_shell_whitelist_tool,
#     edit_file_tool,
#     execute_vetted_shell_command_tool,
#     get_os_info_tool,
#     google_search_grounding,
#     list_available_tools_tool,
#     list_dir_tool,
#     list_tools_tool,
#     read_file_tool,
# )

# Import tools via the tools package __init__
# from .tools import (
#     configure_approval_tool as configure_edit_approval_tool,  # Keep alias for now
# )

# from .tools.project_context import load_project_context

# logger = logging.getLogger(__name__)


# --- Agent Definition ---

# Model name as recognized by *your* vLLM endpoint configuration
# model_name_at_endpoint = "ollama_chat/llama3.2"  # Actually does not work as documented on ADK.
model_name_at_endpoint = "hosted_vllm/llama3.2"  # Example from vllm_test.py

# REF: https://google.github.io/adk-docs/agents/models/#using-open-local-models-via-litellm
root_agent = LlmAgent(
    model=LiteLlm(model=model_name_at_endpoint),
    name="coordinator_agent",
    description="An AI software engineer assistant that helps with various software development tasks",
    instruction="""
    - You are a software engineer assistant
    - You help and lead developers with various software development tasks including code reviews, design patterns, testing, debugging, documentation, and DevOps
    - Format your responses back to users with markdown. Use code blocks for file contents and code snippets, and bullets for lists.
    - After every tool call, summarize the result and keep your response concise
    """,
    # instruction=prompt.ROOT_AGENT_INSTR,
    # sub_agents=[
    #     design_pattern_agent,
    #     documentation_agent,
    #     code_review_agent,
    #     code_quality_agent,
    #     testing_agent,
    #     debugging_agent,
    #     devops_agent,  # TODO: Move command tools to devops_agent with more guardrails
    # ],
    tools=[
        # read_file_tool,
        # list_dir_tool,
        # edit_file_tool,
        # configure_edit_approval_tool,
        # check_command_exists_tool,
        # check_shell_command_safety_tool,
        # configure_shell_approval_tool,
        # configure_shell_whitelist_tool,
        # execute_vetted_shell_command_tool,
        # google_search_grounding,
        # codebase_search_tool,
        # get_os_info_tool,
        # list_available_tools_tool,  # NOTE: This is needed for LiteLLM models in order to use the FunctionTool.
        # list_tools_tool,
        # available_tools_tool,
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    '-y',  # Arguments for the command
                    '@modelcontextprotocol/server-filesystem',
                    os.path.dirname(os.path.abspath(__file__)),
                ],
            ),
            # don't want agent to do write operation
            # tool_predicate=lambda tool, ctx=None: tool.name
            # not in ('write_file', 'edit_file', 'create_directory', 'move_file'),
        ),
    ],
    # Pass the function directly, not as a list
    # before_agent_callback=load_project_context,
    # output_key="software_engineer",
)
