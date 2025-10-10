"""
Simple RAG Utilities
===================

Core utilities for implementing simple, fast RAG (Retrieval-Augmented Generation) functionality.

This module provides:
- Web scraping capabilities
- Text chunking strategies
- Embedding generation
- Vector similarity search
- Simple RAG pipeline implementation

🎯 LEARNING OBJECTIVES:
- Understanding RAG architecture
- Implementing semantic chunking
- Working with embeddings and vector search
- Building production-ready RAG systems
"""

import asyncio
import re
import os
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import nltk
from sentence_transformers import SentenceTransformer
import logging

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

# Also download punkt_tab for newer NLTK versions
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Represents a chunk of text with metadata"""
    content: str
    url: str
    chunk_index: int
    metadata: Dict[str, Any]

class WebScraper:
    """Simple web scraper for extracting content from URLs"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=10.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
    
    async def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape content from a URL
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary with title, content, and metadata
        """
        try:
            logger.info(f"Scraping URL: {url}")
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            response = await self.client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            # Check if content is HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(f"URL {url} is not HTML content: {content_type}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]):
                element.decompose()
            
            # Extract main content
            content = ""
            
            # Try multiple strategies to find main content
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
            
            # Strategy 3: Look for div with high text content
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
            
            if main_content:
                content = main_content.get_text(separator=' ', strip=True)
            else:
                # Last resort: get all text
                content = soup.get_text(separator=' ', strip=True)
            
            # Clean up content
            content = self._clean_text(content)
            
            if not content or len(content) < 50:
                logger.warning(f"Content too short or empty for URL: {url} (length: {len(content)})")
                return None
            
            logger.info(f"Successfully scraped URL {url}: {len(content)} characters")
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'content_length': len(content)
            }
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error scraping URL {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common web artifacts
        text = re.sub(r'Cookie Policy|Privacy Policy|Terms of Service|Subscribe|Newsletter', '', text, flags=re.IGNORECASE)
        
        # Remove email addresses and phone numbers
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '', text)
        
        return text.strip()
    
    def chunk_content(self, content_data: Dict[str, Any], chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """
        Split content into overlapping chunks
        
        Args:
            content_data: Dictionary with title and content
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        content = content_data['content']
        title = content_data.get('title', '')
        
        # Add title to beginning of content
        if title:
            full_content = f"{title}\n\n{content}"
        else:
            full_content = content
        
        # Split into sentences first
        sentences = self._split_into_sentences(full_content)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size, start a new chunk
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
        
        logger.info(f"Created {len(chunks)} chunks from content of length {len(full_content)}")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK"""
        try:
            # Download required NLTK data if not present
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
            
            from nltk.tokenize import sent_tokenize
            return sent_tokenize(text)
        except Exception as e:
            logger.warning(f"NLTK sentence tokenization failed: {e}. Using simple split.")
            # Fallback to simple sentence splitting
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]

class EmbeddingProvider:
    """Provider for generating text embeddings"""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedding provider
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if not self.model:
                raise Exception("Embedding model not loaded")
            
            # Generate embeddings
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            
            # Convert to list of lists
            if len(embeddings.shape) == 1:
                embeddings = [embeddings.tolist()]
            else:
                embeddings = embeddings.tolist()
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
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

class SimpleRAGPipeline:
    """Simple RAG pipeline implementation"""
    
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
        Retrieve the most relevant document chunks for a query
        
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
                similarity = self.embedding_provider.cosine_similarity(query_embedding, doc_embedding)
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
    
    async def generate_answer_stream(self, question: str, relevant_chunks: List[DocumentChunk]) -> AsyncGenerator[str, None]:
        """
        Generate a streaming answer using the LLM and relevant chunks
        
        Args:
            question: The user's question
            relevant_chunks: Relevant document chunks
            
        Yields:
            Chunks of the generated answer
        """
        try:
            if not relevant_chunks:
                yield "I don't have enough information to answer your question. Please make sure the URL has been processed and contains relevant content."
                return
            
            # Prepare context from relevant chunks
            context_parts = []
            for i, chunk in enumerate(relevant_chunks, 1):
                context_parts.append(f"Source {i} (from {chunk.url}):\n{chunk.content}")
            
            context = "\n\n".join(context_parts)
            
            # Create RAG prompt
            prompt = f"""You are the official chatbot for this website. You represent the website and its services. Answer questions as if you are the website's own customer service representative.

Context from the website:
{context}

User Question: {question}

Instructions:
1. Answer as the website's chatbot - be helpful, friendly, and professional
2. Use "we", "our", "us" when referring to the website's services
3. Be specific and cite relevant information from the website content
4. If you don't have enough information, politely explain what you can help with
5. Keep answers concise but comprehensive
6. Focus on what the website offers and how it can help the user

Answer:"""
            
            # Generate streaming answer
            async for chunk in self.llm_provider.generate_stream(prompt, temperature=0.3, max_tokens=1000):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error generating streaming answer: {e}")
            yield f"Sorry, I encountered an error while generating an answer: {str(e)}"

# Example usage and testing
if __name__ == "__main__":
    async def test_rag_pipeline():
        """Test the RAG pipeline with sample data"""
        from utils.llm_provider import get_llm_provider
        
        # Initialize components
        llm_provider = get_llm_provider()
        embedding_provider = EmbeddingProvider()
        web_scraper = WebScraper()
        rag_pipeline = SimpleRAGPipeline(llm_provider, embedding_provider)
        
        # Test web scraping
        print("Testing web scraping...")
        content = await web_scraper.scrape_url("https://example.com")
        if content:
            print(f"Scraped content: {content['title']}")
            
            # Test chunking
            chunks = web_scraper.chunk_content(content, chunk_size=200, chunk_overlap=50)
            print(f"Created {len(chunks)} chunks")
            
            # Test embeddings
            print("Testing embeddings...")
            embeddings = await embedding_provider.generate_embeddings(chunks)
            print(f"Generated {len(embeddings)} embeddings")
            
            # Test RAG
            print("Testing RAG...")
            question = "What is this website about?"
            query_embedding = await embedding_provider.generate_embeddings([question])
            
            # Create document chunks
            documents = []
            for i, chunk in enumerate(chunks):
                doc = DocumentChunk(
                    content=chunk,
                    url="https://example.com",
                    chunk_index=i,
                    metadata={"title": content['title']}
                )
                documents.append(doc)
            
            relevant_chunks = rag_pipeline.retrieve_relevant_chunks(
                query_embedding[0], embeddings, documents, max_chunks=3
            )
            
            print("Streaming answer:")
            async for chunk in rag_pipeline.generate_answer_stream(question, relevant_chunks):
                print(chunk, end="", flush=True)
            print()
    
    # Run test
    asyncio.run(test_rag_pipeline())