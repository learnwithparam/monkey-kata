"""
CV Analyzer - Multi-Agent System
================================

🎯 LEARNING OBJECTIVES:
This module teaches you how to build a multi-agent AI system:

1. Multi-Agent Design - How to decompose tasks into specialized agents
2. Workflow Orchestration - How to coordinate agents with workflows
3. State Management - How agents share information through shared state
4. Agent Specialization - Why focused agents outperform general prompts
5. Cost Optimization - How targeted prompts reduce API costs
6. Workflow Design - How to design sequential and parallel agent flows

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: State Definition - Define shared state for agents
Step 2: Agent Design - Create specialized agents (one per task)
Step 3: Workflow Construction - Build workflow to coordinate agents
Step 4: Agent Execution - Run workflow with state management
Step 5: Result Extraction - Extract and structure results

Key Concept: Multi-agent systems break complex tasks into specialized agents
that work together. Each agent has a single responsibility and collaborates
through shared state. This improves quality, reduces costs, and makes systems
more maintainable.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass
from datetime import datetime

# LangGraph imports
from langgraph.graph import StateGraph, END

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# STEP 1: STATE DEFINITION
# ============================================================================
"""
State Management in Multi-Agent Systems:

The state is the "shared memory" that all agents read from and write to.
This is how agents collaborate without directly calling each other.

Key Concepts:
- TypedDict: Type-safe state definition
- Shared State: All agents access the same state object
- State Updates: Agents read state, modify it, return updates
- State Flow: State evolves as workflow progresses

The State Contains:
- cv_content: Input CV text
- job_description: Optional job description for targeted analysis
- analysis_results: Intermediate results from agents
- strengths/weaknesses: Output from analysis agents
- improvement_suggestions: Output from suggester agent
- score: Output from scorer agent
- error: Error handling
"""
class CVAnalysisState(TypedDict):
    """State for CV analysis workflow - shared memory for all agents"""
    cv_content: str  # Input: Raw CV text
    job_description: Optional[str]  # Input: Optional job description
    analysis_results: Dict[str, Any]  # Intermediate: Extracted structured data
    improvement_suggestions: List[str]  # Output: From Suggester Agent
    strengths: List[str]  # Output: From Strengths Agent
    weaknesses: List[str]  # Output: From Weaknesses Agent
    score: int  # Output: From Scorer Agent (overall score)
    keyword_match_score: int  # Output: From Scorer Agent
    experience_relevance: int  # Output: From Scorer Agent
    skills_alignment: int  # Output: From Scorer Agent
    format_score: int  # Output: From Scorer Agent
    error: Optional[str]  # Error handling


@dataclass
class CVAnalysisResult:
    """Final result of CV analysis - combines outputs from all agents"""
    overall_score: int  # From Scorer Agent
    strengths: List[str]  # From Strengths Agent
    weaknesses: List[str]  # From Weaknesses Agent
    improvement_suggestions: List[str]  # From Suggester Agent
    keyword_match_score: int  # Placeholder for future enhancement
    experience_relevance: int  # Placeholder for future enhancement
    skills_alignment: int  # Placeholder for future enhancement
    format_score: int  # Placeholder for future enhancement

# ============================================================================
# STEP 2: AGENT DESIGN
# ============================================================================
"""
Multi-Agent System Design:

Each agent has a SINGLE, FOCUSED responsibility:
1. Content Extractor: Structures raw CV into JSON
2. Strengths Analyzer: Identifies CV strengths
3. Weaknesses Analyzer: Finds areas for improvement
4. Improvement Suggester: Generates actionable suggestions
5. CV Scorer: Calculates overall score

Why Specialized Agents?
- Better Quality: Focused prompts outperform general prompts
- Cost Effective: Smaller, targeted prompts cost less
- Maintainable: Easy to modify or replace individual agents
- Collaborative: Agents build on each other's work
- Testable: Each agent can be tested independently

Agent Pattern:
- Each agent is a class with an async method
- Method takes state, returns updated state
- Agent reads from state, writes to state
- Fallback mechanisms for error handling
"""

def _is_content_blocked_error(error: Exception) -> bool:
    """
    Check if an error indicates content was blocked by safety filters.
    
    This is common with Gemini and other providers that have content safety filters.
    
    Args:
        error: Exception to check
        
    Returns:
        True if error indicates blocked content, False otherwise
    """
    error_str = str(error).lower()
    return "blocked" in error_str or "safety" in error_str

def _handle_llm_error(error: Exception, agent_name: str, state: CVAnalysisState, fallback_value: Any) -> CVAnalysisState:
    """
    Handle LLM errors consistently across all agents.
    
    Args:
        error: The exception that occurred
        agent_name: Name of the agent (for logging)
        state: Current state to update
        fallback_value: Value to set in state if content is blocked
        
    Returns:
        Updated state with error handling applied
    """
    if _is_content_blocked_error(error):
        logger.warning(f"Content blocked by safety filters in {agent_name}: {error}")
        # Set fallback value (varies by agent)
        if isinstance(fallback_value, list):
            state[agent_name.lower().replace(" ", "_")] = fallback_value
        else:
            state["error"] = f"{agent_name} blocked by safety filters"
    else:
        logger.error(f"Error in {agent_name}: {error}")
        state["error"] = f"Error in {agent_name}: {str(error)}"
    
    return state
class CVContentExtractor:
    """
    Agent 1: Content Extractor
    
    Purpose: Convert unstructured CV text into structured JSON format.
    This makes downstream agents faster and more reliable.
    
    Input: state["cv_content"] (raw CV text)
    Output: state["analysis_results"]["extracted_content"] (structured JSON)
    """
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def extract_content(self, state: CVAnalysisState) -> CVAnalysisState:
        """
        Extract structured content from CV
        
        This agent:
        1. Takes raw CV text
        2. Asks LLM to extract structured information
        3. Returns JSON with personal info, experience, education, skills, etc.
        4. Stores result in state for other agents to use
        """
        try:
            cv_content = state["cv_content"]
            
            extraction_prompt = """
            Extract key information from this CV in JSON format:
            
            CV Content: {cv_content}
            
            Return JSON with:
            {{
                "personal_info": {{
                    "name": "string",
                    "email": "string",
                    "phone": "string",
                    "location": "string"
                }},
                "summary": "string",
                "experience": [
                    {{
                        "title": "string",
                        "company": "string",
                        "duration": "string",
                        "description": "string"
                    }}
                ],
                "education": [
                    {{
                        "degree": "string",
                        "institution": "string",
                        "year": "string"
                    }}
                ],
                "skills": ["skill1", "skill2"],
                "certifications": ["cert1", "cert2"],
                "projects": [
                    {{
                        "name": "string",
                        "description": "string",
                        "technologies": ["tech1", "tech2"]
                    }}
                ]
            }}
            """
            
            response = await self.llm.generate_text(extraction_prompt.format(cv_content=cv_content))
            
            # Try to parse JSON
            try:
                import json
                extracted_data = json.loads(response)
                state["analysis_results"]["extracted_content"] = extracted_data
            except:
                # Fallback to simple text extraction
                state["analysis_results"]["extracted_content"] = {
                    "summary": cv_content[:500] + "..." if len(cv_content) > 500 else cv_content,
                    "skills": [],
                    "experience": []
                }
            
            logger.info("CV content extracted successfully")
            
        except (ValueError, Exception) as e:
            # Handle blocked content or API errors
            if _is_content_blocked_error(e):
                logger.warning(f"Content blocked by safety filters: {e}")
                # Use fallback extraction
                state["analysis_results"]["extracted_content"] = {
                    "summary": cv_content[:500] + "..." if len(cv_content) > 500 else cv_content,
                    "skills": [],
                    "experience": []
                }
            else:
                logger.error(f"Error extracting CV content: {e}")
                state["error"] = f"Error extracting CV content: {str(e)}"
        
        return state

class CVStrengthsAnalyzer:
    """
    Agent 2: Strengths Analyzer
    
    Purpose: Identify the CV's key strengths and positive attributes.
    
    Input: state["cv_content"], state["analysis_results"]["extracted_content"]
    Output: state["strengths"] (list of strengths)
    
    This agent focuses ONLY on strengths, making it more effective than
    a general "analyze everything" prompt.
    """
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def analyze_strengths(self, state: CVAnalysisState) -> CVAnalysisState:
        """
        Analyze CV strengths
        
        This agent:
        1. Reads CV content and extracted data from state
        2. Focuses specifically on identifying strengths
        3. Returns a list of key strengths
        4. Stores result in state for other agents (e.g., Scorer)
        """
        try:
            cv_content = state["cv_content"]
            extracted = state["analysis_results"].get("extracted_content", {})
            
            strengths_prompt = """
            Analyze this CV and identify its key strengths:
            
            CV Content: {cv_content}
            Extracted Data: {extracted_data}
            
            Focus on:
            1. Relevant experience and achievements
            2. Strong technical skills
            3. Education and certifications
            4. Project accomplishments
            5. Quantifiable results
            
            Return a JSON list of strengths:
            ["strength1", "strength2", "strength3"]
            
            Keep each strength concise (20 words max).
            """
            
            response = await self.llm.generate_text(strengths_prompt.format(
                cv_content=cv_content,
                extracted_data=str(extracted)
            ))
            
            try:
                import json
                strengths = json.loads(response)
                state["strengths"] = strengths if isinstance(strengths, list) else [strengths]
            except:
                # Fallback
                state["strengths"] = [
                    "Relevant work experience",
                    "Technical skills demonstrated",
                    "Educational background"
                ]
            
            logger.info(f"Identified {len(state['strengths'])} strengths")
            
        except (ValueError, Exception) as e:
            # Handle blocked content or API errors
            if _is_content_blocked_error(e):
                logger.warning(f"Content blocked by safety filters: {e}")
                state["strengths"] = [
                    "Relevant work experience",
                    "Technical skills demonstrated",
                    "Educational background"
                ]
            else:
                logger.error(f"Error analyzing strengths: {e}")
                state["strengths"] = ["Analysis completed"]
        
        return state

class CVWeaknessesAnalyzer:
    """
    Agent 3: Weaknesses Analyzer
    
    Purpose: Identify areas for improvement in the CV.
    
    Input: state["cv_content"], state["job_description"]
    Output: state["weaknesses"] (list of weaknesses)
    
    This agent can run in parallel with Strengths Analyzer since they
    don't depend on each other's outputs.
    """
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def analyze_weaknesses(self, state: CVAnalysisState) -> CVAnalysisState:
        """
        Analyze CV weaknesses
        
        This agent:
        1. Reads CV content and job description from state
        2. Focuses specifically on identifying weaknesses
        3. Returns a list of constructive weaknesses
        4. Stores result in state for Suggester and Scorer agents
        """
        try:
            cv_content = state["cv_content"]
            job_description = state.get("job_description", "")
            
            weaknesses_prompt = """
            Analyze this CV and identify areas for improvement:
            
            CV Content: {cv_content}
            Job Description: {job_description}
            
            Look for:
            1. Missing key skills or experience
            2. Weak formatting or structure
            3. Lack of quantifiable achievements
            4. Missing relevant keywords
            5. Gaps in experience or education
            
            Return a JSON list of weaknesses:
            ["weakness1", "weakness2", "weakness3"]
            
            Be constructive and specific. Keep each weakness concise (20 words max).
            """
            
            response = await self.llm.generate_text(weaknesses_prompt.format(
                cv_content=cv_content,
                job_description=job_description
            ))
            
            try:
                import json
                weaknesses = json.loads(response)
                state["weaknesses"] = weaknesses if isinstance(weaknesses, list) else [weaknesses]
            except:
                # Fallback
                state["weaknesses"] = [
                    "Consider adding more quantifiable achievements",
                    "Review formatting for better readability"
                ]
            
            logger.info(f"Identified {len(state['weaknesses'])} weaknesses")
            
        except (ValueError, Exception) as e:
            # Handle blocked content or API errors
            if _is_content_blocked_error(e):
                logger.warning(f"Content blocked by safety filters: {e}")
                state["weaknesses"] = [
                    "Consider adding more quantifiable achievements",
                    "Review formatting for better readability"
                ]
            else:
                logger.error(f"Error analyzing weaknesses: {e}")
                state["weaknesses"] = ["Analysis completed"]
        
        return state

class CVImprovementSuggester:
    """
    Agent 4: Improvement Suggester
    
    Purpose: Generate actionable improvement suggestions based on analysis.
    
    Input: state["cv_content"], state["strengths"], state["weaknesses"], state["job_description"]
    Output: state["improvement_suggestions"] (list of suggestions)
    
    This agent demonstrates agent collaboration:
    - It uses weaknesses from Weaknesses Analyzer
    - It can use strengths from Strengths Analyzer
    - Agents build on each other's work
    """
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def generate_suggestions(self, state: CVAnalysisState) -> CVAnalysisState:
        """
        Generate actionable improvement suggestions
        
        This agent:
        1. Reads weaknesses from Weaknesses Analyzer
        2. Reads strengths from Strengths Analyzer
        3. Generates specific, actionable suggestions
        4. Stores result in state
        """
        try:
            cv_content = state["cv_content"]
            strengths = state.get("strengths", [])
            weaknesses = state.get("weaknesses", [])
            job_description = state.get("job_description", "")
            
            suggestions_prompt = """
            Based on the CV analysis, provide actionable improvement suggestions:
            
            CV Content: {cv_content}
            Strengths: {strengths}
            Weaknesses: {weaknesses}
            Job Description: {job_description}
            
            Provide specific, actionable suggestions:
            1. Content improvements
            2. Formatting suggestions
            3. Missing elements to add
            4. Keyword optimization
            5. Experience enhancement
            
            Return a JSON list of suggestions:
            ["suggestion1", "suggestion2", "suggestion3"]
            
            Each suggestion should be specific and actionable.
            Keep each suggestion concise (20 words max).
            """
            
            response = await self.llm.generate_text(suggestions_prompt.format(
                cv_content=cv_content,
                strengths=str(strengths),
                weaknesses=str(weaknesses),
                job_description=job_description
            ))
            
            try:
                import json
                suggestions = json.loads(response)
                state["improvement_suggestions"] = suggestions if isinstance(suggestions, list) else [suggestions]
            except:
                # Fallback
                state["improvement_suggestions"] = [
                    "Add quantifiable achievements to experience section",
                    "Include relevant keywords from job description",
                    "Improve formatting for better readability"
                ]
            
            logger.info(f"Generated {len(state['improvement_suggestions'])} suggestions")
            
        except (ValueError, Exception) as e:
            # Handle blocked content or API errors
            if _is_content_blocked_error(e):
                logger.warning(f"Content blocked by safety filters: {e}")
                state["improvement_suggestions"] = [
                    "Add quantifiable achievements to experience section",
                    "Include relevant keywords from job description",
                    "Improve formatting for better readability"
                ]
            else:
                logger.error(f"Error generating suggestions: {e}")
                state["improvement_suggestions"] = ["Review and improve CV content"]
        
        return state

class CVScorer:
    """
    Agent 5: CV Scorer
    
    Purpose: Calculate overall CV quality score (1-100).
    
    Input: state["cv_content"], state["strengths"], state["weaknesses"], state["job_description"]
    Output: state["score"] (overall score)
    
    This agent demonstrates agent collaboration:
    - Uses strengths from Strengths Analyzer
    - Uses weaknesses from Weaknesses Analyzer
    - Combines multiple agent outputs for final score
    """
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def score_cv(self, state: CVAnalysisState) -> CVAnalysisState:
        """
        Calculate CV scores using LLM
        
        This agent:
        1. Reads strengths, weaknesses, and extracted data from previous agents
        2. Asks LLM to score the CV in 5 categories
        3. Stores all scores in state
        
        Simple approach: Let the LLM do the scoring analysis.
        """
        try:
            cv_content = state["cv_content"]
            strengths = state.get("strengths", [])
            weaknesses = state.get("weaknesses", [])
            job_description = state.get("job_description", "")
            extracted = state["analysis_results"].get("extracted_content", {})
            
            scoring_prompt = """Score this CV on a scale of 1-100 for each category. Return ONLY a JSON object:

CV Content: {cv_content}
Extracted Data: {extracted_data}
Strengths: {strengths}
Weaknesses: {weaknesses}
Job Description: {job_description}

Return JSON with these scores (1-100 each):
{{
    "overall_score": <overall CV quality score>,
    "keyword_match_score": <how well CV matches job keywords>,
    "experience_relevance": <relevance of experience to job>,
    "skills_alignment": <how well skills match job requirements>,
    "format_score": <CV formatting and structure quality>
}}

Return ONLY the JSON object."""
            
            response = await self.llm.generate_text(scoring_prompt.format(
                cv_content=cv_content[:2000],
                extracted_data=str(extracted)[:1000],
                strengths=str(strengths),
                weaknesses=str(weaknesses),
                job_description=job_description[:1000]
            ))
            
            # Parse JSON from response
            import re
            import json as json_module
            
            # Extract JSON (handle markdown code blocks)
            json_match = re.search(r'\{[^{}]*"overall_score"[^{}]*\}', response, re.DOTALL)
            if not json_match:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                try:
                    scores = json_module.loads(json_match.group(0))
                    
                    # Validate all required scores are present
                    required_scores = ["overall_score", "keyword_match_score", "experience_relevance", "skills_alignment", "format_score"]
                    for score_key in required_scores:
                        if score_key not in scores:
                            raise KeyError(f"Missing required score: {score_key}")
                    
                    # Validate and set scores
                    state["score"] = min(max(int(scores["overall_score"]), 1), 100)
                    state["keyword_match_score"] = min(max(int(scores["keyword_match_score"]), 1), 100)
                    state["experience_relevance"] = min(max(int(scores["experience_relevance"]), 1), 100)
                    state["skills_alignment"] = min(max(int(scores["skills_alignment"]), 1), 100)
                    state["format_score"] = min(max(int(scores["format_score"]), 1), 100)
                    
                    logger.info(
                        f"CV scored: overall={state['score']}, "
                        f"keyword={state['keyword_match_score']}, "
                        f"experience={state['experience_relevance']}, "
                        f"skills={state['skills_alignment']}, "
                        f"format={state['format_score']}"
                    )
                    return state
                except (json_module.JSONDecodeError, ValueError, KeyError) as e:
                    logger.error(f"Failed to parse JSON scores: {e}, response: {response[:300]}")
                    raise ValueError(f"Invalid score format from LLM: {e}") from e
            
            # If JSON parsing fails, raise error - don't return fake scores
            logger.error(f"Failed to parse scores from LLM response: {response[:200]}")
            raise ValueError("Failed to parse CV scores from LLM response")
            
        except ValueError as e:
            # Handle blocked content or API errors
            if _is_content_blocked_error(e):
                logger.warning(f"Content blocked by safety filters: {e}")
                # Use default scores when content is blocked
                state["score"] = 50
                state["keyword_match_score"] = 50
                state["experience_relevance"] = 50
                state["skills_alignment"] = 50
                state["format_score"] = 50
                logger.info("Using default scores due to content blocking")
                return state
            else:
                logger.error(f"Error scoring CV: {e}")
                raise
        except Exception as e:
            logger.error(f"Error scoring CV: {e}")
            # Don't return fake scores - re-raise the error
            raise

# ============================================================================
# STEP 3: WORKFLOW CONSTRUCTION
# ============================================================================
"""
Workflow Orchestration:

The workflow orchestrates agents using a graph structure:
- Nodes: Agents (each agent is a node)
- Edges: Transitions between agents (defines flow)
- State: Shared memory passed between nodes
- Entry Point: Where workflow starts
- End: Where workflow completes

The Workflow:
1. Extract Content → 2. Analyze Strengths → 3. Analyze Weaknesses → 
4. Generate Suggestions → 5. Score CV → End

Future Enhancement: Strengths and Weaknesses can run in parallel
since they don't depend on each other.

Why Workflow Orchestration?
- Visual workflow representation
- State management built-in
- Error handling
- Parallel execution support
- Easy to modify workflow structure
"""
class CVAnalyzer:
    """
    Main multi-agent CV analyzer
    
    This class:
    1. Initializes all agents
    2. Builds the workflow to coordinate agents
    3. Executes the workflow with state management
    4. Returns structured results
    """
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
        
        # Initialize all agents
        self.content_extractor = CVContentExtractor(llm_provider)
        self.strengths_analyzer = CVStrengthsAnalyzer(llm_provider)
        self.weaknesses_analyzer = CVWeaknessesAnalyzer(llm_provider)
        self.improvement_suggester = CVImprovementSuggester(llm_provider)
        self.scorer = CVScorer(llm_provider)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """
        Build the workflow to coordinate agents
        
        This creates a workflow graph with:
        - Nodes: Each agent is a node
        - Edges: Define the flow between agents
        - Entry Point: Where workflow starts
        - End: Where workflow completes
        
        Current Flow (Sequential):
        Extract → Strengths → Weaknesses → Suggestions → Score → End
        
        Future Enhancement:
        Could run Strengths and Weaknesses in parallel since they're independent.
        """
        workflow = StateGraph(CVAnalysisState)
        
        # Add nodes
        workflow.add_node("extract_content", self.content_extractor.extract_content)
        workflow.add_node("analyze_strengths", self.strengths_analyzer.analyze_strengths)
        workflow.add_node("analyze_weaknesses", self.weaknesses_analyzer.analyze_weaknesses)
        workflow.add_node("generate_suggestions", self.improvement_suggester.generate_suggestions)
        workflow.add_node("score_cv", self.scorer.score_cv)
        
        # Define the flow
        workflow.set_entry_point("extract_content")
        workflow.add_edge("extract_content", "analyze_strengths")
        workflow.add_edge("analyze_strengths", "analyze_weaknesses")
        workflow.add_edge("analyze_weaknesses", "generate_suggestions")
        workflow.add_edge("generate_suggestions", "score_cv")
        workflow.add_edge("score_cv", END)
        
        return workflow.compile()
    
    # ============================================================================
    # STEP 4: WORKFLOW EXECUTION
    # ============================================================================
    """
    Workflow Execution:
    
    The workflow is executed with:
    1. Initial state: CV content and job description
    2. Workflow invokes agents in sequence
    3. Each agent reads from and writes to state
    4. State evolves as workflow progresses
    5. Final state contains all agent outputs
    
    Error Handling:
    - Each agent has fallback mechanisms
    - If an agent fails, workflow continues with defaults
    - Final result includes all successful agent outputs
    """
    async def analyze_cv(self, cv_content: str, job_description: str = "") -> CVAnalysisResult:
        """
        Analyze CV using multi-agent workflow
        
        This is the main entry point that:
        1. Creates initial state
        2. Runs the multi-agent workflow
        3. Extracts results from final state
        4. Returns structured analysis result
        
        Args:
            cv_content: Raw CV text
            job_description: Optional job description for targeted analysis
            
        Returns:
            CVAnalysisResult with outputs from all agents
        """
        try:
            # Initialize state
            initial_state = CVAnalysisState(
                cv_content=cv_content,
                job_description=job_description,
                analysis_results={},
                improvement_suggestions=[],
                strengths=[],
                weaknesses=[],
                score=0,
                keyword_match_score=0,
                experience_relevance=0,
                skills_alignment=0,
                format_score=0,
                error=None
            )
            
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            # Return structured result - scores must come from scorer agent
            # Check that all scores are present (not 0 or missing)
            if not result.get("score") or not result.get("keyword_match_score") or \
               not result.get("experience_relevance") or not result.get("skills_alignment") or \
               not result.get("format_score"):
                raise ValueError("CV scoring incomplete - missing scores")
            
            return CVAnalysisResult(
                overall_score=result["score"],
                strengths=result.get("strengths", []),
                weaknesses=result.get("weaknesses", []),
                improvement_suggestions=result.get("improvement_suggestions", []),
                keyword_match_score=result["keyword_match_score"],
                experience_relevance=result["experience_relevance"],
                skills_alignment=result["skills_alignment"],
                format_score=result["format_score"]
            )
            
        except Exception as e:
            logger.error(f"Error in CV analysis: {e}")
            # Don't return fake data - re-raise the error
            raise

# ============================================================================
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How to design specialized agents with single responsibilities
✓ How workflow orchestration coordinates multi-agent systems
✓ How shared state enables agent collaboration
✓ Why specialized agents outperform general prompts
✓ How agents build on each other's work
✓ How to handle errors in multi-agent systems

Key Multi-Agent Concepts:
- Agent Specialization: Each agent has one focused task
- State Management: Shared state connects agents
- Workflow Orchestration: Workflow manages agent execution
- Agent Collaboration: Agents read from and write to shared state
- Cost Optimization: Targeted prompts cost less than general prompts
- Maintainability: Easy to modify or replace individual agents

Multi-Agent Workflow:
1. Content Extractor: Structures CV into JSON
2. Strengths Analyzer: Identifies strengths
3. Weaknesses Analyzer: Finds weaknesses
4. Suggester Agent: Generates suggestions (uses weaknesses)
5. Scorer Agent: Calculates score (uses strengths + weaknesses)

Next Steps:
1. Add parallel execution for independent agents (strengths + weaknesses)
2. Add new agents (e.g., FormatChecker, KeywordOptimizer)
3. Implement conditional routing (different agents for different CV types)
4. Add agent retry logic for failed agents
5. Implement human-in-the-loop for agent review

Questions to Consider:
- How would you handle conflicting agent outputs?
- How could you add a "supervisor" agent to coordinate other agents?
- What if one agent fails? Should workflow continue or stop?
- How would you optimize for speed vs quality?
- How could agents learn from user feedback?
"""

# Example usage and testing
if __name__ == "__main__":
    async def test_cv_analyzer():
        """Test the CV analyzer with sample data"""
        
        # Mock LLM provider for testing
        class MockLLM:
            async def generate_text(self, prompt: str) -> str:
                if "strengths" in prompt.lower():
                    return '["Strong technical background", "Relevant experience", "Good education"]'
                elif "weaknesses" in prompt.lower():
                    return '["Missing quantifiable achievements", "Could improve formatting"]'
                elif "suggestions" in prompt.lower():
                    return '["Add metrics to achievements", "Improve section formatting", "Include more keywords"]'
                elif "score" in prompt.lower():
                    return "78"
                else:
                    return '{"summary": "Test CV", "skills": ["Python", "JavaScript"], "experience": []}'
        
        # Test the analyzer
        analyzer = CVAnalyzer(MockLLM())
        
        sample_cv = """
        John Doe
        Software Engineer
        john@email.com
        
        Experience:
        - Software Developer at Tech Corp (2020-2023)
        - Built web applications using Python and JavaScript
        
        Education:
        - BS Computer Science, University of Tech (2018-2020)
        
        Skills:
        - Python, JavaScript, React, Node.js
        """
        
        result = await analyzer.analyze_cv(sample_cv, "Looking for a Python developer with React experience")
        
        print(f"Overall Score: {result.overall_score}/100")
        print(f"Strengths: {result.strengths}")
        print(f"Weaknesses: {result.weaknesses}")
        print(f"Suggestions: {result.improvement_suggestions}")
    
    # Run test
    asyncio.run(test_cv_analyzer())
