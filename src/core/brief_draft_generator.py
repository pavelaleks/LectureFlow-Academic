"""
Brief draft generator for short lecture versions (800-1200 words).
"""
from typing import Dict, List
from src.utils.text_generator import generate_text


def build_brief_draft_prompt(metadata: Dict, pdf_summary: str = "") -> str:
    """
    Build prompt for brief draft generation.
    
    Args:
        metadata: Lecture metadata (title, subtitle, keywords)
        pdf_summary: Summary of uploaded PDF sources
    
    Returns:
        Formatted prompt string
    """
    return f"""
Выступай как профессор-литературовед. 

Создай КРАТКИЙ вариант лекции, объем 800–1200 слов.

СТРУКТУРА:

1. Основные тезисы (5–8)

2. Ключевые термины + краткие определения

3. Основные авторы + биографическая справка (3–5 строк)

4. Методологические акценты

5. Как объяснять студентам

ИСПОЛЬЗУЙ загруженные PDF (приоритет):  

{pdf_summary if pdf_summary else "Загруженные источники не предоставлены"}

Тема лекции: {metadata.get('title', 'Без названия')}
Подзаголовок: {metadata.get('subtitle', '')}
Ключевые слова: {', '.join(metadata.get('keywords', []))}
"""


def generate_brief_draft(
    metadata: Dict,
    pdf_summary: str = "",
    model_name: str = "grok-4-fast-reasoning"
) -> str:
    """
    Generate brief draft lecture (800-1200 words).
    
    Args:
        metadata: Lecture metadata
        pdf_summary: Summary of uploaded PDF sources
        model_name: Model to use for generation
    
    Returns:
        Brief draft text
    """
    prompt = build_brief_draft_prompt(metadata, pdf_summary)
    return generate_text(prompt, model_name=model_name)


def build_lecture_summary_prompt(metadata: Dict, pdf_summary: str = "") -> str:
    """
    Build prompt for lecture summary generation (600-800 words).
    
    Args:
        metadata: Lecture metadata (title, subtitle, keywords)
        pdf_summary: Summary of uploaded PDF sources
    
    Returns:
        Formatted prompt string
    """
    return f"""
Создай структурированное резюме университетской лекции объёмом 600–800 слов.

Стиль: академический, концептуально точный, насыщенный понятиями, без воды.

СТРУКТУРА РЕЗЮМЕ:

1. Проблемное поле лекции: что ставится в центр разбора?

2. Ключевые теоретические положения (3–5 блока).

3. Основные исследователи/мыслители, связанные с темой (краткая характеристика).

4. Методологические принципы, используемые в лекции.

5. Значение темы для курса и для гуманитарных исследований в целом.

6. Конечные выводы (что студент должен унести с занятия).

Если загружены PDF-файлы — ИСПОЛЬЗУЙ ИХ с приоритетом, интегрируя идеи, термины, цитаты:

{pdf_summary if pdf_summary else "Загруженные источники не предоставлены"}

Тема лекции: {metadata.get('title', 'Без названия')}

Подзаголовок: {metadata.get('subtitle', '')}

Ключевые слова: {', '.join(metadata.get('keywords', []))}
"""


def generate_lecture_summary(
    metadata: Dict,
    pdf_summary: str = "",
    model_name: str = "grok-4-fast-reasoning"
) -> str:
    """
    Generate lecture summary (600-800 words).
    
    Args:
        metadata: Lecture metadata
        pdf_summary: Summary of uploaded PDF sources
        model_name: Model to use for generation
    
    Returns:
        Lecture summary text
    """
    prompt = build_lecture_summary_prompt(metadata, pdf_summary)
    return generate_text(prompt, model_name=model_name)

