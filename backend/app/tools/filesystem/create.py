import os
from typing import Dict, Any

def create_file(filepath: str, content: str = "", overwrite: bool = False) -> Dict[str, Any]:
    """Create or overwrite a file safely."""
    abs_path = os.path.abspath(filepath)
    if os.path.exists(abs_path) and not overwrite:
        return {"success": False, "error": f"File already exists at: {filepath}"}

    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {
            "success": True,
            "path": abs_path,
            "bytesWritten": len(content.encode("utf-8")),
            "message": f"File created successfully at {filepath}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def read_file(filepath: str, max_chars: int = 10000) -> Dict[str, Any]:
    """Read contents of a file safely."""
    abs_path = os.path.abspath(filepath)
    if not os.path.exists(abs_path):
        return {"success": False, "error": f"File not found: {filepath}"}

    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars)
        return {
            "success": True,
            "path": abs_path,
            "content": content,
            "size": len(content),
            "truncated": len(content) == max_chars
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
