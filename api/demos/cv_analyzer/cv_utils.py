"""
CV Document Processing Utilities
==================================

🎯 LEARNING OBJECTIVES:
This module teaches CV-specific document processing:

1. CV Parsing - Extract text from CV documents (PDF, Word, text)
2. Section Detection - Identify CV sections (Experience, Education, Skills, etc.)
3. CV-Specific Chunking - Split CVs intelligently by sections
4. Embeddings - Convert CV chunks to vectors for semantic search
5. CV Structure Understanding - How to parse structured resume formats

📚 LEARNING FLOW:
Follow this code from top to bottom:

Step 1: Document Parsing - How to extract text from CV files
Step 2: Section Detection - How to identify CV sections automatically
Step 3: CV-Specific Chunking - How to chunk CVs by sections
Step 4: Embeddings - How to convert CV chunks to vectors
Step 5: Similarity Search - How to find relevant CV sections

Key Difference from Generic Document Processing:
- CVs have specific sections (Experience, Education, Skills, etc.)
- Section-aware chunking preserves context better
- CV sections have different importance levels
"""

import asyncio
import re
import os
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import tempfile
import shutil

# LlamaIndex imports
from llama_index.core import (
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    Settings
)

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure LlamaIndex settings
Settings.embed_model = None
Settings.llm = None
logger.info("LlamaIndex configured with fallback embeddings")


# ============================================================================
# STEP 1: DATA STRUCTURES
# ============================================================================
"""
DocumentChunk:
Represents a chunk of CV text with section metadata. This helps us:
- Track which CV section each chunk came from (Experience, Education, etc.)
- Maintain section context during chunking
- Retrieve chunks with their section information
"""
@dataclass
class DocumentChunk:
    """Represents a chunk of CV text with metadata"""
    content: str
    document_id: str
    chunk_index: int
    section: str  # CV section: Experience, Education, Skills, etc.
    metadata: Dict[str, Any]

# ============================================================================
# STEP 2: DOCUMENT PARSING
# ============================================================================
"""
Document Parsing:
The first step in CV processing is extracting text from files.

Key Concepts:
- File Type Detection: Different formats need different parsers
- Text Extraction: Get clean text from PDFs, Word docs, text files
- Error Handling: Handle corrupted or unsupported files

Supported Formats:
- PDF: Extracts text from PDF CVs
- Word (.doc, .docx): Extracts text from Microsoft Word CVs
- Text (.txt): Reads plain text CVs
"""
class CVDocumentProcessor:
    """Document processor for CVs with section detection"""
    
    def __init__(self):
        self.index = None
        self.documents = []
    
    async def parse_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse a CV document and extract text content
        
        Process:
        1. Detect file type (PDF, Word, text)
        2. Use document parser (handles all formats)
        3. Extract text content from all pages
        4. Get page count
        5. Return structured data with metadata
        
        Args:
            file_path: Path to the CV document file
            
        Returns:
            Dictionary with title, content, pages, and metadata
        """
        try:
            logger.info(f"Parsing CV document: {file_path}")
            
            # Create a temporary directory for document parsing
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, os.path.basename(file_path))
            shutil.copy2(file_path, temp_file)
            
            # Use document reader (handles PDF, Word, text files)
            reader = SimpleDirectoryReader(input_dir=temp_dir)
            documents = reader.load_data()
            
            if not documents:
                raise Exception("No content extracted from CV document")
            
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
            logger.error(f"Error parsing CV document {file_path}: {e}")
            return None
    
    # ============================================================================
    # STEP 3: CV-SPECIFIC SECTION DETECTION & CHUNKING
    # ============================================================================
    """
    CV-Specific Chunking:
    Unlike generic documents, CVs have specific sections that should be preserved.
    
    Why CV-Specific Chunking?
    - CVs have structured sections (Experience, Education, Skills, etc.)
    - Section-aware chunking preserves context better
    - Makes it easier to analyze CV structure
    - Better for agentic analysis (agents can focus on specific sections)
    
    How It Works:
    1. Detect CV sections using pattern matching
    2. Chunk within each section (preserves section context)
    3. Use sentence-based chunking for better semantic preservation
    4. Maintain section metadata for each chunk
    """
    def chunk_cv_document(self, document_content: Dict[str, Any], chunk_size: int = 300, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
        """
        Split CV document into semantic chunks based on sections
        
        This is CV-specific chunking that:
        1. Detects CV sections (Experience, Education, Skills, etc.)
        2. Chunks within each section (preserves context)
        3. Uses sentence-based splitting (preserves meaning)
        4. Maintains section metadata
        
        Args:
            document_content: Parsed document content
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters to overlap between chunks
            
        Returns:
            List of document chunks with section metadata
        """
        content = document_content['content']
        pages = document_content.get('pages', 1)
        
        # CV-specific section detection
        sections = self._detect_cv_sections(content)
        
        chunks = []
        current_chunk = ""
        current_section = "General"
        
        for section_name, section_content in sections.items():
            # Split section into sentences
            sentences = self._split_into_sentences(section_content)
            
            for sentence in sentences:
                # If adding this sentence would exceed chunk size, start a new chunk
                if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'section': current_section,
                        'page_number': 1
                    })
                    
                    # Start new chunk with overlap
                    if chunk_overlap > 0:
                        overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
                        current_chunk = overlap_text + " " + sentence
                    else:
                        current_chunk = sentence
                else:
                    current_chunk += " " + sentence if current_chunk else sentence
            
            current_section = section_name
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'section': current_section,
                'page_number': 1
            })
        
        # Filter out very short chunks
        chunks = [chunk for chunk in chunks if len(chunk['content']) > 30]
        
        logger.info(f"Created {len(chunks)} CV chunks from document of length {len(content)}")
        return chunks
    
    def _detect_cv_sections(self, content: str) -> Dict[str, str]:
        """
        Detect CV sections based on common patterns
        
        CV Sections We Look For:
        - Personal Info: Name, contact information
        - Summary: Professional summary or objective
        - Experience: Work history and employment
        - Education: Academic background
        - Skills: Technical and soft skills
        - Projects: Portfolio and work samples
        - Certifications: Professional certifications
        - Achievements: Awards and recognition
        
        This uses regex pattern matching to identify section headers.
        """
        sections = {}
        
        # Common CV section patterns
        section_patterns = {
            'Personal Info': r'(?i)(name|contact|email|phone|address|location)',
            'Summary': r'(?i)(summary|profile|objective|about)',
            'Experience': r'(?i)(experience|work history|employment|career)',
            'Education': r'(?i)(education|academic|degree|university|college)',
            'Skills': r'(?i)(skills|technical skills|competencies|technologies)',
            'Projects': r'(?i)(projects|portfolio|work samples)',
            'Certifications': r'(?i)(certifications|certificates|licenses)',
            'Achievements': r'(?i)(achievements|awards|honors|recognition)'
        }
        
        # Split content into lines
        lines = content.split('\n')
        current_section = 'General'
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line matches a section header
            section_found = False
            for section_name, pattern in section_patterns.items():
                if re.search(pattern, line) and len(line) < 100:  # Likely a header
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    current_section = section_name
                    current_content = [line]
                    section_found = True
                    break
            
            if not section_found:
                current_content.append(line)
        
        # Save the last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using NLTK or fallback
        
        Why sentence-based splitting?
        - Preserves meaning better than character-based splitting
        - Sentences are natural semantic units
        - Better for embeddings (sentences have clearer meaning)
        """
        try:
            from nltk.tokenize import sent_tokenize
            return sent_tokenize(text)
        except Exception as e:
            logger.warning(f"NLTK sentence tokenization failed: {e}. Using simple split.")
        
        # Fallback to simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    # ============================================================================
    # STEP 4: EMBEDDINGS
    # ============================================================================
    """
    Embeddings Generation:
    Converts CV chunks into vectors for semantic search.
    
    Uses the same approach as other demos (sentence-transformers):
    - Local model (no API costs)
    - Fast and efficient
    - Semantic understanding of CV content
    
    Each embedding is a vector representing the text's meaning.
    Similar meanings → similar vectors.
    """
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of CV chunk texts
        
        Uses the same approach as other demos:
        - SentenceTransformer for semantic embeddings
        - Local model (no API costs)
        - Fast and efficient
        
        Args:
            texts: List of CV chunk text strings to embed
            
        Returns:
            List of embedding vectors (one per text)
        """
        try:
            # Use the same approach as other demos
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
        """
        Generate simple hash-based embeddings as fallback
        
        If sentence-transformers fails, this creates simple hash-based embeddings.
        Not as good as semantic embeddings, but ensures the system keeps working.
        """
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
        """
        Calculate cosine similarity between two vectors
        
        Used for finding similar CV sections or matching CV content to job descriptions.
        Returns a value between -1 and 1, where 1 means identical meaning.
        """
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

# ============================================================================
# LEARNING CHECKLIST
# ============================================================================
"""
After reading this code, you should understand:

✓ How to parse CV documents (PDF, Word, text)
✓ How CV-specific section detection works (Experience, Education, Skills, etc.)
✓ How CV chunking preserves section context
✓ How embeddings convert CV chunks to vectors
✓ Why section-aware chunking improves CV analysis quality
✓ The complete CV document processing pipeline

Key CV Processing Concepts:
- CV sections: Experience, Education, Skills, Projects, etc.
- Section detection: Pattern matching to identify sections
- Section-aware chunking: Chunk within sections (preserves context)
- Embeddings: Convert CV sections to searchable vectors

Next Steps:
1. Experiment with different chunk sizes for CV sections
2. Try different section detection patterns
3. Add support for more CV formats
4. Improve section detection accuracy
5. Add support for parsing CVs with tables or complex formatting

Questions to Consider:
- How would you handle CVs with non-standard section names?
- What if a CV doesn't have clear sections?
- How would you improve chunking for technical CVs vs creative CVs?
- How would you handle CVs in different languages?
- What are the trade-offs between section-aware chunking and generic chunking?
"""

# Example usage and testing
if __name__ == "__main__":
    async def test_cv_processor():
        """Test the CV document processor with sample data"""
        
        # Initialize processor
        document_processor = CVDocumentProcessor()
        
        # Test CV section detection
        print("Testing CV section detection...")
        sample_cv = """
        John Doe
        Software Engineer
        john@email.com
        (555) 123-4567
        
        SUMMARY
        Experienced software engineer with 5 years of experience in web development.
        
        EXPERIENCE
        Software Developer at Tech Corp (2020-2023)
        - Built web applications using Python and JavaScript
        - Led team of 3 developers
        
        EDUCATION
        BS Computer Science, University of Tech (2018-2020)
        
        SKILLS
        - Python, JavaScript, React, Node.js
        - Database design and management
        """
        
        sections = document_processor._detect_cv_sections(sample_cv)
        print(f"Detected sections: {list(sections.keys())}")
        
        # Test chunking
        print("Testing CV chunking...")
        sample_content = {
            'content': sample_cv,
            'title': 'Sample CV',
            'pages': 1
        }
        chunks = document_processor.chunk_cv_document(sample_content)
        print(f"Created {len(chunks)} chunks")
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"Chunk {i+1} ({chunk['section']}): {chunk['content'][:100]}...")
        
        # Test embeddings
        print("Testing embeddings...")
        texts = ["Python developer", "React experience", "Team leadership"]
        embeddings = await document_processor.generate_embeddings(texts)
        print(f"Generated {len(embeddings)} embeddings")
        
        print("CV document processor test completed!")
    
    # Run test
    asyncio.run(test_cv_processor())
