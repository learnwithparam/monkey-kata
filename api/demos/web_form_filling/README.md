# Web Form Filling AI Bot

## 🎯 Learning Objectives

This demo teaches you how to build a browser automation agent that can:

1. **Browser Automation** - Using Playwright to control browsers programmatically
2. **Tool Calling** - Agents use browser tools to interact with web pages
3. **Workflow Orchestration** - Coordinating navigation, detection, filling, and submission
4. **Form Field Detection** - Identifying and matching form fields automatically

## 📚 Key Concepts

### Browser Automation
Agents can control browsers using Playwright:
- Navigate to URLs
- Detect form fields
- Fill input fields
- Submit forms

### Tool Calling
The agent uses specialized tools:
- `navigate_to_url()` - Navigate to a webpage
- `detect_form_fields()` - Find all form fields on a page
- `fill_form()` - Fill form fields with data
- `submit_form()` - Submit the completed form

### Workflow Orchestration
The system coordinates multiple steps:
1. Navigate to URL
2. Detect form fields
3. Match data to fields
4. Fill form
5. Submit (optional)

## 🏗️ Architecture

```
User Request
    ↓
FastAPI Endpoint
    ↓
Background Task
    ↓
Form Filling Agent
    ↓
Browser Tools (Playwright)
    ↓
Web Page
```

## 📁 File Structure

- `main.py` - FastAPI router with endpoints
- `form_agent.py` - Agent definition and workflow
- `browser_tools.py` - Playwright browser automation tools
- `README.md` - This file

## 🚀 Usage

### API Endpoints

1. **POST /web-form-filling/fill-form**
   - Start form filling workflow
   - Body: `{ "url": "https://example.com/form", "form_data": {"name": "John", "email": "john@example.com"}, "auto_submit": false }`
   - Returns: `{ "session_id": "...", "status": "processing" }`

2. **GET /web-form-filling/status/{session_id}**
   - Check form filling status
   - Returns: `{ "status": "processing|completed|error", "message": "..." }`

3. **GET /web-form-filling/result/{session_id}**
   - Get final form filling result
   - Returns: `{ "status": "success", "form_filling": "...", "submitted": true }`

## 🔧 Implementation Details

### Browser Tools
- Uses Playwright for browser automation
- Headless browser mode for server-side execution
- Automatic form field detection
- Field matching by id, name, or label

### Agent
- Single agent with browser automation tools
- Lower temperature (0.2) for deterministic behavior
- Step-by-step workflow execution
- Error handling and status reporting

### Workflow
1. User submits form filling request
2. Background task starts
3. Agent navigates to URL
4. Agent detects form fields
5. Agent fills form with provided data
6. Agent optionally submits form
7. Results stored in session

## 🎓 Challenges

### Challenge 1: Add Screenshot Capture
Add functionality to capture screenshots before and after form filling.

**Hint:** Use Playwright's `page.screenshot()` method.

### Challenge 2: Handle CAPTCHA
Detect and handle CAPTCHA challenges on forms.

**Hint:** Add a tool to detect CAPTCHA elements and pause for manual solving.

### Challenge 3: Multi-Step Forms
Support forms that span multiple pages.

**Hint:** Track form state across page navigations.

### Challenge 4: Form Validation
Add validation to check if form was filled correctly before submission.

**Hint:** Re-detect form fields after filling and verify values.

## 🔍 Key Code Patterns

### Tool Definition
```python
@tool
async def fill_form(url: str, form_data: Dict[str, str]) -> str:
    """Fill a form on a webpage."""
    # Browser automation code
```

### Agent Creation
```python
def create_form_filling_agent() -> AgentExecutor:
    llm = get_llm(temperature=0.2)
    tools = get_all_tools()
    # ... create agent with tools
```

### Workflow Execution
```python
# Navigate
nav_result = await agent.ainvoke({"input": f"Navigate to {url}"})

# Detect fields
detect_result = await agent.ainvoke({"input": "Detect form fields"})

# Fill form
fill_result = await agent.ainvoke({"input": fill_prompt})
```

## 📖 Related Concepts

- **Browser Automation**: Controlling browsers programmatically
- **Tool Calling**: Agents using tools to extend capabilities
- **Workflow Orchestration**: Coordinating multiple steps
- **Form Interaction**: Detecting and filling web forms

## 🐛 Troubleshooting

### Issue: Browser not launching
- Install Playwright browsers: `playwright install chromium`
- Check if running in headless mode
- Verify system dependencies

### Issue: Form fields not detected
- Check if page loaded completely
- Verify form fields are visible (not hidden)
- Some forms load dynamically (may need wait)

### Issue: Field matching fails
- Try using exact field id or name
- Check field labels match expected format
- Some fields may have dynamic identifiers

### Issue: Form submission fails
- Verify submit button selector
- Check if form requires validation first
- Some forms use JavaScript submission

