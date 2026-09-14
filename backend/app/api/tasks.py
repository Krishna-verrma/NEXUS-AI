from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from app.models.schemas import TaskCreateRequest, TaskResponse, TaskListItem
from app.services.task_service import TaskService
from app.services.demo_service import DemoService
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.post("", response_model=TaskResponse)
async def create_task(req: TaskCreateRequest):
    if req.is_demo:
        task = await DemoService.start_demo_task()
    else:
        task = await TaskService.create_and_run_task(
            prompt=req.prompt,
            file_ids=req.file_ids,
            is_demo=False
        )
    return task

@router.post("/demo", response_model=TaskResponse)
async def start_demo_task():
    task = await DemoService.start_demo_task()
    return task

@router.get("", response_model=list[TaskListItem])
def list_tasks(limit: int = 50):
    return TaskService.list_tasks(limit)

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    task = TaskService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/{task_id}/status")
def get_task_status(task_id: str):
    task = TaskService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task["id"],
        "status": task["status"],
        "duration_seconds": task.get("duration_seconds", 0),
        "steps_total": len(task.get("steps", [])),
        "steps_completed": sum(1 for s in task.get("steps", []) if s["status"] == "completed")
    }

@router.post("/{task_id}/run", response_model=TaskResponse)
async def run_task(task_id: str, background_tasks: BackgroundTasks):
    task = TaskService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    background_tasks.add_task(orchestrator.execute_task, task_id)
    return task

@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(task_id: str):
    task = await TaskService.cancel_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
