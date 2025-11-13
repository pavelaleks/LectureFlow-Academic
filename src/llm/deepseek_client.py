"""
DeepSeek API client using OpenAI-compatible interface.
"""
import os
from openai import OpenAI
from typing import Optional, List, Dict
import config


def call_deepseek(prompt: str, model: str = "deepseek-chat") -> str:
    """
    Simple function to call DeepSeek API.
    
    Args:
        prompt: User prompt
        model: Model name (default: deepseek-chat)
    
    Returns:
        Response text
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", config.DEEPSEEK_API_KEY)
    if not api_key:
        print("\033[91m[DeepSeek ERROR] DEEPSEEK_API_KEY not set\033[0m")
        return "DeepSeek API error: API key not configured"
    
    print("\033[95m[DeepSeek] Using deepseek model\033[0m")
    print(f"\033[96m[DeepSeek] Prompt length: {len(prompt)} chars\033[0m")
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url=config.DEEPSEEK_BASE_URL
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4096
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"\033[91m[DeepSeek ERROR]\033[0m {str(e)}")
        return f"DeepSeek API error: {str(e)}"


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
            # Estimate how many tokens are needed for the lecture
            # 1 word ≈ 1.2 tokens (Russian text)
            approx_tokens = int(target_words * 1.6)
            # DeepSeek maximum is 8192 — set safe boundary
            return min(approx_tokens, 7800)
        else:
            # If no target_words, use default but ensure it's sufficient for long lectures
            # Use higher default (6000) for lecture generation to prevent truncation
            return min(max(default_tokens, 6000), 7800)
    
    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        extra_messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Send chat request to DeepSeek API with continuation support.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            extra_messages: Optional list of additional messages (format: [{"role": "user/assistant", "content": "..."}])
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
        
        Returns:
            Full response content string (with continuation if needed)
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        if extra_messages:
            messages.extend(extra_messages)
        
        print("\033[95m[DeepSeek] Using deepseek model\033[0m")
        print(f"\033[96m[DeepSeek] Total prompt length: {len(system_prompt) + len(user_prompt)} chars\033[0m")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_text = response.choices[0].message.content or ""
            finish_reason = response.choices[0].finish_reason
            
            # Check if response was cut off and request continuation
            # finish_reason == "length" means response hit max_tokens limit
            if finish_reason == "length" and response_text:
                # Request continuation for truncated response
                continuation_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": response_text},
                    {"role": "user", "content": "Продолжи текст лекции без повторов. Продолжай с последнего предложения естественным образом."}
                ]
                
                # Calculate continuation tokens (up to 3000 or remaining budget)
                continuation_max_tokens = min(3000, 7800 - max_tokens)
                
                try:
                    continuation_response = self.client.chat.completions.create(
                        model=self.model,
                        messages=continuation_messages,
                        temperature=temperature,
                        max_tokens=continuation_max_tokens
                    )
                    
                    continuation_text = continuation_response.choices[0].message.content or ""
                    full_text = response_text + continuation_text
                    
                    return full_text
                except Exception as e:
                    # If continuation fails, return what we have
                    print(f"Warning: Continuation failed: {e}. Returning partial text.")
                    return response_text
            
            return response_text
            
        except Exception as e:
            raise Exception(f"DeepSeek API error: {str(e)}")

