from fastapi import APIRouter, HTTPException
from app.models.schemas import ReportResponse, ReportRenameRequest
from app.database.repository import Repository

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("", response_model=list[ReportResponse])
def list_reports(limit: int = 50):
    return Repository.list_reports(limit)

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: str):
    rep = Repository.get_report(report_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found")
    return rep

@router.put("/{report_id}", response_model=ReportResponse)
def rename_report(report_id: str, req: ReportRenameRequest):
    updated = Repository.update_report_title(report_id, req.title)
    if not updated:
        raise HTTPException(status_code=404, detail="Report not found")
    return updated

@router.delete("/{report_id}")
def delete_report(report_id: str):
    deleted = Repository.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted successfully", "id": report_id}
