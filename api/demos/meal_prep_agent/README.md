# 30-Day Meal Prep Agent: Your Personalized Healthy Eating Assistant

## 🎯 Learning Objectives

This demo teaches you how to build a real-world meal prep assistant with human-in-the-loop:

1. **Human-in-the-Loop Pattern** - How to integrate human oversight and approval at each step
2. **AutoGen Integration** - How to build agents that request human approval
3. **Step-by-Step Workflows** - How to manage multi-step processes with interruption capability
4. **PDF Generation** - How to export final meal plans as downloadable PDFs
5. **Production Patterns** - How to structure approval systems for meal planning applications

## 📚 Real-World Use Case

A 30-Day Meal Prep Agent that helps users create personalized meal plans:
- Collects dietary preferences, restrictions, and goals through conversation
- Generates meal suggestions step-by-step using function calling
- Requests human approval at each step (preferences, meal selection, final plan)
- Allows users to interrupt, modify, or redo any step
- Exports final approved meal plan as PDF

## 🏗️ Architecture Overview

```
User → Chat Interface → AutoGen Agent → Tools → Human Approval → PDF Export
```

### Key Components

1. **AutoGen Agent** - Conversational AI agent that orchestrates the meal planning workflow
2. **Meal Planning Tools** - Functions for meal suggestions, nutrition calculation, shopping lists
3. **Approval System** - Human-in-the-loop workflow for step-by-step approval
4. **PDF Generator** - Exports final meal plans as downloadable PDFs

## 📖 Code Structure

```
meal_prep_agent/
├── main.py          # Main API with AutoGen agent, tools, and endpoints
└── README.md        # This file
```

### Key Files

- `main.py`: Contains all the logic:
  - Data models (Pydantic)
  - Meal planning tools
  - AutoGen agent setup
  - Approval workflow
  - PDF generation
  - API endpoints

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- FastAPI
- AutoGen AgentChat
- ReportLab (for PDF generation)

### Installation

1. Install dependencies:
```bash
pip install fastapi autogen-agentchat[openai] reportlab
```

2. Set up environment variables (see `env.example`)

3. Run the API:
```bash
python -m uvicorn main:app --reload
```

### API Endpoints

- `POST /meal-prep/chat/stream` - Chat with the meal prep assistant (streaming)
- `GET /meal-prep/approvals` - List all pending approvals
- `GET /meal-prep/approvals/{approval_id}` - Get approval details
- `POST /meal-prep/approvals/{approval_id}/review` - Review and approve/reject a step
- `GET /meal-prep/plans/{plan_id}` - Get meal plan details
- `GET /meal-prep/plans/{plan_id}/pdf` - Download meal plan as PDF
- `GET /meal-prep/health` - Health check

## 🔄 Workflow

### Step 1: Collect Preferences
- Agent asks about dietary preferences, restrictions, goals
- User provides information through conversation
- Agent requests approval for collected preferences

### Step 2: Generate Meal Suggestions
- Agent uses `get_dietary_meal_suggestions()` to suggest meals
- Filters meals based on preferences and restrictions
- Presents meal options for each meal type (breakfast, lunch, dinner, snack)
- Requests approval for meal selections

### Step 3: Calculate Nutrition
- Agent uses `calculate_daily_nutrition()` to verify nutrition goals
- Compares calculated values with user goals
- Requests approval for nutrition plan

### Step 4: Create Shopping List
- Agent uses `generate_shopping_list()` to create shopping list
- Aggregates ingredients from selected meals
- Requests approval for shopping list

### Step 5: Final Plan Review
- Agent compiles all information into final meal plan
- Requests final approval
- Once approved, plan is saved and can be downloaded as PDF

## 🛠️ Key Concepts

### Human-in-the-Loop Pattern

The agent performs actions but requires human approval at each critical step:

```python
# Agent requests approval
approval_id = request_human_approval(
    step_name="meal_selection",
    step_number=2,
    content={"meals": selected_meals},
    session_id=session_id
)

# Human reviews and approves/rejects
# Agent continues based on decision
```

### Function Calling

The agent uses tools to:
- Get meal suggestions: `get_dietary_meal_suggestions()`
- Calculate nutrition: `calculate_daily_nutrition()`
- Generate shopping lists: `generate_shopping_list()`
- Request approvals: `request_human_approval()`

### Step Interruption

Users can:
- Reject any step and provide feedback
- Request modifications
- Restart from any point
- Skip or redo steps

## 📝 Example Usage

### Starting a Meal Plan

```python
# User starts conversation
POST /meal-prep/chat/stream
{
  "message": "I want to create a 30-day meal plan. I'm vegetarian and need 2000 calories per day.",
  "session_id": "session_123"
}
```

### Approving a Step

```python
POST /meal-prep/approvals/{approval_id}/review
{
  "approval_id": "approval_123",
  "decision": "approve",
  "feedback": "Looks good!"
}
```

### Downloading PDF

```python
GET /meal-prep/plans/{plan_id}/pdf
# Returns PDF file for download
```

## 🎓 Learning Challenges

### Challenge 1: Add More Dietary Options
**Difficulty:** Easy

Add support for more dietary preferences:
- Keto diet
- Paleo diet
- Mediterranean diet
- Low-carb diet

**Steps:**
1. Extend the `MEAL_DATABASE` with more meal options
2. Update `get_dietary_meal_suggestions()` to handle new preferences
3. Test with different dietary requirements

### Challenge 2: Add Meal Prep Schedule
**Difficulty:** Medium

Create a meal prep schedule that shows:
- Which meals to prep on which days
- Prep day recommendations
- Storage instructions

**Steps:**
1. Add a new tool `generate_prep_schedule()`
2. Create logic to distribute meals across prep days
3. Add schedule to approval workflow
4. Include schedule in PDF export

### Challenge 3: Add Recipe Details
**Difficulty:** Medium

Expand meal database to include:
- Full recipe instructions
- Cooking times
- Serving sizes
- Ingredient quantities

**Steps:**
1. Extend meal database structure
2. Add recipe display in approval UI
3. Include recipes in PDF export

### Challenge 4: Add Budget Tracking
**Difficulty:** Medium

Implement budget tracking:
- Calculate estimated costs per meal
- Track weekly/monthly budget
- Suggest cost-effective alternatives

**Steps:**
1. Add price data to meal database
2. Create `calculate_meal_costs()` tool
3. Add budget validation in approval workflow
4. Display budget info in PDF

### Challenge 5: Add Nutrition Goals Validation
**Difficulty:** Hard

Implement advanced nutrition validation:
- Macro and micronutrient tracking
- Daily/weekly nutrition balance
- Goal achievement tracking
- Nutritional recommendations

**Steps:**
1. Expand nutrition calculation to include micronutrients
2. Add validation logic for nutrition goals
3. Create recommendations for adjustments
4. Add nutrition charts to PDF

### Challenge 6: Add Meal Plan Variations
**Difficulty:** Hard

Allow users to:
- Generate multiple plan variations
- Compare different plans
- Mix and match meals from different plans

**Steps:**
1. Modify agent to generate multiple variations
2. Create comparison tool
3. Add plan selection to approval workflow
4. Support plan merging

## 🔍 Key Implementation Details

### Approval Workflow

```python
# Agent creates approval request
approval_id = request_human_approval(
    step_name="meal_selection",
    step_number=2,
    content={"meals": meals},
    session_id=session_id
)

# Approval stored in pending_approvals
pending_approvals[approval_id] = {
    "approval_id": approval_id,
    "step_name": "meal_selection",
    "step_number": 2,
    "content": {"meals": meals},
    "status": "pending",
    ...
}

# Human reviews and makes decision
# Agent continues based on approval/rejection
```

### PDF Generation

```python
def generate_meal_plan_pdf(plan: Dict[str, Any]) -> BytesIO:
    # Create PDF using ReportLab
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Add content: preferences, meals, nutrition, shopping list
    # Return PDF buffer
```

### Tool Execution

```python
# Agent decides to call tool
meals = get_dietary_meal_suggestions(
    meal_type="breakfast",
    dietary_preferences=["vegetarian"],
    dietary_restrictions=["gluten-free"],
    calorie_range=(300, 400)
)

# Tool returns filtered meal suggestions
# Agent incorporates results into response
```

## 🐛 Common Issues & Solutions

### Issue: Agent not requesting approvals
**Solution:** Ensure `request_human_approval()` is called after each step in the agent's system message.

### Issue: PDF generation fails
**Solution:** Check that ReportLab is installed: `pip install reportlab`

### Issue: Meals not filtering correctly
**Solution:** Verify dietary restrictions are properly checked in `get_dietary_meal_suggestions()`

## 📚 Further Reading

- [AutoGen Documentation](https://microsoft.github.io/autogen/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- Human-in-the-Loop AI Patterns
- Function Calling Best Practices

## 🤔 Questions to Consider

- How would you handle partial approvals (approve some meals but not others)?
- How could you add meal plan persistence across sessions?
- What additional validation would you add before final approval?
- How would you implement meal plan sharing between users?
- What analytics would you track for meal planning insights?

## ✅ Checklist

After implementing this demo, you should understand:

- ✓ How to build human-in-the-loop workflows with AutoGen
- ✓ How to request and handle human approvals
- ✓ How to create step-by-step workflows with interruption capability
- ✓ How to generate PDFs from structured data
- ✓ How to structure approval systems for production use
- ✓ How to use function calling for meal planning tools
- ✓ How to handle user feedback and modifications

## 🚀 Next Steps

1. Add more meal options to the database
2. Implement meal plan persistence (database storage)
3. Add user authentication and meal plan history
4. Implement meal plan sharing features
5. Add nutrition tracking and analytics
6. Create mobile app integration
7. Add meal prep video tutorials
8. Implement grocery delivery integration

