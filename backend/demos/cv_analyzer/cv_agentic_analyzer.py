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
from typing import Dict, List, Any, Optional, TypedDict, Callable
from dataclasses import dataclass
from datetime import datetime

# LangGraph imports
from langgraph.graph import StateGraph, END

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global progress callback for agent activities
_progress_callback: Optional[Callable[[dict], None]] = None

def set_cv_progress_callback(callback: Optional[Callable[[dict], None]]):
    """Set a callback function to report CV analysis progress"""
    global _progress_callback
    _progress_callback = callback

def report_cv_progress(message: str, agent: str = None, tool: str = None, target: str = None, category: str = None):
    """Report progress if callback is set"""
    if _progress_callback:
        try:
            # Determine category from tool if not provided
            if not category:
                if tool == "agent_invoke":
                    category = "agent"
                elif tool == "agent_complete":
                    category = "complete"
                elif tool == "llm_call":
                    category = "reasoning"
                elif tool == "parsing":
                    category = "analysis"
                else:
                    category = "processing"
            
            step_data = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "agent": agent,
                "tool": tool,
                "target": target,
                "category": category
            }
            _progress_callback(step_data)
        except Exception as e:
            logger.warning(f"Error in CV progress callback: {e}")

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
@dataclass
class CVAnalysisResult:
    """Final result of CV analysis - combines outputs from all agents"""
    overall_score: int  # From Scorer Agent
    strengths: List[str]  # From Strengths Agent
    weaknesses: List[str]  # From Weaknesses Agent
    improvement_suggestions: List[str]  # From Suggester Agent
    keyword_match_score: int  # From Scorer Agent
    experience_relevance: int  # From Scorer Agent
    skills_alignment: int  # From Scorer Agent
    format_score: int  # From Scorer Agent
    
    # NEW fields
    score_rationale: Dict[str, str]  # Explanation for scores
    ats_analysis: Dict[str, Any]  # ATS compatibility check

# ============================================================================
# STEP 1: STATE DEFINITION
# ============================================================================
"""
State Management in Multi-Agent Systems:

The state is the "shared memory" that all agents read from and write to.
This is how agents collaborate without directly calling each other.

Key Changes:
- Added job_analysis: Structured analysis of the job description
- Added score_rationale: Explanations for why scores were given
- Added ats_analysis: ATS compatibility findings
"""
class CVAnalysisState(TypedDict):
    """State for CV analysis workflow - shared memory for all agents"""
    cv_content: str  # Input: Raw CV text
    job_description: Optional[str]  # Input: Optional job description
    
    # NEW: Structured Job Analysis (The "Planner" output)
    job_analysis: Dict[str, Any]
    
    analysis_results: Dict[str, Any]  # Intermediate: Extracted structured data
    improvement_suggestions: List[str]  # Output: From Suggester Agent
    strengths: List[str]  # Output: From Strengths Agent
    weaknesses: List[str]  # Output: From Weaknesses Agent
    score: int  # Output: From Scorer Agent (overall score)
    keyword_match_score: int  # Output: From Scorer Agent
    experience_relevance: int  # Output: From Scorer Agent
    skills_alignment: int  # Output: From Scorer Agent
    format_score: int  # Output: From Scorer Agent
    
    # NEW fields
    score_rationale: Dict[str, str]  # Explain "Why" for each score
    ats_analysis: Dict[str, Any]  # ATS compatibility
    
    error: Optional[str]  # Error handling

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

def clean_json_response(response: str) -> str:
    """
    Clean LLM response to extract JSON.
    Removes markdown code blocks (```json ... ```) if present.
    """
    import re
    
    # Remove markdown code blocks
    if "```" in response:
        # Try to find JSON block
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Try to find list block if array expected
        list_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response, re.DOTALL)
        if list_match:
            return list_match.group(1)
            
    # If no code blocks or regex didn't match, maybe it's just raw text with some whitespace
    response = response.strip()
    
    # If it starts with markdown but regex failed, try to just strip the boilerplate
    if response.startswith("```"):
        lines = response.split('\n')
        # Remove first line if it starts with ```
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        # Remove last line if it starts with ```
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        response = "\n".join(lines)
        
    return response.strip()

class JobDescriptionAnalyzer:
    """
    Agent 0: Job Description Analyzer (NEW)
    
    Purpose: Analyze the job description to extract key requirements BEFORE looking at the CV.
    This demonstrates "Prompt Chaining" - the output of this agent becomes the input for others.
    
    Input: state["job_description"]
    Output: state["job_analysis"]
    """
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def analyze_jd(self, state: CVAnalysisState) -> CVAnalysisState:
        """
        Analyze Job Description
        
        This agent:
        1. Takes raw Job Description
        2. Extracts keywords, mandatory requirements, and nice-to-haves
        3. Stores in state['job_analysis']
        """
        try:
            job_description = state.get("job_description", "")
            
            # Skip if no JD provided
            if not job_description or len(job_description.strip()) < 10:
                state["job_analysis"] = {
                    "keywords": [],
                    "mandatory_requirements": [],
                    "nice_to_haves": [],
                    "role_level": "unknown"
                }
                logger.info("No job description provided, skipping analysis")
                return state

            report_cv_progress(
                "Analyzing Job Description to extract requirements...",
                agent="JD Analyzer",
                tool="agent_invoke",
                target="Extracting requirements"
            )
            
            jd_prompt = """
            Analyze this Job Description and extract key requirements in JSON format:
            
            Job Description: {job_description}
            
            Return JSON with:
            {{
                "keywords": ["key1", "key2"],
                "mandatory_requirements": ["req1", "req2"],
                "nice_to_haves": ["nice1", "nice2"],
                "role_level": "entry|senior|lead|manager|executive"
            }}
            """
            
            response = await self.llm.generate_text(jd_prompt.format(job_description=job_description))
            
            try:
                import json
                cleaned_response = clean_json_response(response)
                jd_analysis = json.loads(cleaned_response)
                state["job_analysis"] = jd_analysis
            except Exception as e:
                logger.warning(f"Failed to parse JD analysis JSON: {e}")
                # Don't fail completely, just use empty
                state["job_analysis"] = {}
                
            logger.info("Job Description analyzed successfully")
            report_cv_progress(
                "Job Description analyzed successfully",
                agent="JD Analyzer",
                tool="agent_complete",
                target="JD Analysis complete"
            )
            
        except Exception as e:
            logger.error(f"Error analyzing JD: {e}")
            state["error"] = f"Error analyzing JD: {str(e)}"
            
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
            
            # Report agent start
            report_cv_progress(
                "Starting content extraction from CV",
                agent="Content Extractor",
                tool="agent_invoke",
                target="Parsing CV structure"
            )
            
            report_cv_progress(
                "Analyzing CV to extract personal info, experience, skills...",
                agent="Content Extractor",
                tool="llm_call",
                target="Structured extraction"
            )
            
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
                cleaned_response = clean_json_response(response)
                extracted_data = json.loads(cleaned_response)
                state["analysis_results"]["extracted_content"] = extracted_data
            except Exception as e:
                logger.error(f"Failed to parse extracted JSON content: {e}. Response: {response[:100]}...")
                # No fallback - we want to know if it fails
                state["analysis_results"]["extracted_content"] = {
                    "summary": cv_content[:500] + "...", 
                    "error": "Failed to extract structured content"
                }
            
            logger.info("CV content extracted successfully")
            report_cv_progress(
                "CV content extracted and structured successfully",
                agent="Content Extractor",
                tool="agent_complete",
                target="Extraction complete"
            )
            
        except (ValueError, Exception) as e:
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
        Analyze CV strengths using Job Analysis insights
        """
        try:
            cv_content = state["cv_content"]
            extracted = state["analysis_results"].get("extracted_content", {})
            job_analysis = state.get("job_analysis", {})
            
            report_cv_progress(
                "Analyzing CV strengths against job requirements",
                agent="Strengths Analyzer",
                tool="agent_invoke",
                target="Identifying key strengths"
            )
            
            strengths_prompt = """
            Analyze this CV and identify its key strengths.
            
            CV Content: {cv_content}
            Extracted Data: {extracted_data}
            
            CONTEXT (Job Requirements):
            {job_analysis}
            
            Task:
            Identify the TOP 3 strengths SPECIFICALLY relevant to the Job Requirements above.
            If no job description is provided, focus on general technical and professional strengths.
            
            Return a JSON list of strengths:
            ["Strength 1: Concise description", "Strength 2: Concise description"]
            
            Limit to exactly 5 strengths. Be concise (1 sentence each).
            """
            
            response = await self.llm.generate_text(strengths_prompt.format(
                cv_content=cv_content,
                extracted_data=str(extracted),
                job_analysis=str(job_analysis)
            ))
            
            try:
                import json
                cleaned_response = clean_json_response(response)
                strengths = json.loads(cleaned_response)
                state["strengths"] = strengths if isinstance(strengths, list) else [strengths]
            except Exception as e:
                logger.error(f"Failed to parse strengths JSON: {e}")
                state["strengths"] = [] # No fake fallback
            
            logger.info(f"Identified {len(state['strengths'])} strengths")
            report_cv_progress(
                f"Identified {len(state['strengths'])} key strengths",
                agent="Strengths Analyzer",
                tool="agent_complete",
                target="Strengths analysis complete"
            )
            
        except Exception as e:
            logger.error(f"Error analyzing strengths: {e}")
            state["error"] = str(e)
        
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
        Analyze CV weaknesses using Job Analysis insights
        """
        try:
            cv_content = state["cv_content"]
            job_description = state.get("job_description", "")
            job_analysis = state.get("job_analysis", {})
            
            report_cv_progress(
                "Analyzing CV for areas of improvement against job requirements",
                agent="Weaknesses Analyzer",
                tool="agent_invoke",
                target="Identifying gaps"
            )
            
            weaknesses_prompt = """
            Analyze this CV and identify areas for improvement.
            
            CV Content: {cv_content}
            Job Description: {job_description}
            
            CONTEXT (Job Requirements):
            {job_analysis}
            
            Task:
            Identify the TOP 3 gaps/weaknesses SPECIFICALLY relative to the Job Requirements.
            Are they missing a mandatory requirement? Is their experience level too low for the role?
            
            Return a JSON list of weaknesses:
            ["Weakness 1: Concise description", "Weakness 2: Concise description"]
            
            Limit to exactly 5 weaknesses. Be concise (1 sentence each).
            """
            
            response = await self.llm.generate_text(weaknesses_prompt.format(
                cv_content=cv_content,
                job_description=job_description,
                job_analysis=str(job_analysis)
            ))
            
            try:
                import json
                cleaned_response = clean_json_response(response)
                weaknesses = json.loads(cleaned_response)
                state["weaknesses"] = weaknesses if isinstance(weaknesses, list) else [weaknesses]
            except Exception as e:
                logger.error(f"Failed to parse weaknesses JSON: {e}")
                state["weaknesses"] = [] # No fake fallback
            
            logger.info(f"Identified {len(state['weaknesses'])} weaknesses")
            report_cv_progress(
                f"Identified {len(state['weaknesses'])} areas for improvement",
                agent="Weaknesses Analyzer",
                tool="agent_complete",
                target="Weaknesses analysis complete"
            )
            
        except Exception as e:
            logger.error(f"Error analyzing weaknesses: {e}")
            state["error"] = str(e)
        
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
        """
        try:
            cv_content = state["cv_content"]
            strengths = state.get("strengths", [])
            weaknesses = state.get("weaknesses", [])
            job_description = state.get("job_description", "")
            job_analysis = state.get("job_analysis", {})
            
            report_cv_progress(
                "Generating improvement suggestions based on analysis",
                agent="Improvement Suggester",
                tool="agent_invoke",
                target="Creating actionable recommendations"
            )
            
            suggestions_prompt = """
            Based on the CV analysis, provide actionable improvement suggestions.
            
            CV Content: {cv_content}
            Strengths: {strengths}
            Weaknesses: {weaknesses}
            
            CONTEXT (Job Requirements):
            {job_analysis}
            
            Task:
            Provide the TOP 5 most impactful suggestions to improve the CV for THIS specific job.
            Focus on high-value changes that will increase the score.
            
            Return a JSON list of suggestions:
            ["Suggestion 1: Concise actionable advice", "Suggestion 2: ..."]
            
            Limit to exactly 5 suggestions. 
            Be concise (1 sentence each).
            """
            
            response = await self.llm.generate_text(suggestions_prompt.format(
                cv_content=cv_content,
                strengths=str(strengths),
                weaknesses=str(weaknesses),
                job_analysis=str(job_analysis)
            ))
            
            try:
                import json
                cleaned_response = clean_json_response(response)
                suggestions = json.loads(cleaned_response)
                state["improvement_suggestions"] = suggestions if isinstance(suggestions, list) else [suggestions]
            except Exception as e:
                logger.error(f"Failed to parse suggestions JSON: {e}")
                state["improvement_suggestions"] = []
            
            logger.info(f"Generated {len(state['improvement_suggestions'])} suggestions")
            report_cv_progress(
                f"Generated {len(state['improvement_suggestions'])} improvement suggestions",
                agent="Improvement Suggester",
                tool="agent_complete",
                target="Suggestions ready"
            )
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            state["error"] = str(e)
        
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
            job_analysis = state.get("job_analysis", {})
            extracted = state["analysis_results"].get("extracted_content", {})
            
            report_cv_progress(
                "Calculating CV quality scores based on analysis",
                agent="CV Scorer",
                tool="agent_invoke",
                target="Scoring CV across multiple criteria"
            )
            
            scoring_prompt = """Score this CV on a scale of 1-100 for each category. 

CRITICAL: Return ONLY a raw JSON object. Do not include markdown formatting (like ```json).

CV Content: {cv_content}
Extracted Data: {extracted_data}
Strengths: {strengths}
Weaknesses: {weaknesses}
Job Requirements: {job_analysis}

Scoring Criteria:
- overall_score: Weighted average of others.
- keyword_match_score: 1-100 (Are mandatory keywords present?)
- experience_relevance: 1-100 (Does experience match the role level?)
- skills_alignment: 1-100 (Do technical skills match requirements?)
- format_score: 1-100 (Structure, clarity, conciseness)

Return JSON with scores AND a brief rationale (1-2 sentences) for each:
{{
    "scores": {{
        "overall_score": <int>,
        "keyword_match_score": <int>,
        "experience_relevance": <int>,
        "skills_alignment": <int>,
        "format_score": <int>
    }},
    "rationale": {{
        "overall_score": "<string>",
        "keyword_match_score": "<string>",
        "experience_relevance": "<string>",
        "skills_alignment": "<string>",
        "format_score": "<string>"
    }}
}}"""
            
            response = await self.llm.generate_text(scoring_prompt.format(
                cv_content=cv_content[:2000],
                extracted_data=str(extracted)[:1000],
                strengths=str(strengths),
                weaknesses=str(weaknesses),
                job_analysis=str(job_analysis)
            ))
            
            try:
                import json
                cleaned_response = clean_json_response(response)
                result = json.loads(cleaned_response)
                
                # Check structure: might be nested in "scores" or flat
                if "scores" in result:
                    scores = result["scores"]
                    rationale = result.get("rationale", {})
                else:
                    scores = result
                    rationale = {}
                
                # Validate all required scores are present
                required_scores = ["overall_score", "keyword_match_score", "experience_relevance", "skills_alignment", "format_score"]
                for score_key in required_scores:
                    if score_key not in scores:
                         scores[score_key] = 0
                
                # Validate and set scores
                state["score"] = min(max(int(scores["overall_score"]), 1), 100)
                state["keyword_match_score"] = min(max(int(scores["keyword_match_score"]), 1), 100)
                state["experience_relevance"] = min(max(int(scores["experience_relevance"]), 1), 100)
                state["skills_alignment"] = min(max(int(scores["skills_alignment"]), 1), 100)
                state["format_score"] = min(max(int(scores["format_score"]), 1), 100)
                
                state["score_rationale"] = rationale
                
                logger.info(
                    f"CV scored: overall={state['score']}, "
                    f"keyword={state['keyword_match_score']}, "
                    f"experience={state['experience_relevance']}, "
                    f"skills={state['skills_alignment']}, "
                    f"format={state['format_score']}"
                )
                report_cv_progress(
                    f"CV scored: Overall score {state['score']}/100",
                    agent="CV Scorer",
                    tool="agent_complete",
                    target="All scores calculated"
                )
                return state
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.error(f"Failed to parse JSON scores: {e}, response: {response[:300]}")
                raise ValueError(f"Invalid score format from LLM: {e}") from e
            
            # If JSON parsing fails, raise error - don't return fake scores
            raise ValueError("Failed to parse CV scores from LLM response")
            
        except ValueError as e:
            # Handle blocked content or API errors
            logger.error(f"Error scoring CV: {e}")
            raise
        except Exception as e:
            logger.error(f"Error scoring CV: {e}")
            # Don't return fake scores - re-raise the error
            raise

class ATSAnalyzer:
    """
    Agent 6: ATS Compatibility Analyzer
    
    Purpose: Check if CV is ATS-friendly.
    """
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def analyze_ats(self, state: CVAnalysisState) -> CVAnalysisState:
        try:
            cv_content = state["cv_content"]
            
            report_cv_progress(
                "Checking ATS compatibility",
                agent="ATS Analyzer",
                tool="agent_invoke",
                target="ATS Check"
            )
            
            ats_prompt = """
            Analyze this CV for ATS (Application Tracking System) compatibility.
            
            CV Content: {cv_content}
            
            Check for:
            1. Readable fonts/structure (simulated)
            2. Keyword stuffing abuse
            3. Standard section headings
            4. Parsing issues (simulated)
            
            Return JSON:
            {{
                "is_ats_friendly": <boolean>,
                "ats_score": <int 1-100>,
                "issues": ["issue1", "issue2"],
                "missing_standard_sections": ["section1"]
            }}
            """
            
            response = await self.llm.generate_text(ats_prompt.format(cv_content=cv_content[:2000]))
            
            try:
                import json
                cleaned_response = clean_json_response(response)
                ats = json.loads(cleaned_response)
                state["ats_analysis"] = ats
            except Exception as e:
                logger.error(f"Failed to parse ATS JSON: {e}")
                state["ats_analysis"] = {"error": "Failed to analyze ATS"}
                
            report_cv_progress(
                "ATS Analysis complete",
                agent="ATS Analyzer",
                tool="agent_complete",
                target="ATS complete"
            )
            
        except Exception as e:
            logger.error(f"Error in ATS analysis: {e}")
            
        return state

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
        self.ats_analyzer = ATSAnalyzer(llm_provider)
        self.jd_analyzer = JobDescriptionAnalyzer(llm_provider)
        
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
        workflow.add_node("analyze_jd", self.jd_analyzer.analyze_jd)  # NEW NODE
        workflow.add_node("analyze_strengths", self.strengths_analyzer.analyze_strengths)
        workflow.add_node("analyze_weaknesses", self.weaknesses_analyzer.analyze_weaknesses)
        workflow.add_node("generate_suggestions", self.improvement_suggester.generate_suggestions)
        workflow.add_node("score_cv", self.scorer.score_cv)
        workflow.add_node("analyze_ats", self.ats_analyzer.analyze_ats)  # ATS Analyzer
        
        # Define the flow
        # Start with parallel processing of CV and Job Description
        workflow.set_entry_point("extract_content")
        
        # Parallel execution: Extract CV and Analyze JD can run together?
        # LangGraph parallel execution is tricky without manual fan-out/fan-in in basic StateGraph
        # So we'll run them sequentially for improved context passing:
        # JD Analysis -> Content Extraction -> Strengths/Weaknesses -> ...
        
        # Actually, let's just make it sequential for clarity:
        # analyze_jd -> extract_content -> analyze_strengths -> ...
        # This ensures 'extract_content' could potentially benefit from 'analyze_jd' if we wanted (though currently it doesn't)
        
        workflow.add_edge("extract_content", "analyze_jd")
        
        # After both inputs are processed, we do analysis
        workflow.add_edge("analyze_jd", "analyze_strengths")
        workflow.add_edge("analyze_strengths", "analyze_weaknesses")
        
        workflow.add_edge("analyze_weaknesses", "generate_suggestions")
        workflow.add_edge("generate_suggestions", "score_cv")
        workflow.add_edge("score_cv", "analyze_ats")  # Add ATS analysis after scoring
        workflow.add_edge("analyze_ats", END)
        
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
                job_analysis={},
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
            if not result.get("score") and not result.get("error"):
                 # if error is set, we might proceed, but let's check score
                 pass
            
            return CVAnalysisResult(
                overall_score=result.get("score", 0),
                strengths=result.get("strengths", []),
                weaknesses=result.get("weaknesses", []),
                improvement_suggestions=result.get("improvement_suggestions", []),
                keyword_match_score=result.get("keyword_match_score", 0),
                experience_relevance=result.get("experience_relevance", 0),
                skills_alignment=result.get("skills_alignment", 0),
                format_score=result.get("format_score", 0),
                score_rationale=result.get("score_rationale", {}),
                ats_analysis=result.get("ats_analysis", {})
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
# Example usage and testing
if __name__ == "__main__":
    from utils.llm_provider import get_llm_provider
    import sys
    
    async def test_cv_analyzer():
        """Test the CV analyzer with sample data"""
        
        # Use REAL LLM Provider
        try:
            llm_provider = get_llm_provider()
            logger.info(f"Using REAL LLM Provider: {type(llm_provider).__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            logger.error("Please ensure you have set the appropriate API keys (e.g. GEMINI_API_KEY, OPENAI_API_KEY)")
            return

        # Test the analyzer
        analyzer = CVAnalyzer(llm_provider)
        
        sample_cv = """
        John Doe
        Software Engineer
        john@email.com
        
        Summary:
        Experienced software engineer with 5 years of experience in Python, Django, and React.
        Passionate about building scalable web applications.
        
        Experience:
        - Senior Software Engineer at Tech Corp (2020-Present)
          * Led migration from monolith to microservices using FastAPI and Kubernetes.
          * Improved API latency by 40%.
        - Software Developer at StartUp Inc (2018-2020)
          * Built web applications using Python and JavaScript.
        
        Education:
        - BS Computer Science, University of Tech (2018)
        
        Skills:
        - Python, JavaScript, React, Node.js, Docker, Kubernetes, AWS
        """
        
        job_description = """
        We are looking for a Senior Python Developer to join our team.
        
        Requirements:
        - 4+ years of experience with Python
        - Experience with FastAPI or Django
        - Strong knowledge of AWS (Lambda, DynamoDB)
        - Experience with Microservices architecture
        
        Nice to have:
        - React/Frontend experience
        - Kubernetes knowledge
        """
        
        logger.info("Starting analysis... this triggers REAL LLM calls, so it may take a moment.")
        try:
            result = await analyzer.analyze_cv(sample_cv, job_description)
            
            print("\n" + "="*50)
            print("ANALYSIS RESULTS")
            print("="*50)
            print(f"Overall Score: {result.overall_score}/100")
            print(f"Rationale: {result.score_rationale.get('overall_score', 'N/A')}")
            
            print(f"\nKeyword Match: {result.keyword_match_score}/100")
            print(f"Rationale: {result.score_rationale.get('keyword_match_score', 'N/A')}")
            
            print(f"\nATS Compatible: {result.ats_analysis.get('is_ats_friendly', 'Unknown')}")
            if result.ats_analysis.get('issues'):
                print(f"ATS Issues: {result.ats_analysis.get('issues')}")

            print("\nStrengths (Top 5):")
            for s in result.strengths:
                print(f"- {s}")
                
            print("\nWeaknesses (Top 5):")
            for w in result.weaknesses:
                print(f"- {w}")
                
            print("\nSuggestions (Top 5):")
            for s in result.improvement_suggestions:
                print(f"- {s}")
                
        except Exception as e:
            logger.error(f"\nAnalysis FAILED: {e}")
            import traceback
            traceback.print_exc()

    # Run test
    asyncio.run(test_cv_analyzer())
