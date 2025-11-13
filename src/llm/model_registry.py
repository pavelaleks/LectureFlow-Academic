"""
Model registry for managing different LLM clients (DeepSeek, Grok, OpenAI).
"""
import os
from typing import Optional, Any
from .deepseek_client import DeepSeekClient
from .grok_client import GrokClient

# Complete list of available models
MODEL_REGISTRY = [
    # xAI Grok — reasoning + fast + base
    "grok-4-fast-reasoning",
    "grok-4-reasoning",
    "grok-4-fast",
    "grok-4",
    # DeepSeek
    "deepseek-chat",
    "deepseek-reasoner",
    # OpenAI fallback (если не используется)
    "gpt-4o-mini",
]


def get_llm_client(model_name: Optional[str] = None) -> Any:
    """
    Get LLM client based on model name.
    
    Args:
        model_name: Model name. If None, defaults to DeepSeek.
            Supported models:
            - deepseek-chat (default DeepSeek)
            - grok-4-fast-reasoning
            - grok-4-fast-non-reasoning
    
    Returns:
        LLM client instance
    """
    if model_name is None:
        model_name = "deepseek-chat"
    
    # GROK MODELS
    if model_name and model_name.startswith("grok"):
        api_key = os.getenv("GROK_API_KEY")
        if not api_key:
            raise ValueError("GROK_API_KEY environment variable is required for Grok models")
        # Map to appropriate Grok model - use model_name as-is if it's in registry
        if model_name in MODEL_REGISTRY and model_name.startswith("grok"):
            grok_model = model_name
        elif model_name == "grok-4-fast-non-reasoning":
            # Legacy support
            grok_model = "grok-4-fast"
        else:
            # Default to grok-4-fast-reasoning for any grok model
            grok_model = "grok-4-fast-reasoning"
        return GrokClient(
            api_key=api_key,
            model=grok_model
        )
    
    # DEEPSEEK MODELS
    if model_name and model_name.startswith("deepseek"):
        return DeepSeekClient()
    
    # OPENAI/GPT models are handled by text_generator.py, not here
    # Default to DeepSeek if model not recognized
    return DeepSeekClient()


def get_max_tokens_for_model(model_name: Optional[str], target_words: int = None) -> int:
    """
    Get appropriate max_tokens for a given model.
    
    Args:
        model_name: Model name
        target_words: Target word count (optional)
    
    Returns:
        Appropriate max_tokens value
    """
    if model_name and model_name.startswith("grok"):
        # Grok supports up to 2M tokens, use 50k for safety
        if target_words:
            # Estimate tokens needed
            approx_tokens = int(target_words * 1.6)
            return min(approx_tokens, 50000)
        return 50000
    else:
        # DeepSeek/OpenAI limits
        if target_words:
            approx_tokens = int(target_words * 1.6)
            return min(approx_tokens, 7800)
        return 7800

