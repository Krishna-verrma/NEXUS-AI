import os
import uuid
from pathlib import Path
from typing import Any, Optional
from fastapi import UploadFile
from app.core.config import UPLOAD_DIR
from app.core.security import sanitize_filename, validate_file_extension, validate_file_size, safe_file_path
from app.database.repository import Repository

class FileService:
    @staticmethod
    async def save_uploaded_file(file: UploadFile, task_id: Optional[str] = None) -> dict[str, Any]:
        original_name = file.filename or "uploaded_file"
        clean_name = sanitize_filename(original_name)
        file_ext = validate_file_extension(clean_name)
        
        file_id = str(uuid.uuid4())
        unique_disk_name = f"{file_id}_{clean_name}"
        disk_path = safe_file_path(UPLOAD_DIR, unique_disk_name)

        content = await file.read()
        file_size = len(content)
        validate_file_size(file_size)

        with open(disk_path, "wb") as f:
            f.write(content)

        metadata: dict[str, Any] = {"extension": file_ext}
        if file_ext == "csv":
            try:
                lines = content.decode("utf-8-sig", errors="ignore").splitlines()
                metadata["line_count"] = len(lines)
                if lines:
                    metadata["columns"] = [c.strip() for c in lines[0].split(",")]
            except Exception:
                pass

        file_rec = Repository.create_file(
            file_id=file_id,
            filename=clean_name,
            original_name=original_name,
            file_type=file_ext,
            file_size=file_size,
            file_path=str(disk_path),
            task_id=task_id,
            metadata=metadata
        )
        return file_rec

    @staticmethod
    def list_files(task_id: Optional[str] = None) -> list[dict[str, Any]]:
        return Repository.list_files(task_id)

    @staticmethod
    def get_file(file_id: str) -> Optional[dict[str, Any]]:
        return Repository.get_file(file_id)

    @staticmethod
    def delete_file(file_id: str) -> bool:
        f = Repository.get_file(file_id)
        if not f:
            return False
        disk_path = Path(f["file_path"])
        if disk_path.exists():
            try:
                disk_path.unlink()
            except Exception:
                pass
        return Repository.delete_file(file_id)
