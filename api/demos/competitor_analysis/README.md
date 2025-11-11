# Competitor Analysis Research Agent

## 🎯 Learning Objectives

This demo teaches you how to build a multi-agent research system that can:

1. **Tool Calling & Function Integration** - Agents use web search and scraping tools to gather information
2. **Multi-Agent Coordination** - Multiple specialized agents work together in a coordinated workflow
3. **Web Search Integration** - Using DuckDuckGo for internet research without API keys
4. **Workflow Orchestration** - Coordinating multiple agents in sequence to complete complex tasks

## 📚 Key Concepts

### Tool Calling
Agents can call functions (tools) to interact with the external world. In this demo:
- `search_web()` - Searches the internet using DuckDuckGo
- `scrape_website()` - Extracts content from web pages
- `analyze_competitor()` - Orchestrates multiple searches for comprehensive analysis

### Multi-Agent Coordination
Three specialized agents work together:
1. **Research Agent** - Gathers information from the web
2. **Analysis Agent** - Analyzes competitive positioning
3. **Report Agent** - Creates comprehensive reports

### Workflow Orchestration
The system coordinates agents in sequence:
1. Research phase - Gather data
2. Analysis phase - Process and analyze
3. Report phase - Synthesize into final report

## 🏗️ Architecture

```
User Request
    ↓
FastAPI Endpoint
    ↓
Background Task
    ↓
Research Agent → Analysis Agent → Report Agent
    ↓
Final Report
```

## 📁 File Structure

- `main.py` - FastAPI router with endpoints
- `agents.py` - Agent definitions and orchestration
- `tools.py` - Web search and scraping tools
- `README.md` - This file

## 🚀 Usage

### API Endpoints

1. **POST /competitor-analysis/start-analysis**
   - Start a new competitor analysis
   - Body: `{ "company_name": "Your Company", "competitors": ["Competitor 1", "Competitor 2"], "focus_areas": ["pricing", "features"] }`
   - Returns: `{ "session_id": "...", "status": "processing" }`

2. **GET /competitor-analysis/status/{session_id}**
   - Check analysis status
   - Returns: `{ "status": "processing|completed|error", "message": "..." }`

3. **GET /competitor-analysis/result/{session_id}**
   - Get final analysis report
   - Returns: `{ "report": "...", "status": "completed" }`

## 🔧 Implementation Details

### Tools
- Uses `duckduckgo-search` package for web search (no API key required)
- Uses LangChain's `WebBaseLoader` for web scraping
- Tools are wrapped as LangChain tools for agent use

### Agents
- Each agent has a specific role, goal, and backstory
- Agents use different temperature settings for different tasks
- Research agent has access to web tools
- Report agent only uses LLM (no tools needed)

### Workflow
1. User submits analysis request
2. Background task starts
3. Research agent searches for each competitor
4. Analysis agent processes the research
5. Report agent creates final report
6. Results stored in session

## 🎓 Challenges

### Challenge 1: Add More Tools
Add a tool to search for recent news articles about competitors.

**Hint:** Create a new tool function that searches for news using DuckDuckGo.

### Challenge 2: Parallel Research
Modify the research phase to search for all competitors in parallel instead of sequentially.

**Hint:** Use `asyncio.gather()` to run multiple agent invocations concurrently.

### Challenge 3: Add Caching
Implement caching to avoid re-searching for the same competitors.

**Hint:** Use a dictionary to store search results by query.

### Challenge 4: Enhanced Analysis
Add sentiment analysis to determine if competitor mentions are positive or negative.

**Hint:** Create a new analysis agent that focuses on sentiment analysis.

## 🔍 Key Code Patterns

### Tool Definition
```python
@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    results = duckduckgo_search.run(query)
    return results
```

### Agent Creation
```python
def create_research_agent() -> AgentExecutor:
    llm = get_llm(temperature=0.3)
    tools = get_all_tools()
    # ... create agent with tools
```

### Multi-Agent Workflow
```python
# Research phase
research_result = research_agent.invoke({"input": query})

# Analysis phase
analysis_result = analysis_agent.invoke({"input": analysis_prompt})

# Report phase
report_result = report_agent.invoke({"input": report_prompt})
```

## 📖 Related Concepts

- **Tool Calling**: Agents can call functions to interact with external systems
- **Multi-Agent Systems**: Multiple agents with specialized roles
- **Workflow Orchestration**: Coordinating agents in sequence
- **Web Search Integration**: Using search engines as agent tools

## 🐛 Troubleshooting

### Issue: Web search returns no results
- Check internet connection
- Verify DuckDuckGo is accessible
- Try a different search query

### Issue: Agents taking too long
- Reduce number of competitors
- Limit focus areas
- Check LLM API rate limits

### Issue: Scraping fails
- Verify URLs are accessible
- Check if website blocks scrapers
- Some sites may require headers

