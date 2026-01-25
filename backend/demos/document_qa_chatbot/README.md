# Document QA Chatbot

Learn how to build a production-ready Document RAG (Retrieval Augmented Generation) system using **Dense Vector Search and Reranking**.

## Learning Objectives

Master the core components of a **Fast RAG Pipeline**:

- **Layout-Aware Parsing:** Use **PyMuPDF4LLM** to extract Markdown with tables and headers preserved.
- **Robust Chunking:** Split based on Markdown structure (headers) for better context.
- **Hybrid Embeddings:** combine **Dense** (all-MiniLM-L6-v2) and **Sparse** (BM25) vectors.
- **Hybrid Retrieval:** Find relevant content using **Reciprocal Rank Fusion (RRF)** in Qdrant.
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

### Challenge 1: The Parser (Layout Aware)

**Goal:** Extract clean **Markdown** from PDFs to preserve structure.

- **The Problem:** Standard PDF extraction (`pypdf`) flattens tables and headers into garbled text.
- **The Solution:** Use **PyMuPDF4LLM** to convert PDF elements into Markdown format.
- **Your Task:** Upload a PDF with tables. See how tables are converted to Markdown tables, preserving row/column relationships.
- **Key Concepts:** PDF to Markdown, Layout Preservation.

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

### Challenge 3: The Embedder (Hybrid)

**Goal:** Convert text into both **Dense** (meaning) and **Sparse** (keyword) vectors.

- **The Problem:** Dense vectors understand meaning but miss exact keywords (e.g. part numbers, names).
- **The Solution:** **Hybrid Embeddings**.
- **Dense:** `all-MiniLM-L6-v2` (384-dim) for semantic match.
- **Sparse:** `BM25-style` (30k-dim) for keyword match.
- **Your Task:** See how "Apple" (fruit) vs "Apple" (company) is handled.
- **Key Concepts:** Hybrid Search, Sparse Vectors, Tokenization.

-----

### Challenge 4: The Retriever (Hybrid RRF)

**Goal:** Find relevant content using **Reciprocal Rank Fusion (RRF)**.

- **Architecture:**
  - Parallel Search: Dense Search (Semantic) + Sparse Search (Keyword)
  - **Fusion:** Combine results using RRF (rank-based weighting).
- **Your Task:** Ask a question that requires both understanding (dense) and specific details (sparse).
- **Key Concepts:** Reciprocal Rank Fusion, Hybrid Search.

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

