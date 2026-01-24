# Website RAG Chatbot

Learn Retrieval-Augmented Generation (RAG) by building a real chatbot that scrapes, indexes, and answers questions about any website.

## Learning Objectives

Master the fundamentals of **Retrieval-Augmented Generation (RAG)** through hands-on implementation:

- **Web Scraping & Content Extraction:** Extract meaningful text content from live website URLs.
- **Text Pre-processing:** Implement semantic chunking strategies to prepare content for search.
- **Vector Embeddings & Similarity Search:** Convert text into vectors and build a searchable index.
- **RAG Pipeline:** Integrate retrieved context with an LLM prompt to generate accurate, sourced answers.
- **System Optimization:** Understand RAG's limitations and how to improve performance and quality.

## Quick Start

```bash
# Start the demo
make dev

# Visit: http://localhost:4020/demos/website-rag
```

-----

## Your Learning Path: Incremental Challenges

Follow these incremental challenges to build your application. Each one adds a new layer of functionality and learning.

### Challenge 1: The Scraper (Content Ingestion)

**Goal:** Get the raw content from a website. This is the first step of any RAG pipeline.

- **Your Task:**

  1. Take a single URL as input.

  2. Use a web scraping library (like `BeautifulSoup` or `Jina AI's reader.jina.ai`) to fetch the HTML.

  3. Extract all the raw text from the page's `<body>`.

  4. Display the raw, unformatted text.

- **Experiment:** Try this with several sites. Notice how you get a lot of "junk" text (navbars, footers, ads, "Copyright 2025"). This highlights the need for cleaning.

- **Key Concepts:** Web Scraping, HTML Parsing, Content Extraction.

-----

### Challenge 2: The "Naive" Chatbot (Context Stuffing)

**Goal:** Understand *why* RAG is necessary by seeing the "context stuffing" method fail.

- **Architecture:**

  ```mermaid
  graph TD
      A["Website URL"] --> B["Web Scraper"]
      B --> C["Full Page Text"]
      F["User Question"] --> G["LLM Prompt"]
      C --> G
      G --> H["LLM Generation"]
      H --> I["Answer"]
      style A fill:#e1f5fe
      style F fill:#e8f5e8
      style G fill:#fce4ec
      style I fill:#fff3e0
  ```

- **Your Task:**

  1. Use your scraper from Challenge 1 to get the full page text.

  2. Create a single, large prompt that "stuffs" all the text into the context.

  3. *Example:* `"Here is a website's content:\n---{scraped_text}---\n\nBased ONLY on this content, answer the following question:\n{user_question}"`

  4. Send this to the LLM and get an answer.

- **Experiment:** Try this with a large Wikipedia page. The API call will likely fail due to exceeding the model's **context window**. You've just proven *why* we need RAG.

- **Key Concepts:** Context Window Limits, Prompt Engineering, Naive RAG.

-----

### Challenge 3: Building the Index (The "R" in RAG)

**Goal:** Implement the "Retrieval" pipeline by chunking, embedding, and indexing the content.

- **Ingestion Architecture:**

  ```mermaid
  graph TD
      A["Website URL"] --> B["Web Scraper"]
      B --> C["Clean Page Text"]
      C --> D["Text Chunker"]
      D --> E["Chunk 1...N"]
      E --> F["Embedding Model"]
      F --> G["Vector 1...N"]
      G --> H["Vector Store"]
      style A fill:#e1f5fe
      style C fill:#e8f5e8
      style H fill:#fce4ec
  ```

- **Your Task:**

  1. Take the scraped text and use a **text splitter** (e.g., `RecursiveCharacterTextSplitter`) to break it into small, overlapping chunks (e.g., 500 chars with 50 char overlap).

  2. Use the `EMBEDDING_MODEL` to create a **vector embedding** for each chunk.

  3. Store these embeddings in an **in-memory vector store** (like FAISS or ChromaDB). This is your website's searchable "memory."

- **Key Concepts:** Text Chunking, Embedding Models, Vector Databases, Ingestion Pipeline.

-----

### Challenge 4: The Full RAG Pipeline (Querying)

**Goal:** Connect your index to the LLM to generate context-aware answers. This is the complete query loop.

- **Query Architecture:**

  ```mermaid
  graph TD
      A["User Question"] --> B["Embedding Model"]
      B --> C["Query Vector"]
      C --> D["Similarity Search"]
      E["Vector Store"] --> D
      D --> F["Top-K Relevant Chunks"]
      F --> G["RAG Prompt Engineering"]
      A --> G
      G --> H["LLM Generation"]
      H --> I["Answer"]
      style A fill:#e8f5e8
      style E fill:#fce4ec
      style H fill:#e0f7fa
      style I fill:#fff3e0
  ```

- **Your Task:**

  1. When a user asks a question, generate an embedding for the **question itself**.

  2. Perform a **similarity search** against your vector store to find the `top-k` (e.g., top 3) most relevant text chunks.

  3. **Engineer a RAG prompt:** Create a new prompt that includes *only* these relevant chunks as context.

  4. Send this *new prompt* to the LLM and display the answer.

- **Key Concepts:** RAG Pipeline, Similarity Search, RAG Prompt Engineering.

-----

### Challenge 5: The *Trustworthy* Chatbot (Source Attribution)

**Goal:** Make your chatbot trustworthy by showing the user *where* it found the answer.

- **Your Task:**

  1. When you create your chunks (Challenge 3), add **metadata** to them. At a minimum, include the `source_url`.

  2. After the LLM generates an answer (Challenge 4), retrieve the metadata from the `top-k` chunks that were used as context.

  3. Display these `source_url`s alongside the answer.

- **Experiment:** Ask a question. Look at the answer and *then* check the sources. Does the source text *actually* support the answer? This is how you manually spot **hallucinations**.

- **Key Concepts:** Metadata, Source Attribution, Verifiability, Hallucination Detection.

-----

### Challenge 6: The *Quality* Chatbot (Pre-processing)

**Goal:** Improve answer quality by cleaning the "junk" text *before* it gets into your index.

- **Your Task:**

  1. Modify your scraper from Challenge 1.

  2. Instead of just taking `<body>.text`, use CSS selectors or a library's "main content" extraction feature to *only* get the article/blog post text.

  3. **Exclude** common "junk" elements like `<nav>`, `<footer>`, `<aside>`, and elements with IDs like "sidebar" or "menu."

  4. Re-build your index (Challenge 3) with this *clean* text and compare the answer quality to Challenge 4.

- **Key Concepts:** Pre-processing, Data Cleaning, DOM Traversal, CSS Selectors, Signal-to-Noise Ratio.

-----

### Challenge 7: The *Multi-Source* Chatbot (Scaling)

**Goal:** Scale your system to allow the user to add and chat with *multiple* website URLs at once.

- **Your Task:**

  1. Allow the user to "add" multiple URLs.

  2. When a new URL is added, run it through your ingestion pipeline (Challenge 3) and add its chunks (with the correct `source_url` metadata) to the *same* vector store.

  3. Your query pipeline (Challenge 4) doesn't need to change! The similarity search will now automatically find the most relevant chunks from *any* of the indexed sites.

- **Experiment:** Add two competing news articles about the same event. Ask a question. See how the chatbot synthesizes (or gets confused by) the information.

- **Key Concepts:** Multi-source RAG, Scalable Indexing, Information Synthesis.

## Configuration

```bash
# .env
FIREWORKS_API_KEY=your_key_here
FIREWORKS_MODEL=accounts/fireworks/models/qwen3-235b-a22b-instruct-2507
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Fast & cheap
```

## Critical Thinking Questions

1. **What if the website content changes?** How would you handle updates and keep your index fresh?
2. **How would you prevent hallucination?** What validation step could you add *after* the LLM generates an answer but *before* you show it to the user?
3. **What if you had 10,000 URLs?** How would your in-memory vector store fail? What would you replace it with?
4. **How would you measure RAG quality?** What metrics matter most? (Hint: `Retrieval-Precision`, `Answer-Faithfulness`).
5. **How would you handle conflicting information from different sources?**
6. **What if one source is more authoritative (e.g., a "docs" site) than another (e.g., a "blog" site)?** How could you tell your RAG pipeline to "trust" one source more?

## Further Learning

**Essential Reading:**

- [Building the Entire RAG Ecosystem](https://levelup.gitconnected.com/building-the-entire-rag-ecosystem-and-optimizing-every-component-8f23349b96a4) - Production-ready RAG components
- [LangChain RAG Guide](https://python.langchain.com/docs/use_cases/question_answering/) - Production patterns

**Next Steps:**

- Implement a persistent vector database (Pinecone, Weaviate, Chroma, Qdrant, PgVector).
- Implement **recursive scraping** (Challenge 8: give it one URL, and it finds and scrapes all links on that page).
- Add a **re-ranking** step after retrieval to improve the quality of chunks sent to the LLM.
- Implement caching (e.g., with Redis) to avoid re-scraping and re-embedding the same URL.
