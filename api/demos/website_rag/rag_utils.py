"""
RAG Utilities
=============

🎯 LEARNING OBJECTIVES:
This module teaches the core components of RAG:

1. Web Scraping - Extract content from websites
2. Text Chunking - Split content into searchable pieces
3. Embeddings - Convert text to vectors for similarity search
4. Vector Search - Find relevant information
5. RAG Prompting - Combine context with questions

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Web Scraping - How to extract clean content from HTML
Step 2: Text Chunking - How to split text intelligently
Step 3: Embeddings - How to convert text to numbers
Step 4: Similarity Search - How to find relevant chunks
Step 5: RAG Generation - How to create prompts with context
"""

import re
import os
import numpy as np
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import nltk
from sentence_transformers import SentenceTransformer

# Download required NLTK data for sentence tokenization
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)


# ============================================================================
# STEP 1: DATA STRUCTURES
# ============================================================================
"""
DocumentChunk:
Represents a piece of text with metadata. This helps us:
- Track where each chunk came from (URL)
- Store additional context (title, chunk index)
- Retrieve chunks with their source information
"""
@dataclass
class DocumentChunk:
    """Represents a chunk of text with metadata"""
    content: str
    url: str
    chunk_index: int
    metadata: Dict[str, Any]


# ============================================================================
# STEP 2: WEB SCRAPING
# ============================================================================
"""
Web Scraping:
The first step in RAG is getting content from websites.

Key Concepts:
- HTML Parsing: Extract text from HTML structure
- Content Extraction: Find the main content (not nav, footer, ads)
- Text Cleaning: Remove extra whitespace and irrelevant text
- Error Handling: Handle network errors and invalid URLs

Strategy:
1. Fetch HTML from URL
2. Parse with BeautifulSoup
3. Remove unwanted elements (scripts, navs, footers)
4. Find main content area
5. Extract and clean text
"""
class WebScraper:
    """Extracts clean text content from websites"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=10.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
    
    async def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape content from a URL
        
        Process:
        1. Fetch HTML content
        2. Parse with BeautifulSoup
        3. Remove unwanted elements
        4. Find main content
        5. Extract and clean text
        
        Returns dictionary with title, content, and metadata.
        """
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        response = await self.client.get(url, follow_redirects=True)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""
        
        # Remove unwanted elements (scripts, styles, navigation, etc.)
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]):
            element.decompose()
        
        # Find main content using multiple strategies
        main_content = None
        
        # Strategy 1: Look for semantic HTML5 elements
        for tag in ['main', 'article', 'section']:
            main_content = soup.find(tag)
            if main_content:
                break
        
        # Strategy 2: Look for common content class names
        if not main_content:
            for class_name in ['content', 'main-content', 'post-content', 'entry-content', 'article-content']:
                main_content = soup.find('div', class_=re.compile(class_name, re.I))
                if main_content:
                    break
        
        # Strategy 3: Find div with most text content
        if not main_content:
            divs = soup.find_all('div')
            max_text_length = 0
            for div in divs:
                text_length = len(div.get_text(strip=True))
                if text_length > max_text_length and text_length > 200:
                    max_text_length = text_length
                    main_content = div
        
        # Strategy 4: Fallback to body
        if not main_content:
            main_content = soup.find('body')
        
        # Extract text
        if main_content:
            content = main_content.get_text(separator=' ', strip=True)
        else:
            content = soup.get_text(separator=' ', strip=True)
        
        # Clean text
        content = self._clean_text(content)
        
        if not content or len(content) < 50:
            return None
        
        return {
            'title': title,
            'content': content,
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'content_length': len(content)
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove navigation elements
        text = re.sub(r'Skip to content|Menu|Navigation|Search', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def chunk_content(self, content_data: Dict[str, Any], chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """
        Split content into overlapping chunks
        
        Why Chunking?
        - LLMs have context window limits
        - Smaller chunks are easier to search
        - Overlap preserves context across boundaries
        
        How It Works:
        1. Split text into sentences
        2. Build chunks by adding sentences
        3. When chunk would exceed size, start new chunk
        4. Use overlap to preserve context
        
        Args:
            content_data: Dictionary with 'title' and 'content'
            chunk_size: Maximum characters per chunk
            chunk_overlap: Characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        content = content_data['content']
        title = content_data.get('title', '')
        
        # Add title to beginning for context
        if title:
            full_content = f"{title}\n\n{content}"
        else:
            full_content = content
        
        # Split into sentences (preserves meaning better than character splitting)
        sentences = self._split_into_sentences(full_content)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size, finalize current chunk
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
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
            chunks.append(current_chunk.strip())
        
        # Filter out very short chunks
        chunks = [chunk for chunk in chunks if len(chunk) > 50]
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK"""
        try:
            from nltk.tokenize import sent_tokenize
            return sent_tokenize(text)
        except Exception:
            # Fallback to simple sentence splitting
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]


# ============================================================================
# STEP 3: EMBEDDINGS
# ============================================================================
"""
Embeddings:
Convert text into vectors (arrays of numbers) that represent meaning.

Key Concepts:
- Semantic Similarity: Similar meanings → similar vectors
- Dimensionality: Each embedding is a fixed-size vector (e.g., 384 numbers)
- Distance Metrics: Cosine similarity measures how similar two vectors are

How It Works:
1. Load a pre-trained embedding model (SentenceTransformer)
2. Encode text → vector
3. Compare vectors using cosine similarity
4. Similar vectors = similar meaning

Why Embeddings?
- Enable semantic search (find "car" when user asks about "automobile")
- Much faster than keyword matching
- Works across languages (if using multilingual models)
"""
class EmbeddingProvider:
    """Generates embeddings (vector representations) of text"""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedding provider
        
        Uses SentenceTransformer models which are:
        - Fast (runs locally)
        - Free (no API costs)
        - Good quality for semantic search
        
        Popular models:
        - all-MiniLM-L6-v2: Fast, 384 dimensions
        - all-mpnet-base-v2: Slower, better quality, 768 dimensions
        """
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model = SentenceTransformer(self.model_name)
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Process:
        1. Pass texts to model
        2. Model encodes each text to a vector
        3. Return list of vectors
        
        Each vector is a list of floats representing the text's meaning.
        """
        # Generate embeddings (this is synchronous, but we wrap in async for consistency)
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        
        # Convert numpy array to list of lists
        if len(embeddings.shape) == 1:
            return [embeddings.tolist()]
        else:
            return embeddings.tolist()
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Cosine similarity measures the angle between two vectors.
        - Returns value between -1 and 1
        - 1 = identical meaning
        - 0 = unrelated
        - -1 = opposite meaning
        
        Formula: dot_product(vec1, vec2) / (norm(vec1) * norm(vec2))
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


# ============================================================================
# STEP 4: RAG PIPELINE
# ============================================================================
"""
RAG Pipeline:
Combines retrieval (finding relevant chunks) with generation (LLM answering).

The Complete Flow:
1. User asks a question
2. Generate embedding for the question
3. Compare with all document embeddings (similarity search)
4. Retrieve top-K most similar chunks
5. Build prompt with question + relevant chunks
6. Generate answer using LLM

Why This Works:
- Only relevant context sent to LLM (saves tokens, improves accuracy)
- LLM has exactly what it needs to answer
- Much better than sending entire website content
"""
class SimpleRAGPipeline:
    """Complete RAG pipeline: retrieval + generation"""
    
    def __init__(self, llm_provider, embedding_provider: EmbeddingProvider):
        self.llm_provider = llm_provider
        self.embedding_provider = embedding_provider
    
    def retrieve_relevant_chunks(
        self, 
        query_embedding: List[float], 
        document_embeddings: List[List[float]], 
        documents: List[DocumentChunk], 
        max_chunks: int = 5
    ) -> List[DocumentChunk]:
        """
        Find the most relevant document chunks for a query
        
        Process:
        1. Calculate similarity between query and each document
        2. Sort by similarity (highest first)
        3. Return top-K chunks
        
        This is the "R" (Retrieval) part of RAG.
        """
        if not document_embeddings or not documents:
            return []
        
        # Calculate similarities
        similarities = []
        for i, doc_embedding in enumerate(document_embeddings):
            similarity = self.embedding_provider.cosine_similarity(query_embedding, doc_embedding)
            similarities.append((similarity, i))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Get top chunks
        top_indices = [idx for _, idx in similarities[:max_chunks]]
        return [documents[i] for i in top_indices]
    
    async def generate_answer_stream(
        self, 
        question: str, 
        relevant_chunks: List[DocumentChunk]
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming answer using LLM with retrieved context
        
        This is the "G" (Generation) part of RAG.
        
        Process:
        1. Build context from relevant chunks
        2. Create RAG prompt with context + question
        3. Stream answer from LLM
        
        RAG Prompt Structure:
        - Context from retrieved chunks
        - User question
        - Instructions to use only the context
        """
        if not relevant_chunks:
            yield "I don't have enough information to answer your question."
            return
        
        # Build context from relevant chunks
        context_parts = []
        for i, chunk in enumerate(relevant_chunks, 1):
            context_parts.append(f"Source {i} (from {chunk.url}):\n{chunk.content}")
        
        context = "\n\n".join(context_parts)
        
        # Create RAG prompt
        prompt = f"""You are a helpful chatbot that answers questions based on website content.

Context from the website:
{context}

User Question: {question}

Instructions:
1. Answer the question using ONLY information from the context above
2. Be concise and helpful
3. If the context doesn't contain relevant information, say so
4. Do not make up information that's not in the context
5. Focus on what the website offers and how it can help

Answer:"""
        
        # Stream answer from LLM
        async for chunk in self.llm_provider.generate_stream(
            prompt,
            temperature=0.1,  # Low temperature for factual accuracy
            max_tokens=300
        ):
            yield chunk


# ============================================================================
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How to scrape and clean website content
✓ How to chunk text intelligently (sentence-based, with overlap)
✓ How embeddings convert text to vectors
✓ How cosine similarity finds relevant chunks
✓ How to build a RAG prompt with context
✓ The complete RAG pipeline flow

Key RAG Concepts:
- Ingestion: URL → scrape → chunk → embed → store
- Query: Question → embed → search → context → answer
- Why RAG works: Relevant context + LLM understanding = accurate answers

Next Steps:
1. Experiment with different chunk sizes
2. Try different embedding models
3. Add multiple URLs and see cross-source retrieval
4. Implement persistent vector database
5. Add re-ranking for better chunk quality

Questions to Consider:
- What's the optimal chunk size? (too small = lost context, too large = less precise)
- How does overlap affect retrieval quality?
- What happens if no relevant chunks are found?
- How would you handle conflicting information from different sources?
"""