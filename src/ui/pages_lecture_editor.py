"""
Lecture Editor Page for Streamlit.
"""
import streamlit as st
from src.core.course_manager import CourseManager
from src.core.lecture_pipeline import LecturePipeline
from src.llm.model_registry import MODEL_REGISTRY
from src.storage.lecture_store import load_full_lecture_data, save_lecture_data
from src.utils.io_utils import read_json, write_text
from src.utils.text_postprocessing import count_words
import config


def render_lecture_editor_page():
    """Render the lecture editor page."""
    st.title("📝 Редактор лекции")
    
    # Get selected lecture from session state
    if "selected_lecture" not in st.session_state:
        st.warning("Лекция не выбрана. Вернитесь к списку лекций.")
        if st.button("← Назад к списку лекций"):
            st.session_state["selected_lecture"] = None
            st.session_state["current_page"] = "courses"
            st.rerun()
        return
    
    selected_lecture = st.session_state["selected_lecture"]
    course_id = selected_lecture.get("course_id")
    lecture_id = selected_lecture.get("lecture_id")
    
    if not course_id or not lecture_id:
        st.error("Неверные данные лекции. Вернитесь к списку.")
        if st.button("← Назад к списку лекций"):
            st.session_state["selected_lecture"] = None
            st.session_state["current_page"] = "courses"
            st.rerun()
        return
    
    # Load lecture data
    try:
        lecture_data = load_full_lecture_data(course_id, lecture_id)
    except Exception as e:
        st.error(f"Ошибка загрузки лекции: {str(e)}")
        if st.button("← Назад к списку лекций"):
            st.session_state["selected_lecture"] = None
            st.session_state["current_page"] = "courses"
            st.rerun()
        return
    
    # Initialize pipeline for regeneration
    pipeline = LecturePipeline()
    
    # Sidebar with lecture info
    with st.sidebar:
        st.subheader("Информация о лекции")
        st.write(f"**Курс:** {course_id}")
        st.write(f"**ID лекции:** {lecture_id}")
        st.write(f"**Порядковый номер:** {lecture_data.get('order', 0)}")
        
        # Word count info
        draft_words = count_words(lecture_data.get("draft", ""))
        final_words = count_words(lecture_data.get("final", ""))
        target_words = lecture_data.get("target_length", 4000)
        
        st.write(f"**Целевой объём:** {target_words} слов")
        st.write(f"**Черновик:** {draft_words} слов")
        st.write(f"**Финальная версия:** {final_words} слов")
        
        if st.button("← Назад к списку лекций"):
            st.session_state["selected_lecture"] = None
            st.session_state["current_page"] = "courses"
            st.rerun()
    
    # Main content
    st.header("Метаданные лекции")
    
    with st.form("edit_metadata_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Название лекции", value=lecture_data.get("title", ""))
            subtitle = st.text_input("Подзаголовок", value=lecture_data.get("subtitle", ""))
            order = st.number_input("Порядковый номер", min_value=0, value=lecture_data.get("order", 0))
        
        with col2:
            keywords_str = ", ".join(lecture_data.get("keywords", []))
            keywords = st.text_input("Ключевые слова (через запятую)", value=keywords_str)
            target_length = st.number_input(
                "Целевой объём (слов)",
                min_value=3000,
                value=lecture_data.get("target_length", 4000),
                step=200
            )
        
        if st.form_submit_button("💾 Сохранить метаданные"):
            # Update lecture data
            lecture_data["title"] = title
            lecture_data["subtitle"] = subtitle
            lecture_data["order"] = order
            lecture_data["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]
            lecture_data["target_length"] = target_length
            
            # Save to storage
            save_lecture_data(lecture_data)
            st.success("Метаданные сохранены!")
            st.rerun()
    
    # Outline section
    st.header("План лекции")
    outline = st.text_area(
        "План",
        value=lecture_data.get("outline", ""),
        height=200,
        key="outline_editor"
    )
    
    if outline != lecture_data.get("outline", ""):
        if st.button("💾 Сохранить план"):
            lecture_data["outline"] = outline
            output_dir = config.OUTPUTS_DIR / course_id
            output_dir.mkdir(parents=True, exist_ok=True)
            write_text(output_dir / f"{lecture_id}_outline.md", outline)
            st.success("План сохранён!")
    
    # Draft section
    st.header("Черновик лекции")
    
    draft_text = st.text_area(
        "Черновик",
        value=lecture_data.get("draft", ""),
        height=400,
        key="draft_editor"
    )
    
    # Model selection for draft
    # Set default index to grok-4-fast-reasoning if available
    default_index = 0
    if "grok-4-fast-reasoning" in MODEL_REGISTRY:
        default_index = MODEL_REGISTRY.index("grok-4-fast-reasoning")
    
    draft_model = st.selectbox(
        "Модель для черновика",
        options=MODEL_REGISTRY,
        index=default_index,
        key="draft_model"
    )
    
    st.info(f"📌 Модель для черновика: **{draft_model}**")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("🔄 Регенерировать черновик", type="primary"):
            if not lecture_data.get("outline"):
                st.warning("Сначала сохраните план лекции!")
            else:
                with st.spinner("Генерация черновика (это может занять время)..."):
                    try:
                        # Get required data for draft generation
                        sources_data = {
                            "key_ideas": lecture_data.get("sources_key_ideas", [])
                        }
                        
                        # Load bibliography if available
                        bibliography = lecture_data.get("bibliography", {"core": [], "recent": []})
                        if not bibliography:
                            bibliography = {"core": [], "recent": []}
                        
                        # Generate draft using pipeline
                        draft = pipeline.run_draft_step(
                            course_id=course_id,
                            lecture_id=lecture_id,
                            outline_text=lecture_data.get("outline", ""),
                            uploaded_sources_keypoints=lecture_data.get("sources_key_ideas", []),
                            bibliography=bibliography,
                            model_name=draft_model
                        )
                        
                        lecture_data["draft"] = draft
                        save_lecture_data(lecture_data)
                        st.success("Черновик регенерирован!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка генерации черновика: {str(e)}")
    
    with col_btn2:
        if draft_text != lecture_data.get("draft", ""):
            if st.button("💾 Сохранить черновик"):
                lecture_data["draft"] = draft_text
                save_lecture_data(lecture_data)
                st.success("Черновик сохранён!")
                st.rerun()
    
    # Final lecture section
    st.header("Финальная лекция")
    
    final_text = st.text_area(
        "Финальный текст",
        value=lecture_data.get("final", ""),
        height=400,
        key="final_editor"
    )
    
    # Model selection for final
    # Set default index to grok-4-fast-reasoning if available
    final_default_index = 0
    if "grok-4-fast-reasoning" in MODEL_REGISTRY:
        final_default_index = MODEL_REGISTRY.index("grok-4-fast-reasoning")
    
    final_model = st.selectbox(
        "Модель для финальной версии",
        options=MODEL_REGISTRY,
        index=final_default_index,
        key="final_model"
    )
    
    st.info(f"📌 Модель для финальной версии: **{final_model}**")
    
    col_btn3, col_btn4 = st.columns(2)
    
    with col_btn3:
        if st.button("🔄 Регенерировать финальную версию", type="primary"):
            if not lecture_data.get("draft"):
                st.warning("Сначала создайте черновик!")
            else:
                with st.spinner("Генерация финальной версии (это может занять время)..."):
                    try:
                        # Generate final using revision step
                        final = pipeline.run_revision_step(
                            course_id=course_id,
                            lecture_id=lecture_id,
                            raw_lecture_text=lecture_data.get("draft", ""),
                            model_name=final_model
                        )
                        
                        lecture_data["final"] = final
                        save_lecture_data(lecture_data)
                        st.success("Финальная версия регенерирована!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка генерации финальной версии: {str(e)}")
    
    with col_btn4:
        if final_text != lecture_data.get("final", ""):
            if st.button("💾 Сохранить финальную версию"):
                lecture_data["final"] = final_text
                save_lecture_data(lecture_data)
                st.success("Финальная версия сохранена!")
                st.rerun()
    
    # Bibliography section
    st.header("Библиография")
    bibliography = lecture_data.get("bibliography")
    
    if bibliography:
        from src.ui.components import display_bibliography_table
        display_bibliography_table(bibliography.get("core", []), "Основные работы (Core)")
        display_bibliography_table(bibliography.get("recent", []), "Недавние работы (Recent)")
        
        bib_summary = lecture_data.get("bibliography_summary", "")
        if bib_summary:
            st.subheader("Резюме библиографии")
            st.markdown(bib_summary)
    else:
        st.info("Библиография пока не сгенерирована.")
    
    # Glossary section
    glossary = lecture_data.get("glossary", "")
    if glossary:
        with st.expander("Глоссарий"):
            st.markdown(glossary)
    
    # Sources section
    sources_summary = lecture_data.get("sources_summary", "")
    if sources_summary:
        with st.expander("Резюме загруженных источников"):
            st.markdown(sources_summary)
        
        sources_key_ideas = lecture_data.get("sources_key_ideas", [])
        if sources_key_ideas:
            from src.ui.components import display_key_ideas
            display_key_ideas(sources_key_ideas)

