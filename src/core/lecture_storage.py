"""
Lecture storage and deletion utilities.
"""
import json
import shutil
from pathlib import Path
from src.core.course_manager import CourseManager
from src.utils.io_utils import read_json, write_json
import config


def delete_lecture(course_id: str, lecture_id: str) -> None:
    """
    Delete lecture and all associated files.
    
    Args:
        course_id: Course identifier
        lecture_id: Lecture identifier
    """
    # Delete lecture directory in uploads
    upload_dir = config.UPLOADS_DIR / course_id / lecture_id
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    
    # Delete lecture outputs
    output_files = [
        config.OUTPUTS_DIR / course_id / f"{lecture_id}_sources.json",
        config.OUTPUTS_DIR / course_id / f"{lecture_id}_bibliography.json",
        config.OUTPUTS_DIR / course_id / f"{lecture_id}_bibliography_summary.md",
        config.OUTPUTS_DIR / course_id / f"{lecture_id}_outline.md",
        config.OUTPUTS_DIR / course_id / f"{lecture_id}_draft.md",
        config.OUTPUTS_DIR / course_id / f"{lecture_id}_final.md",
        config.OUTPUTS_DIR / course_id / f"{lecture_id}_glossary.md",
        config.OUTPUTS_DIR / course_id / f"{lecture_id}_gamma_prompt.md",
    ]
    
    for file_path in output_files:
        if file_path.exists():
            file_path.unlink()
    
    # Remove lecture from courses.json
    course_manager = CourseManager()
    courses = course_manager.list_courses()
    
    if course_id in courses:
        if "lectures" in courses[course_id]:
            if lecture_id in courses[course_id]["lectures"]:
                del courses[course_id]["lectures"][lecture_id]
                write_json(config.COURSES_JSON, courses)

