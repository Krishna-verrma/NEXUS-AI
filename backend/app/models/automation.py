import datetime
import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean
from app.database.base import Base

class AutomationModel(Base):
    __tablename__ = "automations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    trigger_type = Column(String(50), default="cron") # cron, event, interval
    trigger_schedule = Column(String(100), nullable=False) # e.g. "0 9 * * *" or "10m"
    enabled = Column(Boolean, default=True)
    target_agent = Column(String(50), default="orchestrator")
    action_prompt = Column(Text, nullable=False)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
