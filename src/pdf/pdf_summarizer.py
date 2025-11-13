"""
PDF summarization using Grok (primary) or DeepSeek (fallback).
Grok is used for large document analysis due to its 2M token context window.
"""
from typing import List, Dict
from src.llm.model_registry import get_llm_client
from src.utils.io_utils import read_text, write_json
from src.utils.text_postprocessing import calculate_max_tokens
from src.utils.llm_utils import auto_extend_text
from pathlib import Path
import config


def summarize_pdf_chunks(
    chunks: List[str],
    llm_client,  # Accept any LLM client (Grok, DeepSeek, etc.)
    prompt_template: str,
    course_id: str,
    lecture_id: str
) -> Dict:
    """
    Summarize PDF chunks using LLM (Grok recommended for large documents).
    
    Args:
        chunks: List of text chunks
        llm_client: LLM client instance (Grok, DeepSeek, etc.)
        prompt_template: Template for summarization prompt
        course_id: Course ID for saving
        lecture_id: Lecture ID for saving
    
    Returns:
        Dictionary with full_summary, key_ideas, and chunks with summaries
    """
    chunk_summaries = []
    all_key_ideas = []
    
    # Determine max_tokens based on model type
    # Grok can handle much larger context
    is_grok = hasattr(llm_client, 'model') and 'grok' in str(llm_client.model).lower()
    
    # Summarize each chunk
    for i, chunk in enumerate(chunks):
        user_prompt = prompt_template.format(chunk_text=chunk)
        
        # Use appropriate max_tokens based on model
        if is_grok:
            max_tokens = 50000  # Grok supports up to 2M tokens
        else:
            max_tokens = calculate_max_tokens(1500)
        
        # Use Grok for PDF analysis if available (simplified call)
        if is_grok:
            from src.llm.grok_client import call_grok
            # Build full prompt for Grok
            full_prompt = f"""Ты — эксперт по анализу научных текстов. Делай краткие, точные резюме.

{user_prompt}"""
            # Use reasoning model for PDF analysis - get default_model from client
            if hasattr(llm_client, 'default_model'):
                grok_model = llm_client.default_model
            else:
                grok_model = None  # Will use default in call_grok
            summary = call_grok(full_prompt, model=grok_model)
        else:
            summary = llm_client.chat(
                system_prompt="Ты — эксперт по анализу научных текстов. Делай краткие, точные резюме.",
                user_prompt=user_prompt,
                temperature=0.5,
                max_tokens=max_tokens
            )
        
        # Auto-extend if incomplete (only for non-Grok models)
        if not is_grok:
            summary = auto_extend_text(
                llm_client,
                "Ты — эксперт по анализу научных текстов. Делай краткие, точные резюме.",
                user_prompt,
                summary,
                max_tokens
            )
        
        chunk_summaries.append({
            "chunk_index": i,
            "chunk_text": chunk[:500] + "..." if len(chunk) > 500 else chunk,  # Store preview
            "summary": summary
        })
    
    # Create combined summary
    combined_chunks_text = "\n\n---\n\n".join([cs["summary"] for cs in chunk_summaries])
    
    combined_prompt = f"""Объедини все резюме фрагментов в единое структурированное резюме документа.

Резюме фрагментов:
{combined_chunks_text}

Создай:
1. Краткое содержание (5-10 предложений)
2. Ключевые идеи (bullet list)
3. Важные термины
4. Методологические опоры
5. Значение для лекции"""
    
    # Use appropriate max_tokens for combined summary
    if is_grok:
        from src.llm.grok_client import call_grok
        full_prompt = f"""Ты — эксперт по анализу научных текстов.

{combined_prompt}"""
        # Use reasoning model for PDF analysis - get default_model from client
        if hasattr(llm_client, 'default_model'):
            grok_model = llm_client.default_model
        else:
            grok_model = None  # Will use default in call_grok
        full_summary = call_grok(full_prompt, model=grok_model)
    else:
        max_tokens = calculate_max_tokens(2500)
        full_summary = llm_client.chat(
            system_prompt="Ты — эксперт по анализу научных текстов.",
            user_prompt=combined_prompt,
            temperature=0.5,
            max_tokens=max_tokens
        )
    
    # Auto-extend if incomplete (only for non-Grok models)
    if not is_grok:
        full_summary = auto_extend_text(
            llm_client,
            "Ты — эксперт по анализу научных текстов.",
            combined_prompt,
            full_summary,
            max_tokens
        )
    
    # Extract key ideas
    key_ideas_prompt = f"""Из следующего резюме извлеки только ключевые идеи в виде списка (bullet points):

{full_summary}

Верни только список ключевых идей, по одной на строку."""
    
    # Use appropriate max_tokens for key ideas
    if is_grok:
        from src.llm.grok_client import call_grok
        full_prompt = f"""Ты — эксперт по анализу научных текстов.

{key_ideas_prompt}"""
        # Use reasoning model for PDF analysis - get default_model from client
        if hasattr(llm_client, 'default_model'):
            grok_model = llm_client.default_model
        else:
            grok_model = None  # Will use default in call_grok
        key_ideas_text = call_grok(full_prompt, model=grok_model)
    else:
        max_tokens = calculate_max_tokens(1500)
        key_ideas_text = llm_client.chat(
            system_prompt="Ты — эксперт по анализу научных текстов.",
            user_prompt=key_ideas_prompt,
            temperature=0.3,
            max_tokens=max_tokens
        )
    
    # Auto-extend if incomplete (only for non-Grok models)
    if not is_grok:
        key_ideas_text = auto_extend_text(
            llm_client,
            "Ты — эксперт по анализу научных текстов.",
            key_ideas_prompt,
            key_ideas_text,
            max_tokens
        )
    
    key_ideas = [line.strip("- •").strip() for line in key_ideas_text.split("\n") if line.strip() and line.strip().startswith(("-", "•"))]
    
    result = {
        "full_summary": full_summary,
        "key_ideas": key_ideas,
        "chunks": chunk_summaries
    }
    
    # Save to JSON
    upload_dir = config.UPLOADS_DIR / course_id / lecture_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    sources_file = upload_dir / "sources.json"
    write_json(sources_file, result)
    
    return result

