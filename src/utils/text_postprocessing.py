"""
Text post-processing utilities.
"""
import re


def clean_whitespace(text: str) -> str:
    """Clean excessive whitespace while preserving structure."""
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple newlines (more than 2) with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove trailing whitespace from lines
    lines = [line.rstrip() for line in text.split('\n')]
    return '\n'.join(lines)


def normalize_text(text: str) -> str:
    """Normalize text for processing."""
    text = clean_whitespace(text)
    # Remove zero-width characters
    text = re.sub(r'[\u200b-\u200f\ufeff]', '', text)
    return text.strip()

