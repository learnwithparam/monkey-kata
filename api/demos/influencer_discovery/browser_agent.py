"""
Influencer Discovery Browser Agent
==================================

🎯 LEARNING OBJECTIVES:
This module teaches you how to build browser automation agents:

1. Browser Automation - Using browser_use to control web browsers
2. Web Search Integration - Using DuckDuckGo for open-source search
3. Structured Output - Extracting structured data from web pages
4. Agentic Navigation - AI agents navigating and extracting data from websites

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Setup - Import libraries and configure browser
Step 2: Search Tools - Create web search tools using DuckDuckGo
Step 3: Browser Agent - Create agent with browser automation capabilities
Step 4: Structured Extraction - Extract influencer profiles with validation

Key Concept: This demo shows how AI agents can autonomously navigate the web,
search for information, and extract structured data from websites.
"""

import asyncio
import logging
import json
from typing import List, Optional, Dict, Any, Callable
from pydantic import BaseModel, Field

from .models import InfluencerProfile, DiscoveryRequest
from ddgs import DDGS

logger = logging.getLogger(__name__)

# Global callback for progress updates
_progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None


def set_progress_callback(callback: Optional[Callable[[Dict[str, Any]], None]]):
    """Set a callback function to report progress updates"""
    global _progress_callback
    _progress_callback = callback


def _report_progress(message: str, step: str = None, data: Dict[str, Any] = None):
    """Report progress if callback is set"""
    if _progress_callback:
        try:
            progress_data = {
                "message": message,
                "step": step,
                **(data or {})
            }
            _progress_callback(progress_data)
        except Exception as e:
            logger.warning(f"Error in progress callback: {e}")


async def search_web_for_influencers(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search the web using DuckDuckGo for influencer-related queries.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        
    Returns:
        List of search results with title, body, and URL
    """
    try:
        logger.info(f"Searching web for: {query}")
        _report_progress(f"Searching: {query}", "search", {"query": query})
        
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title = r.get('title', '')
                body = r.get('body', '')
                url = r.get('href', '')
                if title and body:
                    results.append({
                        "title": title,
                        "body": body,
                        "url": url
                    })
        
        _report_progress(
            f"Found {len(results)} search results",
            "search_complete",
            {"count": len(results)}
        )
        return results
        
    except Exception as e:
        logger.error(f"Error in web search: {e}")
        _report_progress(f"Search error: {str(e)}", "search_error")
        return []


async def discover_influencers_agentic(
    request: DiscoveryRequest,
    provider=None
) -> List[InfluencerProfile]:
    """
    Agentic influencer discovery using LLM to analyze search results and extract profiles.
    
    This function:
    1. Searches for influencers based on criteria
    2. Uses LLM to analyze results and extract structured data
    3. Validates and returns influencer profiles
    
    Args:
        request: Discovery request with criteria
        provider: Optional LLM provider (uses default if not provided)
        
    Returns:
        List of InfluencerProfile objects
    """
    try:
        _report_progress("Starting influencer discovery", "start")
        
        # Get LLM provider
        if provider is None:
            from utils.llm_provider import get_llm_provider
            provider = get_llm_provider()
        
        # Build search queries
        keywords_str = ", ".join(request.content_keywords)
        search_queries = [
            f"Indian Instagram influencers {keywords_str} {request.location}",
            f"Instagram creators {keywords_str} India {request.min_followers} followers",
            f"Tech influencers India Instagram {keywords_str}",
        ]
        
        all_search_results = []
        for query in search_queries:
            _report_progress(f"Searching: {query}", "searching", {"query": query})
            results = await search_web_for_influencers(query, max_results=5)
            all_search_results.extend(results)
            await asyncio.sleep(1)  # Rate limiting
        
        if not all_search_results:
            _report_progress("No search results found", "error")
            return []
        
        # Use LLM to extract influencer profiles from search results
        _report_progress("Analyzing search results", "analyzing")
        
        # Format search results for LLM
        results_text = "\n\n".join([
            f"Title: {r['title']}\nContent: {r['body']}\nURL: {r['url']}"
            for r in all_search_results[:15]  # Limit to avoid token limits
        ])
        
        # Create prompt for LLM to extract influencer profiles
        prompt = f"""You are an AI assistant helping to find Indian Instagram influencers for collaboration.

Search Criteria:
- Location: {request.location}
- Minimum followers: {request.min_followers}
- Maximum followers: {request.max_followers or 'No limit'}
- Content focus: {', '.join(request.content_keywords)}
- Number needed: {request.count}
- Platform: https://learnwithparam.com

Search Results:
{results_text}

Task:
1. Analyze the search results above
2. Extract Instagram influencer profiles that match the criteria
3. For each influencer, try to determine:
   - Instagram username (extract from URLs or content)
   - Profile URL (construct from username if needed)
   - Estimated follower count (if mentioned)
   - Content focus (AI, tech, etc.)
   - Whether they have their own platform (look for mentions of personal websites, courses, etc.)
   - Collaboration potential (assess based on content and follower count)

Important:
- Only include influencers with at least {request.min_followers} followers
- Focus on those who create content about {', '.join(request.content_keywords)}
- Prefer influencers who don't have their own major platform (no personal courses/websites)
- Extract up to {request.count} profiles
- If username is not clear, try to extract it from URLs or content

Return a JSON array of influencer profiles in this format:
[
  {{
    "username": "instagram_username",
    "profile_url": "https://www.instagram.com/username/",
    "follower_count": 15000,
    "bio": "Brief bio if available",
    "content_focus": "AI and technology",
    "has_own_platform": false,
    "collaboration_potential": "High - creates tech content, no personal platform",
    "location": "India"
  }}
]

Return ONLY valid JSON, no additional text."""
        
        # Get LLM response
        response_text = await provider.generate_text(prompt)
        
        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            profiles_data = json.loads(response_text)
            
            # Convert to InfluencerProfile objects
            profiles = []
            for profile_data in profiles_data[:request.count]:
                try:
                    profile = InfluencerProfile(**profile_data)
                    profiles.append(profile)
                except Exception as e:
                    logger.warning(f"Error parsing profile: {e}, data: {profile_data}")
                    continue
            
            _report_progress(
                f"Found {len(profiles)} influencer profiles",
                "complete",
                {"count": len(profiles)}
            )
            
            return profiles
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            _report_progress("Error parsing LLM response", "error", {"error": str(e)})
            return []
            
    except Exception as e:
        logger.error(f"Error in influencer discovery: {e}", exc_info=True)
        _report_progress(f"Discovery error: {str(e)}", "error")
        return []


async def discover_influencers_with_browser(
    request: DiscoveryRequest,
    provider=None
) -> List[InfluencerProfile]:
    """
    Discover influencers using browser automation (future enhancement).
    
    This is a placeholder for browser-based discovery using browser_use.
    For now, we use the agentic search approach.
    
    Args:
        request: Discovery request with criteria
        provider: Optional LLM provider
        
    Returns:
        List of InfluencerProfile objects
    """
    # For now, use the agentic approach
    # In the future, this could use browser_use to navigate Instagram directly
    return await discover_influencers_agentic(request, provider)

