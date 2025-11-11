"""
Competitor Analysis Agents
===========================

🎯 LEARNING OBJECTIVES:
This module teaches you how to create specialized AI agents:

1. Agent Roles - How to define agent roles and responsibilities
2. Agent Goals - How to set clear objectives for agents
3. Agent Backstories - How to give agents context and expertise
4. Tool Integration - How to equip agents with tools
5. Multi-Agent Coordination - How agents work together

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Research Agent - Gathers information from the web
Step 2: Analysis Agent - Analyzes and synthesizes information
Step 3: Report Agent - Creates comprehensive reports

Key Concept: Each agent has a specific role. They work together as a team,
with each agent handling a different part of the competitor analysis workflow.
"""

from typing import List
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from utils.llm_provider import get_llm
from .tools import get_all_tools


def create_research_agent() -> AgentExecutor:
    """
    Create a Research Agent specialized in gathering competitor information.
    
    This agent:
    - Searches the web for competitor information
    - Scrapes competitor websites
    - Gathers market data and trends
    
    Returns:
        AgentExecutor ready to use
    """
    llm = get_llm(temperature=0.3)
    tools = get_all_tools()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Research Specialist with expertise in market research and competitive intelligence.
        
Your role is to:
- Search the web for comprehensive information about competitors
- Gather data on competitor products, pricing, market position, and strategies
- Extract relevant information from competitor websites
- Provide detailed, factual information for analysis

IMPORTANT TOOL USAGE RULES:
- Use search_web(query) for SEARCH QUERIES only (e.g., "Maven AI courses pricing")
- Use scrape_website(url) for URLs only (e.g., "https://maven.com/courses")
- NEVER use search_web with a URL - always use scrape_website for URLs
- NEVER use scrape_website with a search query - always use search_web for queries

Be thorough and gather information from multiple sources. Focus on facts and data."""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


def create_analysis_agent() -> AgentExecutor:
    """
    Create an Analysis Agent specialized in analyzing competitor data.
    
    This agent:
    - Analyzes competitor strengths and weaknesses
    - Identifies market positioning
    - Compares competitors to target company
    
    Returns:
        AgentExecutor ready to use
    """
    llm = get_llm(temperature=0.4)
    tools = get_all_tools()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Market Analysis Expert with deep knowledge of competitive strategy and market positioning.
        
Your role is to:
- Analyze competitor data and identify key insights
- Determine market positioning and competitive advantages
- Compare competitors and identify differentiation opportunities
- Provide strategic recommendations based on analysis

Be analytical and provide clear, actionable insights."""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


def create_report_agent() -> AgentExecutor:
    """
    Create a Report Agent specialized in creating comprehensive reports.
    
    This agent:
    - Synthesizes research and analysis into reports
    - Structures information clearly
    - Creates executive summaries
    
    Returns:
        AgentExecutor ready to use
    """
    llm = get_llm(temperature=0.5)
    # Report agent doesn't need web tools, just LLM
    tools = []
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Business Report Writer specializing in competitive intelligence reports.
        
Your role is to:
- Synthesize research and analysis into comprehensive reports
- Structure information clearly with sections and summaries
- Create executive summaries for decision-makers
- Present findings in a professional, actionable format

Be clear, concise, and professional in your writing."""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


async def run_competitor_analysis(
    company_name: str,
    competitors: List[str],
    focus_areas: List[str]
) -> str:
    """
    Run a complete competitor analysis workflow using multiple agents.
    
    This function orchestrates three agents:
    1. Research Agent - Gathers information
    2. Analysis Agent - Analyzes the data
    3. Report Agent - Creates the final report
    
    Args:
        company_name: Name of the company being analyzed
        competitors: List of competitor company names
        focus_areas: List of areas to focus on (e.g., ["pricing", "features", "market share"])
    
    Returns:
        Comprehensive competitor analysis report
    """
    from .tools import _report_progress
    
    # Step 1: Research Phase - Single comprehensive research task
    _report_progress(
        f"Research Agent: Starting research phase for {len(competitors)} competitors",
        agent="Research Agent",
        tool="agent_invoke",
        target=f"Analyzing {company_name} vs {', '.join(competitors)}"
    )
    research_agent = create_research_agent()
    
    # Create a single comprehensive research query instead of many small ones
    research_prompt = f"""Research and gather comprehensive information about the following competitors:

Company to analyze: {company_name}
Competitors: {', '.join(competitors)}
Focus areas: {', '.join(focus_areas)}

For each competitor, search for:
1. Products and offerings
2. Pricing information
3. Market position and market share
4. Key features and differentiators
5. Recent news and developments

Use web search and website scraping tools to gather this information. Be thorough but efficient - focus on the most relevant information."""
    
    research_result = research_agent.invoke({"input": research_prompt})
    research_summary = research_result.get("output", "")
    
    _report_progress(
        f"Research Agent: Completed data gathering phase",
        agent="Research Agent",
        tool="agent_complete",
        target=f"Collected data on {len(competitors)} competitors"
    )
    
    # Step 2: Analysis Phase
    _report_progress(
        f"Analysis Agent: Starting competitive analysis",
        agent="Analysis Agent",
        tool="agent_invoke",
        target="Processing research data"
    )
    analysis_agent = create_analysis_agent()
    
    analysis_prompt = f"""Based on the following research data, analyze the competitive landscape:

Company: {company_name}
Competitors: {', '.join(competitors)}
Focus Areas: {', '.join(focus_areas)}

Research Data:
{research_summary}

Please provide:
1. Competitive positioning analysis
2. Key differentiators for each competitor
3. Market opportunities and threats
4. Strategic recommendations"""
    
    analysis_result = analysis_agent.invoke({"input": analysis_prompt})
    analysis_output = analysis_result.get("output", "")
    
    _report_progress(
        f"Analysis Agent: Completed competitive positioning analysis",
        agent="Analysis Agent",
        tool="agent_complete",
        target="Identified market opportunities and threats"
    )
    
    # Step 3: Report Generation
    _report_progress(
        f"Report Agent: Generating structured analysis report",
        agent="Report Agent",
        tool="agent_invoke",
        target="Creating final report"
    )
    report_agent = create_report_agent()
    
    report_prompt = f"""Create a structured competitor analysis report in JSON format based on the following:

Company: {company_name}
Competitors: {', '.join(competitors)}

Research Summary:
{research_summary}

Analysis:
{analysis_output}

Please create a structured JSON report with the following format:
{{
  "executive_summary": "Brief 2-3 sentence summary of key findings",
  "market_positioning": {{
    "your_company": "Brief positioning statement",
    "competitors": [
      {{
        "name": "Competitor name",
        "positioning": "Their market position",
        "strengths": ["strength 1", "strength 2"],
        "weaknesses": ["weakness 1", "weakness 2"],
        "pricing": "Pricing strategy or range",
        "key_features": ["feature 1", "feature 2"]
      }}
    ]
  }},
  "competitive_advantages": [
    "Advantage 1",
    "Advantage 2",
    "Advantage 3"
  ],
  "competitive_disadvantages": [
    "Disadvantage 1",
    "Disadvantage 2"
  ],
  "market_opportunities": [
    "Opportunity 1",
    "Opportunity 2"
  ],
  "market_threats": [
    "Threat 1",
    "Threat 2"
  ],
  "strategic_recommendations": [
    "Recommendation 1",
    "Recommendation 2",
    "Recommendation 3"
  ],
  "key_insights": [
    "Insight 1",
    "Insight 2",
    "Insight 3"
  ]
}}

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no code blocks, just the raw JSON object."""
    
    report_result = report_agent.invoke({"input": report_prompt})
    _report_progress(
        f"Report Agent: Completed report generation",
        agent="Report Agent",
        tool="agent_complete",
        target="Final report ready"
    )
    
    report_text = report_result.get("output", "")
    
    # Try to extract JSON from the response
    import re
    import json as json_lib
    
    # Try to find JSON in the response
    json_match = re.search(r'\{.*\}', report_text, re.DOTALL)
    if json_match:
        try:
            structured_data = json_lib.loads(json_match.group())
            return json_lib.dumps(structured_data, indent=2)
        except:
            pass
    
    # Fallback to original text if JSON parsing fails
    return report_text

