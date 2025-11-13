"""
Course and lecture management.
"""
from pathlib import Path
from typing import Dict, List, Optional
from src.utils.io_utils import read_json, write_json, read_text, write_text
import config
import json


class CourseManager:
    """Manages courses and lectures."""
    
    def __init__(self):
        """Initialize course manager."""
        self.courses_file = config.COURSES_JSON
        self.contexts_dir = config.COURSE_CONTEXTS_DIR
        self._ensure_courses_file()
    
    def _ensure_courses_file(self):
        """Ensure courses.json exists."""
        if not self.courses_file.exists():
            write_json(self.courses_file, {})
    
    def list_courses(self) -> Dict[str, Dict]:
        """
        List all courses.
        
        Returns:
            Dictionary of course_id -> course_data
        """
        return read_json(self.courses_file)
    
    def get_course(self, course_id: str) -> Optional[Dict]:
        """
        Get course by ID.
        
        Args:
            course_id: Course identifier
        
        Returns:
            Course data dictionary or None
        """
        courses = self.list_courses()
        return courses.get(course_id)
    
    def save_course(
        self,
        course_id: str,
        title: str,
        description: str = "",
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Save or update course.
        
        Args:
            course_id: Course identifier
            title: Course title
            description: Course description
            metadata: Additional metadata
        """
        courses = self.list_courses()
        
        if course_id not in courses:
            courses[course_id] = {
                "title": title,
                "description": description,
                "lectures": {},
                "metadata": metadata or {}
            }
        else:
            courses[course_id]["title"] = title
            courses[course_id]["description"] = description
            if metadata:
                courses[course_id]["metadata"].update(metadata)
        
        write_json(self.courses_file, courses)
    
    def add_or_update_lecture(
        self,
        course_id: str,
        lecture_id: str,
        title: str,
        subtitle: str = "",
        order: int = 0,
        keywords: List[str] = None,
        target_length: int = 4000,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add or update lecture.
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier
            title: Lecture title
            subtitle: Lecture subtitle
            order: Lecture order in course
            keywords: List of keywords
            target_length: Target word count
            metadata: Additional metadata
        """
        courses = self.list_courses()
        
        if course_id not in courses:
            raise ValueError(f"Course {course_id} does not exist")
        
        if "lectures" not in courses[course_id]:
            courses[course_id]["lectures"] = {}
        
        if lecture_id not in courses[course_id]["lectures"]:
            courses[course_id]["lectures"][lecture_id] = {
                "title": title,
                "subtitle": subtitle,
                "order": order,
                "keywords": keywords or [],
                "target_length": target_length,
                "metadata": metadata or {}
            }
        else:
            lecture = courses[course_id]["lectures"][lecture_id]
            lecture["title"] = title
            lecture["subtitle"] = subtitle
            lecture["order"] = order
            lecture["keywords"] = keywords or []
            lecture["target_length"] = target_length
            if metadata:
                lecture["metadata"].update(metadata)
        
        write_json(self.courses_file, courses)
    
    def get_previous_lectures_summary(
        self,
        course_id: str,
        lecture_order: int
    ) -> str:
        """
        Get summary of previous lectures in course.
        
        Args:
            course_id: Course identifier
            lecture_order: Current lecture order
        
        Returns:
            Summary text of previous lectures
        """
        courses = self.list_courses()
        course = courses.get(course_id)
        
        if not course:
            return "Нет предыдущих лекций."
        
        lectures = course.get("lectures", {})
        previous_lectures = [
            (lid, lect) for lid, lect in lectures.items()
            if lect.get("order", 0) < lecture_order
        ]
        
        if not previous_lectures:
            return "Это первая лекция курса."
        
        # Sort by order
        previous_lectures.sort(key=lambda x: x[1].get("order", 0))
        
        summary_parts = []
        for lid, lect in previous_lectures:
            title = lect.get("title", "Без названия")
            order = lect.get("order", 0)
            summary_parts.append(f"Лекция {order}: {title}")
        
        return "\n".join(summary_parts)
    
    def get_course_context_text(self, course_id: str) -> str:
        """
        Get course context text from markdown file.
        
        Args:
            course_id: Course identifier
        
        Returns:
            Course context text or empty string
        """
        context_file = self.contexts_dir / f"{course_id}_context.md"
        
        if context_file.exists():
            return read_text(context_file)
        
        return ""
    
    def save_course_context(self, course_id: str, context_text: str) -> None:
        """
        Save course context to markdown file.
        
        Args:
            course_id: Course identifier
            context_text: Context text to save
        """
        context_file = self.contexts_dir / f"{course_id}_context.md"
        write_text(context_file, context_text)
    
    def get_lecture(self, course_id: str, lecture_id: str) -> Optional[Dict]:
        """
        Get lecture by ID.
        
        Args:
            course_id: Course identifier
            lecture_id: Lecture identifier
        
        Returns:
            Lecture data dictionary or None
        """
        courses = self.list_courses()
        course = courses.get(course_id)
        
        if not course:
            return None
        
        return course.get("lectures", {}).get(lecture_id)

