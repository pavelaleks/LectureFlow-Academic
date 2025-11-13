"""
Lecture Wizard Page for Streamlit.
"""
import streamlit as st
from pathlib import Path
from src.core.course_manager import CourseManager
from src.core.lecture_pipeline import LecturePipeline
from src.ui.components import display_bibliography_table, display_key_ideas, display_summary
from src.utils.io_utils import read_text, read_json
import config
import uuid


def render_lecture_wizard_page():
    """Render the lecture wizard page."""
    st.title("🎓 Мастер создания лекций")
    
    course_manager = CourseManager()
    pipeline = LecturePipeline()
    
    courses = course_manager.list_courses()
    
    if not courses:
        st.warning("Сначала создайте курс на странице 'Управление курсами'.")
        return
    
    # Step 1: Select Course
    st.header("Шаг 1: Выбор курса")
    course_ids = list(courses.keys())
    selected_course_id = st.selectbox("Выберите курс", options=course_ids)
    
    if not selected_course_id:
        return
    
    # Initialize session state
    if "lecture_id" not in st.session_state:
        st.session_state.lecture_id = str(uuid.uuid4())[:8]
    
    lecture_id = st.session_state.lecture_id
    
    # Step 2: Lecture Metadata
    st.header("Шаг 2: Метаданные лекции")
    
    with st.form("lecture_metadata_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            lecture_title = st.text_input("Название лекции", value="")
            lecture_subtitle = st.text_input("Подзаголовок", value="")
            lecture_order = st.number_input("Порядковый номер", min_value=0, value=0)
        
        with col2:
            keywords_input = st.text_input("Ключевые слова (через запятую)", value="")
            target_length = st.number_input("Целевой объём (слов)", min_value=1000, value=4000)
        
        save_metadata = st.form_submit_button("Сохранить метаданные")
        
        if save_metadata:
            keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
            course_manager.add_or_update_lecture(
                course_id=selected_course_id,
                lecture_id=lecture_id,
                title=lecture_title,
                subtitle=lecture_subtitle,
                order=lecture_order,
                keywords=keywords,
                target_length=target_length
            )
            st.success("Метаданные сохранены!")
    
    # Step 3: Upload Sources
    st.header("Шаг 3: Загрузка источников (PDF, DOCX, TXT)")
    st.info("⚠️ Загруженные источники имеют ПРИОРИТЕТ над всеми остальными источниками информации.")
    
    uploaded_files = st.file_uploader(
        "Загрузите файлы",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )
    
    sources_data = None
    if uploaded_files:
        if st.button("Обработать загруженные файлы"):
            with st.spinner("Обработка файлов..."):
                try:
                    sources_data = pipeline.run_uploaded_sources_step(
                        course_id=selected_course_id,
                        lecture_id=lecture_id,
                        uploaded_files=uploaded_files
                    )
                    st.session_state.sources_data = sources_data
                    st.success("Файлы обработаны!")
                except Exception as e:
                    st.error(f"Ошибка обработки: {str(e)}")
    
    # Display sources summary if available
    if "sources_data" in st.session_state:
        sources_data = st.session_state.sources_data
        if sources_data.get("full_summary"):
            display_summary(sources_data["full_summary"], "Резюме загруженных источников")
        if sources_data.get("key_ideas"):
            display_key_ideas(sources_data["key_ideas"])
    
    # Step 4: OpenAlex Bibliography
    st.header("Шаг 4: Библиография OpenAlex")
    
    lecture = course_manager.get_lecture(selected_course_id, lecture_id)
    keywords = lecture.get("keywords", []) if lecture else []
    
    if keywords:
        if st.button("Сгенерировать библиографию"):
            with st.spinner("Поиск в OpenAlex..."):
                try:
                    bibliography = pipeline.run_bibliography_step(
                        course_id=selected_course_id,
                        lecture_id=lecture_id,
                        keywords=keywords
                    )
                    st.session_state.bibliography = bibliography
                    st.success("Библиография сгенерирована!")
                except Exception as e:
                    st.error(f"Ошибка: {str(e)}")
        
        if "bibliography" in st.session_state:
            bibliography = st.session_state.bibliography
            display_bibliography_table(bibliography.get("core", []), "Основные работы (Core)")
            display_bibliography_table(bibliography.get("recent", []), "Недавние работы (Recent)")
    else:
        st.warning("Сначала укажите ключевые слова в метаданных лекции.")
    
    # Step 5: Bibliography Summary
    st.header("Шаг 5: Резюме библиографии")
    
    if "bibliography" in st.session_state:
        if st.button("Создать резюме библиографии"):
            with st.spinner("Генерация резюме..."):
                try:
                    bib_summary = pipeline.run_bibliography_summary_step(
                        course_id=selected_course_id,
                        lecture_id=lecture_id,
                        bibliography=st.session_state.bibliography
                    )
                    st.session_state.bibliography_summary = bib_summary
                    st.success("Резюме создано!")
                except Exception as e:
                    st.error(f"Ошибка: {str(e)}")
        
        if "bibliography_summary" in st.session_state:
            display_summary(st.session_state.bibliography_summary, "Резюме библиографии")
    else:
        st.info("Сначала сгенерируйте библиографию.")
    
    # Step 6: Outline Generation
    st.header("Шаг 6: Генерация плана лекции")
    
    if st.button("Сгенерировать план"):
        if "sources_data" not in st.session_state:
            st.warning("Рекомендуется сначала обработать загруженные источники.")
        
        with st.spinner("Генерация плана..."):
            try:
                sources_data = st.session_state.get("sources_data", {})
                bib_summary = st.session_state.get("bibliography_summary", "")
                
                outline = pipeline.run_outline_step(
                    course_id=selected_course_id,
                    lecture_id=lecture_id,
                    uploaded_sources_summary=sources_data.get("full_summary", ""),
                    uploaded_sources_keypoints=sources_data.get("key_ideas", []),
                    bibliography_summary=bib_summary
                )
                st.session_state.outline = outline
                st.success("План сгенерирован!")
            except Exception as e:
                st.error(f"Ошибка: {str(e)}")
    
    if "outline" in st.session_state:
        st.subheader("План лекции")
        editable_outline = st.text_area(
            "План (можно редактировать)",
            value=st.session_state.outline,
            height=400
        )
        if editable_outline != st.session_state.outline:
            st.session_state.outline = editable_outline
    
    # Step 7: Draft → Revision → Glossary
    st.header("Шаг 7: Генерация лекции")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Сгенерировать черновик"):
            if "outline" not in st.session_state:
                st.warning("Сначала сгенерируйте план.")
            else:
                with st.spinner("Генерация черновика (это может занять время)..."):
                    try:
                        sources_data = st.session_state.get("sources_data", {})
                        bibliography = st.session_state.get("bibliography", {"core": [], "recent": []})
                        
                        draft = pipeline.run_draft_step(
                            course_id=selected_course_id,
                            lecture_id=lecture_id,
                            outline_text=st.session_state.outline,
                            uploaded_sources_keypoints=sources_data.get("key_ideas", []),
                            bibliography=bibliography
                        )
                        st.session_state.draft = draft
                        st.success("Черновик создан!")
                    except Exception as e:
                        st.error(f"Ошибка: {str(e)}")
    
    with col2:
        if st.button("Отредактировать до финала"):
            if "draft" not in st.session_state:
                st.warning("Сначала сгенерируйте черновик.")
            else:
                with st.spinner("Редактура..."):
                    try:
                        revised = pipeline.run_revision_step(
                            course_id=selected_course_id,
                            lecture_id=lecture_id,
                            raw_lecture_text=st.session_state.draft
                        )
                        st.session_state.final = revised
                        st.success("Финальная версия готова!")
                    except Exception as e:
                        st.error(f"Ошибка: {str(e)}")
    
    with col3:
        if st.button("Извлечь глоссарий"):
            if "final" not in st.session_state:
                st.warning("Сначала создайте финальную версию.")
            else:
                with st.spinner("Извлечение глоссария..."):
                    try:
                        glossary = pipeline.run_glossary_step(
                            course_id=selected_course_id,
                            lecture_id=lecture_id,
                            final_lecture_text=st.session_state.final
                        )
                        st.session_state.glossary = glossary
                        st.success("Глоссарий создан!")
                    except Exception as e:
                        st.error(f"Ошибка: {str(e)}")
    
    # Display outputs
    if "draft" in st.session_state:
        with st.expander("Черновик лекции"):
            st.markdown(st.session_state.draft)
    
    if "final" in st.session_state:
        with st.expander("Финальная лекция"):
            st.markdown(st.session_state.final)
    
    if "glossary" in st.session_state:
        with st.expander("Глоссарий"):
            st.markdown(st.session_state.glossary)
    
    # Step 8: Presentation Prompt
    st.header("Шаг 8: Промпт для Gamma")
    
    if st.button("Сгенерировать промпт для Gamma"):
        if "final" not in st.session_state:
            st.warning("Сначала создайте финальную версию лекции.")
        else:
            with st.spinner("Генерация промпта..."):
                try:
                    sources_data = st.session_state.get("sources_data", {})
                    
                    gamma_prompt = pipeline.run_presentation_prompt_step(
                        course_id=selected_course_id,
                        lecture_id=lecture_id,
                        final_lecture_text=st.session_state.final,
                        glossary_text=st.session_state.get("glossary", ""),
                        uploaded_sources_keypoints=sources_data.get("key_ideas", [])
                    )
                    st.session_state.gamma_prompt = gamma_prompt
                    st.success("Промпт создан!")
                except Exception as e:
                    st.error(f"Ошибка: {str(e)}")
    
    if "gamma_prompt" in st.session_state:
        st.subheader("Промпт для Gamma")
        st.text_area(
            "Промпт (скопируйте в Gamma)",
            value=st.session_state.gamma_prompt,
            height=400
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Копировать в буфер обмена"):
                st.code(st.session_state.gamma_prompt)
                st.info("Используйте Ctrl+C для копирования из поля выше.")
        
        with col2:
            output_file = config.OUTPUTS_DIR / selected_course_id / f"{lecture_id}_gamma_prompt.md"
            st.download_button(
                "💾 Скачать",
                data=st.session_state.gamma_prompt,
                file_name=f"{lecture_id}_gamma_prompt.md",
                mime="text/markdown"
            )

