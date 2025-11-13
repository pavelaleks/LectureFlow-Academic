"""
Universal text generator that routes to appropriate LLM based on model name.
"""
from typing import Optional


def generate_text(prompt: str, model_name: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
    """
    Universal text generator that routes to appropriate LLM based on model name.
    Uses simple call functions (call_grok, call_deepseek, call_openai).
    
    Args:
        prompt: Text prompt
        model_name: Model name (grok-4-fast, deepseek-chat, gpt-4o-mini, etc.)
                   If None, defaults to deepseek-chat
        max_tokens: Maximum tokens to generate (optional)
    
    Returns:
        Generated text
    """
    if model_name is None:
        # Default to deepseek-chat if not specified
        model_name = "deepseek-chat"
    
    if model_name.startswith("grok"):
        from src.llm.grok_client import call_grok
        # Use provided max_tokens or default
        if max_tokens is None:
            max_tokens = 4096
        return call_grok(prompt, model=model_name, max_tokens=max_tokens)
    elif model_name.startswith("deepseek"):
        from src.llm.deepseek_client import call_deepseek
        return call_deepseek(prompt, model=model_name)
    else:
        # OpenAI or other
        from src.llm.openai_client import call_openai
        return call_openai(prompt, model=model_name)

