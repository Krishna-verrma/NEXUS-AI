import datetime
import uuid
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(50), default="medium") # low, medium, high, critical
    status = Column(String(50), default="queued") # queued, in_progress, completed, failed, cancelled
    progress = Column(Integer, default=0)
    assigned_agent = Column(String(50), default="orchestrator")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    steps = relationship("TaskStepModel", back_populates="task", cascade="all, delete-orphan", order_by="TaskStepModel.created_at")

class TaskStepModel(Base):
    __tablename__ = "task_steps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    title = Column(String(255), nullable=False)
    agent_role = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")
    details = Column(Text, nullable=True)
    tool_used = Column(String(100), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    task = relationship("TaskModel", back_populates="steps")
