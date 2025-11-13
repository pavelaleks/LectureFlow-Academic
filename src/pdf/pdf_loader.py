"""
PDF text extraction utilities.
"""
import io
import pdfplumber
import fitz  # PyMuPDF
from typing import Optional
from pathlib import Path


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF file bytes.
    
    Args:
        file_bytes: PDF file as bytes
    
    Returns:
        Extracted text as string
    """
    text = ""
    
    # Try pdfplumber first (better for complex layouts)
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        # Fallback to PyMuPDF
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
        except Exception as e2:
            raise Exception(f"Failed to extract text from PDF: {str(e2)}")
    
    # Clean up text
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Remove excessive whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from DOCX file bytes.
    
    Args:
        file_bytes: DOCX file as bytes
    
    Returns:
        Extracted text as string
    """
    from docx import Document
    from io import BytesIO
    
    doc = Document(BytesIO(file_bytes))
    text_parts = []
    
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text)
    
    return '\n'.join(text_parts)


def extract_text_from_txt(file_bytes: bytes, encoding: str = 'utf-8') -> str:
    """
    Extract text from TXT file bytes.
    
    Args:
        file_bytes: TXT file as bytes
        encoding: Text encoding (default: utf-8)
    
    Returns:
        Extracted text as string
    """
    try:
        return file_bytes.decode(encoding)
    except UnicodeDecodeError:
        # Try other common encodings
        for enc in ['cp1251', 'latin-1', 'iso-8859-1']:
            try:
                return file_bytes.decode(enc)
            except UnicodeDecodeError:
                continue
        raise Exception("Failed to decode text file with any encoding")


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from file based on extension.
    
    Args:
        file_bytes: File as bytes
        filename: Original filename (for extension detection)
    
    Returns:
        Extracted text as string
    """
    path = Path(filename)
    ext = path.suffix.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_bytes)
    elif ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_bytes)
    elif ext == '.txt':
        return extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

