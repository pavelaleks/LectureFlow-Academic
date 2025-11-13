"""
PDF summarization using DeepSeek.
"""
from typing import List, Dict
from src.llm.deepseek_client import DeepSeekClient
from src.utils.io_utils import read_text, write_json
from pathlib import Path
import config


def summarize_pdf_chunks(
    chunks: List[str],
    deepseek: DeepSeekClient,
    prompt_template: str,
    course_id: str,
    lecture_id: str
) -> Dict:
    """
    Summarize PDF chunks using DeepSeek.
    
    Args:
        chunks: List of text chunks
        deepseek: DeepSeek client instance
        prompt_template: Template for summarization prompt
        course_id: Course ID for saving
        lecture_id: Lecture ID for saving
    
    Returns:
        Dictionary with full_summary, key_ideas, and chunks with summaries
    """
    chunk_summaries = []
    all_key_ideas = []
    
    # Summarize each chunk
    for i, chunk in enumerate(chunks):
        user_prompt = prompt_template.format(chunk_text=chunk)
        
        summary = deepseek.chat(
            system_prompt="Ты — эксперт по анализу научных текстов. Делай краткие, точные резюме.",
            user_prompt=user_prompt,
            temperature=0.5,
            max_tokens=1000
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
    
    full_summary = deepseek.chat(
        system_prompt="Ты — эксперт по анализу научных текстов.",
        user_prompt=combined_prompt,
        temperature=0.5,
        max_tokens=2000
    )
    
    # Extract key ideas
    key_ideas_prompt = f"""Из следующего резюме извлеки только ключевые идеи в виде списка (bullet points):

{full_summary}

Верни только список ключевых идей, по одной на строку."""
    
    key_ideas_text = deepseek.chat(
        system_prompt="Ты — эксперт по анализу научных текстов.",
        user_prompt=key_ideas_prompt,
        temperature=0.3,
        max_tokens=1000
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

