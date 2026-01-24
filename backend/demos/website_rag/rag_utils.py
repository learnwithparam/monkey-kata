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
import shutil
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# STEP 2: WEB SCRAPING
# ============================================================================
class WebScraper:
    """Extracts clean text content from websites"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=10.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            follow_redirects=True
        )
        # Use LangChain's splitter for more robust chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
    
    async def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape content from a URL"""
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else ""
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "iframe"]):
                element.decompose()
            
            # Extract main content (simplified strategy for robustness)
            # Try to find common main content containers
            main_content = soup.find('main') or \
                           soup.find('article') or \
                           soup.find('div', class_=re.compile(r'content|main|article', re.I)) or \
                           soup.body
                           
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)
            
            # Clean text
            clean_text = self._clean_text(text)
            
            if not clean_text or len(clean_text) < 50:
                logger.warning(f"Extracted content too short for {url}")
                return None
            
            return {
                'title': title,
                'content': clean_text,
                'url': url,
                'scraped_at': datetime.now().isoformat(),
                'content_length': len(clean_text)
            }
            
        except httpx.RequestError as e:
            logger.error(f"Error scraping {url}: {e}")
            raise Exception(f"Failed to fetch website: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            raise Exception(f"Failed to process website content: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def chunk_content(self, content_data: Dict[str, Any], chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """Split content into chunks using LangChain splitter"""
        # Update splitter settings if needed
        self.text_splitter._chunk_size = chunk_size
        self.text_splitter._chunk_overlap = chunk_overlap
        
        content = content_data['content']
        chunks = self.text_splitter.split_text(content)
        return chunks


# ============================================================================
# STEP 3: EMBEDDINGS & RERANKING
# ============================================================================
class EmbeddingProvider:
    """Generates embeddings (vector representations) of text"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(self.model_name)
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        if not texts:
            return []
        
        # Run in executor to avoid blocking asyncio loop
        # For simplicity in this demo, we run directly since SentenceTransformer is fast enough for small batches
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        
        if len(embeddings.shape) == 1:
            return [embeddings.tolist()]
        else:
            return embeddings.tolist()


class Reranker:
    """Reranks retrieved documents to improve relevance"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        try:
            self.model = CrossEncoder(model_name)
        except Exception as e:
            logger.warning(f"Failed to load reranker model {model_name}: {e}")
            self.model = None

    def rerank(self, query: str, docs: List[DocumentChunk], top_k: int = 5) -> List[DocumentChunk]:
        """
        Rerank a list of documents based on query relevance using a Cross-Encoder.
        Cross-Encoders are more accurate but slower than bi-encoders (embeddings).
        """
        if not self.model or not docs:
            return docs[:top_k]
        
        # Prepare pairs for cross-encoder
        pairs = [[query, doc.content] for doc in docs]
        
        # Predict scores
        scores = self.model.predict(pairs)
        
        # Combine docs with scores
        doc_scores = list(zip(docs, scores))
        
        # Sort by score (descending)
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k docs
        return [doc for doc, score in doc_scores[:top_k]]


# ============================================================================
# STEP 4: VECTOR STORE (ChromaDB)
# ============================================================================
class VectorStore:
    """Manages document storage and retrieval using ChromaDB"""
    
    def __init__(self, collection_name: str = "website_rag"):
        self.persist_directory = "./chroma_db"
        self.collection_name = collection_name
        
        # Initialize client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Get or create collection
        # We don't provide an embedding function here because we generate embeddings manually
        # to have control over the model used
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
    def add_documents(self, documents: List[DocumentChunk], embeddings: List[List[float]]):
        """Add documents and their embeddings to the store"""
        if not documents:
            return
            
        ids = [f"{doc.url}_{doc.chunk_index}" for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        documents_content = [doc.content for doc in documents]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents_content
        )
        
    def query(self, query_embedding: List[float], n_results: int = 20, where: Optional[Dict] = None) -> List[DocumentChunk]:
        """Query the vector store"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        # Parse results back to DocumentChunks
        chunks = []
        if results['ids'] and len(results['ids']) > 0:
            # Create a simplified dict traversal for safety
            result_ids = results['ids'][0]
            result_docs = results['documents'][0]
            result_metadatas = results['metadatas'][0]
            
            for i in range(len(result_ids)):
                # Reconstruct DocumentChunk
                meta = result_metadatas[i] if result_metadatas else {}
                content = result_docs[i] if result_docs else ""
                url = meta.get('url', '')
                # Try to parse index from ID or metadata, default to 0
                try:
                    chunk_index = int(result_ids[i].split('_')[-1])
                except:
                    chunk_index = 0
                
                chunk = DocumentChunk(
                    content=content,
                    url=url,
                    chunk_index=chunk_index,
                    metadata=meta
                )
                chunks.append(chunk)
                
        return chunks
        
    def clear(self):
        """Clear the collection"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)


# ============================================================================
# STEP 5: RAG PIPELINE
# ============================================================================
class SimpleRAGPipeline:
    """Complete RAG pipeline: retrieval + reranking + generation"""
    
    def __init__(self, llm_provider, embedding_provider: EmbeddingProvider, vector_store: VectorStore):
        self.llm_provider = llm_provider
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.reranker = Reranker()
    
    async def retrieve(self, query: str, filters: Optional[Dict] = None) -> List[DocumentChunk]:
        """Retrieve and rerank relevant chunks"""
        # 1. Generate query embedding
        query_embedding = (await self.embedding_provider.generate_embeddings([query]))[0]
        
        # 2. Retrieve candidates (get more than needed to allow for reranking)
        candidates = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=20, # Fetch top 20 candidates
            where=filters
        )
        
        # 3. Rerank candidates
        final_chunks = self.reranker.rerank(query, candidates, top_k=5)
        
        return final_chunks
    
    async def generate_answer_stream(
        self, 
        question: str, 
        relevant_chunks: List[DocumentChunk]
    ) -> AsyncGenerator[str, None]:
        """Generate streaming answer using LLM with retrieved context"""
        
        if not relevant_chunks:
            yield "I couldn't find any relevant information to answer your question."
            return
        
        # Build context
        context_parts = []
        for i, chunk in enumerate(relevant_chunks):
            context_parts.append(f"Source {i+1}:\n{chunk.content}")
        
        context = "\n\n".join(context_parts)
        
        # Create robust RAG prompt
        prompt = f"""You are a helpful AI assistant for a website. 
Answer the user's question using ONLY the context provided below.
If the answer is not in the context, say you don't know. Do not make up information.
Keep your answer professional, concise, and helpful.

Context:
{context}

Question: {question}

Answer:"""
        
        # Stream answer
        try:
            async for chunk in self.llm_provider.generate_stream(
                prompt,
                temperature=0.3, # Slightly higher for more natural flow but still focused
                max_tokens=1000
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            yield f"\n\nError generating response: {str(e)}"