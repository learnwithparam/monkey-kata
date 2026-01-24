"""
Document Processing Utilities (Lightweight Version)
===================================================

🎯 LEARNING OBJECTIVES:
This module teaches the core components of RAG with a lightweight, fast stack:

1. Fast Parsing - Extract text using standard libraries (PyPDF2, python-docx)
2. Robust Chunking - Use RecursiveCharacterTextSplitter for context preservation
3. Efficient Embeddings - Use all-MiniLM-L6-v2 (Fast, 384-dim)
4. Vector Search - Dense vector retrieval with Qdrant
5. Reranking - Improve precision with Cross-Encoder

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Document Parsing - Handling PDF/Word/Text
Step 2: Chunking - Splitting text intelligently
Step 3: Embeddings - Converting text to vectors
Step 4: Retrieval - Finding the right chunks
"""

import os
import uuid
import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from utils.thinking_streamer import ThinkingStreamer

# Lightweight PDF/Doc parsers
import pypdf
import docx

# Embeddings & Reranking (Fast CPU friendly models)
from sentence_transformers import SentenceTransformer, CrossEncoder

# Text Splitting
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Qdrant for vector database
from qdrant_client import QdrantClient, models

# ============================================================================
# MODULE-LEVEL SINGLETONS (Pre-loaded for performance)
# ============================================================================
print("🔧 Loading Embedding Model (all-MiniLM-L6-v2)...", flush=True)
_EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Embedding Model Loaded.", flush=True)

print("🔧 Loading Reranker Model...", flush=True)
_RERANKER_MODEL = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
print("✅ Reranker Model Loaded.", flush=True)


# ============================================================================
# STEP 1: DATA STRUCTURES
# ============================================================================
@dataclass
class DocumentChunk:
    """Represents a chunk of document text with metadata"""
    content: str
    document_id: str
    chunk_index: int
    page_number: int
    metadata: Dict[str, Any]
    vector: Optional[List[float]] = None # Dense vector

    def to_payload(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            **self.metadata
        }

# ============================================================================
# STEP 2: DOCUMENT PROCESSING
# ============================================================================
class DocumentProcessor:
    """Parses and chunks documents"""
    
    def __init__(self):
        self.embedding_model = _EMBEDDING_MODEL
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    async def parse_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Parse PDF, Docx, or Text file"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            content = ""
            pages = 1
            
            if ext == '.pdf':
                reader = pypdf.PdfReader(file_path)
                parts = []
                for i, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        if text:
                            parts.append(text)
                    except Exception as e:
                        logging.warning(f"Error reading page {i}: {e}")
                content = "\n\n".join(parts)
                pages = len(parts) if parts else 1
                
                # Cleaning PDF extraction artifacts
                import re
                
                # 1. Normalize whitespace (remove excessive spaces/newlines)
                content = re.sub(r'\s+', ' ', content)
                
                # Removed aggressive character merging logic as it can be risky.
                # Rely on the LLM to understand spacing issues if they persist.
                
            elif ext in ['.docx', '.doc']:
                doc = docx.Document(file_path)
                content = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                # Docx doesn't map strictly to pages in this lib, approx 1 page
                pages = max(1, len(content) // 3000)
                
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                pages = max(1, len(content) // 3000)
            
            else:
                logging.error(f"Unsupported file format: {ext}")
                return None
                
            return {
                'title': os.path.basename(file_path),
                'content': content,
                'pages': pages,
                'parsed_at': datetime.now().isoformat(),
                'content_length': len(content)
            }
            
        except Exception as e:
            logging.error(f"Error parsing document: {e}")
            return None

    def chunk_document(self, document_content: Dict[str, Any], chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
        """Split content using RecursiveCharacterTextSplitter"""
        # Update splitter settings
        self.text_splitter._chunk_size = chunk_size
        self.text_splitter._chunk_overlap = chunk_overlap
        
        content = document_content['content']
        texts = self.text_splitter.split_text(content)
        
        chunks = []
        for i, text in enumerate(texts):
            # Estimate page number (very rough if not tracking per-page text)
            # For pypdf we joined pages, so we lost exact alignment. 
            # For this simple versions, we just assume page 1 or scale linearly.
            # Ideally we'd chunk per page text, but for RAG content flow is often better.
            chunks.append({
                'content': text,
                'page_number': 1 # Simplified
            })
            
        return chunks

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate dense embeddings"""
        if not texts:
            return []
            
        # Run in executor
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.embedding_model.encode(texts, convert_to_tensor=False)
        )
        
        if len(embeddings.shape) == 1:
            return [embeddings.tolist()]
        return embeddings.tolist()

# ============================================================================
# STEP 3: RETRIEVAL & RAG (Qdrant)
# ============================================================================
class RAGPipeline:
    """RAG pipeline with Qdrant + Reranking"""
    
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
        self.reranker = _RERANKER_MODEL
        
        qdrant_host = os.getenv("QDRANT_HOST", "qdrant")
        qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)

    def get_collection_name(self, document_id: str) -> str:
        return f"doc_{document_id}"

    def upsert_documents(self, document_id: str, chunks: List[DocumentChunk]):
        """Upload chunks to Qdrant"""
        collection_name = self.get_collection_name(document_id)
        
        # 384 dimensions for all-MiniLM-L6-v2
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )
        
        points = []
        for doc in chunks:
            points.append(models.PointStruct(
                id=str(uuid.uuid4()),
                payload=doc.to_payload(),
                vector=doc.vector
            ))
            
        batch_size = 100
        for i in range(0, len(points), batch_size):
            self.client.upsert(
                collection_name=collection_name,
                points=points[i : i + batch_size]
            )

    def retrieve_relevant_chunks(
        self, 
        query_text: str,
        query_vector: List[float], 
        document_id: str,
        max_chunks: int = 5,
        thinking_streamer: Optional[ThinkingStreamer] = None
    ) -> List[DocumentChunk]:
        """Dense Search + Cross-Encoder Reranking"""
        collection_name = self.get_collection_name(document_id)
        
        # 1. Retrieve Pattern (Fetch more for reranking)
        limit = max(20, max_chunks * 4)
        print(f"Retrieving top {limit} candidates...", flush=True)
        
        # Use query_points which is more stable across versions
        search_result = self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True
        )
        
        candidates = []
        # query_points returns a QueryResponse object which has .points typically or just the list if internal
        # In recent versions it returns QueryResponse(points=[ScoredPoint...])
        points = search_result.points
        
        for point in points:
            candidates.append(DocumentChunk(
                content=point.payload['content'],
                document_id=point.payload['document_id'],
                chunk_index=point.payload['chunk_index'],
                page_number=point.payload['page_number'],
                metadata=point.payload
            ))
            
        # 2. Reranking Pattern
        if not candidates:
            return []
            
        print("Reranking candidates...", flush=True)
        pairs = [[query_text, doc.content] for doc in candidates]
        scores = self.reranker.predict(pairs)
        
        # Combine docs with scores and sort
        doc_scores = list(zip(candidates, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top K
        return [doc for doc, score in doc_scores[:max_chunks]]

    async def generate_answer_stream(
        self, 
        question: str, 
        relevant_chunks: List[DocumentChunk],
        thinking_streamer: Optional[ThinkingStreamer] = None
    ) -> AsyncGenerator[str, None]:
        """Generate answer with Gemini"""
        if not relevant_chunks:
            yield "I don't have enough information from the document to answer that."
            return
            
        context = "\n\n".join([c.content for c in relevant_chunks])
        
        prompt = f"""You are a helpful AI assistant. Answer the user's question using ONLY the context provided below.
If the text contains broken words (e.g. "val idat ing"), please reconstruct them to understand the meaning.
If the answer is not in the context, say you don't know. Do not make up information.
Keep your answer professional, concise, and helpful.

Context:
{context}

Question: {question}

Answer:"""

        if thinking_streamer:
            await thinking_streamer.emit_thinking("processing", "Synthesizing answer from document content...")
            
        async for chunk in self.llm_provider.generate_stream(prompt, temperature=0.1):
            yield chunk