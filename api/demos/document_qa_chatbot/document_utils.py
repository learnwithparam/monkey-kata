"""
Document Processing Utilities
=============================

🎯 LEARNING OBJECTIVES:
This module teaches the core components of document RAG:

1. Document Parsing - Extract text from PDFs, Word docs, text files
2. Text Chunking - Split documents into searchable pieces
3. Embeddings - Convert text to vectors for similarity search
4. Vector Search - Find relevant information in documents
5. RAG Prompting - Combine document context with questions

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Document Parsing - How to extract text from different file types
Step 2: Text Chunking - How to split documents intelligently
Step 3: Embeddings - How to convert text to numbers
Step 4: Similarity Search - How to find relevant chunks
Step 5: RAG Generation - How to create prompts with document context
"""

import os
import uuid
import numpy as np
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import tempfile
import shutil

# LlamaIndex for document parsing
from llama_index.core import SimpleDirectoryReader

# Sentence transformers for embeddings (same as website_rag)
from sentence_transformers import SentenceTransformer

# Vector Store - Using Chroma as an example implementation
# Other vector stores: Pinecone (cloud), Weaviate, FAISS, Qdrant
import chromadb

# NLTK for sentence tokenization
import nltk
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)


# ============================================================================
# STEP 1: DATA STRUCTURES
# ============================================================================
"""
DocumentChunk:
Represents a piece of document text with metadata. This helps us:
- Track where each chunk came from (document_id, page_number)
- Store additional context (title, chunk index)
- Retrieve chunks with their source information
"""
@dataclass
class DocumentChunk:
    """Represents a chunk of document text with metadata"""
    content: str
    document_id: str
    chunk_index: int
    page_number: int
    metadata: Dict[str, Any]


# ============================================================================
# STEP 2: DOCUMENT PARSING
# ============================================================================
"""
Document Parsing:
The first step in document RAG is extracting text from files.

Key Concepts:
- File Type Detection: Different formats need different parsers
- Text Extraction: Get clean text from PDFs, Word docs, text files
- Error Handling: Handle corrupted or unsupported files
- LlamaIndex: Uses robust parsers for various document types

Supported Formats:
- PDF: Extracts text from PDF documents
- Word (.doc, .docx): Extracts text from Microsoft Word files
- Text (.txt): Reads plain text files
"""
class DocumentProcessor:
    """Parses documents and generates embeddings"""
    
    def __init__(self):
        self.embedding_model = None
        self._load_embedding_model()
    
    def _load_embedding_model(self):
        """Load the embedding model (same as website_rag demo)"""
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.embedding_model = SentenceTransformer(model_name)
    
    async def parse_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse a document and extract text content
        
        Process:
        1. Detect file type
        2. Use appropriate parser (LlamaIndex handles this)
        3. Extract text content
        4. Get accurate page count
        5. Return structured data with metadata
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with title, content, and metadata
        """
        try:
            # First, try to get actual page count for PDFs
            actual_page_count = None
            if file_path.lower().endswith('.pdf'):
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        actual_page_count = len(pdf_reader.pages)
                except Exception:
                    pass  # Fall back to estimation
            
            # Create temporary directory for LlamaIndex
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, os.path.basename(file_path))
            shutil.copy2(file_path, temp_file)
            
            # Use LlamaIndex SimpleDirectoryReader (handles PDF, Word, text)
            reader = SimpleDirectoryReader(input_dir=temp_dir)
            documents = reader.load_data()
            
            if not documents:
                raise Exception("No content extracted from document")
            
            # Extract text content
            content = "\n".join([doc.text for doc in documents])
            
            # Determine page count
            if actual_page_count:
                # Use actual page count from PDF metadata
                page_count = actual_page_count
            else:
                # Try to get page count from document metadata
                page_numbers = set()
                for doc in documents:
                    metadata = getattr(doc, 'metadata', {}) or {}
                    page_label = metadata.get('page_label') or metadata.get('page_number') or metadata.get('page')
                    if page_label:
                        try:
                            page_numbers.add(int(page_label))
                        except (ValueError, TypeError):
                            pass
                
                if page_numbers:
                    page_count = max(page_numbers)
                else:
                    # Estimate: assume roughly 2-3 nodes per page for PDFs
                    page_count = max(1, len(documents) // 2)
            
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            
            return {
                'title': os.path.basename(file_path),
                'content': content,
                'pages': page_count,
                'document_nodes': len(documents),  # Actual number of document nodes from LlamaIndex
                'parsed_at': datetime.now().isoformat(),
                'content_length': len(content)
            }
                
        except Exception as e:
            return None
    
    def chunk_document(
        self, 
        document_content: Dict[str, Any], 
        chunk_size: int = 500, 
        chunk_overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Split document content into overlapping chunks
        
        Why Chunking?
        - Documents are too large for LLM context windows
        - Smaller chunks are easier to search
        - Overlap preserves context across boundaries
        
        How It Works:
        1. Split text into sentences (preserves meaning)
        2. Build chunks by adding sentences
        3. When chunk would exceed size, start new chunk
        4. Use overlap to preserve context
        
        Args:
            document_content: Dictionary with 'content'
            chunk_size: Maximum characters per chunk
            chunk_overlap: Characters to overlap between chunks
            
        Returns:
            List of document chunks with page numbers
        """
        content = document_content['content']
        
        # Split into sentences (preserves meaning better than character splitting)
        sentences = self._split_into_sentences(content)
        
        chunks = []
        current_chunk = ""
        current_page = 1  # Simple page tracking
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size, finalize current chunk
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
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK"""
        from nltk.tokenize import sent_tokenize
        return sent_tokenize(text)
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Uses the same approach as website_rag demo:
        - SentenceTransformer for semantic embeddings
        - Local model (no API costs)
        - Fast and efficient
        
        Each embedding is a vector representing the text's meaning.
        Similar meanings → similar vectors.
        """
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
        
        # Convert numpy array to list of lists
        if len(embeddings.shape) == 1:
            return [embeddings.tolist()]
        else:
            return embeddings.tolist()
    


# ============================================================================
# STEP 3: RAG PIPELINE (With Vector Store)
# ============================================================================
"""
Vector Stores - The Concept:
Instead of manually calculating cosine similarity for every chunk,
vector stores are specialized databases optimized for similarity search.

Why Vector Stores Instead of Manual Cosine Similarity?
- Faster: Optimized algorithms (indexing, approximate search)
- Scalable: Handle millions of vectors efficiently
- Metadata Support: Store and filter by document_id, page_number, etc.
- Production-Ready: Built for real-world use cases
- Better Accuracy: Advanced indexing techniques improve results

What is a Vector Store?
A vector store (also called vector database) is a database designed
specifically for storing and searching high-dimensional vectors.

Common Vector Stores:
- Chroma: Open-source, Python-friendly (what we use here)
- Pinecone: Managed cloud service
- Weaviate: Open-source with GraphQL API
- FAISS: Facebook's library for similarity search
- Qdrant: Fast vector database

Key Concepts:
- Index: Data structure optimized for fast similarity search
- Query: Search for vectors similar to your query vector
- Metadata: Additional data stored with each vector
- Collections/Tables: Groups of vectors with the same structure

The Complete Flow:
1. User asks a question about a document
2. Generate embedding for the question
3. Use vector store to find top-K similar chunks (fast & accurate)
4. Build prompt with question + relevant document chunks
5. Generate answer using LLM

This is incremental learning:
- Website RAG: Learned manual cosine similarity (understand the math)
- Document RAG: Learn vector stores (production-ready approach)
"""
class RAGPipeline:
    """Complete RAG pipeline: retrieval + generation with vector store"""
    
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
        Find the most relevant document chunks using a vector store
        
        Process:
        1. Create vector store index with document embeddings
        2. Query for top-K similar chunks
        3. Return relevant chunks with metadata
        
        This uses a vector store for efficient similarity search - much faster
        and more scalable than manual cosine similarity calculations.
        """
        if not document_embeddings or not documents:
            return []
        
        # Use vector store for efficient similarity search
        # We're using Chroma here, but you could swap it with Pinecone, Weaviate, etc.
        return self._retrieve_with_vector_store(query_embedding, document_embeddings, documents, max_chunks)
    
    def _retrieve_with_vector_store(
        self,
        query_embedding: List[float],
        document_embeddings: List[List[float]],
        documents: List[DocumentChunk],
        max_chunks: int
    ) -> List[DocumentChunk]:
        """
        Use vector store for efficient similarity search
        
        How Vector Stores Work:
        1. Create an index (like a database table)
        2. Add all document embeddings to the index
        3. Query the index with your question embedding
        4. Get back the most similar chunks
        
        We're using Chroma here as an example, but the same concept
        applies to any vector store (Pinecone, Weaviate, FAISS, etc.)
        """
        # Create in-memory vector store client (Chroma implementation)
        client = chromadb.EphemeralClient()
        
        # Create a collection (similar to a database table)
        collection_name = f"chunks_{uuid.uuid4().hex[:8]}"
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        # Add document embeddings to the vector store with metadata
        ids = []
        metadatas = []
        for i, doc in enumerate(documents):
            ids.append(str(i))
            metadatas.append({
                "document_id": doc.document_id,
                "chunk_index": doc.chunk_index,
                "page_number": doc.page_number
            })
        
        # Store embeddings in vector store
        collection.add(
            embeddings=document_embeddings,
            ids=ids,
            metadatas=metadatas
        )
        
        # Query vector store for similar chunks
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(max_chunks, len(documents))
        )
        
        # Extract indices from results
        if results['ids'] and len(results['ids']) > 0:
            top_indices = [int(idx) for idx in results['ids'][0]]
            return [documents[i] for i in top_indices if i < len(documents)]
        
        return []
    
    async def generate_answer_stream(
        self, 
        question: str, 
        relevant_chunks: List[DocumentChunk]
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming answer using LLM with retrieved document context
        
        This is the "G" (Generation) part of RAG.
        
        Process:
        1. Build context from relevant document chunks
        2. Create RAG prompt with context + question
        3. Stream answer from LLM
        
        RAG Prompt Structure:
        - Context from retrieved document chunks
        - User question
        - Instructions to use only the document context
        """
        if not relevant_chunks:
            yield "I don't have enough information to answer your question from the document."
            return
        
        # Build context from relevant chunks
        context_parts = []
        for chunk in relevant_chunks:
            context_parts.append(chunk.content)
        
        context = "\n\n".join(context_parts)
        
        # Create simple RAG prompt - just answer the question naturally
        prompt = f"""Based on this document content, answer the question.

Document content:
{context}

Question: {question}

Answer directly and concisely:"""
        
        # Stream answer from LLM
        try:
            async for chunk in self.llm_provider.generate_stream(
                prompt,
                temperature=0.1,
                max_tokens=1000  # Increased from 100 to allow longer responses
            ):
                yield chunk
        except RuntimeError as e:
            # Handle StopIteration converted to RuntimeError
            if "StopIteration" in str(e) or "async generator" in str(e).lower():
                # Generator finished normally, just return
                return
            # Re-raise other RuntimeErrors
            raise
        except Exception as e:
            # Handle any other errors gracefully
            yield f"\n\nError generating response: {str(e)}"
            return
                

# ============================================================================
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How to parse different document types (PDF, Word, text)
✓ How to chunk documents intelligently (sentence-based, with overlap)
✓ How embeddings convert text to vectors
✓ How vector stores enable efficient similarity search
✓ Why vector stores are better than manual cosine similarity
✓ How to build a RAG prompt with document context
✓ The complete document RAG pipeline flow

Key Document RAG Concepts:
- Ingestion: Upload → parse → chunk → embed → store in vector store
- Query: Question → embed → vector store search → context → answer
- Why Document RAG works: Relevant sections + LLM understanding = accurate answers

Vector Store Concepts:
- Vector stores are specialized databases for similarity search
- Much faster than calculating cosine similarity manually
- Can handle millions of vectors efficiently
- Support metadata filtering (by document_id, page_number, etc.)
- Examples: Chroma (used here), Pinecone, Weaviate, FAISS, Qdrant

Next Steps:
1. Experiment with different chunk sizes
2. Try different embedding models
3. Upload multiple documents and see cross-document retrieval
4. Try a different vector store (Pinecone, Weaviate, FAISS)
5. Add support for tables and images in documents
6. Make the vector store persistent (save/load indexes)

Questions to Consider:
- What's the optimal chunk size for documents? (too small = lost context, too large = less precise)
- How does overlap affect retrieval quality?
- What happens if no relevant chunks are found in the document?
- How would you handle documents with tables or images?
- How would you improve chunking for technical or legal documents?
"""