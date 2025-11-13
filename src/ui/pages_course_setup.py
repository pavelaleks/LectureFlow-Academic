"""
Course Setup Page for Streamlit.
"""
import streamlit as st
from src.core.course_manager import CourseManager
from src.utils.io_utils import read_text, write_text
import config


def render_course_setup_page():
    """Render the course setup page."""
    st.title("📚 Управление курсами")
    
    course_manager = CourseManager()
    courses = course_manager.list_courses()
    
    # Sidebar for course selection
    st.sidebar.header("Курсы")
    
    course_ids = list(courses.keys())
    if not course_ids:
        st.info("Создайте первый курс, используя форму ниже.")
        new_course_mode = True
    else:
        selected_course_id = st.sidebar.selectbox(
            "Выберите курс",
            options=["-- Создать новый --"] + course_ids
        )
        new_course_mode = selected_course_id == "-- Создать новый --"
    
    # Main content area
    if new_course_mode:
        st.header("Создать новый курс")
        
        with st.form("new_course_form"):
            course_id = st.text_input("ID курса (латиница, без пробелов)", value="")
            course_title = st.text_input("Название курса", value="")
            course_description = st.text_area("Описание курса", value="", height=100)
            
            submitted = st.form_submit_button("Создать курс")
            
            if submitted:
                if not course_id or not course_title:
                    st.error("Заполните ID и название курса.")
                elif course_id in courses:
                    st.error(f"Курс с ID '{course_id}' уже существует.")
                else:
                    course_manager.save_course(
                        course_id=course_id,
                        title=course_title,
                        description=course_description
                    )
                    st.success(f"Курс '{course_title}' создан!")
                    st.rerun()
    
    else:
        # Edit existing course
        course = courses[selected_course_id]
        
        st.header(f"Редактирование: {course['title']}")
        
        # Course metadata
        with st.form("edit_course_form"):
            course_title = st.text_input("Название курса", value=course.get("title", ""))
            course_description = st.text_area(
                "Описание курса",
                value=course.get("description", ""),
                height=100
            )
            
            submitted = st.form_submit_button("Сохранить изменения")
            
            if submitted:
                course_manager.save_course(
                    course_id=selected_course_id,
                    title=course_title,
                    description=course_description
                )
                st.success("Изменения сохранены!")
                st.rerun()
        
        # Course context editor
        st.subheader("Контекст курса")
        st.info("Контекст курса используется при генерации всех лекций для обеспечения согласованности.")
        
        context_file = config.COURSE_CONTEXTS_DIR / f"{selected_course_id}_context.md"
        current_context = ""
        
        if context_file.exists():
            current_context = read_text(context_file)
        
        context_text = st.text_area(
            "Контекст курса (Markdown)",
            value=current_context,
            height=300
        )
        
        if st.button("Сохранить контекст"):
            course_manager.save_course_context(selected_course_id, context_text)
            st.success("Контекст сохранён!")
        
        # List lectures
        st.subheader("Лекции курса")
        lectures = course.get("lectures", {})
        
        if not lectures:
            st.info("В этом курсе пока нет лекций. Создайте лекции на странице 'Мастер лекций'.")
        else:
            # Sort by order
            sorted_lectures = sorted(
                lectures.items(),
                key=lambda x: x[1].get("order", 0)
            )
            
            for lecture_id, lecture_data in sorted_lectures:
                with st.expander(f"Лекция {lecture_data.get('order', 0)}: {lecture_data.get('title', 'Без названия')}"):
                    st.write(f"**Подзаголовок:** {lecture_data.get('subtitle', '—')}")
                    st.write(f"**Ключевые слова:** {', '.join(lecture_data.get('keywords', []))}")
                    st.write(f"**Целевой объём:** {lecture_data.get('target_length', 4000)} слов")

