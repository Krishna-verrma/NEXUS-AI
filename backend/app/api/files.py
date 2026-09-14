from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from app.models.schemas import FileResponse
from app.services.file_service import FileService

router = APIRouter(prefix="/api/files", tags=["files"])

@router.post("/upload", response_model=FileResponse)
async def upload_file(file: UploadFile = File(...), task_id: Optional[str] = Form(None)):
    saved = await FileService.save_uploaded_file(file=file, task_id=task_id)
    return saved

@router.get("", response_model=list[FileResponse])
def list_files(task_id: Optional[str] = None):
    return FileService.list_files(task_id=task_id)

@router.get("/{file_id}", response_model=FileResponse)
def get_file(file_id: str):
    f = FileService.get_file(file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    return f

@router.delete("/{file_id}")
def delete_file(file_id: str):
    deleted = FileService.delete_file(file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="File not found")
    return {"message": "File deleted successfully", "id": file_id}
