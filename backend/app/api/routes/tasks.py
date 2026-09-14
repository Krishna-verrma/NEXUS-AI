import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies.db import get_db
from app.models.task import TaskModel, TaskStepModel
from app.schemas.task import TaskItemResponse, TaskCreateRequest

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

# Seed some default tasks if database is empty
def ensure_seed_tasks(db: Session):
    if db.query(TaskModel).count() == 0:
        t1 = TaskModel(
            id="task-1",
            title="Index Local Project Documentation",
            description="Autonomous scanning of markdown and documentation files to build embedding index.",
            priority="high",
            status="completed",
            progress=100,
            assigned_agent="file_agent",
            completed_at=datetime.datetime.utcnow()
        )
        s1 = TaskStepModel(
            id="step-1",
            task_id="task-1",
            title="Discover Workspace Files",
            agent_role="file_agent",
            status="completed",
            details="Identified 42 files across 6 folders"
        )
        t1.steps.append(s1)
        db.add(t1)

        t2 = TaskModel(
            id="task-2",
            title="Desktop Resource Optimization",
            description="Analyze background processes and suggest memory reclamation strategies.",
            priority="medium",
            status="in_progress",
            progress=65,
            assigned_agent="computer_agent"
        )
        s2 = TaskStepModel(
            id="step-2",
            task_id="task-2",
            title="Capture Hardware Diagnostics",
            agent_role="computer_agent",
            status="completed",
            details="CPU at 14.5%, RAM at 42%"
        )
        s3 = TaskStepModel(
            id="step-3",
            task_id="task-2",
            title="Scan Memory Hotspots",
            agent_role="computer_agent",
            status="running"
        )
        t2.steps.extend([s2, s3])
        db.add(t2)

        t3 = TaskModel(
            id="task-3",
            title="Generate Weekly Architecture Digest",
            description="Summarize git commits and agent activity into executive memo.",
            priority="low",
            status="queued",
            progress=0,
            assigned_agent="creative_agent"
        )
        db.add(t3)
        db.commit()

@router.get("", response_model=list[TaskItemResponse])
def get_tasks(db: Session = Depends(get_db)):
    ensure_seed_tasks(db)
    tasks = db.query(TaskModel).order_by(TaskModel.created_at.desc()).all()
    out = []
    for t in tasks:
        steps_out = []
        for s in t.steps:
            steps_out.append({
                "id": s.id,
                "title": s.title,
                "agentRole": s.agent_role,
                "status": s.status,
                "details": s.details,
                "toolUsed": s.tool_used,
                "startedAt": s.started_at.isoformat() if s.started_at else None,
                "completedAt": s.completed_at.isoformat() if s.completed_at else None,
            })
        out.append(TaskItemResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            priority=t.priority,
            status=t.status,
            progress=t.progress,
            assignedAgent=t.assigned_agent,
            steps=steps_out,
            createdAt=t.created_at.isoformat() if t.created_at else "",
            updatedAt=t.updated_at.isoformat() if t.updated_at else "",
            completedAt=t.completed_at.isoformat() if t.completed_at else None
        ))
    return out

@router.post("", response_model=TaskItemResponse)
def create_task(payload: TaskCreateRequest, db: Session = Depends(get_db)):
    task_id = f"task-{uuid.uuid4().hex[:6]}"
    new_task = TaskModel(
        id=task_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status="queued",
        progress=0,
        assigned_agent=payload.assigned_agent or "orchestrator"
    )
    # Add initial plan step
    step_id = f"step-{uuid.uuid4().hex[:6]}"
    init_step = TaskStepModel(
        id=step_id,
        task_id=task_id,
        title="Initialize Task Plan",
        agent_role=new_task.assigned_agent,
        status="pending"
    )
    new_task.steps.append(init_step)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return TaskItemResponse(
        id=new_task.id,
        title=new_task.title,
        description=new_task.description,
        priority=new_task.priority,
        status=new_task.status,
        progress=new_task.progress,
        assignedAgent=new_task.assigned_agent,
        steps=[{
            "id": init_step.id,
            "title": init_step.title,
            "agentRole": init_step.agent_role,
            "status": init_step.status
        }],
        createdAt=new_task.created_at.isoformat(),
        updatedAt=new_task.updated_at.isoformat()
    )

@router.post("/{task_id}/cancel")
def cancel_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "cancelled"
    db.commit()
    return {"success": True, "message": f"Task {task_id} cancelled"}
