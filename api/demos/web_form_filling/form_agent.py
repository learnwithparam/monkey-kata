"""
Form Filling Agent
==================

🎯 LEARNING OBJECTIVES:
This module teaches you how to create an agent that uses browser automation tools:

1. Agent with Tools - How to equip an agent with browser automation tools
2. Tool Calling - How agents decide which tools to use
3. Workflow Orchestration - How to coordinate multiple tool calls
4. Error Handling - How to handle browser automation errors

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Agent Creation - Create agent with browser tools
Step 2: Task Execution - Agent uses tools to complete form filling
Step 3: Result Processing - Extract and format results

Key Concept: This agent uses browser automation tools to interact with web pages,
demonstrating how agents can extend their capabilities through tool calling.
"""

import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from utils.llm_provider import get_llm
from .browser_tools import get_all_tools

logger = logging.getLogger(__name__)

# Global callback for progress updates
_progress_callback: Optional[Callable[[Any], None]] = None

def set_progress_callback(callback: Optional[Callable[[Any], None]]):
    """Set a callback function to report progress updates"""
    global _progress_callback
    _progress_callback = callback

def _report_progress(message: str, agent: str = None, tool: str = None, target: str = None):
    """Report progress if callback is set"""
    if _progress_callback:
        try:
            step_data = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "agent": agent,
                "tool": tool,
                "target": target
            }
            _progress_callback(step_data)
        except Exception as e:
            logger.warning(f"Error in progress callback: {e}")


def create_form_filling_agent() -> AgentExecutor:
    """
    Create a Form Filling Agent with browser automation tools.
    
    This agent can:
    - Navigate to web pages
    - Detect form fields
    - Fill forms with provided data
    - Submit forms
    
    Returns:
        AgentExecutor ready to use
    """
    llm = get_llm(temperature=0.2)  # Lower temperature for more deterministic behavior
    tools = get_all_tools()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Web Form Filling Assistant specialized in automatically filling out web forms.

Your capabilities:
- Navigate to web pages using URLs
- Detect and identify form fields on web pages
- Fill form fields with provided data
- Submit completed forms

When given a task:
1. First, navigate to the URL if not already there
2. Detect all form fields on the page
3. Match the provided data to form fields (by id, name, or label)
4. Fill the form fields with the data
5. Submit the form if requested

Be careful to:
- Match field identifiers correctly (case-insensitive)
- Handle different field types (text, email, select, textarea)
- Wait for pages to load before interacting
- Provide clear status updates

Always explain what you're doing at each step."""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


async def fill_form_workflow(
    url: str,
    form_data: Dict[str, str],
    auto_submit: bool = False
) -> Dict[str, Any]:
    """
    Complete form filling workflow using the agent.
    
    This function orchestrates the form filling process:
    1. Navigate to URL
    2. Detect form fields
    3. Fill form with data
    4. Optionally submit form
    
    Args:
        url: URL of the webpage with the form
        form_data: Dictionary mapping field identifiers to values
        auto_submit: Whether to automatically submit the form
    
    Returns:
        Dictionary with workflow results and status
    """
    try:
        agent = create_form_filling_agent()
        
        # Step 1: Navigate to URL
        logger.info(f"Navigating to: {url}")
        _report_progress(
            f"Navigating to {url}",
            agent="Form Filling Agent",
            tool="navigate_to_url",
            target=url
        )
        nav_result = agent.invoke({
            "input": f"Navigate to the URL: {url}"
        })
        _report_progress(
            f"Successfully navigated to {url}",
            agent="Form Filling Agent",
            tool="navigate_to_url",
            target=url
        )
        
        # Step 2: Detect form fields
        logger.info("Detecting form fields...")
        _report_progress(
            "Detecting form fields on the page",
            agent="Form Filling Agent",
            tool="detect_form_fields",
            target=url
        )
        detect_result = agent.invoke({
            "input": f"Detect all form fields on the current page at {url}"
        })
        _report_progress(
            "Form fields detected successfully",
            agent="Form Filling Agent",
            tool="detect_form_fields",
            target=url
        )
        
        # Step 3: Fill form
        logger.info("Filling form...")
        form_data_str = json.dumps(form_data, indent=2)
        fill_prompt = f"""Fill the form on the page at {url} with the following data:
        
{form_data_str}

Match the data keys to form fields by id, name, or label (case-insensitive).
Fill each field with its corresponding value."""
        
        _report_progress(
            f"Filling form with {len(form_data)} fields",
            agent="Form Filling Agent",
            tool="fill_form",
            target=url
        )
        fill_result = agent.invoke({
            "input": fill_prompt
        })
        _report_progress(
            "Form filled successfully",
            agent="Form Filling Agent",
            tool="fill_form",
            target=url
        )
        
        result = {
            "status": "success",
            "url": url,
            "navigation": nav_result.get("output", ""),
            "form_detection": detect_result.get("output", ""),
            "form_filling": fill_result.get("output", ""),
            "form_data": form_data
        }
        
        # Step 4: Submit if requested
        if auto_submit:
            logger.info("Submitting form...")
            _report_progress(
                "Submitting the form",
                agent="Form Filling Agent",
                tool="submit_form",
                target=url
            )
            submit_result = agent.invoke({
                "input": f"Submit the form on the page at {url}"
            })
            result["form_submission"] = submit_result.get("output", "")
            result["submitted"] = True
            _report_progress(
                "Form submitted successfully",
                agent="Form Filling Agent",
                tool="submit_form",
                target=url
            )
        else:
            result["submitted"] = False
        
        return result
        
    except Exception as e:
        logger.error(f"Error in form filling workflow: {e}")
        _report_progress(
            f"Error: {str(e)}",
            agent="Form Filling Agent",
            tool="error",
            target=url
        )
        return {
            "status": "error",
            "url": url,
            "error": str(e),
            "form_data": form_data
        }

