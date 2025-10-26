"""
CV Document Processing Utilities
===============================

Utilities for processing CV documents using LlamaIndex.
Focused on CV-specific parsing and analysis.
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

@dataclass
class DocumentChunk:
    """Represents a chunk of CV text with metadata"""
    content: str
    document_id: str
    chunk_index: int
    section: str
    metadata: Dict[str, Any]

class CVDocumentProcessor:
    """LlamaIndex-based document processor for CVs"""
    
    def __init__(self):
        self.index = None
        self.documents = []
    
    async def parse_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse a CV document using LlamaIndex
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with parsed content and metadata
        """
        try:
            logger.info(f"Parsing CV document with LlamaIndex: {file_path}")
            
            # Create a temporary directory for LlamaIndex
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, os.path.basename(file_path))
            shutil.copy2(file_path, temp_file)
            
            # Use LlamaIndex SimpleDirectoryReader
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
    
    def chunk_cv_document(self, document_content: Dict[str, Any], chunk_size: int = 300, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
        """
        Split CV document into semantic chunks based on sections
        
        Args:
            document_content: Parsed document content
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters to overlap between chunks
            
        Returns:
            List of document chunks with metadata
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
        """Detect CV sections based on common patterns"""
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
        """Split text into sentences using NLTK or fallback"""
        try:
            from nltk.tokenize import sent_tokenize
            return sent_tokenize(text)
        except Exception as e:
            logger.warning(f"NLTK sentence tokenization failed: {e}. Using simple split.")
        
        # Fallback to simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using sentence-transformers (same as other demos)
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
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
        """Generate simple hash-based embeddings as fallback"""
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
