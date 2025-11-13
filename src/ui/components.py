"""
Reusable Streamlit UI components.
"""
import streamlit as st
from typing import List, Dict, Any


def display_bibliography_table(bibliography: List[Dict], title: str = "Bibliography"):
    """Display bibliography as a table."""
    if not bibliography:
        st.info("Нет записей в библиографии.")
        return
    
    st.subheader(title)
    
    for i, entry in enumerate(bibliography, 1):
        with st.expander(f"{i}. {entry.get('title', 'Untitled')}"):
            st.write(f"**Авторы:** {', '.join(entry.get('authors', []))}")
            st.write(f"**Год:** {entry.get('year', 'Unknown')}")
            st.write(f"**Источник:** {entry.get('source', 'Unknown')}")
            if entry.get('doi'):
                st.write(f"**DOI:** {entry['doi']}")


def display_key_ideas(key_ideas: List[str]):
    """Display key ideas as a list."""
    if not key_ideas:
        return
    
    st.subheader("Ключевые идеи из загруженных источников")
    for idea in key_ideas:
        st.write(f"• {idea}")


def display_summary(summary: str, title: str = "Резюме"):
    """Display summary text."""
    st.subheader(title)
    st.markdown(summary)

