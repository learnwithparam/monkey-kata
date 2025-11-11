"""
Shopping Agent Tools
====================

🎯 LEARNING OBJECTIVES:
This module teaches you how to create tools for shopping agents:

1. Web Search Tool - Search for products using DuckDuckGo
2. Product Comparison Tool - Compare multiple products
3. Recommendation Tool - Generate personalized recommendations

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Web Search Tool - Search for products
Step 2: Product Analysis Tool - Analyze product information
Step 3: Comparison Tool - Compare products

Key Concept: Tools extend agent capabilities, allowing them to search the web,
analyze products, and make recommendations based on user preferences.
"""

import logging
from typing import List, Dict, Any
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Initialize DuckDuckGo search tool
duckduckgo_search = DuckDuckGoSearchRun()


@tool
def search_products(query: str) -> str:
    """
    Search for products on the web.
    
    This tool searches the internet for products matching the query.
    Use this to find product information, reviews, and prices.
    
    Args:
        query: Search query (e.g., "best wireless headphones under $100")
    
    Returns:
        Search results as a formatted string
    """
    try:
        logger.info(f"Searching for products: {query}")
        results = duckduckgo_search.run(query)
        return results
    except Exception as e:
        logger.error(f"Error in product search: {e}")
        return f"Error searching for products: {str(e)}"


@tool
def compare_products(product_names: List[str], criteria: str) -> str:
    """
    Compare multiple products based on specified criteria.
    
    This tool searches for information about each product and compares them.
    
    Args:
        product_names: List of product names to compare
        criteria: What to compare (e.g., "price, features, reviews")
    
    Returns:
        Comparison results as a formatted string
    """
    try:
        logger.info(f"Comparing products: {product_names}")
        
        all_results = []
        for product in product_names:
            query = f"{product} {criteria} review comparison"
            results = search_products(query)
            all_results.append(f"Product: {product}\n{results}\n")
        
        combined = "\n---\n".join(all_results)
        return f"Product Comparison:\n\n{combined}"
        
    except Exception as e:
        logger.error(f"Error comparing products: {e}")
        return f"Error comparing products: {str(e)}"


@tool
def analyze_product(product_name: str, focus_areas: List[str]) -> str:
    """
    Analyze a specific product in detail.
    
    This tool searches for comprehensive information about a product,
    focusing on the specified areas.
    
    Args:
        product_name: Name of the product to analyze
        focus_areas: List of areas to focus on (e.g., ["price", "features", "reviews"])
    
    Returns:
        Detailed product analysis
    """
    try:
        logger.info(f"Analyzing product: {product_name}")
        
        focus_str = " ".join(focus_areas)
        query = f"{product_name} {focus_str} detailed review"
        results = search_products(query)
        
        return f"Product Analysis for {product_name}:\n\n{results}"
        
    except Exception as e:
        logger.error(f"Error analyzing product: {e}")
        return f"Error analyzing product: {str(e)}"


def get_all_tools() -> List:
    """Get all available shopping tools"""
    return [
        search_products,
        compare_products,
        analyze_product
    ]

