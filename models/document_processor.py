import io
from typing import List, Dict, Any
import config

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False


class DocumentProcessor:
    """
    Handles file reading (TXT, MD, PDF) and text chunking (sliding window with overlap).
    """

    def __init__(self, chunk_size: int = config.CHUNK_SIZE, chunk_overlap: int = config.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """
        Extracts plain text from file bytes based on filename extension.
        Supports .txt, .md, and .pdf files.
        """
        ext = filename.lower().split('.')[-1]

        if ext in ['txt', 'md']:
            try:
                return file_content.decode('utf-8')
            except UnicodeDecodeError:
                return file_content.decode('latin-1')

        elif ext == 'pdf':
            if not PYPDF_AVAILABLE:
                raise ImportError("pypdf library is required for processing PDF files. Please install pypdf.")
            
            pdf_file = io.BytesIO(file_content)
            reader = pypdf.PdfReader(pdf_file)
            extracted_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
            return "\n\n".join(extracted_text)

        else:
            # Fallback to UTF-8 decoding for unknown plain text files
            return file_content.decode('utf-8', errors='ignore')

    def split_text_into_chunks(self, text: str, filename: str) -> List[Dict[str, Any]]:
        """
        Splits raw text into character chunks with overlap.
        Returns a list of dicts containing metadata and text snippet.
        """
        cleaned_text = text.replace('\r\n', '\n').strip()
        if not cleaned_text:
            return []

        chunks = []
        start = 0
        text_length = len(cleaned_text)
        chunk_index = 0

        while start < text_length:
            end = start + self.chunk_size

            # If not at the end of text, attempt to break at sentence or paragraph boundary
            if end < text_length:
                # Look for paragraph or sentence break near end
                last_newline = cleaned_text.rfind('\n', start, end)
                if last_newline > start + (self.chunk_size // 2):
                    end = last_newline + 1
                else:
                    last_period = cleaned_text.rfind('. ', start, end)
                    if last_period > start + (self.chunk_size // 2):
                        end = last_period + 1

            chunk_text = cleaned_text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "dosya_adi": filename,
                    "chunk_index": chunk_index,
                    "icerik": chunk_text
                })
                chunk_index += 1

            # Advance sliding window with overlap
            step = (end - start) - self.chunk_overlap
            if step <= 0:
                step = self.chunk_size // 2
            start += step

        return chunks
