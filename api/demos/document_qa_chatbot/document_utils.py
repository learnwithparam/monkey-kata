"""
Legal Document Processing Utilities
==================================

Advanced utilities for legal document analysis including:
- Document parsing with docling/unstructured
- Risk analysis and identification
- Key terms extraction
- Legal-specific RAG pipeline

🎯 LEARNING OBJECTIVES:
- Understanding legal document structure
- Implementing risk analysis algorithms
- Working with legal embeddings and search
- Building production-ready legal AI systems
"""

import asyncio
import re
import os
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import logging
import tempfile
import shutil

# LlamaIndex imports
from llama_index.core import (
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    StorageContext,
    load_index_from_storage,
    Settings
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure LlamaIndex settings with simple approach
# Don't configure embeddings here - use the existing sentence-transformers approach
Settings.embed_model = None
Settings.llm = None
logger.info("LlamaIndex configured with fallback embeddings")

@dataclass
class DocumentChunk:
    """Represents a chunk of legal text with metadata"""
    content: str
    document_id: str
    chunk_index: int
    page_number: int
    metadata: Dict[str, Any]

class LegalDocumentProcessor:
    """LlamaIndex-based document processor for legal documents"""
    
    def __init__(self):
        self.index = None
        self.documents = []
    
    async def parse_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse a legal document using LlamaIndex
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with parsed content and metadata
        """
        try:
            logger.info(f"Parsing document with LlamaIndex: {file_path}")
            
            # Create a temporary directory for LlamaIndex
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, os.path.basename(file_path))
            shutil.copy2(file_path, temp_file)
            
            # Use LlamaIndex SimpleDirectoryReader
            reader = SimpleDirectoryReader(input_dir=temp_dir)
            documents = reader.load_data()
            
            if not documents:
                raise Exception("No content extracted from document")
            
            # Create vector index
            self.index = VectorStoreIndex.from_documents(documents)
            self.documents = documents
            
            # Extract content for metadata
            content = "\n".join([doc.text for doc in documents])
            
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
            return {
                'title': os.path.basename(file_path),
                'content': content,
                'pages': len(documents),
                'page_numbers': list(range(1, len(documents) + 1)),
                'parsed_at': datetime.now().isoformat(),
                'content_length': len(content),
                'method': 'llamaindex'
            }
                
        except Exception as e:
            logger.error(f"Error parsing document {file_path}: {e}")
            return None
    
    def chunk_document(self, document_content: Dict[str, Any], chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
        """
        Split legal document into semantic chunks using LlamaIndex
        
        Args:
            document_content: Parsed document content
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters to overlap between chunks
            
        Returns:
            List of document chunks with metadata
        """
        if not self.index:
            return []
        
        # Get nodes from the index
        nodes = self.index.docstore.get_nodes(list(self.index.docstore.docs.keys()))
        
        chunks = []
        for i, node in enumerate(nodes):
            chunks.append({
                'content': node.text,
                'page_number': getattr(node, 'metadata', {}).get('page_label', 1)
            })
        
        logger.info(f"Created {len(chunks)} chunks from document")
        return chunks
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using sentence-transformers (same as website-rag demo)
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            # Use the same approach as website-rag demo
            from sentence_transformers import SentenceTransformer
            
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            logger.info(f"Loading embedding model: {model_name}")
            model = SentenceTransformer(model_name)
            
            # Generate embeddings
            embeddings = model.encode(texts, convert_to_tensor=False)
            
            # Convert to list of lists
            if len(embeddings.shape) == 1:
                embeddings = [embeddings.tolist()]
            else:
                embeddings = embeddings.tolist()
            
            logger.info(f"Generated {len(embeddings)} embeddings using sentence-transformers")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Fallback to simple hash-based embeddings
            return self._generate_fallback_embeddings(texts)
    
    def _generate_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate simple hash-based embeddings as fallback"""
        import hashlib
        
        embeddings = []
        for text in texts:
            # Create a simple hash-based embedding
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert to 128-dimensional vector
            embedding = []
            for i in range(0, len(hash_bytes), 4):
                chunk = hash_bytes[i:i+4]
                if len(chunk) == 4:
                    # Convert 4 bytes to float
                    value = int.from_bytes(chunk, byteorder='big') / (2**32)
                    embedding.append(value)
                else:
                    embedding.append(0.0)
            
            # Pad or truncate to 128 dimensions
            while len(embedding) < 128:
                embedding.append(0.0)
            embedding = embedding[:128]
            
            embeddings.append(embedding)
        
        logger.info(f"Generated {len(embeddings)} fallback embeddings")
        return embeddings
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def chunk_document(self, document_content: Dict[str, Any], chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
        """
        Split legal document into semantic chunks
        
        Args:
            document_content: Parsed document content
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters to overlap between chunks
            
        Returns:
            List of document chunks with metadata
        """
        content = document_content['content']
        pages = document_content.get('pages', 1)
        page_numbers = document_content.get('page_numbers', [1])
        
        # Split into sentences first
        sentences = self._split_into_sentences(content)
        
        chunks = []
        current_chunk = ""
        current_page = 1
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size, start a new chunk
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append({
                    'content': current_chunk.strip(),
                    'page_number': current_page
                })
                
                # Start new chunk with overlap
                if chunk_overlap > 0:
                    overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'page_number': current_page
            })
        
        # Filter out very short chunks
        chunks = [chunk for chunk in chunks if len(chunk['content']) > 50]
        
        logger.info(f"Created {len(chunks)} chunks from document of length {len(content)}")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK or fallback"""
        try:
            from nltk.tokenize import sent_tokenize
            return sent_tokenize(text)
        except Exception as e:
            logger.warning(f"NLTK sentence tokenization failed: {e}. Using simple split.")
        
        # Fallback to simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if not self.embedding_model:
                # Fallback to simple hash-based embeddings
                logger.warning("Using fallback hash-based embeddings")
                return self._generate_fallback_embeddings(texts)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            
            # Convert to list of lists
            if len(embeddings.shape) == 1:
                embeddings = [embeddings.tolist()]
            else:
                embeddings = embeddings.tolist()
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Fallback to simple hash-based embeddings
            return self._generate_fallback_embeddings(texts)
    
    def _generate_fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate simple hash-based embeddings as fallback"""
        import hashlib
        
        embeddings = []
        for text in texts:
            # Create a simple hash-based embedding
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert to 128-dimensional vector
            embedding = []
            for i in range(0, len(hash_bytes), 4):
                chunk = hash_bytes[i:i+4]
                if len(chunk) == 4:
                    # Convert 4 bytes to float
                    value = int.from_bytes(chunk, byteorder='big') / (2**32)
                    embedding.append(value)
                else:
                    embedding.append(0.0)
            
            # Pad or truncate to 128 dimensions
            while len(embedding) < 128:
                embedding.append(0.0)
            embedding = embedding[:128]
            
            embeddings.append(embedding)
        
        logger.info(f"Generated {len(embeddings)} fallback embeddings")
        return embeddings
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

class RiskAnalyzer:
    """Analyzer for identifying legal risks in documents"""
    
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
        self.risk_keywords = {
            'high': [
                'liability', 'indemnification', 'breach', 'termination', 'penalty',
                'damages', 'warranty', 'guarantee', 'force majeure', 'default'
            ],
            'medium': [
                'confidentiality', 'non-disclosure', 'intellectual property', 'copyright',
                'trademark', 'patent', 'proprietary', 'exclusive', 'non-compete'
            ],
            'low': [
                'governing law', 'jurisdiction', 'dispute resolution', 'arbitration',
                'mediation', 'notice', 'assignment', 'severability'
            ]
        }
    
    async def analyze_risks(self, document_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze document for potential risks
        
        Args:
            document_content: Parsed document content
            
        Returns:
            List of identified risks with analysis
        """
        try:
            content = document_content['content']
            
            # Use LLM for advanced risk analysis
            risk_prompt = f"""
            Analyze this legal document for potential risks and issues. Focus on:
            1. High-risk clauses (liability, termination, penalties)
            2. Unfavorable terms for either party
            3. Missing important protections
            4. Ambiguous language that could cause disputes
            
            Document content:
            {content[:3000]}  # Limit content for prompt
            
            Provide analysis in this format:
            RISK_LEVEL: [low/medium/high/critical]
            CATEGORY: [Financial/Legal/Operational/Compliance]
            DESCRIPTION: [Brief description of the risk]
            CLAUSE: [Relevant text from document]
            RECOMMENDATION: [Suggested action]
            
            Identify up to 5 key risks.
            """
            
            response = await self.llm_provider.generate(risk_prompt, temperature=0.1, max_tokens=1000)
            
            # Parse the response into structured risks
            risks = self._parse_risk_response(response)
            
            # Add keyword-based risk detection
            keyword_risks = self._detect_keyword_risks(content)
            risks.extend(keyword_risks)
            
            # Remove duplicates and limit to top 5
            unique_risks = self._deduplicate_risks(risks)
            
            logger.info(f"Identified {len(unique_risks)} risks in document")
            return unique_risks[:5]
            
        except Exception as e:
            logger.error(f"Error analyzing risks: {e}")
            return []
    
    def _parse_risk_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured risk data"""
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
    
    def _detect_keyword_risks(self, content: str) -> List[Dict[str, Any]]:
        """Detect risks based on keyword analysis"""
        risks = []
        content_lower = content.lower()
        
        for risk_level, keywords in self.risk_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    # Find the sentence containing the keyword
                    sentences = re.split(r'[.!?]+', content)
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            risks.append({
                                'risk_level': risk_level,
                                'category': 'Keyword Detection',
                                'description': f'Document contains "{keyword}" which may indicate potential risks',
                                'clause': sentence.strip(),
                                'recommendation': f'Review clauses containing "{keyword}" for potential issues'
                            })
                            break
        
        return risks
    
    def _deduplicate_risks(self, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate risks based on description similarity"""
        unique_risks = []
        seen_descriptions = set()
        
        for risk in risks:
            description_key = risk.get('description', '').lower()
            if description_key not in seen_descriptions:
                unique_risks.append(risk)
                seen_descriptions.add(description_key)
        
        return unique_risks

class KeyTermsExtractor:
    """Extractor for identifying key legal terms and definitions"""
    
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
        self.legal_terms = [
            'agreement', 'contract', 'party', 'parties', 'obligation', 'liability',
            'indemnification', 'warranty', 'guarantee', 'breach', 'termination',
            'confidentiality', 'intellectual property', 'copyright', 'trademark',
            'patent', 'proprietary', 'exclusive', 'non-compete', 'governing law',
            'jurisdiction', 'dispute resolution', 'arbitration', 'mediation'
        ]
    
    async def extract_key_terms(self, document_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract key legal terms and their definitions
        
        Args:
            document_content: Parsed document content
            
        Returns:
            List of key terms with definitions and importance
        """
        try:
            content = document_content['content']
            
            # Use LLM for term extraction
            terms_prompt = f"""
            Extract key legal terms and their definitions from this document. Focus on:
            1. Important legal concepts and definitions
            2. Technical terms specific to the agreement
            3. Terms that define rights, obligations, or procedures
            
            Document content:
            {content[:3000]}  # Limit content for prompt
            
            Provide terms in this format:
            TERM: [term name]
            DEFINITION: [definition or explanation]
            IMPORTANCE: [low/medium/high]
            CLAUSE: [relevant text from document]
            
            Extract up to 10 key terms.
            """
            
            response = await self.llm_provider.generate(terms_prompt, temperature=0.1, max_tokens=1000)
            
            # Parse the response into structured terms
            terms = self._parse_terms_response(response)
            
            # Add keyword-based term detection
            keyword_terms = self._detect_keyword_terms(content)
            terms.extend(keyword_terms)
            
            # Remove duplicates and limit to top 10
            unique_terms = self._deduplicate_terms(terms)
            
            logger.info(f"Extracted {len(unique_terms)} key terms from document")
            return unique_terms[:10]
            
        except Exception as e:
            logger.error(f"Error extracting key terms: {e}")
            return []
    
    def _parse_terms_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured term data"""
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
    
    def _detect_keyword_terms(self, content: str) -> List[Dict[str, Any]]:
        """Detect terms based on keyword analysis"""
        terms = []
        content_lower = content.lower()
        
        for term in self.legal_terms:
            if term in content_lower:
                # Find the sentence containing the term
                sentences = re.split(r'[.!?]+', content)
                for sentence in sentences:
                    if term in sentence.lower():
                        terms.append({
                            'term': term.title(),
                            'definition': f'Legal term related to {term}',
                            'importance': 'medium',
                            'clause': sentence.strip()
                        })
                        break
        
        return terms
    
    def _deduplicate_terms(self, terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate terms based on term name"""
        unique_terms = []
        seen_terms = set()
        
        for term in terms:
            term_key = term.get('term', '').lower()
            if term_key not in seen_terms:
                unique_terms.append(term)
                seen_terms.add(term_key)
        
        return unique_terms

class LegalRAGPipeline:
    """RAG pipeline specifically designed for legal document analysis"""
    
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
    
    def retrieve_relevant_chunks(
        self, 
        query_embedding: List[float], 
        document_embeddings: List[List[float]], 
        documents: List[DocumentChunk], 
        max_chunks: int = 5
    ) -> List[DocumentChunk]:
        """
        Retrieve the most relevant document chunks for a legal query
        
        Args:
            query_embedding: Embedding vector for the query
            document_embeddings: List of embedding vectors for documents
            documents: List of document chunks
            max_chunks: Maximum number of chunks to return
            
        Returns:
            List of most relevant document chunks
        """
        try:
            if not document_embeddings or not documents:
                return []
            
            # Calculate similarities
            similarities = []
            for i, doc_embedding in enumerate(document_embeddings):
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                similarities.append((similarity, i))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # Get top chunks
            top_indices = [idx for _, idx in similarities[:max_chunks]]
            relevant_chunks = [documents[i] for i in top_indices]
            
            logger.info(f"Retrieved {len(relevant_chunks)} relevant chunks out of {len(documents)} total")
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving relevant chunks: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    async def generate_answer_stream(self, question: str, relevant_chunks: List[DocumentChunk]) -> AsyncGenerator[str, None]:
        """
        Generate a streaming document analysis using the LLM and relevant chunks
        
        Args:
            question: The user's question
            relevant_chunks: Relevant document chunks
            
        Yields:
            Chunks of the generated document analysis
        """
        try:
            if not relevant_chunks:
                yield "I don't have enough information to answer your question. Please make sure the document has been processed and contains relevant content."
                return
            
            # Prepare context from relevant chunks
            context_parts = []
            for i, chunk in enumerate(relevant_chunks, 1):
                context_parts.append(f"Source {i} (Page {chunk.page_number}):\n{chunk.content}")
            
            context = "\n\n".join(context_parts)
            
            # Create concise chatbot prompt
            prompt = f"""You are a helpful chatbot analyzing a document. Give concise, direct answers.

Document Context:
{context}

Question: {question}

Instructions:
1. Answer in MAX 100 words - be concise and direct
2. ONLY use information from the document context above
3. If no relevant info, say "I don't have that information in the document."
4. Focus on answering the question directly
5. Use simple, conversational language
6. Include specific details from the document when relevant

Answer:"""
            
            # Generate streaming answer
            async for chunk in self.llm_provider.generate_stream(prompt, temperature=0.1, max_tokens=150):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error generating streaming document analysis: {e}")
            yield f"Sorry, I encountered an error while analyzing your question: {str(e)}"

# Example usage and testing
if __name__ == "__main__":
    async def test_legal_pipeline():
        """Test the legal analysis pipeline with sample data"""
        from utils.llm_provider import get_llm_provider
        
        # Initialize components
        llm_provider = get_llm_provider()
        document_processor = LegalDocumentProcessor()
        risk_analyzer = RiskAnalyzer(llm_provider)
        key_terms_extractor = KeyTermsExtractor(llm_provider)
        legal_rag_pipeline = LegalRAGPipeline(llm_provider)
        
        # Test document processing
        print("Testing legal document processing...")
        
        # Test risk analysis
        print("Testing risk analysis...")
        sample_content = {
            'content': 'This agreement contains liability limitations and termination clauses...',
            'title': 'Sample Contract'
        }
        risks = await risk_analyzer.analyze_risks(sample_content)
        print(f"Identified {len(risks)} risks")
        
        # Test key terms extraction
        print("Testing key terms extraction...")
        terms = await key_terms_extractor.extract_key_terms(sample_content)
        print(f"Extracted {len(terms)} key terms")
        
        print("Legal analysis pipeline test completed!")
    
    # Run test
    asyncio.run(test_legal_pipeline())
