"""
Main lecture generation pipeline.
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
from src.llm.deepseek_client import DeepSeekClient
from src.llm.model_registry import get_llm_client, get_max_tokens_for_model
from src.openalex.openalex_client import OpenAlexClient
from src.pdf.pdf_loader import extract_text_from_file
from src.pdf.pdf_splitter import split_into_chunks
from src.pdf.pdf_summarizer import summarize_pdf_chunks
from src.core.course_manager import CourseManager
from src.core.prompts_loader import load_prompt, render_prompt
from src.utils.io_utils import read_json, write_json, write_text, read_text
from src.utils.text_postprocessing import normalize_text, count_words, calculate_max_tokens
from src.utils.llm_utils import auto_extend_text
import config
import uuid


class LecturePipeline:
    """Main pipeline for generating lectures."""
    
    def __init__(self):
        """Initialize pipeline."""
        self.deepseek = DeepSeekClient()  # Default for backward compatibility
        self.openalex = OpenAlexClient()
        self.course_manager = CourseManager()
        # Grok client for PDF analysis (primary engine) - use reasoning model
        try:
            self.grok = get_llm_client("grok-4-fast-reasoning")
        except:
            self.grok = None  # Fallback to DeepSeek if Grok not configured
    
    def run_uploaded_sources_step(
        self,
        course_id: str,
        lecture_id: str,
        uploaded_files: List[Any]
    ) -> Dict[str, Any]:
        """
        Process uploaded PDF/DOCX/TXT files.
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier
            uploaded_files: List of Streamlit UploadedFile objects
        
        Returns:
            Dictionary with summary and key_ideas
        """
        if not uploaded_files:
            return {
                "full_summary": "",
                "key_ideas": [],
                "chunks": []
            }
        
        all_texts = []
        
        # Extract text from all files
        for file in uploaded_files:
            file_bytes = file.read()
            text = extract_text_from_file(file_bytes, file.name)
            all_texts.append(text)
        
        combined_text = "\n\n---\n\n".join(all_texts)
        
        # Split into chunks
        chunks = split_into_chunks(combined_text, chunk_size=2500, overlap=200)
        
        # Load PDF summary prompt
        pdf_prompt_template = load_prompt("steps/pdf_summary.md")
        
        # Summarize chunks using Grok (primary) or DeepSeek (fallback)
        # Grok is better for large documents due to 2M token context window
        pdf_llm = self.grok if self.grok else self.deepseek
        
        result = summarize_pdf_chunks(
            chunks=chunks,
            llm_client=pdf_llm,
            prompt_template=pdf_prompt_template,
            course_id=course_id,
            lecture_id=lecture_id
        )
        
        # Save to outputs
        output_dir = config.OUTPUTS_DIR / course_id
        output_dir.mkdir(parents=True, exist_ok=True)
        write_json(output_dir / f"{lecture_id}_sources.json", result)
        
        return result
    
    def run_bibliography_step(
        self,
        course_id: str,
        lecture_id: str,
        core_keywords: str = "",
        core_authors: str = "",
        recent_keywords: str = ""
    ) -> Dict[str, List[Dict]]:
        """
        Search OpenAlex and build bibliography.
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier
            core_keywords: Keywords for core works search
            core_authors: Authors for core works filter
            recent_keywords: Keywords for recent works search
        
        Returns:
            Dictionary with "core" and "recent" bibliography lists
        """
        bibliography = self.openalex.generate_bibliography(
            core_keywords=core_keywords,
            core_authors=core_authors,
            recent_keywords=recent_keywords
        )
        
        # Save bibliography
        output_dir = config.OUTPUTS_DIR / course_id
        output_dir.mkdir(parents=True, exist_ok=True)
        write_json(output_dir / f"{lecture_id}_bibliography.json", bibliography)
        
        return bibliography
    
    def run_bibliography_summary_step(
        self,
        course_id: str,
        lecture_id: str,
        bibliography: Dict[str, List[Dict]]
    ) -> str:
        """
        Summarize bibliography using DeepSeek.
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier
            bibliography: Bibliography dictionary
        
        Returns:
            Summary text
        """
        core_text = "\n".join([
            f"- {entry['title']} ({entry['year']}) - {', '.join(entry['authors'][:3])}"
            for entry in bibliography.get("core", [])[:5]
        ])
        
        recent_text = "\n".join([
            f"- {entry['title']} ({entry['year']}) - {', '.join(entry['authors'][:3])}"
            for entry in bibliography.get("recent", [])[:5]
        ])
        
        prompt = f"""Проанализируй следующий библиографический корпус и создай краткое резюме основных направлений, методологий и ключевых идей.

Основные работы (core):
{core_text}

Недавние работы (recent):
{recent_text}

Создай структурированное резюме (3-5 абзацев), выделяя:
1. Основные теоретические направления
2. Ключевые методологии
3. Важные концепции и идеи
4. Актуальные тренды в исследованиях"""
        
        # Use dynamic max_tokens calculation (default to 3000 words for summaries)
        max_tokens = calculate_max_tokens(3000)
        
        summary = self.deepseek.chat(
            system_prompt="Ты — эксперт по анализу научной литературы.",
            user_prompt=prompt,
            temperature=0.6,
            max_tokens=max_tokens
        )
        
        # Auto-extend if incomplete
        summary = auto_extend_text(
            self.deepseek,
            "Ты — эксперт по анализу научной литературы.",
            prompt,
            summary,
            max_tokens
        )
        
        # Save summary
        output_dir = config.OUTPUTS_DIR / course_id
        output_dir.mkdir(parents=True, exist_ok=True)
        write_text(output_dir / f"{lecture_id}_bibliography_summary.md", summary)
        
        return summary
    
    def run_outline_step(
        self,
        course_id: str,
        lecture_id: str,
        uploaded_sources_summary: str,
        uploaded_sources_keypoints: List[str],
        bibliography_summary: str
    ) -> str:
        """
        Generate lecture outline.
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier
            uploaded_sources_summary: Summary of uploaded sources
            uploaded_sources_keypoints: Key points from uploaded sources
            bibliography_summary: Summary of bibliography
        
        Returns:
            Outline text
        """
        lecture = self.course_manager.get_lecture(course_id, lecture_id)
        if not lecture:
            raise ValueError(f"Lecture {lecture_id} not found")
        
        lecture_title = lecture.get("title", "")
        lecture_order = lecture.get("order", 0)
        
        course_context = self.course_manager.get_course_context_text(course_id)
        previous_lectures_summary = self.course_manager.get_previous_lectures_summary(
            course_id, lecture_order
        )
        
        # Load outline prompt template
        outline_template = load_prompt("steps/step3_outline.md")
        
        outline_prompt = render_prompt(
            outline_template,
            lecture_title=lecture_title,
            course_context=course_context,
            uploaded_sources_summary=uploaded_sources_summary,
            uploaded_sources_keypoints="\n".join(f"- {kp}" for kp in uploaded_sources_keypoints),
            bibliography_summary=bibliography_summary,
            previous_lectures_summary=previous_lectures_summary
        )
        
        # Load system prompt
        system_prompt = load_prompt("system/base_system_prompt.md")
        
        # Use dynamic max_tokens (outline should be ~2000 words)
        max_tokens = calculate_max_tokens(2000)
        
        outline = self.deepseek.chat(
            system_prompt=system_prompt,
            user_prompt=outline_prompt,
            temperature=0.7,
            max_tokens=max_tokens
        )
        
        # Auto-extend if incomplete
        outline = auto_extend_text(
            self.deepseek,
            system_prompt,
            outline_prompt,
            outline,
            max_tokens
        )
        
        # Save outline
        output_dir = config.OUTPUTS_DIR / course_id
        output_dir.mkdir(parents=True, exist_ok=True)
        write_text(output_dir / f"{lecture_id}_outline.md", outline)
        
        return outline
    
    def run_draft_step(
        self,
        course_id: str,
        lecture_id: str,
        outline_text: str,
        uploaded_sources_keypoints: List[str],
        bibliography: Dict[str, List[Dict]],
        model_name: str = "deepseek-chat"
    ) -> str:
        """
        Generate draft lecture (4000 words).
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier
            outline_text: Generated outline
            uploaded_sources_keypoints: Key points from uploaded sources
            bibliography: Bibliography dictionary
        
        Returns:
            Draft lecture text
        """
        # Get lecture metadata for target_length
        lecture = self.course_manager.get_lecture(course_id, lecture_id)
        target_length = lecture.get("target_length", 4000) if lecture else 4000
        # Get target word count and calculate max_tokens
        target_words = target_length  # target_length is already in words
        max_tokens = int(target_words * 1.5)  # Approximate tokens needed
        
        # Get LLM client based on model selection
        llm_client = get_llm_client(model_name)
        
        # Get uploaded sources summary if available (for injection into draft)
        sources_file = config.UPLOADS_DIR / course_id / lecture_id / "sources.json"
        uploaded_sources_summary = ""
        if sources_file.exists():
            sources_data = read_json(sources_file)
            uploaded_sources_summary = sources_data.get("full_summary", "")
        
        # Load draft prompt template
        draft_template = load_prompt("steps/step4_lecture_draft.md")
        
        # Format bibliography for prompt
        core_bib = "\n".join([
            f"- {entry['title']} ({entry['year']})"
            for entry in bibliography.get("core", [])[:5]
        ])
        recent_bib = "\n".join([
            f"- {entry['title']} ({entry['year']})"
            for entry in bibliography.get("recent", [])[:5]
        ])
        
        # Prepare draft prompt with target word count instruction
        draft_prompt_base = render_prompt(
            draft_template,
            outline_text=outline_text,
            target_length=target_length,
            uploaded_sources_keypoints="\n".join(f"- {kp}" for kp in uploaded_sources_keypoints),
            core_bibliography=core_bib,
            recent_bibliography=recent_bib
        )
        
        # Add instruction about target word count at the beginning
        draft_prompt = (
            f"Ты пишешь академическую лекцию. "
            f"Целевой объём: минимум {target_words} слов.\n"
            f"Ты обязана довести текст до полной логической завершённости.\n"
            f"Если достигнут лимит токенов — продолжай текст автоматически.\n\n"
        ) + draft_prompt_base
        
        # Load system prompt
        system_prompt = load_prompt("system/base_system_prompt.md")
        
        # Inject PDF analysis results if available
        if uploaded_sources_summary:
            system_prompt += f"\n\nУчти результаты анализа загруженных файлов:\n{uploaded_sources_summary}"
        
        # Calculate safe max_tokens based on model and target_length
        max_tokens_safe = get_max_tokens_for_model(model_name, target_length)
        # Use the larger of calculated max_tokens
        max_tokens = max(max_tokens, max_tokens_safe)
        is_grok = model_name and model_name.startswith("grok")
        
        # Generate draft - use call_grok directly for Grok models to get auto-continue
        if is_grok:
            from src.llm.grok_client import call_grok
            # Combine system and user prompts for call_grok
            full_prompt_for_grok = f"{system_prompt}\n\n{draft_prompt}"
            draft = call_grok(full_prompt_for_grok, model=model_name, max_tokens=max_tokens)
        else:
            draft = llm_client.chat(
                system_prompt=system_prompt,
                user_prompt=draft_prompt,
                temperature=0.8,
                max_tokens=max_tokens
            )
            
            # Auto-extend if incomplete (only for non-Grok models)
            draft = auto_extend_text(
                llm_client,
                system_prompt,
                draft_prompt,
                draft,
                max_tokens
            )
        
        # Post-check: verify word count and expand if needed
        word_count = count_words(draft)
        if word_count < target_length:
            missing = target_length - word_count
            expansion_prompt = (
                f"Текущий объём: {word_count} слов. "
                f"Добавь не менее {missing} слов, заверши последний раздел, "
                f"дополни вывод, примеры и теоретические детали.\n\n"
                f"Текущий текст:\n{draft}"
            )
            
            # Calculate safe max_tokens for expansion - use full budget
            expansion_max_tokens = get_max_tokens_for_model(model_name, target_length)
            expansion_max_tokens = max(expansion_max_tokens, int(missing * 1.5))
            
            # Generate expansion - use call_grok directly for Grok models
            if is_grok:
                from src.llm.grok_client import call_grok
                full_expansion_prompt = f"{system_prompt}\n\n{expansion_prompt}"
                expansion_text = call_grok(full_expansion_prompt, model=model_name, max_tokens=expansion_max_tokens)
                # Merge expansion with original draft
                draft = draft + "\n\n" + expansion_text
            else:
                draft = llm_client.chat(
                    system_prompt=system_prompt,
                    user_prompt=expansion_prompt,
                    temperature=0.7,
                    max_tokens=expansion_max_tokens
                )
                
                # Auto-extend expansion if incomplete (only for non-Grok models)
                draft = auto_extend_text(
                    llm_client,
                    system_prompt,
                    expansion_prompt,
                    draft,
                    expansion_max_tokens
                )
            
            # Verify final word count
            final_word_count = count_words(draft)
            print(f"\033[92m[LECTURE] Draft final word count: {final_word_count} / {target_length} words\033[0m")
        
        # Save draft
        output_dir = config.OUTPUTS_DIR / course_id
        output_dir.mkdir(parents=True, exist_ok=True)
        write_text(output_dir / f"{lecture_id}_draft.md", draft)
        
        return draft
    
    def run_revision_step(
        self,
        course_id: str,
        lecture_id: str,
        raw_lecture_text: str,
        model_name: str = "deepseek-chat"
    ) -> str:
        """
        Revise lecture with style improvements.
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier
            raw_lecture_text: Draft lecture text
        
        Returns:
            Revised lecture text
        """
        lecture = self.course_manager.get_lecture(course_id, lecture_id)
        if not lecture:
            raise ValueError(f"Lecture {lecture_id} not found")
        
        # Get target word count and calculate max_tokens
        target_length = lecture.get("target_length", 4000)
        target_words = target_length  # target_length is already in words
        max_tokens = int(target_words * 1.5)  # Approximate tokens needed
        lecture_order = lecture.get("order", 0)
        previous_lectures_summary = self.course_manager.get_previous_lectures_summary(
            course_id, lecture_order
        )
        
        # Get uploaded sources summary if available
        sources_file = config.UPLOADS_DIR / course_id / lecture_id / "sources.json"
        uploaded_sources_summary = ""
        if sources_file.exists():
            sources_data = read_json(sources_file)
            uploaded_sources_summary = sources_data.get("full_summary", "")
        
        # Load style reference
        style_reference = load_prompt("system/style_samira.md")
        
        # Load revision prompt
        revision_template = load_prompt("steps/step5_revision.md")
        
        revision_prompt_base = render_prompt(
            revision_template,
            target_length=target_length,
            style_reference_text=style_reference,
            raw_lecture_text=raw_lecture_text,
            previous_lectures_summary=previous_lectures_summary,
            uploaded_sources_summary=uploaded_sources_summary
        )
        
        # Add instruction about target word count at the beginning
        revision_prompt = (
            f"Ты редактируешь академическую лекцию. "
            f"Целевой объём: минимум {target_words} слов.\n"
            f"Ты обязана довести текст до полной логической завершённости.\n"
            f"Если достигнут лимит токенов — продолжай текст автоматически.\n\n"
        ) + revision_prompt_base
        
        # Load system prompt
        system_prompt = load_prompt("system/base_system_prompt.md")
        
        # Get LLM client based on model selection
        llm_client = get_llm_client(model_name)
        
        # Calculate safe max_tokens based on model and target_length
        max_tokens_safe = get_max_tokens_for_model(model_name, target_length)
        # Use the larger of calculated max_tokens
        max_tokens = max(max_tokens, max_tokens_safe)
        is_grok = model_name and model_name.startswith("grok")
        
        # Generate revision - use call_grok directly for Grok models to get auto-continue
        if is_grok:
            from src.llm.grok_client import call_grok
            # Combine system and user prompts for call_grok
            full_prompt_for_grok = f"{system_prompt}\n\n{revision_prompt}"
            revised = call_grok(full_prompt_for_grok, model=model_name, max_tokens=max_tokens)
        else:
            revised = llm_client.chat(
                system_prompt=system_prompt,
                user_prompt=revision_prompt,
                temperature=0.7,
                max_tokens=max_tokens
            )
            
            # Auto-extend if incomplete (only for non-Grok models)
            revised = auto_extend_text(
                llm_client,
                system_prompt,
                revision_prompt,
                revised,
                max_tokens
            )
        
        # Post-check: verify word count and expand if needed
        word_count = count_words(revised)
        if word_count < target_length:
            missing = target_length - word_count
            expansion_prompt = (
                f"Текущий объём: {word_count} слов. "
                f"Добавь не менее {missing} слов, заверши последний раздел, "
                f"дополни вывод, примеры и теоретические детали.\n\n"
                f"Текущий текст:\n{revised}\n\n"
                f"ВАЖНО: НЕ сокращай существующий текст, только расширяй его."
            )
            
            # Calculate safe max_tokens for expansion - use full budget
            expansion_max_tokens = get_max_tokens_for_model(model_name, target_length)
            expansion_max_tokens = max(expansion_max_tokens, int(missing * 1.5))
            
            # Generate expansion - use call_grok directly for Grok models
            if is_grok:
                from src.llm.grok_client import call_grok
                full_expansion_prompt = f"{system_prompt}\n\n{expansion_prompt}"
                expansion_text = call_grok(full_expansion_prompt, model=model_name, max_tokens=expansion_max_tokens)
                # Merge expansion with original revised text
                revised = revised + "\n\n" + expansion_text
            else:
                revised = llm_client.chat(
                    system_prompt=system_prompt,
                    user_prompt=expansion_prompt,
                    temperature=0.7,
                    max_tokens=expansion_max_tokens
                )
                
                # Auto-extend expansion if incomplete (only for non-Grok models)
                revised = auto_extend_text(
                    llm_client,
                    system_prompt,
                    expansion_prompt,
                    revised,
                    expansion_max_tokens
                )
            
            # Verify final word count
            final_word_count = count_words(revised)
            print(f"\033[92m[LECTURE] Final revised word count: {final_word_count} / {target_length} words\033[0m")
        
        # Save revised lecture
        output_dir = config.OUTPUTS_DIR / course_id
        output_dir.mkdir(parents=True, exist_ok=True)
        write_text(output_dir / f"{lecture_id}_final.md", revised)
        
        return revised
    
    def run_glossary_step(
        self,
        course_id: str,
        lecture_id: str,
        final_lecture_text: str
    ) -> str:
        """
        Extract glossary from final lecture.
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier
            final_lecture_text: Final lecture text
        
        Returns:
            Glossary text
        """
        # Load glossary prompt
        glossary_template = load_prompt("steps/step6_glossary.md")
        
        glossary_prompt = render_prompt(
            glossary_template,
            lecture_text=final_lecture_text
        )
        
        # Load system prompt
        system_prompt = load_prompt("system/base_system_prompt.md")
        
        # Glossary is typically shorter, but use dynamic calculation
        max_tokens = calculate_max_tokens(2000)
        
        glossary = self.deepseek.chat(
            system_prompt=system_prompt,
            user_prompt=glossary_prompt,
            temperature=0.5,
            max_tokens=max_tokens
        )
        
        # Auto-extend if incomplete
        glossary = auto_extend_text(
            self.deepseek,
            system_prompt,
            glossary_prompt,
            glossary,
            max_tokens
        )
        
        # Save glossary
        output_dir = config.OUTPUTS_DIR / course_id
        output_dir.mkdir(parents=True, exist_ok=True)
        write_text(output_dir / f"{lecture_id}_glossary.md", glossary)
        
        return glossary
    
    def run_presentation_prompt_step(
        self,
        course_id: str,
        lecture_id: str,
        final_lecture_text: str,
        glossary_text: str,
        uploaded_sources_keypoints: List[str]
    ) -> str:
        """
        Generate Gamma presentation prompt.
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier
            final_lecture_text: Final lecture text
            glossary_text: Glossary text
            uploaded_sources_keypoints: Key points from uploaded sources
        
        Returns:
            Gamma prompt text
        """
        # Load Gamma prompt template
        gamma_template = load_prompt("presentation/gamma_prompt_template.md")
        
        gamma_prompt = render_prompt(
            gamma_template,
            final_lecture_text=final_lecture_text,
            glossary_text=glossary_text,
            uploaded_sources_keypoints="\n".join(f"- {kp}" for kp in uploaded_sources_keypoints)
        )
        
        # Save Gamma prompt
        output_dir = config.OUTPUTS_DIR / course_id
        output_dir.mkdir(parents=True, exist_ok=True)
        write_text(output_dir / f"{lecture_id}_gamma_prompt.md", gamma_prompt)
        
        return gamma_prompt

