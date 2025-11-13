"""
Lecture Wizard Page for Streamlit.
"""
import streamlit as st
from pathlib import Path
import tempfile
import os
from src.core.course_manager import CourseManager
from src.core.lecture_pipeline import LecturePipeline
from src.ui.components import display_bibliography_table, display_key_ideas, display_summary
from src.utils.io_utils import read_text, read_json
from src.export.docx_exporter import export_lecture_to_docx
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
            target_length = st.number_input("Целевой объём (слов)", min_value=3000, value=3800, step=200)
        
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
    
    # Load saved OpenAlex parameters or use defaults
    if lecture:
        default_core_keywords = lecture.get("metadata", {}).get("core_keywords", st.session_state.get("core_keywords", ""))
        default_core_authors = lecture.get("metadata", {}).get("core_authors", st.session_state.get("core_authors", ""))
        default_recent_keywords = lecture.get("metadata", {}).get("recent_keywords", st.session_state.get("recent_keywords", ""))
    else:
        default_core_keywords = st.session_state.get("core_keywords", "")
        default_core_authors = st.session_state.get("core_authors", "")
        default_recent_keywords = st.session_state.get("recent_keywords", "")
    
    st.subheader("Параметры запроса OpenAlex")
    
    core_keywords = st.text_input(
        "Core keywords (через запятую)",
        value=default_core_keywords,
        key="core_keywords_input"
    )
    
    core_authors = st.text_input(
        "Core authors (через запятую)",
        value=default_core_authors,
        key="core_authors_input"
    )
    
    recent_keywords = st.text_input(
        "Recent keywords (через запятую)",
        value=default_recent_keywords,
        key="recent_keywords_input"
    )
    
    # Save to session state
    st.session_state["core_keywords"] = core_keywords
    st.session_state["core_authors"] = core_authors
    st.session_state["recent_keywords"] = recent_keywords
    
    # Save to lecture metadata when button is clicked
    if st.button("Сохранить параметры OpenAlex"):
        course_manager.add_or_update_lecture(
            course_id=selected_course_id,
            lecture_id=lecture_id,
            title=lecture.get("title", "") if lecture else "",
            subtitle=lecture.get("subtitle", "") if lecture else "",
            order=lecture.get("order", 0) if lecture else 0,
            keywords=lecture.get("keywords", []) if lecture else [],
            target_length=lecture.get("target_length", 3800) if lecture else 3800,
            metadata={
                **(lecture.get("metadata", {}) if lecture else {}),
                "core_keywords": core_keywords,
                "core_authors": core_authors,
                "recent_keywords": recent_keywords
            }
        )
        st.success("Параметры сохранены!")
    
    if st.button("Сгенерировать библиографию"):
        with st.spinner("Поиск в OpenAlex..."):
            try:
                bibliography = pipeline.run_bibliography_step(
                    course_id=selected_course_id,
                    lecture_id=lecture_id,
                    core_keywords=core_keywords,
                    core_authors=core_authors,
                    recent_keywords=recent_keywords
                )
                
                # Count total results
                core_count = len(bibliography.get("core", []))
                recent_count = len(bibliography.get("recent", []))
                total_count = core_count + recent_count
                
                st.session_state.bibliography = bibliography
                
                if total_count > 0:
                    st.success(f"Библиография сгенерирована! Найдено {total_count} работ (core: {core_count}, recent: {recent_count})")
                    st.info(f"📘 OpenAlex: найдено {total_count} релевантных работ")
                else:
                    st.warning("⚠️ OpenAlex не вернул результатов. Попробуйте упростить ключевые слова или изменить параметры поиска.")
            except Exception as e:
                st.error(f"Ошибка: {str(e)}")
                import traceback
                st.error(f"Детали ошибки: {traceback.format_exc()}")
    
    if "bibliography" in st.session_state:
        bibliography = st.session_state.bibliography
        core_count = len(bibliography.get("core", []))
        recent_count = len(bibliography.get("recent", []))
        
        if core_count == 0 and recent_count == 0:
            st.warning("⚠️ OpenAlex не вернул результатов. Попробуйте упростить ключевые слова.")
        else:
            display_bibliography_table(bibliography.get("core", []), "Основные работы (Core)")
            display_bibliography_table(bibliography.get("recent", []), "Недавние работы (Recent)")
    
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
    
    # Model selection
    st.subheader("Выбор модели для генерации")
    from src.llm.model_registry import MODEL_REGISTRY
    
    # Set default index to grok-4-fast-reasoning if available
    default_index = 0
    if "grok-4-fast-reasoning" in MODEL_REGISTRY:
        default_index = MODEL_REGISTRY.index("grok-4-fast-reasoning")
    
    selected_model = st.selectbox(
        "Выберите модель",
        options=MODEL_REGISTRY,
        index=default_index,
        help="Grok reasoning — лучший для сложных задач и PDF. DeepSeek — быстрый и экономичный. GPT — качественный стиль."
    )
    
    # Display selected model
    st.info(f"📌 Модель, которая будет использоваться: **{selected_model}**")
    
    # Store in session state
    st.session_state["model_choice"] = selected_model
    
    # Check model availability
    if selected_model.startswith("grok"):
        try:
            import os
            if not os.getenv("GROK_API_KEY"):
                st.warning("⚠️ GROK_API_KEY не установлен в переменных окружения. Grok недоступен.")
                selected_model = "deepseek-chat"
                st.session_state["model_choice"] = selected_model
        except:
            pass
    
    # Create 5 columns for all generation buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("Сгенерировать краткий черновик"):
            if "outline" not in st.session_state:
                st.warning("Сначала сгенерируйте план.")
            else:
                with st.spinner("Генерация краткого черновика..."):
                    try:
                        from src.core.brief_draft_generator import generate_brief_draft
                        
                        # Get lecture metadata
                        lecture = course_manager.get_lecture(selected_course_id, lecture_id)
                        metadata = {
                            "title": lecture.get("title", "") if lecture else "",
                            "subtitle": lecture.get("subtitle", "") if lecture else "",
                            "keywords": lecture.get("keywords", []) if lecture else []
                        }
                        
                        # Get PDF summary if available
                        sources_data = st.session_state.get("sources_data", {})
                        pdf_summary = sources_data.get("full_summary", "")
                        
                        # Generate brief draft
                        brief_draft = generate_brief_draft(
                            metadata=metadata,
                            pdf_summary=pdf_summary,
                            model_name=selected_model
                        )
                        
                        st.session_state["brief_draft"] = brief_draft
                        st.success("Краткий черновик готов!")
                    except Exception as e:
                        st.error(f"Ошибка: {str(e)}")
    
    with col2:
        if st.button("Сгенерировать черновик"):
            if "outline" not in st.session_state:
                st.warning("Сначала сгенерируйте план.")
            else:
                with st.spinner("Генерация черновика (это может занять время)..."):
                    try:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        sources_data = st.session_state.get("sources_data", {})
                        bibliography = st.session_state.get("bibliography", {"core": [], "recent": []})
                        
                        status_text.text("🔄 Инициализация генерации...")
                        progress_bar.progress(10)
                        
                        status_text.text("📝 Генерация основного текста...")
                        progress_bar.progress(30)
                        
                        draft = pipeline.run_draft_step(
                            course_id=selected_course_id,
                            lecture_id=lecture_id,
                            outline_text=st.session_state.outline,
                            uploaded_sources_keypoints=sources_data.get("key_ideas", []),
                            bibliography=bibliography,
                            model_name=selected_model
                        )
                        
                        from src.utils.text_postprocessing import count_words
                        word_count = count_words(draft)
                        
                        # Get target length for display
                        lecture = course_manager.get_lecture(selected_course_id, lecture_id)
                        target_length = lecture.get("target_length", 4000) if lecture else 4000
                        
                        if word_count >= target_length:
                            status_text.text(f"✅ Черновик готов: {word_count} слов (цель: {target_length})")
                        else:
                            status_text.text(f"⚙️ Расширение до целевого объёма... ({word_count} → {target_length} слов)")
                            progress_bar.progress(70)
                            # Pipeline will handle expansion automatically
                            draft = pipeline.run_draft_step(
                                course_id=selected_course_id,
                                lecture_id=lecture_id,
                                outline_text=st.session_state.outline,
                                uploaded_sources_keypoints=sources_data.get("key_ideas", []),
                                bibliography=bibliography,
                                model_name=selected_model
                            )
                            final_word_count = count_words(draft)
                            status_text.text(f"✅ Черновик готов: {final_word_count} слов (цель: {target_length})")
                        
                        progress_bar.progress(100)
                        st.session_state.draft = draft
                        st.success(f"Черновик создан! Объём: {count_words(draft)} слов")
                        progress_bar.empty()
                        status_text.empty()
                    except Exception as e:
                        st.error(f"Ошибка: {str(e)}")
                        import traceback
                        st.error(f"Детали: {traceback.format_exc()}")
    
    with col3:
        if st.button("Отредактировать до финала"):
            if "draft" not in st.session_state:
                st.warning("Сначала сгенерируйте черновик.")
            else:
                with st.spinner("Редактура..."):
                    try:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        status_text.text("🔄 Инициализация редактуры...")
                        progress_bar.progress(10)
                        
                        status_text.text("✏️ Редактирование и стилизация...")
                        progress_bar.progress(40)
                        
                        revised = pipeline.run_revision_step(
                            course_id=selected_course_id,
                            lecture_id=lecture_id,
                            raw_lecture_text=st.session_state.draft,
                            model_name=selected_model
                        )
                        
                        from src.utils.text_postprocessing import count_words
                        word_count = count_words(revised)
                        
                        # Get target length for display
                        lecture = course_manager.get_lecture(selected_course_id, lecture_id)
                        target_length = lecture.get("target_length", 4000) if lecture else 4000
                        
                        if word_count >= target_length:
                            status_text.text(f"✅ Редактура завершена: {word_count} слов (цель: {target_length})")
                        else:
                            status_text.text(f"⚙️ Расширение до целевого объёма... ({word_count} → {target_length} слов)")
                            progress_bar.progress(70)
                            # Pipeline will handle expansion automatically
                            revised = pipeline.run_revision_step(
                                course_id=selected_course_id,
                                lecture_id=lecture_id,
                                raw_lecture_text=st.session_state.draft,
                                model_name=selected_model
                            )
                            final_word_count = count_words(revised)
                            status_text.text(f"✅ Редактура завершена: {final_word_count} слов (цель: {target_length})")
                        
                        progress_bar.progress(100)
                        st.session_state.final = revised
                        st.success(f"Финальная версия готова! Объём: {count_words(revised)} слов")
                        progress_bar.empty()
                        status_text.empty()
                    except Exception as e:
                        st.error(f"Ошибка: {str(e)}")
                        import traceback
                        st.error(f"Детали: {traceback.format_exc()}")
    
    with col4:
        if st.button("Сгенерировать резюме лекции"):
            if "outline" not in st.session_state:
                st.warning("Сначала сгенерируйте план.")
            else:
                with st.spinner("Генерация резюме лекции (600–800 слов)..."):
                    try:
                        from src.core.brief_draft_generator import generate_lecture_summary
                        
                        # Get lecture metadata
                        lecture = course_manager.get_lecture(selected_course_id, lecture_id)
                        metadata = {
                            "title": lecture.get("title", "") if lecture else "",
                            "subtitle": lecture.get("subtitle", "") if lecture else "",
                            "keywords": lecture.get("keywords", []) if lecture else []
                        }
                        
                        # Get PDF summary if available
                        sources_data = st.session_state.get("sources_data", {})
                        pdf_summary = sources_data.get("full_summary", "")
                        
                        # Generate lecture summary
                        lecture_summary = generate_lecture_summary(
                            metadata=metadata,
                            pdf_summary=pdf_summary,
                            model_name=selected_model
                        )
                        
                        st.session_state["lecture_summary"] = lecture_summary
                        st.success("Резюме лекции готово!")
                    except Exception as e:
                        st.error(f"Ошибка: {str(e)}")
    
    with col5:
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
    if "brief_draft" in st.session_state:
        with st.expander("Краткий черновик лекции"):
            st.markdown(st.session_state.brief_draft)
            
            # Export brief draft to DOCX
            st.subheader("Экспорт краткого черновика")
            try:
                import tempfile
                from src.export.docx_exporter import export_lecture_to_docx
                
                lecture = course_manager.get_lecture(selected_course_id, lecture_id)
                lecture_title = lecture.get("title", "Лекция") if lecture else "Лекция"
                lecture_subtitle = lecture.get("subtitle", "") if lecture else ""
                lecture_keywords = lecture.get("keywords", []) if lecture else []
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    tmp_path = tmp.name
                
                export_lecture_to_docx(
                    title=f"{lecture_title} (Краткий вариант)",
                    subtitle=lecture_subtitle,
                    keywords=lecture_keywords,
                    lecture_text=st.session_state.brief_draft,
                    bibliography=None,
                    file_path=tmp_path
                )
                
                with open(tmp_path, "rb") as f:
                    docx_data = f.read()
                
                safe_title = "".join(c for c in lecture_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                file_name = f"{safe_title}_brief.docx" if safe_title else f"lecture_{lecture_id}_brief.docx"
                
                st.download_button(
                    label="📥 Скачать краткий черновик в .docx",
                    data=docx_data,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            except Exception as e:
                st.error(f"Ошибка при создании DOCX: {str(e)}")
    
    if "lecture_summary" in st.session_state:
        with st.expander("✨ Резюме лекции (600–800 слов)"):
            st.markdown(st.session_state.lecture_summary)
            
            # Export lecture summary to DOCX
            st.subheader("Экспорт резюме")
            try:
                import tempfile
                from src.export.docx_exporter import export_lecture_to_docx
                
                lecture = course_manager.get_lecture(selected_course_id, lecture_id)
                lecture_title = lecture.get("title", "Лекция") if lecture else "Лекция"
                lecture_subtitle = lecture.get("subtitle", "") if lecture else ""
                lecture_keywords = lecture.get("keywords", []) if lecture else []
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    tmp_path = tmp.name
                
                export_lecture_to_docx(
                    title=f"{lecture_title} (Резюме)",
                    subtitle=lecture_subtitle,
                    keywords=lecture_keywords,
                    lecture_text=st.session_state.lecture_summary,
                    bibliography=None,
                    file_path=tmp_path
                )
                
                with open(tmp_path, "rb") as f:
                    docx_data = f.read()
                
                safe_title = "".join(c for c in lecture_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                file_name = f"{safe_title}_summary.docx" if safe_title else f"lecture_{lecture_id}_summary.docx"
                
                st.download_button(
                    label="📥 Скачать резюме в .docx",
                    data=docx_data,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            except Exception as e:
                st.error(f"Ошибка при создании DOCX: {str(e)}")
    
    if "draft" in st.session_state:
        with st.expander("Черновик лекции"):
            st.markdown(st.session_state.draft)
            
            # Export draft to DOCX
            st.subheader("Экспорт черновика")
            try:
                import tempfile
                from src.export.docx_exporter import export_lecture_to_docx
                
                lecture = course_manager.get_lecture(selected_course_id, lecture_id)
                lecture_title = lecture.get("title", "Лекция") if lecture else "Лекция"
                lecture_subtitle = lecture.get("subtitle", "") if lecture else ""
                lecture_keywords = lecture.get("keywords", []) if lecture else []
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    tmp_path = tmp.name
                
                export_lecture_to_docx(
                    title=f"{lecture_title} (Черновик)",
                    subtitle=lecture_subtitle,
                    keywords=lecture_keywords,
                    lecture_text=st.session_state.draft,
                    bibliography=None,
                    file_path=tmp_path
                )
                
                with open(tmp_path, "rb") as f:
                    docx_data = f.read()
                
                safe_title = "".join(c for c in lecture_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                file_name = f"{safe_title}_draft.docx" if safe_title else f"lecture_{lecture_id}_draft.docx"
                
                st.download_button(
                    label="📥 Скачать черновик в .docx",
                    data=docx_data,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            except Exception as e:
                st.error(f"Ошибка при создании DOCX: {str(e)}")
    
    if "final" in st.session_state:
        with st.expander("Финальная лекция"):
            st.markdown(st.session_state.final)
            
            # Export to DOCX button
            st.subheader("Экспорт")
            
            # Get lecture metadata
            lecture = course_manager.get_lecture(selected_course_id, lecture_id)
            lecture_title = lecture.get("title", "Лекция") if lecture else "Лекция"
            lecture_subtitle = lecture.get("subtitle", "") if lecture else ""
            lecture_keywords = lecture.get("keywords", []) if lecture else []
            
            # Format bibliography if available
            bibliography_text = None
            if "bibliography" in st.session_state:
                bib = st.session_state.bibliography
                bib_lines = []
                
                # Core bibliography
                if bib.get("core"):
                    bib_lines.append("Основные работы (Core):")
                    for entry in bib["core"]:
                        authors = ", ".join(entry.get("authors", []))
                        year = entry.get("year", "")
                        title = entry.get("title", "")
                        bib_lines.append(f"{authors} ({year}). {title}")
                    bib_lines.append("")
                
                # Recent bibliography
                if bib.get("recent"):
                    bib_lines.append("Недавние работы (Recent):")
                    for entry in bib["recent"]:
                        authors = ", ".join(entry.get("authors", []))
                        year = entry.get("year", "")
                        title = entry.get("title", "")
                        bib_lines.append(f"{authors} ({year}). {title}")
                
                bibliography_text = "\n".join(bib_lines) if bib_lines else None
            
            # Export to DOCX
            try:
                # Create temporary file for export
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                    tmp_path = tmp.name
                
                # Export lecture to DOCX
                export_lecture_to_docx(
                    title=lecture_title,
                    subtitle=lecture_subtitle,
                    keywords=lecture_keywords,
                    lecture_text=st.session_state.final,
                    bibliography=bibliography_text,
                    file_path=tmp_path
                )
                
                # Read the file data
                with open(tmp_path, "rb") as f:
                    docx_data = f.read()
                
                # Clean filename
                safe_title = "".join(c for c in lecture_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                file_name = f"{safe_title}.docx" if safe_title else f"lecture_{lecture_id}.docx"
                
                # Create download button
                st.download_button(
                    label="📥 Скачать лекцию в .docx",
                    data=docx_data,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                    
            except Exception as e:
                st.error(f"Ошибка при создании DOCX файла: {str(e)}")
    
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

