# Job Application Form Auto-Fill Demo

## 🎯 Learning Objectives

This demo teaches you how to build an AI agent system for form automation:

1. **Document Parsing** - Extract structured data from PDF resumes using LLMs
2. **Agent-Based Form Filling** - AI agents automatically fill forms from extracted data
3. **Real-Time Streaming** - Stream form filling progress for better user experience
4. **Structured Data Extraction** - Using LLMs to extract structured data from unstructured documents

## 📚 Key Concepts

### Document Parsing
- Parse PDF resumes using document readers (LlamaIndex)
- Extract text content from PDFs
- Use LLMs to structure unstructured resume data

### Agent-Based Form Filling
- Intelligent mapping of resume data to form fields
- Field-by-field form filling with visual feedback
- Handling different field types and formats

### Real-Time Streaming
- Server-Sent Events (SSE) for real-time updates
- Progress tracking and status updates
- Field-by-field completion visualization

## 🏗️ Architecture

```
Resume PDF Upload
    ↓
PDF Text Extraction (LlamaIndex)
    ↓
LLM Structured Extraction (ResumeData)
    ↓
Form Filling Agent
    ↓
Field-by-Field Mapping
    ↓
Streaming Updates (SSE)
    ↓
Filled Form
```

## 📁 File Structure

- `main.py` - FastAPI router with endpoints
- `resume_parser.py` - Resume PDF parsing and extraction
- `form_agent.py` - Agent logic for form filling
- `form_template.py` - Form structure definition
- `models.py` - Data models for requests/responses
- `README.md` - This file

## 🚀 Usage

### API Endpoints

1. **GET /job-application-form-filling/job-listing**
   - Get the job listing information
   - Returns: Job listing with title, description, requirements, benefits

2. **GET /job-application-form-filling/form-structure**
   - Get the form structure/template
   - Returns: Form structure with sections and fields

3. **POST /job-application-form-filling/upload-resume**
   - Upload and parse a resume PDF
   - Body: Form data with PDF file
   - Returns: `{ "session_id": "...", "resume_data": {...}, "status": "parsed" }`

4. **POST /job-application-form-filling/fill-form-stream**
   - Stream form filling updates in real-time
   - Query param: `session_id` (from upload-resume response)
   - Returns: SSE stream with field-by-field updates

5. **GET /job-application-form-filling/session/{session_id}**
   - Get session information
   - Returns: Session data including parsed resume and filled form

6. **GET /job-application-form-filling/health**
   - Health check endpoint
   - Returns: Service status

## 🔄 Workflow

1. **Upload Resume**: User uploads a PDF resume
2. **Parse Resume**: System extracts text and uses LLM to structure data
3. **Start Form Filling**: User initiates form filling process
4. **Stream Updates**: Agent fills form fields one by one, streaming progress
5. **Complete**: Form is fully filled and ready for review

## 💡 Key Implementation Details

### Resume Parsing
- Uses LlamaIndex `SimpleDirectoryReader` for PDF text extraction
- LLM extracts structured data using Pydantic models
- Handles various resume formats and structures

### Form Filling Agent
- Maps resume data to form fields intelligently
- Handles different field types (text, email, tel, textarea)
- Provides real-time progress updates

### Streaming
- Uses Server-Sent Events (SSE) for real-time updates
- Streams field-by-field completion
- Shows progress percentage and status messages

## 🎓 Learning Outcomes

After completing this demo, you'll understand:

1. How to parse PDF documents and extract text
2. How to use LLMs for structured data extraction
3. How to build agents that automate form filling
4. How to implement real-time streaming updates
5. How to map unstructured data to structured forms
6. Practical application in HR/recruiting workflows

## 🔧 Technical Stack

- **FastAPI** - Web framework
- **LlamaIndex** - Document parsing
- **Pydantic** - Data validation and models
- **LLM Provider** - Multi-provider LLM integration
- **Server-Sent Events** - Real-time streaming

