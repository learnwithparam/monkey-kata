# Document QA Chatbot

Learn how to build a production-ready Document RAG (Retrieval Augmented Generation) system using **Dense Vector Search and Reranking**.

## Learning Objectives

Master the core components of a **Fast RAG Pipeline**:

- **Document Parsing:** Handle PDF and Word documents efficiently.
- **Robust Chunking:** Split text based on meaning while preserving context (recursive splitting).
- **Fast Embeddings:** Use **all-MiniLM-L6-v2** (384-dim) for high-speed, low-latency vectors.
- **Dense Retrieval:** Find relevant content using semantic similarity in **Qdrant**.
- **Cross-Encoder Reranking:** Use a dedicated model to re-score results for maximum precision.

## Quick Start

```bash
# Start the demo (Backend + Frontend + Qdrant)
make dev

# Visit: http://localhost:4020/demos/document-qa-chatbot
# API Docs: http://localhost:4010/docs
```

-----

## Your Learning Path: Incremental Challenges

Follow these incremental challenges to master Document RAG.

### Challenge 1: The Parser

**Goal:** Extract clean text from PDFs and Docs.

- **The Problem:** Documents come in binary formats.
- **The Solution:** Use libraries like `pypdf` and `python-docx` to extract text.
- **Your Task:** Upload a PDF and check the logs. See how text is extracted and normalized.
- **Key Concepts:** Text Extraction, File Formats.

-----

### Challenge 2: The Chunker

**Goal:** Split the document into searchable pieces without breaking sentences.

- **The Problem:** Splitting by character count blindly breaks words and sentences.
- **The Solution:** **Recursive Character Splitting**.
- **Your Task:**
  1. We split by paragraphs (`\n\n`) first.
  2. Then by lines (`\n`).
  3. Then by sentences (`. `).
  4. Finally by characters if needed.
- **Key Concepts:** Recursive Splitting, Overlap (Preserving context).

-----

### Challenge 3: The Embedder (Dense)

**Goal:** Convert text into numbers (vectors) that represent meaning.

- **The Problem:** Computers can't compare text directly.
- **The Solution:** **Sentence Transformers**.
- **Model:** `all-MiniLM-L6-v2` (Small, Fast, Effective).
- **Your Task:** See how fast the 384-dimensional vectors are generated compared to larger models.
- **Key Concepts:** Dense Embeddings, Vector Space.

-----

### Challenge 4: The Retriever (Qdrant)

**Goal:** Find roughly relevant content from thousands of chunks.

- **Architecture:**
  - Query -> Embedding -> Vector (384 floats)
  - Vector -> Qdrant -> Nearest Neighbors (Cosine Similarity)
- **Your Task:** Ask a question and see the "Top 20" candidates retrieved by Qdrant.
- **Key Concepts:** Vector Database, Cosine Similarity, ANN Search.

-----

### Challenge 5: The Reranker (Precision)

**Goal:** Re-order the results to ensure the absolute best chunk is served to the LLM.

- **The Problem:** Similarity search provides "good enough" results but misses nuance.
- **The Solution:** **Cross-Encoder Reranking**.
- **Your Task:**
  1. We retrieve 20 chunks using Qdrant.
  2. We ask a Cross-Encoder: "How relevant is this chunk to this specific question?"
  3. We sort by that score and return the Top 5.
- **Key Concepts:** Reranking, Cross-Encoders, Precision vs Recall.

## Configuration

```bash
# .env parameters used
QDRANT_HOST=qdrant
QDRANT_PORT=6333
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## Critical Thinking Questions

1.  **Speed vs Quality:** We switched from BGE-M3 (Giant) to MiniLM (Tiny). What did we lose? What did we gain?
2.  **Reranking Cost:** Cross-encoders are slow (they process every pair). How many documents should we rerank? 10? 50? 100?
3.  **PDF Tables:** `pypdf` flattens tables into text lines. How does this affect answering questions about data in columns? (Hint: This is where Docling was better).

## Further Learning

- [Sentence Transformers](https://www.sbert.net/) - The library powering our embeddings.
- [Qdrant Documentation](https://qdrant.tech/) - Learn about vector search.

