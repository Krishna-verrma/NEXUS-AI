"""
Nexus AI Database Seed Script
Populates the SQLite database with initial agents, sample tasks, automations, and demonstration dialogues.
"""

import sys
import os

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database.session import init_db, SessionLocal
from app.models.task import TaskModel, TaskStepModel
from app.models.automation import AutomationModel
from app.models.chat import ChatSessionModel, ChatMessageModel

def seed():
    init_db()
    db = SessionLocal()

    # Check if already seeded
    if db.query(TaskModel).count() > 0:
        print("[Nexus Seed] Database already contains records. Skipping seed.")
        db.close()
        return

    print("[Nexus Seed] Populating initial tasks...")
    t1 = TaskModel(
        id="task-init-1",
        title="Initialize System Hardware Matrix",
        description="Verify logical cores, RAM availability, and disk storage.",
        priority="high",
        status="completed",
        progress=100,
        assigned_agent="computer_agent"
    )
    s1 = TaskStepModel(
        id="step-init-1",
        task_id="task-init-1",
        title="Read Hardware Telemetry",
        agent_role="computer_agent",
        status="completed",
        details="16 logical CPUs, 32GB RAM detected"
    )
    t1.steps.append(s1)
    db.add(t1)

    print("[Nexus Seed] Populating initial chat demonstration...")
    chat = ChatSessionModel(
        id="session-demo-1",
        title="Welcome to Nexus AI"
    )
    msg1 = ChatMessageModel(
        id="msg-demo-1",
        session_id="session-demo-1",
        sender="assistant",
        content="Welcome to **Nexus AI**, your intelligent operating layer. All 9 specialized agents are idle and awaiting your command. How can I assist you today?",
        agent_role="orchestrator",
        status="completed"
    )
    chat.messages.append(msg1)
    db.add(chat)

    db.commit()
    db.close()
    print("[Nexus Seed] Database seeding completed successfully.")

if __name__ == "__main__":
    seed()
