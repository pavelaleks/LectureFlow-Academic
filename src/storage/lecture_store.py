"""
Lecture storage utilities for loading and saving complete lecture data.
"""
from pathlib import Path
from typing import Dict, Optional, Any
from src.core.course_manager import CourseManager
from src.utils.io_utils import read_json, write_json, read_text
import config


def load_full_lecture_data(course_id: str, lecture_id: str) -> Dict[str, Any]:
    """
    Load complete lecture data from both courses.json and output files.
    
    Args:
        course_id: Course identifier
        lecture_id: Lecture identifier
    
    Returns:
        Dictionary with all lecture data
    """
    course_manager = CourseManager()
    
    # Get metadata from courses.json
    lecture_metadata = course_manager.get_lecture(course_id, lecture_id)
    
    if not lecture_metadata:
        raise ValueError(f"Lecture {lecture_id} not found in course {course_id}")
    
    # Initialize lecture data with metadata
    lecture_data = {
        "course_id": course_id,
        "lecture_id": lecture_id,
        "title": lecture_metadata.get("title", ""),
        "subtitle": lecture_metadata.get("subtitle", ""),
        "keywords": lecture_metadata.get("keywords", []),
        "target_length": lecture_metadata.get("target_length", 4000),
        "order": lecture_metadata.get("order", 0),
        "metadata": lecture_metadata.get("metadata", {}),
        "draft": "",
        "final": "",
        "outline": "",
        "glossary": "",
        "bibliography": None,
        "bibliography_summary": "",
        "sources_summary": "",
        "sources_key_ideas": []
    }
    
    # Load text files from outputs directory
    output_dir = config.OUTPUTS_DIR / course_id
    
    # Load draft
    draft_file = output_dir / f"{lecture_id}_draft.md"
    if draft_file.exists():
        lecture_data["draft"] = read_text(draft_file)
    
    # Load final
    final_file = output_dir / f"{lecture_id}_final.md"
    if final_file.exists():
        lecture_data["final"] = read_text(final_file)
    
    # Load outline
    outline_file = output_dir / f"{lecture_id}_outline.md"
    if outline_file.exists():
        lecture_data["outline"] = read_text(outline_file)
    
    # Load glossary
    glossary_file = output_dir / f"{lecture_id}_glossary.md"
    if glossary_file.exists():
        lecture_data["glossary"] = read_text(glossary_file)
    
    # Load bibliography summary
    bib_summary_file = output_dir / f"{lecture_id}_bibliography_summary.md"
    if bib_summary_file.exists():
        lecture_data["bibliography_summary"] = read_text(bib_summary_file)
    
    # Load bibliography JSON
    bib_file = output_dir / f"{lecture_id}_bibliography.json"
    if bib_file.exists():
        lecture_data["bibliography"] = read_json(bib_file)
    
    # Load sources data
    sources_file = config.UPLOADS_DIR / course_id / lecture_id / "sources.json"
    if sources_file.exists():
        sources_data = read_json(sources_file)
        lecture_data["sources_summary"] = sources_data.get("full_summary", "")
        lecture_data["sources_key_ideas"] = sources_data.get("key_ideas", [])
    
    return lecture_data


def save_lecture_data(lecture_data: Dict[str, Any]) -> None:
    """
    Save complete lecture data to both courses.json and output files.
    
    Args:
        lecture_data: Complete lecture data dictionary
    """
    course_id = lecture_data["course_id"]
    lecture_id = lecture_data["lecture_id"]
    
    course_manager = CourseManager()
    
    # Save metadata to courses.json
    course_manager.add_or_update_lecture(
        course_id=course_id,
        lecture_id=lecture_id,
        title=lecture_data.get("title", ""),
        subtitle=lecture_data.get("subtitle", ""),
        order=lecture_data.get("order", 0),
        keywords=lecture_data.get("keywords", []),
        target_length=lecture_data.get("target_length", 4000),
        metadata=lecture_data.get("metadata", {})
    )
    
    # Save text files to outputs directory
    output_dir = config.OUTPUTS_DIR / course_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    from src.utils.io_utils import write_text
    
    # Save draft
    if lecture_data.get("draft"):
        write_text(output_dir / f"{lecture_id}_draft.md", lecture_data["draft"])
    
    # Save final
    if lecture_data.get("final"):
        write_text(output_dir / f"{lecture_id}_final.md", lecture_data["final"])
    
    # Save outline
    if lecture_data.get("outline"):
        write_text(output_dir / f"{lecture_id}_outline.md", lecture_data["outline"])
    
    # Save glossary
    if lecture_data.get("glossary"):
        write_text(output_dir / f"{lecture_id}_glossary.md", lecture_data["glossary"])


def list_all_lectures() -> list[tuple[str, str, Dict]]:
    """
    List all lectures from all courses.
    
    Returns:
        List of tuples (course_id, lecture_id, lecture_data)
    """
    course_manager = CourseManager()
    courses = course_manager.list_courses()
    
    all_lectures = []
    for course_id, course_data in courses.items():
        lectures = course_data.get("lectures", {})
        for lecture_id, lecture_data in lectures.items():
            all_lectures.append((course_id, lecture_id, lecture_data))
    
    return all_lectures




