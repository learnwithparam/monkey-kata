"""
CV Analyzer - LangGraph-based Job CV Analysis and Improvement Suggester
======================================================================

A cost-effective multi-agent system for analyzing CVs and providing improvement suggestions.
Uses LangGraph for orchestration with specialized agents for different analysis tasks.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass
from datetime import datetime

# LangGraph imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CVAnalysisState(TypedDict):
    """State for CV analysis workflow"""
    cv_content: str
    job_description: Optional[str]
    analysis_results: Dict[str, Any]
    improvement_suggestions: List[str]
    strengths: List[str]
    weaknesses: List[str]
    score: int
    error: Optional[str]

@dataclass
class CVAnalysisResult:
    """Result of CV analysis"""
    overall_score: int
    strengths: List[str]
    weaknesses: List[str]
    improvement_suggestions: List[str]
    keyword_match_score: int
    experience_relevance: int
    skills_alignment: int
    format_score: int

class CVContentExtractor:
    """Agent for extracting and structuring CV content"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def extract_content(self, state: CVAnalysisState) -> CVAnalysisState:
        """Extract structured content from CV"""
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
            
        except Exception as e:
            logger.error(f"Error extracting CV content: {e}")
            state["error"] = f"Error extracting CV content: {str(e)}"
        
        return state

class CVStrengthsAnalyzer:
    """Agent for analyzing CV strengths"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def analyze_strengths(self, state: CVAnalysisState) -> CVAnalysisState:
        """Analyze CV strengths"""
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
            
            Keep each strength concise (1-2 sentences max).
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
            
        except Exception as e:
            logger.error(f"Error analyzing strengths: {e}")
            state["strengths"] = ["Analysis completed"]
        
        return state

class CVWeaknessesAnalyzer:
    """Agent for analyzing CV weaknesses"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def analyze_weaknesses(self, state: CVAnalysisState) -> CVAnalysisState:
        """Analyze CV weaknesses"""
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
            
            Be constructive and specific. Keep each weakness concise.
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
            
        except Exception as e:
            logger.error(f"Error analyzing weaknesses: {e}")
            state["weaknesses"] = ["Analysis completed"]
        
        return state

class CVImprovementSuggester:
    """Agent for generating improvement suggestions"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def generate_suggestions(self, state: CVAnalysisState) -> CVAnalysisState:
        """Generate actionable improvement suggestions"""
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
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            state["improvement_suggestions"] = ["Review and improve CV content"]
        
        return state

class CVScorer:
    """Agent for scoring CV overall quality"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def score_cv(self, state: CVAnalysisState) -> CVAnalysisState:
        """Calculate overall CV score"""
        try:
            cv_content = state["cv_content"]
            strengths = state.get("strengths", [])
            weaknesses = state.get("weaknesses", [])
            job_description = state.get("job_description", "")
            
            scoring_prompt = """
            Score this CV on a scale of 1-100:
            
            CV Content: {cv_content}
            Strengths: {strengths}
            Weaknesses: {weaknesses}
            Job Description: {job_description}
            
            Consider:
            - Relevance to job description (30%)
            - Experience and achievements (25%)
            - Skills and qualifications (20%)
            - Formatting and presentation (15%)
            - Completeness (10%)
            
            Return only a number between 1-100.
            """
            
            response = await self.llm.generate_text(scoring_prompt.format(
                cv_content=cv_content,
                strengths=str(strengths),
                weaknesses=str(weaknesses),
                job_description=job_description
            ))
            
            # Extract number from response
            import re
            score_match = re.search(r'\b(\d{1,3})\b', response)
            if score_match:
                score = int(score_match.group(1))
                state["score"] = min(max(score, 1), 100)  # Clamp between 1-100
            else:
                state["score"] = 75  # Default score
            
            logger.info(f"CV scored: {state['score']}/100")
            
        except Exception as e:
            logger.error(f"Error scoring CV: {e}")
            state["score"] = 75
        
        return state

class CVAnalyzer:
    """Main LangGraph-based CV analyzer"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
        self.content_extractor = CVContentExtractor(llm_provider)
        self.strengths_analyzer = CVStrengthsAnalyzer(llm_provider)
        self.weaknesses_analyzer = CVWeaknessesAnalyzer(llm_provider)
        self.improvement_suggester = CVImprovementSuggester(llm_provider)
        self.scorer = CVScorer(llm_provider)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
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
    
    async def analyze_cv(self, cv_content: str, job_description: str = "") -> CVAnalysisResult:
        """Analyze CV and return results"""
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
                error=None
            )
            
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            # Return structured result
            return CVAnalysisResult(
                overall_score=result["score"],
                strengths=result["strengths"],
                weaknesses=result["weaknesses"],
                improvement_suggestions=result["improvement_suggestions"],
                keyword_match_score=75,  # Placeholder
                experience_relevance=80,  # Placeholder
                skills_alignment=70,  # Placeholder
                format_score=85  # Placeholder
            )
            
        except Exception as e:
            logger.error(f"Error in CV analysis: {e}")
            return CVAnalysisResult(
                overall_score=50,
                strengths=["Analysis completed"],
                weaknesses=["Review required"],
                improvement_suggestions=["Please try again"],
                keyword_match_score=50,
                experience_relevance=50,
                skills_alignment=50,
                format_score=50
            )

# Example usage
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
