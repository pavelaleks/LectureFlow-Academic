"""
I/O utilities for reading and writing files.
"""
import json
from pathlib import Path
from typing import Any, Dict, List


def read_text(file_path: str | Path) -> str:
    """Read text file with UTF-8 encoding."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_text(file_path: str | Path, content: str) -> None:
    """Write text file with UTF-8 encoding."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def read_json(file_path: str | Path) -> Dict[str, Any] | List[Any]:
    """Read JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(file_path: str | Path, data: Dict[str, Any] | List[Any]) -> None:
    """Write JSON file with proper formatting."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

