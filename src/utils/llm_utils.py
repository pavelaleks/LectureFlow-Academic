"""
LLM utilities for token calculation and text continuation.
"""
from typing import Optional, Any


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


def auto_extend_text(
    llm: Any,  # Accept any LLM client (DeepSeek, Grok, etc.)
    system_prompt: str,
    user_prompt: str,
    initial_text: str,
    max_tokens: int
) -> str:
    """
    Continues generation if the model output seems incomplete.
    
    Args:
        llm: LLM client instance
        system_prompt: System prompt
        user_prompt: Original user prompt
        initial_text: Text generated so far
        max_tokens: Max tokens for continuation
    
    Returns:
        Extended text if continuation was needed, otherwise original text
    """
    text = initial_text
    
    # Detect cutoff: ends unexpectedly without punctuation OR ends mid-sentence
    # Check if text ends with proper punctuation
    text_stripped = text.strip()
    if not text_stripped:
        return text
    
    # Check if ends with proper punctuation
    last_char = text_stripped[-1]
    proper_endings = [".", "!", "?", "\"", "”", "»", "…", "\n"]
    
    # If text doesn't end properly, request continuation
    if last_char not in proper_endings:
        # Also check if text seems too short for expected length
        # (rough check: if we're generating a long text but got cut off)
        continuation_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": text},
            {"role": "user", "content": "Продолжи текст с того места, где он оборвался. Продолжай естественным образом без повторов."}
        ]
        
        try:
            # Use remaining tokens (up to 3000)
            continuation_max_tokens = min(3000, max_tokens)
            
            continuation = llm.chat(
                system_prompt=system_prompt,
                user_prompt=f"Продолжи текст с того места, где он оборвался:\n\n{text}\n\nПродолжай естественным образом без повторов.",
                temperature=0.7,
                max_tokens=continuation_max_tokens
            )
            
            # Only append if we got meaningful continuation
            if continuation and len(continuation.strip()) > 10:
                text += "\n\n" + continuation
        except Exception as e:
            # If continuation fails, return what we have
            print(f"Warning: Auto-extend failed: {e}")
            pass
    
    return text

