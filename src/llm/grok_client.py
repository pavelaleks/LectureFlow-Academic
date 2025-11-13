"""
Grok API client for xAI Grok ChatCompletion API.
Supports extremely large context windows (2M tokens) and is used for 
PDF/document analysis and long text generation.
"""
import os
import requests
import httpx
from typing import Optional, List, Dict


GROK_API_KEY = os.getenv("GROK_API_KEY")
GROK_BASE_URL = "https://api.x.ai/v1/chat/completions"

# Import MODEL_REGISTRY for validation
try:
    from .model_registry import MODEL_REGISTRY
except ImportError:
    MODEL_REGISTRY = [
        "grok-4-fast-reasoning",
        "grok-4-reasoning",
        "grok-4-fast",
        "grok-4",
    ]


def call_grok(prompt: str, model: str = None, max_tokens: int = 4096) -> str:
    """
    Simple function to call Grok API with auto-continue support.
    
    Args:
        prompt: User prompt
        model: Model name (default: grok-4-fast-reasoning)
        max_tokens: Maximum tokens to generate
    
    Returns:
        Response text (complete, with auto-continue if needed)
    """
    if not GROK_API_KEY:
        print("\033[91m[GROK ERROR] GROK_API_KEY not set\033[0m")
        return "Grok API error: API key not configured"
    
    # Default to reasoning model
    default_model = "grok-4-fast-reasoning"
    
    if model is None:
        model = default_model
    
    # Validate model against registry
    if model not in MODEL_REGISTRY:
        print(f"\033[93m[GROK WARNING] Model '{model}' not in MODEL_REGISTRY, using default\033[0m")
        model = default_model
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROK_API_KEY}"
    }
    
    print(f"\033[92m[GROK] Using model: {model}\033[0m")
    print(f"\033[96m[GROK] Prompt length: {len(prompt)} chars, max_tokens: {max_tokens}\033[0m")
    
    # First request
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(GROK_BASE_URL, headers=headers, json=payload, timeout=300)
        
        if response.status_code != 200:
            print("\033[91m[GROK ERROR]\033[0m", response.text)
            # Fallback to DeepSeek
            try:
                from .deepseek_client import call_deepseek
                print("\033[93m[GROK] Falling back to DeepSeek\033[0m")
                return call_deepseek(prompt)
            except Exception as fallback_error:
                print(f"\033[91m[FALLBACK ERROR]\033[0m {fallback_error}")
                return "Grok API error"
        
        data = response.json()
        full_text = data["choices"][0]["message"]["content"]
        finish_reason = data["choices"][0].get("finish_reason", "stop")
        
        # Auto-continue if generation was cut off due to token limit
        iteration = 1
        while finish_reason == "length":
            iteration += 1
            print(f"\033[93m[GROK] Generation hit token limit (iteration {iteration}), continuing...\033[0m")
            
            # Continue from where it stopped
            continue_prompt = (
                full_text +
                "\n\nПродолжи текст с того места, где он был оборван. "
                "Не повторяй уже написанное. Продолжай логично и связно."
            )
            
            continue_payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": continue_prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            continue_response = requests.post(GROK_BASE_URL, headers=headers, json=continue_payload, timeout=300)
            
            if continue_response.status_code != 200:
                print(f"\033[91m[GROK ERROR] Continue request failed\033[0m")
                break
            
            continue_data = continue_response.json()
            continuation = continue_data["choices"][0]["message"]["content"]
            full_text += " " + continuation
            finish_reason = continue_data["choices"][0].get("finish_reason", "stop")
            
            # Safety limit to prevent infinite loops
            if iteration >= 10:
                print(f"\033[93m[GROK WARNING] Reached max iterations ({iteration}), stopping\033[0m")
                break
        
        if iteration > 1:
            print(f"\033[92m[GROK] Completed after {iteration} iterations, total length: {len(full_text)} chars\033[0m")
        
        return full_text
        
    except Exception as e:
        print(f"\033[91m[GROK ERROR]\033[0m {str(e)}")
        # Fallback to DeepSeek
        try:
            from .deepseek_client import call_deepseek
            print("\033[93m[GROK] Falling back to DeepSeek\033[0m")
            return call_deepseek(prompt)
        except Exception as fallback_error:
            print(f"\033[91m[FALLBACK ERROR]\033[0m {fallback_error}")
            return f"Grok API error: {str(e)}"


class GrokClient:
    """
    Client for xAI Grok ChatCompletion API.
    Supports extremely large context windows (2M tokens)
    and is used for PDF/document analysis and long text generation.
    """
    
    def __init__(self, api_key: str = None, model: str = "grok-4-fast-reasoning"):
        """
        Initialize Grok client.
        
        Args:
            api_key: Grok API key (if None, uses GROK_API_KEY env var)
            model: Model name (grok-4-fast-reasoning by default)
        """
        self.api_key = api_key or GROK_API_KEY
        self.default_model = "grok-4-fast-reasoning"
        self.model = model if model else self.default_model
        self.url = GROK_BASE_URL
    
    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        extra_messages: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3,
        max_tokens: int = 50000
    ) -> str:
        """
        Send chat request to Grok API.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            extra_messages: Optional list of additional messages
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate (Grok supports up to 2M)
        
        Returns:
            Response content string
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        if extra_messages:
            messages.extend(extra_messages)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        print(f"\033[92m[GROK] Using model: {self.model}\033[0m")
        print(f"\033[96m[GROK] Total prompt length: {len(system_prompt) + len(user_prompt)} chars\033[0m")
        
        try:
            with httpx.Client(timeout=300) as client:  # 5 minute timeout for large documents
                response = client.post(self.url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"\033[91m[GROK ERROR]\033[0m {str(e)}")
            raise Exception(f"Grok API error: {str(e)}")
