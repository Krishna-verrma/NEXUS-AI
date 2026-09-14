import os
import glob
from typing import List, Dict, Any

def search_files(directory: str = ".", pattern: str = "*.*", max_results: int = 50) -> Dict[str, Any]:
    """Search files in directory matching wildcard pattern."""
    resolved_dir = os.path.abspath(directory)
    if not os.path.exists(resolved_dir):
        return {"error": f"Directory not found: {directory}", "files": []}

    matches = []
    try:
        search_path = os.path.join(resolved_dir, "**", pattern)
        for filepath in glob.iglob(search_path, recursive=True):
            if len(matches) >= max_results:
                break
            try:
                stat = os.stat(filepath)
                matches.append({
                    "name": os.path.basename(filepath),
                    "path": filepath,
                    "sizeBytes": stat.st_size,
                    "isDir": os.path.isdir(filepath),
                    "modified": stat.st_mtime,
                })
            except (OSError, PermissionError):
                continue
        return {"directory": resolved_dir, "pattern": pattern, "count": len(matches), "files": matches}
    except Exception as e:
        return {"error": str(e), "files": []}
