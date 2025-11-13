"""
Prompt template loader and renderer.
"""
from pathlib import Path
from src.utils.io_utils import read_text
import config


def load_prompt(path: str | Path) -> str:
    """
    Load prompt template from file.
    
    Args:
        path: Relative path from prompts/ directory or absolute path
    
    Returns:
        Prompt template content
    """
    if isinstance(path, str):
        # Check if it's an absolute path
        if Path(path).is_absolute():
            prompt_path = Path(path)
        else:
            # Relative to prompts directory
            prompt_path = config.PROMPTS_DIR / path
    else:
        prompt_path = path
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    return read_text(prompt_path)


def render_prompt(template: str, **kwargs) -> str:
    """
    Render prompt template with variables.
    
    Args:
        template: Template string with {variable} placeholders
        **kwargs: Variables to fill in
    
    Returns:
        Rendered prompt string
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing template variable: {e}")

