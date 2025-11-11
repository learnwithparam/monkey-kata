# Legal Case Intake Workflow

## 🎯 Learning Objectives

This demo teaches you how to build a multi-agent system with human-in-the-loop:

1. **Multi-Agent Coordination** - Intake and Review agents work together
2. **Human-in-the-Loop** - Lawyer review and approval workflow
3. **Workflow Orchestration** - Coordinating intake, analysis, and review
4. **Context Preservation** - Maintaining case information across workflow stages

## 📚 Key Concepts

### Multi-Agent Coordination
Two specialized agents work together:
1. **Intake Agent** - Validates and structures case information
2. **Review Agent** - Analyzes case and provides recommendations

### Human-in-the-Loop
The workflow includes human oversight:
- AI agents process initial intake
- AI generates summary and recommendations
- Human lawyer reviews and makes final decision
- Decision flows back into the system

### Workflow Stages
1. **Intake** - Client submits case information
2. **Processing** - AI agents analyze the case
3. **Pending Lawyer** - Ready for human review
4. **Review** - Lawyer reviews and decides
5. **Final** - Approved, rejected, or needs more info

## 🏗️ Architecture

```
Client Submission
    ↓
Intake Agent (Validation)
    ↓
Review Agent (Analysis)
    ↓
Lawyer Review (Human)
    ↓
Final Decision
```

## 📁 File Structure

- `main.py` - FastAPI router with endpoints
- `intake_agents.py` - Agent definitions and workflow
- `models.py` - Data models for cases
- `README.md` - This file

## 🚀 Usage

### API Endpoints

1. **POST /legal-case-intake/submit-case**
   - Submit a new case for intake
   - Body: Case intake information (client name, email, case type, description, etc.)
   - Returns: `{ "case_id": "...", "status": "processing" }`

2. **GET /legal-case-intake/status/{case_id}**
   - Check case processing status
   - Returns: `{ "status": "processing|pending_lawyer|approved|rejected", "message": "..." }`

3. **GET /legal-case-intake/review/{case_id}**
   - Get case ready for lawyer review
   - Returns: Case with AI summary and recommendations

4. **POST /legal-case-intake/review/{case_id}**
   - Submit lawyer review and decision
   - Body: `{ "lawyer_notes": "...", "lawyer_decision": "approve|reject|request_info" }`
   - Returns: Updated case with lawyer decision

## 🔧 Implementation Details

### Agents
- **Intake Agent**: Validates case information, structures data
- **Review Agent**: Analyzes case, assesses risks, provides recommendations
- Both agents use CrewAI for coordination

### Workflow
1. Client submits case information
2. Background task starts
3. Intake Agent validates and structures case
4. Review Agent analyzes and provides recommendations
5. Case status changes to "pending_lawyer"
6. Lawyer reviews case via API
7. Lawyer submits decision
8. Case status updated based on decision

### Human-in-the-Loop
- AI handles initial processing (intake, analysis)
- Human makes final decision (approve, reject, request info)
- System tracks both AI recommendations and human decisions
- Context preserved throughout workflow

## 🎓 Challenges

### Challenge 1: Add Email Notifications
Send email notifications when case is ready for review.

**Hint:** Add email sending in the review endpoint.

### Challenge 2: Case History
Track case history and changes over time.

**Hint:** Add a history field to track status changes.

### Challenge 3: Multiple Reviewers
Support multiple lawyers reviewing the same case.

**Hint:** Add reviewer_id to track who reviewed.

### Challenge 4: Automated Routing
Route cases to appropriate lawyers based on case type.

**Hint:** Add case type to lawyer mapping logic.

## 🔍 Key Code Patterns

### Multi-Agent Crew
```python
crew = Crew(
    agents=[intake_agent, review_agent],
    tasks=[intake_task, review_task],
    process=Process.sequential
)
result = crew.kickoff()
```

### Human Review Endpoint
```python
@router.post("/review/{case_id}")
async def submit_lawyer_review(case_id: str, request: CaseReviewRequest):
    # Update case with human decision
    session["lawyer_decision"] = request.lawyer_decision
    session["status"] = "approved" if decision == "approve" else "rejected"
```

### Status Management
```python
# Processing stages
"processing" -> "pending_lawyer" -> "approved" | "rejected" | "intake"
```

## 📖 Related Concepts

- **Multi-Agent Coordination**: Agents working together
- **Human-in-the-Loop**: Human oversight in AI workflows
- **Workflow Orchestration**: Coordinating multiple stages
- **Context Preservation**: Maintaining information across stages

## 🐛 Troubleshooting

### Issue: Case stuck in processing
- Check agent execution logs
- Verify LLM API is accessible
- Check for errors in background task

### Issue: Review endpoint returns 400
- Ensure case status is "pending_lawyer"
- Verify case_id is correct
- Check if case was already reviewed

### Issue: Agent output not parsing correctly
- Check agent output format
- Adjust parsing logic in process_case_intake
- Add fallback parsing

