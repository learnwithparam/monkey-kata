"""
Competitor Analysis Tools
=========================

🎯 LEARNING OBJECTIVES:
This module teaches you how to create tools for AI agents:

1. Tool Definition - How to create reusable tools for agents
2. Web Search Integration - How to use DuckDuckGo for web search
3. Web Scraping - How to extract content from web pages
4. Tool Wrapping - How to wrap external libraries as agent tools

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Web Search Tool - Search the internet for information
Step 2: Web Scraping Tool - Extract content from web pages
Step 3: Tool Registration - Make tools available to agents

Key Concept: Tools extend agent capabilities. Agents can call these tools
to interact with the external world (web, databases, APIs, etc.)
"""

import os
import logging
from typing import List, Optional, Callable, Any
from langchain_core.tools import tool
from langchain_community.document_loaders import WebBaseLoader
from ddgs import DDGS

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
                "message": message,
                "agent": agent,
                "tool": tool,
                "target": target
            }
            _progress_callback(step_data)
        except Exception as e:
            logger.warning(f"Error in progress callback: {e}")


@tool
def search_web(query: str) -> str:
    """
    Search the web for information using a search query.
    
    IMPORTANT: This tool is for SEARCH QUERIES only (e.g., "Maven AI courses pricing").
    Do NOT use this tool with URLs. If you have a URL, use scrape_website instead.
    
    This tool uses DuckDuckGo to search the internet and returns relevant search results.
    Use this when you need to find information that's not in your knowledge base.
    
    Args:
        query: Search query string (e.g., "competitor analysis for AI companies", "Maven AI courses pricing")
               DO NOT pass URLs here - use scrape_website for URLs.
    
    Returns:
        Search results as a formatted string
    """
    try:
        logger.info(f"Searching web for: {query}")
        _report_progress(
            f"Searching web for information",
            agent="Research Agent",
            tool="search_web",
            target=query[:60] + "..." if len(query) > 60 else query
        )
        
        # Use ddgs directly to avoid Wikipedia errors
        with DDGS() as ddgs:
            results = []
            # Get text results (not Wikipedia)
            for r in ddgs.text(query, max_results=5):
                title = r.get('title', '')
                body = r.get('body', '')
                url = r.get('href', '')
                if title and body:
                    results.append(f"{title}\n{body}\nSource: {url}")
            
            if results:
                result_text = "\n\n---\n\n".join(results)
                _report_progress(
                    f"Found {len(results)} search results",
                    agent="Research Agent",
                    tool="search_web",
                    target=f"{len(results)} results retrieved"
                )
                return result_text
            else:
                _report_progress(
                    f"No results found for search query",
                    agent="Research Agent",
                    tool="search_web",
                    target="No results"
                )
                return "No search results found. Try a different query."
                
    except Exception as e:
        logger.error(f"Error in web search: {e}")
        _report_progress(
            f"Search error occurred",
            agent="Research Agent",
            tool="search_web",
            target=f"Error: {str(e)[:50]}"
        )
        return f"Error searching the web: {str(e)}"


@tool
def scrape_website(url: str) -> str:
    """
    Scrape content from a website URL.
    
    IMPORTANT: This tool is for URLs only (e.g., "https://maven.com/courses").
    Do NOT use this tool with search queries. If you need to search, use search_web instead.
    
    This tool extracts the main text content from a webpage, useful for
    analyzing competitor websites, product pages, or blog posts.
    
    Args:
        url: Full URL of the website to scrape (must include http:// or https://)
             DO NOT pass search queries here - use search_web for queries.
    
    Returns:
        Extracted text content from the webpage
    """
    try:
        logger.info(f"Scraping website: {url}")
        _report_progress(
            f"Scraping website content",
            agent="Research Agent",
            tool="scrape_website",
            target=url
        )
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            return f"Error: Invalid URL format. URL must start with http:// or https://"
        
        # Use WebBaseLoader from LangChain
        loader = WebBaseLoader(url)
        docs = loader.load()
        
        if docs and len(docs) > 0:
            content = docs[0].page_content
            # Limit content length to avoid token limits
            max_length = 5000
            if len(content) > max_length:
                content = content[:max_length] + "... [content truncated]"
            _report_progress(
                f"Successfully scraped {len(content)} characters",
                agent="Research Agent",
                tool="scrape_website",
                target=url
            )
            return content
        else:
            _report_progress(
                f"No content found on webpage",
                agent="Research Agent",
                tool="scrape_website",
                target=url
            )
            return "No content found on the webpage"
            
    except Exception as e:
        logger.error(f"Error scraping website {url}: {e}")
        _report_progress(
            f"Scraping error occurred",
            agent="Research Agent",
            tool="scrape_website",
            target=f"Error: {str(e)[:50]}"
        )
        return f"Error scraping website: {str(e)}"


def get_all_tools() -> List:
    """
    Get all available tools for competitor analysis agents.
    
    Returns:
        List of tool objects that can be used by LangChain agents
    """
    return [
        search_web,
        scrape_website
    ]

