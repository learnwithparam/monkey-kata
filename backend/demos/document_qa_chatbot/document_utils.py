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
import re
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
from collections import Counter
import math

from utils.thinking_streamer import ThinkingStreamer

# Parsing
import pymupdf4llm
import docx

# Embeddings & Reranking (Fast CPU friendly models)
from sentence_transformers import SentenceTransformer, CrossEncoder

# Text Splitting
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

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
    dense_vector: Optional[List[float]] = None 
    sparse_vector: Optional[Dict[int, float]] = None # Indices -> Values

    def to_payload(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            **self.metadata
        }

# ============================================================================
# STEP 1.5: SPARSE EMBEDDER (BM25-style)
# ============================================================================
class SimpleSparseEmbedder:
    """
    Simple hash-based sparse embedder for demo purposes.
    Maps words to a fixed sparse space (30k dim) using hashing.
    Ideally use SPLADE or similar for production.
    """
    def __init__(self, vocab_size: int = 30000):
        self.vocab_size = vocab_size

    def _tokenize(self, text: str) -> List[str]:
        # Simple whitespace + alphanumeric separation
        return re.findall(r'\w+', text.lower())

    def _hash_token(self, token: str) -> int:
        return int(int(abs(hash(token))) % self.vocab_size)

    def compute_vector(self, text: str) -> models.SparseVector:
        tokens = self._tokenize(text)
        if not tokens:
            return models.SparseVector(indices=[], values=[])
            
        counts = Counter(tokens)
        indices = []
        values = []
        
        for token, count in counts.items():
            idx = self._hash_token(token)
            indices.append(idx)
            # Simple TF (could add IDF if we trained/tracked corpus stats)
            values.append(float(count))
            
        return models.SparseVector(indices=indices, values=values)


# ============================================================================
# STEP 2: DOCUMENT PROCESSING
# ============================================================================
class DocumentParser:
    """Handles parsing of PDF (PyMuPDF4LLM), Docx, etc."""
    
    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """Parse PDF using PyMuPDF4LLM (Layout-aware Markdown)"""
        try:
            # Returns markdown string with tables and headers
            md_text = pymupdf4llm.to_markdown(file_path)
            return md_text
        except Exception as e:
            logging.error(f"PyMuPDF4LLM failed: {e}")
            raise e

    @staticmethod
    def parse_docx(file_path: str) -> str:
        """Parse Docx file"""
        doc = docx.Document(file_path)
        return "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])


class DocumentProcessor:
    """Parses and chunks documents"""
    
    def __init__(self):
        self.embedding_model = _EMBEDDING_MODEL
        self.sparse_embedder = SimpleSparseEmbedder()
        
        # Markdown splitter is better for the structured output from PyMuPDF
        self.md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ]
        )
        self.recursive_splitter = RecursiveCharacterTextSplitter(
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
                # Use PyMuPDF4LLM for robust Markdown extraction
                content = DocumentParser.parse_pdf(file_path)
                # Estimate pages roughly (PyMuPDF4LLM merges, need to check if we can get page counts cleanly)
                # Text length is a proxy for now
                pages = max(1, len(content) // 2000) 
                
            elif ext in ['.docx', '.doc']:
                content = DocumentParser.parse_docx(file_path)
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
        """Split content intelligently"""
        self.recursive_splitter._chunk_size = chunk_size
        self.recursive_splitter._chunk_overlap = chunk_overlap
        
        content = document_content['content']
        
        # 1. First split by Markdown headers if meaningful content
        # (Only effective if parsing produced markdown)
        md_splits = self.md_splitter.split_text(content)
        
        final_chunks = []
        chunk_idx = 0
        
        # 2. Then recursively split within sections
        for split in md_splits:
            # Metadata from headers
            headers = split.metadata
            
            sub_splits = self.recursive_splitter.split_text(split.page_content)
            
            for text in sub_splits:
                final_chunks.append({
                    'content': text,
                    'page_number': 1, # TODO: improve page tracking
                    'chunk_index': chunk_idx,
                    'metadata': headers
                })
                chunk_idx += 1
                
        # Fallback if markdown splitting did nothing (e.g. plain text)
        if not final_chunks:
            texts = self.recursive_splitter.split_text(content)
            for i, text in enumerate(texts):
                final_chunks.append({
                    'content': text,
                    'page_number': 1,
                    'chunk_index': i,
                    'metadata': {}
                })
            
        return final_chunks

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate dense embeddings"""
        if not texts:
            return []
            
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.embedding_model.encode(texts, convert_to_tensor=False)
        )
        
        if len(embeddings.shape) == 1:
            return [embeddings.tolist()]
        return embeddings.tolist()
    
    def generate_sparse_embeddings(self, texts: List[str]) -> List[models.SparseVector]:
        """Generate simple sparse (BM25-like) vectors"""
        return [self.sparse_embedder.compute_vector(text) for text in texts]

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
        """Upload chunks to Qdrant with Hybrid support"""
        collection_name = self.get_collection_name(document_id)
        
        # Configure for Hybrid Search (Dense + Sparse)
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config={
                "dense": models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    index=models.SparseIndexParams(
                        on_disk=False,
                    )
                )
            }
        )
        
        points = []
        for doc in chunks:
            points.append(models.PointStruct(
                id=str(uuid.uuid4()),
                payload=doc.to_payload(),
                vector={
                    "dense": doc.dense_vector,
                    "sparse": doc.sparse_vector
                }
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
        query_sparse_vector: Optional[models.SparseVector], # New argument
        document_id: str,
        max_chunks: int = 5,
        thinking_streamer: Optional[ThinkingStreamer] = None
    ) -> List[DocumentChunk]:
        """Hybrid Search (Dense + Sparse with RRF) + Cross-Encoder Reranking"""
        collection_name = self.get_collection_name(document_id)
        
        # 1. Retrieve Pattern (Fetch more for reranking)
        limit = max(20, max_chunks * 4)
        print(f"Retrieving top {limit} candidates (Hybrid RRF)...", flush=True)
        
        # Use Qdrant Hybrid Search (RRF Fusion)
        if query_sparse_vector:
            search_result = self.client.query_points(
                collection_name=collection_name,
                prefetch=[
                    models.Prefetch(
                        query=query_vector,
                        using="dense",
                        limit=limit
                    ),
                    models.Prefetch(
                        query=query_sparse_vector,
                        using="sparse",
                        limit=limit
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=limit,
                with_payload=True
            )
        else:
            # Fallback to dense only if no sparse vector
            search_result = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                using="dense",
                limit=limit,
                with_payload=True
            )
        
        candidates = []
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
            
        if thinking_streamer:
            asyncio.create_task(thinking_streamer.emit_thinking(
                "processing", 
                f"Reranking {len(candidates)} candidates with Cross-Encoder..."
            ))
            
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