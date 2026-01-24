# Repository Engineering Standards

This document defines the core engineering principles and standards for the `ai-engineering-demos` repository. All future development must adhere to these patterns.

## 🏗️ Core Architecture & Hierarchy

The repository follows a **Mono-Repo Lite** structure:
- **/api**: Core FastAPI backend. Contains shared utilities and individual demo logic.
- **/frontend**: Shared Next.js frontend for all demos.
- **/docker-compose.yml**: The single source of truth for service orchestration.
- **/Makefile**: The primary entry point for all developer operations.

---

## 🛠️ DevOps & Developer Experience

### Makefile (The "Command Center")
- Every common operation MUST have a `make` target.
- `make dev`: The standard command to start everything via Docker Compose using BuildKit.
- `make install`: Handles dependency installation for both API (pip) and Frontend (npm).
- `make clean`: Essential for resetting environments and purging caches.

### Docker & Containerization
- **Caching**: Use BuildKit cache mounts (`--mount=type=cache`) in Dockerfiles to speed up package installs.
- **Exclusions**: Always exclude `node_modules`, `__pycache__`, and `.next` from bind mounts to avoid guest/host conflicts and leverage Docker's native volume performance.
- **Port Mapping**: Standardization is key (e.g., API: 4010, Frontend: 4020).

### Environment Management
- NEVER commit `.env` files.
- Always maintain an `env.example` in both `api` and `frontend` folders.
- Use the `VISION_MODEL` variable consistently to allow switching models without code changes.

---

## 🐍 API Engineering (Python/FastAPI)

### Demo Layout
Every demo must follow this structure inside `api/demos/<name>/`:
1. `main.py`: Endpoint definition (`router = APIRouter(...)`).
2. `<name>_analyzer.py`: Logic that interacts with LLMs.
3. `<name>_utils.py`: Specific helper functions.
4. `README.md`: Detailed documentation of the demo.

### LLM Provider Abstraction
- Use the central `LLMProvider` in `api/utils/llm_provider.py`.
- **Model ID Normalization**: Providers MUST strip LiteLLM-specific prefixes (e.g., `openrouter/`, `fireworks/`) if they are using direct API calls.
- **Why?**: The workshops (.ipynb) use LiteLLM, but the production-ready demos use direct provider clients for stability and control.

### Error Handling (Transparency First)
- **DO NOT MASK ERRORS**: Avoid broad `try/except` blocks that return generic "success" flags (like `is_invoice: false`) when a system error (like an API failure) occurs.
- **Bubble Up**: Let `HTTPException` and other real errors bubble up to the FastAPI level so the frontend (and user) sees the actual 400/500 status and message.

---

## ⚛️ Frontend Engineering (Next.js/React)

### Layout & Routing
- Use the Next.js **App Router**.
- Every demo must have its own route: `frontend/src/app/demos/<demo_name>/page.tsx`.

### UI Consistency
- Use shared components for repetitive tasks:
  - `<FileUpload />`: Handles drag-and-drop, validation, and encoding.
  - `<ProcessingButton />`: Encapsulates loading states for AI calls.
  - `<AlertMessage />`: Used for consistent error/status reporting.
- **Vanilla CSS**: Stick to the repository's design tokens and avoid unapproved utility frameworks unless explicitly requested.

### User Feedback
- Always provide clear context for model limitations.
- *Example*: "Supports PDF (Gemini) and Images (All providers)".

---

## 📖 Documentation Standards

A demo is not finished until its `README.md` includes:
- **🎯 Learning Objectives**: Explicit "Takeaways" from the demo.
- **📚 Key Concepts**: Explanations of the underlying AI theory (RAG, Multimodal, Tool-use).
- **🏗️ Architecture**: A Mermaid.js diagram showing the data flow.
- **🔍 Key Code Patterns**: Explanatory snippets showing correct implementation of standards.
- **🐛 Troubleshooting**: Known limitations or provider-specific quirks.

---

## 🧹 Git Best Practices
- **.gitignore**: Ensure temporary assets, caches, and system files (`.DS_Store`, `__pycache__`, `videos/`) are never committed.
- **Structure**: Keep the root clean; move experimental or placeholder scripts to a `tmp/` or `examples/` dir (both ignored by git).
