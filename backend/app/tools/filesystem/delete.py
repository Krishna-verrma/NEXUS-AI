import os
import shutil
from typing import Dict, Any

def delete_file(target_path: str) -> Dict[str, Any]:
    """Delete a file or directory. Requires user authorization in production mode."""
    target = os.path.abspath(target_path)
    if not os.path.exists(target):
        return {"success": False, "error": f"Target does not exist: {target_path}"}

    try:
        if os.path.isdir(target):
            shutil.rmtree(target)
            return {"success": True, "target": target, "type": "directory", "message": f"Directory deleted: {target_path}"}
        else:
            os.remove(target)
            return {"success": True, "target": target, "type": "file", "message": f"File deleted: {target_path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
