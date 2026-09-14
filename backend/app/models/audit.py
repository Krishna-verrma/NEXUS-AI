import datetime
import uuid
from sqlalchemy import Column, String, Text, DateTime
from app.database.base import Base

class SecurityAuditLogModel(Base):
    __tablename__ = "security_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(50), nullable=True)
    operation_name = Column(String(100), nullable=False)
    risk_level = Column(String(50), nullable=False)
    agent_role = Column(String(50), nullable=False)
    command_or_payload = Column(Text, nullable=False)
    decision = Column(String(50), nullable=False) # approved, rejected, auto_approved
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
