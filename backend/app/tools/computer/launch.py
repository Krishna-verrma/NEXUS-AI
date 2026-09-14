import subprocess
import shutil
from typing import Dict, Any

# Map of friendly names to Windows applications
APP_MAP = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "explorer": "explorer.exe",
    "files": "explorer.exe",
    "chrome": "chrome.exe",
    "edge": "msedge.exe",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "vscode": "code.cmd",
    "code": "code.cmd"
}

def launch_app(app_name: str) -> Dict[str, Any]:
    """Launch a desktop application by name or path."""
    app_key = app_name.strip().lower()
    executable = APP_MAP.get(app_key, app_name)

    try:
        # Check if executable exists or can be found in PATH
        path_check = shutil.which(executable) or shutil.which(f"{executable}.exe")
        target = path_check if path_check else executable
        
        # Start detached process so it doesn't block backend
        subprocess.Popen(target, shell=True)
        return {
            "success": True,
            "application": app_name,
            "executable": executable,
            "message": f"Successfully launched {app_name}"
        }
    except Exception as e:
        return {
            "success": False,
            "application": app_name,
            "error": str(e),
            "message": f"Simulated launch for {app_name} in demo environment"
        }
