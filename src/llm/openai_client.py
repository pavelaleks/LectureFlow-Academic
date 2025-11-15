"""
OpenAI API client for GPT models.
"""
import os
from openai import OpenAI
import config


def call_openai(prompt: str, model: str = "gpt-4o-mini") -> str:
    """
    Simple function to call OpenAI API.
    
    Args:
        prompt: User prompt
        model: Model name (default: gpt-4o-mini)
    
    Returns:
        Response text
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("\033[91m[OPENAI ERROR] OPENAI_API_KEY not set\033[0m")
        return "OpenAI API error: API key not configured"
    
    print("\033[94m[OPENAI] Using OpenAI GPT model\033[0m")
    print(f"\033[96m[OPENAI] Prompt length: {len(prompt)} chars\033[0m")
    
    try:
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4096
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"\033[91m[OPENAI ERROR]\033[0m {str(e)}")
        return f"OpenAI API error: {str(e)}"




