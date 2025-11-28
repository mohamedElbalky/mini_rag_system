from PyPDF2 import PdfReader
from typing import List

import logging
logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Process PDF files and extract text chunks
    """
    
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_pdf(self, file_path: str) -> List[str]:
        """
        Extract text from PDF and split into chunks
        """
        try:
            reader = PdfReader(file_path)
            
            if len(reader.pages) == 0:
                logger.warning("PDF has no pages")
                return []

            # Extract text from all pages
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            if not full_text.strip():
                logger.warning("No text extracted from PDF")
                return []

            # Split into chunks
            chunks = self._split_text(full_text)
            
            logger.info(f"Extracted {len(chunks)} chunks from PDF")
            return chunks

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise

    def _split_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to end at a sentence boundary
            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                last_boundary = max(last_period, last_newline)
                
                if last_boundary > self.chunk_size // 2:
                    end = start + last_boundary + 1
                    chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk.strip())

            start = end - self.chunk_overlap

        return chunks