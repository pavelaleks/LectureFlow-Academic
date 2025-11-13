"""
Text chunking utilities.
"""


def split_text_into_chunks(
    text: str,
    chunk_size: int = 2500,
    overlap: int = 200,
    separator: str = "\n\n"
) -> list[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to split
        chunk_size: Target size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        separator: Separator to prefer when splitting
    
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to find a good break point (prefer separator)
        if separator in text[start:end]:
            # Find last occurrence of separator before end
            last_sep = text.rfind(separator, start, end)
            if last_sep > start:
                end = last_sep + len(separator)
        
        chunks.append(text[start:end].strip())
        start = end - overlap
    
    return chunks

