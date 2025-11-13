"""
LectureFlow Academic - Main Streamlit Application
"""
import streamlit as st

# Configure page
st.set_page_config(
    page_title="LectureFlow Academic",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("🎓 LectureFlow Academic")
st.sidebar.markdown("---")

# Initialize session state for page navigation
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "courses"

# Check if lecture editor should be opened
if "selected_lecture" in st.session_state and st.session_state.get("selected_lecture"):
    st.session_state["current_page"] = "lecture_editor"

# Navigation
if st.session_state["current_page"] == "lecture_editor":
    page_options = ["Управление курсами", "Мастер лекций", "Редактор лекции"]
    page = st.sidebar.radio(
        "Навигация",
        page_options,
        index=2,
        label_visibility="collapsed"
    )
else:
    page = st.sidebar.radio(
        "Навигация",
        ["Управление курсами", "Мастер лекций"],
        label_visibility="collapsed"
    )
    
    # Update session state based on selection
    if page == "Управление курсами":
        st.session_state["current_page"] = "courses"
    elif page == "Мастер лекций":
        st.session_state["current_page"] = "wizard"

# Main content
if st.session_state["current_page"] == "lecture_editor" or page == "Редактор лекции":
    from src.ui.pages_lecture_editor import render_lecture_editor_page
    render_lecture_editor_page()
elif page == "Управление курсами" or st.session_state["current_page"] == "courses":
    from src.ui.pages_course_setup import render_course_setup_page
    render_course_setup_page()
elif page == "Мастер лекций" or st.session_state["current_page"] == "wizard":
    from src.ui.pages_lecture_wizard import render_lecture_wizard_page
    render_lecture_wizard_page()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### О системе")
st.sidebar.info(
    "LectureFlow Academic — система генерации университетских лекций "
    "с использованием DeepSeek API и OpenAlex."
)

