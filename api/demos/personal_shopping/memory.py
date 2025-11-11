"""
Shopping Agent Memory
=====================

🎯 LEARNING OBJECTIVES:
This module teaches you how to implement agent memory:

1. User Preference Storage - How to store and retrieve user preferences
2. Shopping History - How to track past shopping interactions
3. Memory Retrieval - How to use stored preferences in recommendations
4. Context Building - How to build context from memory for agents

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Memory Storage - Store user preferences and history
Step 2: Memory Retrieval - Retrieve relevant preferences
Step 3: Context Building - Build context for agents
Step 4: Memory Updates - Update preferences based on interactions

Key Concept: Agent memory allows the system to remember user preferences
and shopping history, enabling personalized recommendations over time.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ShoppingMemory:
    """
    Memory system for shopping assistant.
    
    Stores:
    - User preferences (budget, style, brands, etc.)
    - Shopping history (past searches, purchases, recommendations)
    - Product interests (categories, features user likes)
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.preferences: Dict[str, Any] = {}
        self.shopping_history: List[Dict[str, Any]] = []
        self.product_interests: Dict[str, List[str]] = {}
        self.memory_file = Path(f"/tmp/shopping_memory_{user_id}.json")
        self._load_memory()
    
    def _load_memory(self):
        """Load memory from file if it exists"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.preferences = data.get("preferences", {})
                    self.shopping_history = data.get("shopping_history", [])
                    self.product_interests = data.get("product_interests", {})
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
    
    def _save_memory(self):
        """Save memory to file"""
        try:
            data = {
                "preferences": self.preferences,
                "shopping_history": self.shopping_history,
                "product_interests": self.product_interests
            }
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def update_preference(self, key: str, value: Any):
        """Update a user preference"""
        self.preferences[key] = value
        self._save_memory()
        logger.info(f"Updated preference: {key} = {value}")
    
    def get_preferences(self) -> Dict[str, Any]:
        """Get all user preferences"""
        return self.preferences.copy()
    
    def add_to_history(self, search_query: str, recommendations: List[Dict], selected_product: Optional[str] = None):
        """Add a shopping interaction to history"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "search_query": search_query,
            "recommendations": recommendations,
            "selected_product": selected_product
        }
        self.shopping_history.append(entry)
        # Keep only last 50 entries
        if len(self.shopping_history) > 50:
            self.shopping_history = self.shopping_history[-50:]
        self._save_memory()
    
    def get_recent_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent shopping history"""
        return self.shopping_history[-limit:] if len(self.shopping_history) > limit else self.shopping_history
    
    def update_interests(self, category: str, interests: List[str]):
        """Update product interests for a category"""
        if category not in self.product_interests:
            self.product_interests[category] = []
        self.product_interests[category].extend(interests)
        # Remove duplicates
        self.product_interests[category] = list(set(self.product_interests[category]))
        self._save_memory()
    
    def get_interests(self, category: Optional[str] = None) -> Dict[str, List[str]]:
        """Get product interests, optionally filtered by category"""
        if category:
            return {category: self.product_interests.get(category, [])}
        return self.product_interests.copy()
    
    def build_context(self) -> str:
        """Build context string from memory for agent use"""
        context_parts = []
        
        if self.preferences:
            context_parts.append("User Preferences:")
            for key, value in self.preferences.items():
                context_parts.append(f"  - {key}: {value}")
        
        recent_history = self.get_recent_history(3)
        if recent_history:
            context_parts.append("\nRecent Shopping History:")
            for entry in recent_history:
                context_parts.append(f"  - Searched: {entry['search_query']}")
                if entry.get('selected_product'):
                    context_parts.append(f"    Selected: {entry['selected_product']}")
        
        if self.product_interests:
            context_parts.append("\nProduct Interests:")
            for category, interests in self.product_interests.items():
                context_parts.append(f"  - {category}: {', '.join(interests[:5])}")
        
        return "\n".join(context_parts) if context_parts else "No previous preferences or history."


# Global memory instances (in production, use a database)
_memory_instances: Dict[str, ShoppingMemory] = {}


def get_memory(user_id: str = "default") -> ShoppingMemory:
    """Get or create memory instance for a user"""
    if user_id not in _memory_instances:
        _memory_instances[user_id] = ShoppingMemory(user_id)
    return _memory_instances[user_id]

