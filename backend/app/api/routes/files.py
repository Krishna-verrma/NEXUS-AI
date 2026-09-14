from fastapi import APIRouter, Query, HTTPException
from app.tools.filesystem.search import search_files
from app.tools.filesystem.create import read_file, create_file
from app.tools.filesystem.delete import delete_file
from pydantic import BaseModel

router = APIRouter(prefix="/api/files", tags=["Files"])

class FileCreateRequest(BaseModel):
    filepath: str
    content: str
    overwrite: bool = False

@router.get("")
def list_workspace_files(dir: str = ".", pattern: str = "*.*"):
    return search_files(directory=dir, pattern=pattern, max_results=100)

@router.get("/content")
def get_file_content(path: str = Query(..., description="File path to read")):
    res = read_file(path)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("")
def create_workspace_file(payload: FileCreateRequest):
    res = create_file(payload.filepath, payload.content, payload.overwrite)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res
