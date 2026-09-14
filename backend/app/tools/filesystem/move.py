import os
import shutil
from typing import Dict, Any

def move_file(source_path: str, destination_path: str) -> Dict[str, Any]:
    """Move or rename a file or directory."""
    src = os.path.abspath(source_path)
    dst = os.path.abspath(destination_path)

    if not os.path.exists(src):
        return {"success": False, "error": f"Source file does not exist: {source_path}"}

    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        return {"success": True, "source": src, "destination": dst, "message": f"Successfully moved to {destination_path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
