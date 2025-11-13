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


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def calculate_max_tokens(target_words: int) -> int:
    """
    Calculate max_tokens dynamically based on target word count.
    
    Args:
        target_words: Target word count
    
    Returns:
        Calculated max_tokens (capped at 7800)
    """
    # Estimate how many tokens are needed for the lecture
    # 1 word ≈ 1.2 tokens (Russian text), use 1.6 for safety margin
    approx_tokens = int(target_words * 1.6)
    # DeepSeek maximum is 8192 — set safe boundary
    return min(approx_tokens, 7800)

