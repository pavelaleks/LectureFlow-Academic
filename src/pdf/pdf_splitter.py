"""
PDF text splitting utilities.
"""
from src.utils.chunking import split_text_into_chunks


def split_into_chunks(
    text: str,
    chunk_size: int = 2500,
    overlap: int = 200
) -> list[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to split
        chunk_size: Target size of each chunk in characters
        overlap: Number of characters to overlap between chunks
    
    Returns:
        List of text chunks
    """
    return split_text_into_chunks(text, chunk_size, overlap)

