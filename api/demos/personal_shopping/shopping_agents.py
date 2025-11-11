"""
Personal Shopping Assistant Agents
==================================

🎯 LEARNING OBJECTIVES:
This module teaches you how to create a multi-agent shopping system:

1. Agent Memory - How to use stored preferences in recommendations
2. Multi-Agent Coordination - Product search, comparison, and recommendation agents
3. Recommendation Systems - How to generate personalized recommendations
4. Context Building - How to build context from memory

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Product Search Agent - Searches for products
Step 2: Comparison Agent - Compares products
Step 3: Recommendation Agent - Generates personalized recommendations

Key Concept: This system uses agent memory to provide personalized
recommendations based on user preferences and shopping history.
"""

import logging
from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from utils.llm_provider import get_llm
from .tools import get_all_tools
from .memory import get_memory, ShoppingMemory

logger = logging.getLogger(__name__)


def create_search_agent(memory_context: str) -> AgentExecutor:
    """
    Create a Product Search Agent.
    
    This agent searches for products based on user queries.
    
    Args:
        memory_context: User preferences and history context
    
    Returns:
        AgentExecutor ready to use
    """
    llm = get_llm(temperature=0.3)
    tools = get_all_tools()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a Product Search Specialist with expertise in finding the best products.

Your role is to:
- Search for products matching user queries
- Find product information, prices, and reviews
- Consider user preferences when searching
- Provide comprehensive product information

User Context:
{memory_context}

Be thorough and find multiple product options for the user."""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


def create_comparison_agent(memory_context: str) -> AgentExecutor:
    """
    Create a Product Comparison Agent.
    
    This agent compares multiple products.
    
    Args:
        memory_context: User preferences and history context
    
    Returns:
        AgentExecutor ready to use
    """
    llm = get_llm(temperature=0.4)
    tools = get_all_tools()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a Product Comparison Expert specializing in analyzing and comparing products.

Your role is to:
- Compare products based on features, price, quality, and reviews
- Consider user preferences when comparing
- Identify pros and cons of each product
- Provide clear comparison results

User Context:
{memory_context}

Be analytical and provide clear, actionable comparisons."""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


def create_recommendation_agent(memory_context: str) -> AgentExecutor:
    """
    Create a Recommendation Agent.
    
    This agent generates personalized product recommendations.
    
    Args:
        memory_context: User preferences and history context
    
    Returns:
        AgentExecutor ready to use
    """
    llm = get_llm(temperature=0.5)
    # Recommendation agent doesn't need web tools, just LLM
    tools = []
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a Personal Shopping Assistant specializing in personalized product recommendations.

Your role is to:
- Generate personalized recommendations based on user preferences
- Consider shopping history and past preferences
- Explain why each product is recommended
- Provide clear, actionable recommendations

User Context:
{memory_context}

Be personal and helpful. Reference user preferences and history when making recommendations."""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


async def get_product_recommendations(
    user_query: str,
    user_id: str = "default",
    budget: Optional[str] = None,
    preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get personalized product recommendations using multi-agent system.
    
    This function:
    1. Updates user preferences if provided
    2. Gets memory context
    3. Searches for products
    4. Compares products
    5. Generates personalized recommendations
    
    Args:
        user_query: User's product search query
        user_id: User identifier for memory
        budget: Optional budget constraint
        preferences: Optional preferences to update
    
    Returns:
        Dictionary with recommendations and analysis
    """
    try:
        # Get or create memory
        memory = get_memory(user_id)
        
        # Update preferences if provided
        if preferences:
            for key, value in preferences.items():
                memory.update_preference(key, value)
        
        # Update budget if provided
        if budget:
            memory.update_preference("budget", budget)
        
        # Get memory context
        memory_context = memory.build_context()
        
        # Step 1: Search for products
        search_agent = create_search_agent(memory_context)
        search_prompt = f"Search for products matching: {user_query}"
        if budget:
            search_prompt += f" within budget: {budget}"
        
        search_result = search_agent.invoke({"input": search_prompt})
        search_output = search_result.get("output", "")
        
        # Step 2: Compare products (if multiple found)
        comparison_agent = create_comparison_agent(memory_context)
        comparison_prompt = f"""Based on the following product search results, compare the products and identify the top options:

{search_output}

Consider the user's preferences and provide a comparison."""
        
        comparison_result = comparison_agent.invoke({"input": comparison_prompt})
        comparison_output = comparison_result.get("output", "")
        
        # Step 3: Generate recommendations
        recommendation_agent = create_recommendation_agent(memory_context)
        recommendation_prompt = f"""Based on the following product search and comparison, provide personalized recommendations:

User Query: {user_query}
Search Results: {search_output}
Comparison: {comparison_output}

Provide:
1. Top 3 recommended products
2. Why each is recommended (considering user preferences)
3. Key features that match user preferences
4. Any concerns or considerations

Format your response clearly with product names and justifications."""
        
        recommendation_result = recommendation_agent.invoke({"input": recommendation_prompt})
        recommendation_output = recommendation_result.get("output", "")
        
        # Store in history
        memory.add_to_history(user_query, [])
        
        return {
            "user_query": user_query,
            "search_results": search_output,
            "comparison": comparison_output,
            "recommendations": recommendation_output,
            "user_preferences": memory.get_preferences(),
            "memory_context": memory_context
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise

