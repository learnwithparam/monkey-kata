# Personal Shopping Assistant

## 🎯 Learning Objectives

This demo teaches you how to build a shopping assistant with agent memory:

1. **Agent Memory** - Storing and retrieving user preferences and shopping history
2. **Recommendation Systems** - Generating personalized product recommendations
3. **Multi-Agent Coordination** - Search, comparison, and recommendation agents working together
4. **Context Building** - Using memory to build context for personalized recommendations

## 📚 Key Concepts

### Agent Memory
The system remembers:
- User preferences (budget, style, brands, etc.)
- Shopping history (past searches and selections)
- Product interests (categories and features user likes)

### Multi-Agent System
Three specialized agents:
1. **Product Search Agent** - Searches for products matching queries
2. **Comparison Agent** - Compares products based on features and reviews
3. **Recommendation Agent** - Generates personalized recommendations

### Recommendation Process
1. User submits product query
2. System retrieves user preferences from memory
3. Search agent finds products
4. Comparison agent analyzes products
5. Recommendation agent generates personalized recommendations
6. Preferences and history updated

## 🏗️ Architecture

```
User Query
    ↓
Memory Retrieval (Preferences & History)
    ↓
Product Search Agent
    ↓
Comparison Agent
    ↓
Recommendation Agent (with memory context)
    ↓
Personalized Recommendations
    ↓
Memory Update
```

## 📁 File Structure

- `main.py` - FastAPI router with endpoints
- `shopping_agents.py` - Agent definitions and workflow
- `tools.py` - Web search and product analysis tools
- `memory.py` - Memory system for preferences and history
- `README.md` - This file

## 🚀 Usage

### API Endpoints

1. **POST /personal-shopping/get-recommendations**
   - Get product recommendations
   - Body: `{ "user_query": "wireless headphones", "budget": "under $100", "preferences": {...} }`
   - Returns: `{ "session_id": "...", "status": "processing" }`

2. **GET /personal-shopping/status/{session_id}**
   - Check recommendation status
   - Returns: `{ "status": "processing|completed|error", "message": "..." }`

3. **GET /personal-shopping/result/{session_id}**
   - Get final recommendations
   - Returns: `{ "recommendations": "...", "user_preferences": {...} }`

4. **POST /personal-shopping/update-preferences**
   - Update user preferences
   - Body: `{ "user_id": "user123", "preferences": {"budget": "under $200", "brand": "Sony"} }`

5. **GET /personal-shopping/preferences/{user_id}**
   - Get user preferences and history

## 🔧 Implementation Details

### Memory System
- Stores preferences in JSON file (in production, use database)
- Tracks shopping history (last 50 interactions)
- Maintains product interests by category
- Builds context string for agents

### Agents
- Each agent receives memory context
- Agents use different temperature settings
- Search and comparison agents have web tools
- Recommendation agent uses only LLM (no tools)

### Workflow
1. User submits query with optional preferences
2. Background task starts
3. Memory retrieved and context built
4. Search agent finds products
5. Comparison agent analyzes products
6. Recommendation agent generates personalized recommendations
7. Results stored in session
8. Memory updated with interaction

## 🎓 Challenges

### Challenge 1: Persistent Memory
Replace file-based memory with a database (SQLite, PostgreSQL).

**Hint:** Use SQLAlchemy or similar ORM for database operations.

### Challenge 2: Product Database
Add a local product database instead of only web search.

**Hint:** Create a product schema and store products locally.

### Challenge 3: Collaborative Filtering
Add collaborative filtering based on similar users' preferences.

**Hint:** Track which products users select and find patterns.

### Challenge 4: Price Tracking
Track product prices over time and alert on price drops.

**Hint:** Store price history and compare current vs. historical prices.

## 🔍 Key Code Patterns

### Memory Usage
```python
memory = get_memory(user_id)
memory.update_preference("budget", "under $100")
context = memory.build_context()
```

### Agent with Memory
```python
def create_recommendation_agent(memory_context: str):
    prompt = f"""User Context:
{memory_context}
..."""
```

### Multi-Agent Workflow
```python
# Search
search_result = await search_agent.ainvoke({"input": query})

# Compare
comparison_result = await comparison_agent.ainvoke({"input": comparison_prompt})

# Recommend
recommendation_result = await recommendation_agent.ainvoke({"input": rec_prompt})
```

## 📖 Related Concepts

- **Agent Memory**: Storing and retrieving user information
- **Recommendation Systems**: Generating personalized suggestions
- **Multi-Agent Coordination**: Agents working together
- **Context Building**: Using memory to build agent context

## 🐛 Troubleshooting

### Issue: Memory not persisting
- Check file permissions for memory file
- Verify memory file path is writable
- Check if user_id is consistent

### Issue: Recommendations not personalized
- Verify preferences are being stored
- Check memory context is being passed to agents
- Ensure agents are using memory context in prompts

### Issue: Search returns no results
- Check internet connection
- Verify DuckDuckGo is accessible
- Try different search query format

