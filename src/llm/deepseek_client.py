"""
DeepSeek API client using OpenAI-compatible interface.
"""
import os
from openai import OpenAI
from typing import Optional, List, Dict
import config


class DeepSeekClient:
    """Client for interacting with DeepSeek API."""
    
    def __init__(self):
        """Initialize DeepSeek client."""
        api_key = os.environ.get("DEEPSEEK_API_KEY", config.DEEPSEEK_API_KEY)
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=config.DEEPSEEK_BASE_URL
        )
        self.model = config.DEEPSEEK_MODEL
    
    @staticmethod
    def safe_max_tokens(target_words: int = None, default_tokens: int = 2000) -> int:
        """
        Calculate safe max_tokens value that never exceeds DeepSeek limit.
        
        Args:
            target_words: Target word count (optional)
            default_tokens: Default tokens if target_words not provided
        
        Returns:
            Safe max_tokens value (max 7800)
        """
        if target_words is not None:
            # Аккуратный пересчёт слов в токены (примерно 1.5 токена на слово для русского)
            approx_tokens = int(target_words * 1.5)
            # Финальный лимит DeepSeek
            return min(approx_tokens, 7800)
        else:
            # Если нет target_words, используем дефолт, но ограничиваем лимитом
            return min(default_tokens, 7800)
    
    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        extra_messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Send chat request to DeepSeek API.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            extra_messages: Optional list of additional messages (format: [{"role": "user/assistant", "content": "..."}])
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
        
        Returns:
            Response content string
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        if extra_messages:
            messages.extend(extra_messages)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"DeepSeek API error: {str(e)}")

