import json
import os
from typing import List, Dict, Any

# Load data on module import
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "travel_data.json")

def load_data() -> Dict[str, Any]:
    with open(DATA_PATH, "r") as f:
        return json.load(f)

# Global data cache
TRAVEL_DATA = load_data()

def get_bookings() -> Dict[str, Any]:
    return TRAVEL_DATA.get("bookings", {})

def get_hotels() -> Dict[str, List[Dict[str, Any]]]:
    return TRAVEL_DATA.get("hotels", {})

def get_flights() -> Dict[str, Any]:
    return TRAVEL_DATA.get("flights", {})

def search_policies_rag(query: str) -> str:
    """
    Simple RAG implementation using keyword matching.
    In a real production system, this would use vector embeddings (e.g., ChromaDB, Qdrant).
    """
    policies = TRAVEL_DATA.get("policies", [])
    query_terms = set(query.lower().split())
    
    scored_policies = []
    
    for policy in policies:
        text = policy["text"]
        text_lower = text.lower()
        score = 0
        for term in query_terms:
            if term in text_lower:
                score += 1
        
        if score > 0:
            scored_policies.append((score, text))
    
    # Sort by score descending
    scored_policies.sort(key=lambda x: x[0], reverse=True)
    
    if not scored_policies:
        return "No specific policy found matching your query."
    
    # Return top 2 relevant policies
    top_policies = [p[1] for p in scored_policies[:2]]
    return "Here are the relevant policy details:\n\n" + "\n\n".join(top_policies)
