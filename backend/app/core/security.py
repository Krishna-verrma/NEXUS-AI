import os
import re
from pathlib import Path
from fastapi import HTTPException
from app.core.config import settings

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal or shell attacks."""
    clean = os.path.basename(filename)
    # Remove any dangerous characters, keep alphanumerics, dots, hyphens, underscores
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean)
    if not clean or clean.startswith('.'):
        clean = f"file_{clean.lstrip('.')}"
    return clean

def validate_file_extension(filename: str) -> str:
    """Validate that the file extension is permitted."""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Allowed: {', '.join(settings.allowed_extensions)}"
        )
    return ext

def validate_file_size(size_bytes: int) -> None:
    """Ensure file does not exceed maximum permissible size."""
    if size_bytes > settings.max_file_size_bytes:
        max_mb = settings.max_file_size_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {max_mb} MB"
        )

def safe_file_path(base_dir: Path, filename: str) -> Path:
    """Ensure the resolved path stays within base_dir."""
    clean_name = sanitize_filename(filename)
    target = (base_dir / clean_name).resolve()
    base = base_dir.resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path detected.")
    return target

def mask_api_key(key: str | None) -> str:
    """Return a masked representation of an API key for safe UI display."""
    if not key:
        return ""
    if len(key) <= 8:
        return "********"
    return f"{key[:3]}...{key[-4:]}"
