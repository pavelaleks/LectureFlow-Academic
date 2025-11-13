"""
Configuration module for LectureFlow Academic.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# DeepSeek Configuration
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# OpenAlex Configuration
OPENALEX_BASE_URL = "https://api.openalex.org"
OPENALEX_EMAIL = os.environ.get("OPENALEX_EMAIL", "")

# Root paths
PROJECT_ROOT = Path(__file__).parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
COURSES_JSON = DATA_DIR / "courses.json"
COURSE_CONTEXTS_DIR = DATA_DIR / "course_contexts"

# Ensure directories exist
for directory in [DATA_DIR, UPLOADS_DIR, OUTPUTS_DIR, COURSE_CONTEXTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Initialize courses.json if it doesn't exist
if not COURSES_JSON.exists():
    import json
    with open(COURSES_JSON, 'w', encoding='utf-8') as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

