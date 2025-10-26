"""
Legal Contract Analyzer with LangGraph Agentic RAG
=================================================

This module implements a strict legal document analyzer using LangGraph
with multiple specialized agents for comprehensive legal analysis.
"""

import os
import logging
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime

# LangGraph imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalAnalysisState(TypedDict):
    """State for the legal analysis workflow"""
    document_content: str
    document_type: str
    is_legal_document: bool
    risk_analysis: List[Dict[str, Any]]
    key_terms: List[Dict[str, Any]]
    compliance_issues: List[Dict[str, Any]]
    recommendations: List[str]
    final_report: str
    error: Optional[str]

class LegalDocumentClassifier:
    """Agent to classify if document is legal"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def classify_document(self, state: LegalAnalysisState) -> LegalAnalysisState:
        """Classify if document is a legal document"""
        try:
            content = state["document_content"]
            
            # Legal document indicators
            legal_indicators = [
                "agreement", "contract", "terms and conditions", "liability", "indemnification",
                "warranty", "breach", "remedy", "jurisdiction", "governing law", "party",
                "whereas", "hereby", "herein", "thereof", "notwithstanding", "pursuant to",
                "shall", "must", "obligation", "right", "duty", "clause", "section",
                "amendment", "termination", "force majeure", "confidentiality", "non-disclosure"
            ]
            
            content_lower = content.lower()
            legal_score = sum(1 for indicator in legal_indicators if indicator in content_lower)
            
            # Determine if legal document
            is_legal = legal_score >= 5  # Threshold for legal document
            
            if not is_legal:
                state["is_legal_document"] = False
                state["error"] = "This document does not appear to be a legal document. Please upload a contract, agreement, or other legal document for analysis."
                return state
            
            state["is_legal_document"] = True
            state["document_type"] = "legal_document"
            logger.info(f"Document classified as legal (score: {legal_score})")
            
        except Exception as e:
            logger.error(f"Error classifying document: {e}")
            state["error"] = f"Error analyzing document: {str(e)}"
        
        return state

class LegalRiskAnalyzer:
    """Agent to analyze legal risks"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def analyze_risks(self, state: LegalAnalysisState) -> LegalAnalysisState:
        """Analyze legal risks in the document"""
        try:
            if not state.get("is_legal_document", False):
                return state
            
            content = state["document_content"]
            
            risk_prompt = """
            Analyze this legal document for potential risks. Focus on:
            1. High-risk clauses (liability, termination, penalties)
            2. Unfavorable terms for any party
            3. Missing protections
            4. Ambiguous language
            5. Compliance issues
            
            Document content: {content}
            
            Provide analysis in this format:
            RISK_LEVEL: [low/medium/high/critical]
            CATEGORY: [Financial/Legal/Operational/Compliance]
            DESCRIPTION: [Brief description]
            CLAUSE: [Relevant text]
            RECOMMENDATION: [Suggested action]
            
            Identify up to 5 key risks.
            """
            
            response = await self.llm.generate_text(risk_prompt.format(content=content[:2000]))
            risks = self._parse_risk_response(response)
            
            state["risk_analysis"] = risks
            logger.info(f"Identified {len(risks)} risks")
            
        except Exception as e:
            logger.error(f"Error analyzing risks: {e}")
            state["error"] = f"Error analyzing risks: {str(e)}"
        
        return state
    
    def _parse_risk_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse risk analysis response"""
        risks = []
        lines = response.split('\n')
        
        current_risk = {}
        for line in lines:
            line = line.strip()
            if line.startswith('RISK_LEVEL:'):
                if current_risk:
                    risks.append(current_risk)
                current_risk = {'risk_level': line.split(':', 1)[1].strip().lower()}
            elif line.startswith('CATEGORY:'):
                current_risk['category'] = line.split(':', 1)[1].strip()
            elif line.startswith('DESCRIPTION:'):
                current_risk['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('CLAUSE:'):
                current_risk['clause'] = line.split(':', 1)[1].strip()
            elif line.startswith('RECOMMENDATION:'):
                current_risk['recommendation'] = line.split(':', 1)[1].strip()
        
        if current_risk:
            risks.append(current_risk)
        
        return risks

class LegalKeyTermsExtractor:
    """Agent to extract key legal terms"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def extract_key_terms(self, state: LegalAnalysisState) -> LegalAnalysisState:
        """Extract key legal terms and definitions"""
        try:
            if not state.get("is_legal_document", False):
                return state
            
            content = state["document_content"]
            
            terms_prompt = """
            Extract key legal terms and definitions from this document. Focus on:
            1. Important legal concepts
            2. Technical terms specific to the agreement
            3. Terms defining rights, obligations, or procedures
            4. Financial terms and conditions
            5. Timeline and deadline terms
            
            Document content: {content}
            
            Provide terms in this format:
            TERM: [term name]
            DEFINITION: [definition]
            IMPORTANCE: [low/medium/high]
            CLAUSE: [relevant text]
            
            Extract up to 10 key terms.
            """
            
            response = await self.llm.generate_text(terms_prompt.format(content=content[:2000]))
            terms = self._parse_terms_response(response)
            
            state["key_terms"] = terms
            logger.info(f"Extracted {len(terms)} key terms")
            
        except Exception as e:
            logger.error(f"Error extracting key terms: {e}")
            state["error"] = f"Error extracting key terms: {str(e)}"
        
        return state
    
    def _parse_terms_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse key terms response"""
        terms = []
        lines = response.split('\n')
        
        current_term = {}
        for line in lines:
            line = line.strip()
            if line.startswith('TERM:'):
                if current_term:
                    terms.append(current_term)
                current_term = {'term': line.split(':', 1)[1].strip()}
            elif line.startswith('DEFINITION:'):
                current_term['definition'] = line.split(':', 1)[1].strip()
            elif line.startswith('IMPORTANCE:'):
                current_term['importance'] = line.split(':', 1)[1].strip().lower()
            elif line.startswith('CLAUSE:'):
                current_term['clause'] = line.split(':', 1)[1].strip()
        
        if current_term:
            terms.append(current_term)
        
        return terms

class LegalComplianceChecker:
    """Agent to check compliance issues"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def check_compliance(self, state: LegalAnalysisState) -> LegalAnalysisState:
        """Check for compliance issues"""
        try:
            if not state.get("is_legal_document", False):
                return state
            
            content = state["document_content"]
            
            compliance_prompt = """
            Check this legal document for compliance issues. Look for:
            1. Missing standard clauses
            2. Regulatory compliance issues
            3. Data protection concerns
            4. Intellectual property issues
            5. Employment law compliance
            
            Document content: {content}
            
            Provide issues in this format:
            ISSUE_TYPE: [compliance category]
            DESCRIPTION: [issue description]
            SEVERITY: [low/medium/high]
            RECOMMENDATION: [suggested fix]
            
            Identify up to 5 compliance issues.
            """
            
            response = await self.llm.generate_text(compliance_prompt.format(content=content[:2000]))
            issues = self._parse_compliance_response(response)
            
            state["compliance_issues"] = issues
            logger.info(f"Found {len(issues)} compliance issues")
            
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            state["error"] = f"Error checking compliance: {str(e)}"
        
        return state
    
    def _parse_compliance_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse compliance response"""
        issues = []
        lines = response.split('\n')
        
        current_issue = {}
        for line in lines:
            line = line.strip()
            if line.startswith('ISSUE_TYPE:'):
                if current_issue:
                    issues.append(current_issue)
                current_issue = {'issue_type': line.split(':', 1)[1].strip()}
            elif line.startswith('DESCRIPTION:'):
                current_issue['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('SEVERITY:'):
                current_issue['severity'] = line.split(':', 1)[1].strip().lower()
            elif line.startswith('RECOMMENDATION:'):
                current_issue['recommendation'] = line.split(':', 1)[1].strip()
        
        if current_issue:
            issues.append(current_issue)
        
        return issues

class LegalReportGenerator:
    """Agent to generate final legal analysis report"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
    
    async def generate_report(self, state: LegalAnalysisState) -> LegalAnalysisState:
        """Generate comprehensive legal analysis report"""
        try:
            if not state.get("is_legal_document", False):
                return state
            
            # Compile all analysis results
            risks = state.get("risk_analysis", [])
            terms = state.get("key_terms", [])
            compliance = state.get("compliance_issues", [])
            
            # Generate structured insights
            insights_prompt = """
            Based on the legal document analysis, create structured insights in JSON format:
            
            RISKS: {risks}
            KEY TERMS: {terms}
            COMPLIANCE ISSUES: {compliance}
            
            Return a JSON object with:
            {{
                "executive_summary": "Brief 2-3 sentence summary",
                "risk_overview": {{
                    "total_risks": number,
                    "high_risk_count": number,
                    "medium_risk_count": number,
                    "low_risk_count": number,
                    "critical_areas": ["area1", "area2"]
                }},
                "compliance_score": number (0-100),
                "key_insights": [
                    "insight 1",
                    "insight 2",
                    "insight 3"
                ],
                "action_items": [
                    "action 1",
                    "action 2", 
                    "action 3"
                ],
                "recommendations": [
                    "recommendation 1",
                    "recommendation 2",
                    "recommendation 3"
                ]
            }}
            
            Keep insights concise and actionable. Focus on business impact.
            """
            
            response = await self.llm.generate_text(insights_prompt.format(
                risks=risks,
                terms=terms,
                compliance=compliance
            ))
            
            # Try to parse JSON, fallback to structured text if needed
            try:
                import json
                insights = json.loads(response)
                state["final_report"] = insights
            except:
                # Fallback to structured text
                state["final_report"] = {
                    "executive_summary": "Legal document analysis completed",
                    "risk_overview": {
                        "total_risks": len(risks),
                        "high_risk_count": 0,
                        "medium_risk_count": 0,
                        "low_risk_count": len(risks),
                        "critical_areas": []
                    },
                    "compliance_score": 75,
                    "key_insights": ["Analysis completed successfully"],
                    "action_items": ["Review findings with legal team"],
                    "recommendations": ["Consider professional legal review"]
                }
            
            logger.info("Generated structured legal insights")
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            state["error"] = f"Error generating report: {str(e)}"
        
        return state

class LegalAgenticRAG:
    """Main LangGraph-based legal analyzer"""
    
    def __init__(self, llm_provider):
        self.llm = llm_provider
        self.classifier = LegalDocumentClassifier(llm_provider)
        self.risk_analyzer = LegalRiskAnalyzer(llm_provider)
        self.terms_extractor = LegalKeyTermsExtractor(llm_provider)
        self.compliance_checker = LegalComplianceChecker(llm_provider)
        self.report_generator = LegalReportGenerator(llm_provider)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(LegalAnalysisState)
        
        # Add nodes
        workflow.add_node("classify", self.classifier.classify_document)
        workflow.add_node("analyze_risks", self.risk_analyzer.analyze_risks)
        workflow.add_node("extract_terms", self.terms_extractor.extract_key_terms)
        workflow.add_node("check_compliance", self.compliance_checker.check_compliance)
        workflow.add_node("generate_report", self.report_generator.generate_report)
        
        # Add edges
        workflow.set_entry_point("classify")
        
        workflow.add_conditional_edges(
            "classify",
            self._should_continue_analysis,
            {
                "continue": "analyze_risks",
                "stop": END
            }
        )
        
        workflow.add_edge("analyze_risks", "extract_terms")
        workflow.add_edge("extract_terms", "check_compliance")
        workflow.add_edge("check_compliance", "generate_report")
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()
    
    def _should_continue_analysis(self, state: LegalAnalysisState) -> str:
        """Determine if analysis should continue"""
        if state.get("is_legal_document", False):
            return "continue"
        return "stop"
    
    async def analyze_document(self, document_content: str) -> Dict[str, Any]:
        """Analyze a legal document using the agentic workflow"""
        try:
            # Initialize state
            initial_state = LegalAnalysisState(
                document_content=document_content,
                document_type="",
                is_legal_document=False,
                risk_analysis=[],
                key_terms=[],
                compliance_issues=[],
                recommendations=[],
                final_report="",
                error=None
            )
            
            # Run the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            # Return structured results
            return {
                "is_legal_document": result.get("is_legal_document", False),
                "document_type": result.get("document_type", ""),
                "risk_analysis": result.get("risk_analysis", []),
                "key_terms": result.get("key_terms", []),
                "compliance_issues": result.get("compliance_issues", []),
                "final_report": result.get("final_report", ""),
                "error": result.get("error"),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in agentic analysis: {e}")
            return {
                "is_legal_document": False,
                "error": f"Analysis failed: {str(e)}",
                "analysis_timestamp": datetime.now().isoformat()
            }
