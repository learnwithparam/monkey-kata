# AI Bootcamp Notebooks

This directory contains comprehensive notebooks for the AI Bootcamp for Software Engineers, organized by week and topic following the single responsibility principle.

## 📚 Syllabus Coverage

### Week 1: AI Foundation — LLMs, Prompts & RAG
**Objective**: Master large language models (LLMs), advanced prompt engineering, and Retrieval-Augmented Generation (RAG)

#### Core Concepts Notebooks:
- `01_llm_fundamentals.ipynb` - LLM architecture, tokenization, context windows, inference pipelines
- `02_prompt_engineering.ipynb` - Zero-shot, few-shot, CoT prompting, structured output, hallucinations
- `03_rag_fundamentals.ipynb` - RAG components, chunking, embeddings, retrieval strategies
- `04_advanced_rag.ipynb` - Semantic chunking, hybrid search, relevance filtering
- `05_streaming_llm_apps.ipynb` - Real-time LLM responses, UI integration, streaming optimization

#### Demo Notebooks:
- `06_demo_bedtime_story.ipynb` - Interactive story app with streaming responses
- `07_demo_legal_analysis.ipynb` - Contract analysis system with prompt chaining
- `08_demo_web_qa.ipynb` - Q&A system using web scraping and RAG
- `09_demo_support_kb.ipynb` - 24/7 Q&A system with vector DB optimization

**Related Examples:**
- `../examples/agentic-rag/` - Advanced RAG implementations
- `../examples/complex-RAG-guide/` - Comprehensive RAG pipeline
- `../examples/rag-ecosystem/` - RAG ecosystem patterns
- `../examples/rag-with-raptor/` - RAPTOR vs RAG comparison
- `../ai-agentic-patterns/patterns/23_agentic_rag.py` - Agentic RAG patterns

---

### Week 2: Building Reliable Conversational Systems
**Objective**: Master voice-enabled conversational systems, memory persistence, and human-in-the-loop patterns

#### Core Concepts Notebooks:
- `01_conversational_ai_fundamentals.ipynb` - Voice vs chat, conversation flows, use cases
- `02_voice_ai_systems.ipynb` - Speech-to-text, text-to-speech, real-time audio processing
- `03_conversation_memory.ipynb` - Session-based vs long-term persistence, summarization
- `04_human_in_loop.ipynb` - Confidence-based escalation, approval workflows
- `05_domain_specific_flows.ipynb` - Medical terminology, sales scoring, branching logic

#### Demo Notebooks:
- `06_demo_lead_qualifier.ipynb` - Chat-based lead scoring with CRM integration
- `07_demo_restaurant_voice.ipynb` - Voice ordering system with order memory
- `08_demo_healthcare_triage.ipynb` - Voice-based triage with HITL escalation

**Related Examples:**
- `../examples/livekit-agents-examples/` - LiveKit voice AI implementations
- `../examples/agentic-guardrails/` - Human-in-the-loop patterns
- `../ai-agentic-patterns/patterns/13_human_in_loop.py` - HITL patterns
- `../ai-agentic-patterns/patterns/08_memory_management.py` - Memory management

---

### Week 3: AI Agents & Workflows
**Objective**: Build autonomous AI agents with tool integration, multi-agent coordination, and workflow orchestration

#### Core Concepts Notebooks:
- `01_ai_agents_fundamentals.ipynb` - Autonomous vs reactive agents, frameworks (CrewAI, Autogen)
- `02_tool_calling_integration.ipynb` - Function schemas, validation, tool calling patterns
- `03_multi_agent_systems.ipynb` - Task distribution, communication protocols, conflict resolution
- `04_workflow_orchestration.ipynb` - State machines, conditional logic, parallel processing
- `05_browser_automation.ipynb` - Selenium/Playwright integration for web automation
- `06_recommendation_systems.ipynb` - Collaborative filtering, user modeling, A/B testing

#### Demo Notebooks:
- `07_demo_competitor_analysis.ipynb` - Web scraping and market analysis agent
- `08_demo_form_filling.ipynb` - Browser automation for form filling
- `09_demo_legal_intake.ipynb` - Chat-based system with HITL and case classification
- `10_demo_shopping_assistant.ipynb` - Recommendation agent with user modeling

**Related Examples:**
- `../examples/crewAI-examples/` - Comprehensive CrewAI implementations
- `../examples/GenAI_Agents/` - Various agent architectures
- `../examples/all-agentic-architectures/` - All agentic patterns
- `../examples/multi-agent-trading-system/` - Multi-agent trading system
- `../examples/Multi-AI-Agent-Systems-with-crewAI/` - CrewAI multi-agent systems
- `../ai-agentic-patterns/patterns/` - All 46 agentic patterns

---

### Week 4: Prototype to Production
**Objective**: Optimize AI systems for speed, accuracy, and cost; implement monitoring and deployment strategies

#### Core Concepts Notebooks:
- `01_production_fundamentals.ipynb` - Latency metrics, cost models, scalability requirements
- `02_rag_optimization.ipynb` - Hybrid search, reranking, cost monitoring
- `03_voice_system_optimization.ipynb` - Latency reduction, noise cancellation
- `04_caching_strategies.ipynb` - Redis caching, performance optimization
- `05_monitoring_metrics.ipynb` - Error tracking, A/B testing, performance metrics
- `06_deployment_patterns.ipynb` - Docker containers, CI/CD pipelines, cloud deployment

#### Demo Notebooks:
- `07_demo_rag_optimization.ipynb` - Optimize Week 1 RAG for 95% accuracy and sub-2s responses
- `08_demo_voice_enhancement.ipynb` - Reduce latency in voice systems with error handling
- `09_demo_agent_scalability.ipynb` - Scale agents with caching and load balancing

**Related Examples:**
- `../examples/ai-eval-system/` - AI evaluation and monitoring
- `../examples/best-llm-finder-pipeline/` - LLM performance optimization
- `../ai-agentic-patterns/patterns/19a_evaluation.py` - Evaluation patterns
- `../ai-agentic-patterns/patterns/19b_monitoring.py` - Monitoring patterns
- `../ai-agentic-patterns/patterns/16_resource_optimization.py` - Resource optimization

---

### Week 5: AI System Design & Architecture
**Objective**: Design scalable, secure, and ethical AI systems with multi-agent coordination and multi-modal capabilities

#### Core Concepts Notebooks:
- `01_enterprise_architecture.ipynb` - Microservices, event-driven systems, API security
- `02_multi_agent_coordination.ipynb` - A2A communication, consensus algorithms, load balancing
- `03_mcp_implementation.ipynb` - Model Context Protocol implementation
- `04_multi_modal_ai.ipynb` - Vision integration with LLMs, edge deployment
- `05_computer_vision_integration.ipynb` - Object detection, OCR, image processing
- `06_ai_ethics_compliance.ipynb` - Bias detection, explainability, GDPR/HIPAA compliance

#### Demo Notebooks:
- `07_demo_enterprise_architecture.ipynb` - Microservices-based AI system design
- `08_demo_a2a_coordination.ipynb` - MCP and coordination protocols
- `09_demo_vision_ethics.ipynb` - Vision-based prototype with compliance framework

**Related Examples:**
- `../examples/best-llm-finder-pipeline/` - Multi-modal AI systems
- `../examples/Video-Generator-AI/` - Multi-modal content generation
- `../ai-agentic-patterns/patterns/10_mcp.py` - MCP implementation
- `../ai-agentic-patterns/patterns/15_inter_agent_communication.py` - A2A communication
- `../ai-agentic-patterns/patterns/18_guardrails.py` - AI safety and guardrails

---

### Week 6: Capstone Project & Demo Day
**Objective**: Integrate all concepts into a production-ready AI application

#### Core Concepts Notebooks:
- `01_capstone_planning.ipynb` - Project selection, requirements gathering, success metrics
- `02_architecture_design.ipynb` - Production-ready system design
- `03_integration_patterns.ipynb` - Combining RAG, agents, voice, multi-modal components
- `04_deployment_strategies.ipynb` - Final deployment, testing, optimization
- `05_testing_optimization.ipynb` - Regression testing, user acceptance, performance tuning
- `06_documentation_presentation.ipynb` - Documentation standards, presentation preparation

#### Demo Notebooks:
- `07_demo_drive_thru_agent.ipynb` - Voice pipeline for drive-thru automation
- `08_demo_personal_shopper.ipynb` - Multi-modal shopping assistant
- `09_demo_financial_reports.ipynb` - Vision-based financial report analysis

**Related Examples:**
- All previous examples and patterns
- `../examples/web-voyager/` - Autonomous web navigation
- `../examples/AI-Coloring-Book-Creator/` - Creative AI applications
- `../examples/nextjs-rag/` - Full-stack RAG applications
- `../examples/openai-nextjs-storygen/` - Story generation applications

---

## 🔗 Pattern Mapping

### AI Agentic Patterns Integration:
- **Prompt Engineering**: `01_prompt_chaining.py`, `17a_chain_of_thought.py`, `17b_self_correction.py`
- **RAG Systems**: `23_agentic_rag.py`, `14_knowledge_retrieval.py`, `29_query_rewriter.py`
- **Multi-Agent**: `07_multi_agent.py`, `15_inter_agent_communication.py`, `10_mcp.py`
- **Memory**: `08_memory_management.py`, `37_episodic_semantic_memory.py`, `41_graph_memory.py`
- **Workflows**: `24_workflow_orchestration.py`, `26_state_machines.py`, `32_plan_executor.py`
- **Production**: `19a_evaluation.py`, `19b_monitoring.py`, `16_resource_optimization.py`
- **Safety**: `18_guardrails.py`, `12_exception_handling.py`, `13_human_in_loop.py`

### Examples Integration:
- **RAG**: `agentic-rag/`, `complex-RAG-guide/`, `rag-ecosystem/`, `rag-with-raptor/`
- **Agents**: `crewAI-examples/`, `GenAI_Agents/`, `all-agentic-architectures/`
- **Voice**: `livekit-agents-examples/`
- **Multi-Agent**: `multi-agent-trading-system/`, `Multi-AI-Agent-Systems-with-crewAI/`
- **Production**: `ai-eval-system/`, `best-llm-finder-pipeline/`
- **Applications**: `nextjs-rag/`, `openai-nextjs-storygen/`, `Video-Generator-AI/`

---

## 📋 Usage Instructions

1. **Follow the weekly progression** - Each week builds upon the previous
2. **Complete core concepts first** - Understand fundamentals before demos
3. **Experiment with examples** - Use provided examples to deepen understanding
4. **Apply patterns** - Integrate agentic patterns into your implementations
5. **Build incrementally** - Each demo adds complexity and real-world applicability

## 🎯 Learning Outcomes

By completing all notebooks, you will:
- Master LLM fundamentals and advanced prompt engineering
- Build production-ready RAG systems with optimization
- Create voice-enabled conversational AI with memory
- Develop multi-agent systems with coordination
- Design enterprise-scale AI architectures
- Implement ethical AI with compliance frameworks
- Deploy and monitor production AI systems
- Present comprehensive capstone projects

---

*This notebook collection provides comprehensive coverage of the AI Bootcamp syllabus with practical implementations, real-world examples, and production-ready patterns.*
