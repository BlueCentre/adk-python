# Agent Improvement Log

This document tracks potential improvements for the multi-agent system.

## Root Agent (`root_agent`)

**Goal:** Maximize delegation to sub-agents; root agent should primarily orchestrate and delegate, performing minimal direct task execution.

**Potential Improvements:**

1.  **Tool Rationalization:**
    *   **Current State:** The root agent possesses a wide array of tools (filesystem, shell execution, code search, etc.).
    *   **Observation:** Sub-agents (e.g., `devops_agent`) also have many of these tools.
    *   **Suggestion:**
        - [x] Review tool duplication. (Addressed for shell, edit, code_search, os_info tools)
        - [x] Consider if the root agent truly needs all these tools if its primary role is delegation. Could it rely on sub-agents for most tool-based actions? (Addressed for shell, edit, code_search, os_info tools)
    *   **Action:**
        - [x] Identify tools that can be exclusively managed by sub-agents. The root agent might only need delegation tools and perhaps very minimal interaction/utility tools. (Addressed for shell, edit, code_search, os_info tools)

2.  **Prompt Focus:**
    *   **Current State:** The root agent's prompt (`ROOT_AGENT_INSTR`) provides detailed instructions on *how* to use various tools (e.g., file editing workflow, shell command workflow).
    *   **Observation:** If sub-agents are responsible for tool execution, these detailed instructions might be more appropriate for sub-agent prompts.
    *   **Suggestion:**
        - [x] Refine the root agent's prompt to focus more on *strategic delegation* (Significantly addressed by removing shell, edit, code_search, os_info tools and updating prompt)
            *   [x] Identifying the correct sub-agent for a task. (Prompt updated)
            *   [x] Passing necessary context to the sub-agent. (Implicit in delegation)
            *   [x] Handling responses from sub-agents. (Standard agent flow)
            *   [x] Less emphasis on the low-level mechanics of tool usage. (Prompt updated)

3.  **Shell Command Tools (as per existing TODO):**
    *   **Current State:** The root agent's `agent.py` has a TODO: "Move command tools to devops_agent with more guardrails."
    *   **Suggestion:**
        - [x] Prioritize this. Centralizing shell command execution within the `devops_agent` (which has a strong safety focus) seems appropriate. The root agent could then request shell operations *through* the `devops_agent`.

4.  **Memory Tool Access:**
    *   **Current State:** The root agent has `load_memory`, `add_memory_fact`, `search_memory_facts` operating on a global memory store.
    *   **Observation:** Clarity was needed on how sub-agents interact with memory.
    *   **Strategy Defined:**
        - [x] Define a clear strategy for memory access across agents.
            *   **Global Project Context:** The root agent manages a global `project_context` (using its memory tools) and passes it as read-only information to sub-agents upon invocation. This provides foundational knowledge. (Aligns with item 5).
            *   **Sub-Agent Local Memory:** Sub-agents performing complex, multi-step tasks can be equipped with the *same memory tool functions* (e.g., `add_memory_fact`,
 `search_memory_facts`). However, for sub-agents, these tools will operate on a **separate, isolated, and potentially ephemeral local memory store**, specific to their current task. This
 allows them to manage intermediate findings without affecting global memory.
            *   **Promoting Information to Global Memory:** If a sub-agent discovers information of lasting global importance (that should update the `project_context` or shared knowledge)
 it should report this back to the root agent as part of its results. The root agent then uses its memory tools to add this information to the global memory store. This maintains centralized
 control and curation of shared knowledge.
            *   **Summary of Access & Tooling:**
                *   Root Agent: Owns global memory tools for the main `project_context`.
                *   Sub-Agents:
                    *   Receive global `project_context` (read-only).
                    *   Can be equipped with identical memory tool *functions* that are scoped to operate on their own *local* memory store for task-specific needs.
                    *   Request updates to global memory via the root agent (by returning facts/insights).

5.  **Project Context (`load_project_context`):**
    *   **Current State:** The `load_project_context` callback loads context into the root agent's state.
    *   **Suggestion:**
        - [x] Ensure this project context is effectively passed down to sub-agents when they are invoked, so they have the necessary background information.
        - [x] Verify the mechanism (current prompts suggest this is happening with `{project_context}` placeholders).

## DevOps Agent (`devops_agent`)

**Goal:** Effectively handle DevOps, CI/CD, deployment, and infrastructure tasks using its specialized tools and knowledge.

**Potential Improvements:**

1.  **MCP Toolset Clarity:**
    *   **Current State:** Uses `MCPToolset` with `npx -y @modelcontextprotocol/server-filesystem`.
    *   **Observation:** The exact capabilities and limitations of this `server-filesystem` via MCP aren't fully clear from the code alone. The commented-out `tool_predicate` suggests an awareness of restricting write operations.
    *   **Suggestion:**
        - [x] Ensure the agent's prompt or internal logic clearly understands when to use these MCP-based file tools versus the standard ADK file tools (`read_file_tool`, `edit_file_tool`).
        - [x] Clarify if the MCP toolset offers advantages (e.g., performance for large files, specific metadata access) that would guide this choice.
        - [x] If the `tool_predicate` for restricting writes is desired, it should be implemented. (ignore for now)

2.  **Tool Redundancy with Root Agent:**
    *   **Current State:** Has `read_file_tool`, `list_dir_tool`, `edit_file_tool`, `codebase_search_tool`, `execute_vetted_shell_command_tool`, `check_command_exists_tool`.
    *   **Observation:** These are also present in the root agent.
    *   **Suggestion:**
        - [x] As part of the broader tool rationalization, confirm if the `devops_agent` should be the primary owner/user of shell command tools. If so, the root agent might not need them directly. (Addressed by moving shell tools to devops_agent)

3.  **Internal `_search_agent` and `_code_execution_agent` Prompts:**
    *   **Current State:** These internal agents have their own specific prompts.
    *   **Suggestion:**
        - [x] Periodically review these prompts to ensure they remain aligned with the `devops_agent`'s overall goals. The `_search_agent`'s instruction for "brief but concise" single-sentence actionable items might be too limiting for complex research tasks the DevOps agent might need.

4.  **Environment Variable Dependency (`MCP_ALLOWED_DIRECTORIES`):**
    *   **Current State:** Relies on `.env` and `MCP_ALLOWED_DIRECTORIES`.
    *   **Suggestion:**
        - [x] Ensure clear documentation for setting up these environment variables. (Fallback exists, which is good). (Documentation added to IMPROVEMENTS.md)

## Code Quality Agent (`code_quality_agent`)

**Goal:** Provide expert analysis of code quality, identify issues, and suggest actionable improvements.

**Potential Improvements:**

1.  **Integration with `edit_file_tool` (Optional/Consideration):**
    *   **Current State:** Suggests fixes.
    *   **Suggestion:**
        - [IN_PROGRESS: Awaiting code quality feedback. Code changes submitted to code_quality_agent for review.] Consider if there are scenarios where, after user approval, this agent *could* apply straightforward, safe fixes using `edit_file_tool`. This would enhance its capability but requires careful safety considerations. Perhaps it proposes an edit, and the user or another agent applies it.

2.  **Clarity on `analyze_code_tool`'s Capabilities:**
    *   **Observation:** The prompt mentions analyzing for various issues (bugs, smells, security, etc.).
    *   **Suggestion:**
        - [ ] Document (for developers/maintainers) what specific linters or analyzers `analyze_code_tool` uses internally. This helps understand its scope and limitations.

3.  **Batch Analysis/Project-Wide Analysis:**
    *   **Current State:** Prompt implies analysis of a "specified file."
    *   **Suggestion:**
        - [ ] Evaluate if the agent should support project-wide or directory-wide analysis. This might need enhancements to `analyze_code_tool` or a more complex interaction pattern for the agent.

## Code Review Agent (`code_review_agent`)

**Goal:** Perform meticulous, deep code reviews, identify a wide range of issues, and provide high-quality, actionable feedback.

**Potential Improvements:**

1.  **Tool Alignment with Prompt (Critical):**
    *   **Current State:** The agent's `tools` list in `agent.py` is missing several tools (`check_command_exists_tool`, `codebase_search_tool`, shell command tools) that its prompt explicitly instructs it to use.
    *   **Suggestion:**
        - [x] Add the necessary tools to `code_review_agent`'s toolset to enable its documented workflow. This is a high-priority fix.
    *   **Action:**
        - [x] Add `check_command_exists_tool`, `codebase_search_tool`, `check_shell_command_safety_tool`, `execute_vetted_shell_command_tool`.
        - [x] Consider `configure_shell_approval_tool` and `configure_shell_whitelist_tool`. (Marked as done as they were added based on previous check)

2.  **Clarify Role of `analyze_code_tool`:**
    *   **Current State:** Has `analyze_code_tool`. The prompt emphasizes manual review and discovery/execution of external tools.
    *   **Suggestion:**
        - [ ] Refine the prompt to clarify how `analyze_code_tool` fits into its workflow. Is it a primary analysis engine, a fallback, or a supplement to externally run tools?

3.  **Max Output Tokens:**
    *   **Current State:** `max_output_tokens=1000`.
    *   **Suggestion:**
        - [ ] Monitor if this is sufficient for detailed code reviews, which can be lengthy.
        *   Consider increasing if truncation is observed.

4.  **Structured Output (Revisit `CodeReviewResponse`):**
    *   **Current State:** A commented-out import for `CodeReviewResponse` exists.
    *   **Suggestion:**
        - [ ] For complex reviews, a structured response type could improve consistency and programmatic usability. (Lower priority).

## Debugging Agent (`debugging_agent`)

**Goal:** Systematically find and fix bugs by analyzing code, errors, and context.

**Potential Improvements:**

1.  **Interactive Debugging Tool (Future Consideration):**
    *   **Current State:** Relies on static analysis and command execution.
    *   **Suggestion:**
        - [ ] For complex scenarios, an interactive debugger tool (set breakpoints, inspect variables) would be a powerful but complex future enhancement.

2.  **State Management for Multi-Step Debugging:**
    *   **Observation:** Debugging can be iterative.
    *   **Suggestion:**
        - [ ] Encourage through prompt or examples how the agent should maintain state/memory of previous attempts and hypotheses during a complex debugging session.

3.  **Clarity on `get_os_info` Tool:**
    *   **Observation:** Uses `get_os_info`.
    *   **Suggestion:**
        - [ ] Ensure this tool provides OS information most relevant for debugging common software issues (e.g., OS version, kernel, key environment variables, CPU architecture).

## Design Pattern Agent (`design_pattern_agent`)

**Goal:** Analyze codebases and recommend appropriate design patterns or architectural improvements.

**Potential Improvements:**

1.  **Clarify Role of `execute_vetted_shell_command_tool`:**
    *   **Current State:** Tool is present, but prompt doesn't strongly guide its usage.
    *   **Suggestion:**
        - [ ] If there are specific scenarios where shell commands are useful (e.g., invoking code generation tools for patterns), add hints to the prompt. Otherwise, consider its necessity for core tasks.

2.  **Integration with Code Generation/Refactoring Tools (Advanced):**
    *   **Current State:** Can generate code snippets/full files for `edit_file_tool`.
    *   **Suggestion:**
        - [ ] Explore integration with automated refactoring or pattern implementation tools (e.g., IDE refactoring tools via CLI) for more advanced capabilities. (Future consideration).

3.  **Knowledge Base of Patterns (Internal vs. External Search):**
    *   **Current State:** Relies on training and `google_search_grounding`.
    *   **Suggestion:**
        - [ ] Guide the agent to balance its internal knowledge with external search effectively.
        - [ ] Ensure robust internal knowledge of common patterns.

## Documentation Agent (`documentation_agent`)

**Goal:** Generate clear, accurate, and comprehensive documentation for code, APIs, and projects.

**Potential Improvements:**

1.  **Tool Alignment for Shell Workflow (Important):**
    *   **Current State:** Prompt instructs use of `check_command_exists_tool` and `check_shell_command_safety_tool` for running doc generators, but these are missing from `agent.py` (though `execute_vetted_shell_command_tool` is present).
    *   **Suggestion:**
        - [x] Add `check_command_exists_tool` and `check_shell_command_safety_tool` to its toolset for the full documented shell workflow.

2.  **Clarify/Correct `file_search` Tool Mention:**
    *   **Current State:** Prompt mentions a `file_search` tool in its latter section, which is not a defined tool.
    *   **Suggestion:**
        - [x] If this is a typo for `codebase_search_tool`, correct it.
        - [ ] If `file_search` is a distinct, intended tool, it needs to be implemented and added.

3.  **Docstring/Comment Insertion Precision:**
    *   **Current State:** Uses `edit_file_content` to insert docstrings/comments.
    *   **Suggestion:**
        - [ ] (In Progress) Inserting into existing code precisely can be hard with a tool that replaces entire files (like the ADK `edit_file_content` seems to be). Consider if a more precise line-based editing tool (like the other `edit_file` we saw) is needed, or if the agent should only generate docstrings for the user to insert manually.

4.  **Awareness of Documentation Formats/Styles:**
    *   **Current State:** Prompt mentions researching standards.
    *   **Suggestion:**
        - [ ] Reinforce through examples or prompt details the expected quality and conventions for common documentation types (Markdown, Python docstrings, Javadoc, etc.).

## Testing Agent (`testing_agent`)

**Goal:** Help developers create comprehensive and effective automated tests.

**Potential Improvements:**

1.  **Tool Alignment for Test Execution Workflow (Critical):**
    *   **Current State:** Prompt mandates a workflow involving `check_command_exists_tool` and `check_shell_command_safety_tool` before running tests, but these tools are missing from `agent.py`.
    *   **Suggestion:**
        - [x] Add `check_command_exists_tool` and `check_shell_command_safety_tool` to its toolset.
        - [x] Consider `configure_shell_approval_tool` and `configure_shell_whitelist_tool` for managing test execution settings.
    *   **Action:**
        - [x] This is critical for the agent to reliably and safely discover and execute project-specific test commands. (Marked as done as suggestions cover this)

2.  **Guidance on Test Framework Interaction:**
    *   **Current State:** General instructions to generate tests.
    *   **Suggestion:**
        - [ ] Enhance the prompt with examples or guidance on structuring tests for common frameworks (e.g., pytest, Jest conventions) to improve the quality of generated tests.

3.  **Coverage Analysis Interpretation:**
    *   **Current State:** Mentions running coverage tools.
    *   **Suggestion:**
        - [ ] If the agent is expected to interpret coverage reports (not just run the tool), it might need more guidance or a specialized tool for parsing common coverage report formats. For now, running the tool and presenting output is a good first step.

4.  **Mocking/Stubbing Assistance:**
    *   **Current State:** Mentions employing mocking.
    *   **Suggestion:**
        - [ ] Prompt the agent to ask for clarification on dependencies to mock or to use `google_search_grounding` for framework-specific mocking examples.


Now that we have a working implementation with mcp tools for working with files in the devops agent, could we possibly reuse the same approach including the fallback for all agents that need to do file operations? Rather than copy/paste, it would be nice to have shared code for this right? Many of our sub agents will likely need these tools otherwise they will always have to delegate/transfer to devops agent which seems like we are wasting compute cycles.