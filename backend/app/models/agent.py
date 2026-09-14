import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer
from app.database.base import Base

class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String(50), primary_key=True)
    role = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    avatar = Column(String(100), default="BrainCircuit")
    color = Column(String(50), default="#00F0FF")
    capabilities = Column(Text, nullable=False) # JSON list
    tools = Column(Text, nullable=False) # JSON list
    status = Column(String(50), default="idle")
    total_executions = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class AgentExecutionLogModel(Base):
    __tablename__ = "agent_execution_logs"

    id = Column(String(36), primary_key=True)
    agent_role = Column(String(50), nullable=False)
    task_id = Column(String(36), nullable=True)
    action = Column(String(255), nullable=False)
    status = Column(String(50), default="completed")
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
