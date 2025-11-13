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

page = st.sidebar.radio(
    "Навигация",
    ["Управление курсами", "Мастер лекций"],
    label_visibility="collapsed"
)

# Main content
if page == "Управление курсами":
    from src.ui.pages_course_setup import render_course_setup_page
    render_course_setup_page()
elif page == "Мастер лекций":
    from src.ui.pages_lecture_wizard import render_lecture_wizard_page
    render_lecture_wizard_page()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### О системе")
st.sidebar.info(
    "LectureFlow Academic — система генерации университетских лекций "
    "с использованием DeepSeek API и OpenAlex."
)

