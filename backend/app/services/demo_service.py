import asyncio
import uuid
from pathlib import Path
from typing import Any
from app.database.repository import Repository
from app.core.config import DATA_DIR
from app.agents.orchestrator import orchestrator

class DemoService:
    DEMO_PROMPT = (
        "Analyze the attached sales dataset, identify why revenue declined, "
        "research market trends, identify business risks, and generate a strategic report."
    )

    @staticmethod
    async def start_demo_task() -> dict[str, Any]:
        """Initialize and execute the deterministic hackathon demo task."""
        demo_csv = DATA_DIR / "demo_sales.csv"
        
        task_id = str(uuid.uuid4())
        task = Repository.create_task(
            task_id=task_id,
            title="Strategic Revenue & Market Analysis (Demo)",
            user_prompt=DemoService.DEMO_PROMPT,
            complexity="complex",
            is_demo=True
        )

        # Register demo file if present
        if demo_csv.exists():
            file_id = f"demo_{task_id[:8]}"
            Repository.create_file(
                file_id=file_id,
                filename="demo_sales.csv",
                original_name="demo_sales.csv",
                file_type="csv",
                file_size=demo_csv.stat().st_size,
                file_path=str(demo_csv),
                task_id=task_id,
                metadata={"demo_dataset": True, "rows": 72}
            )

        # Plan the exact 6-agent workflow required by spec
        plan = [
            {"agent_id": "data_analyst", "agent_name": "Data Analyst", "operation": "Analyzing sales data..."},
            {"agent_id": "research", "agent_name": "Research Agent", "operation": "Researching market trends..."},
            {"agent_id": "risk", "agent_name": "Risk Agent", "operation": "Evaluating business and operational risks..."},
            {"agent_id": "reviewer", "agent_name": "Reviewer Agent", "operation": "Auditing outputs for accuracy and logical consistency..."},
            {"agent_id": "report", "agent_name": "Report Agent", "operation": "Generating strategic executive report..."}
        ]

        for idx, p in enumerate(plan):
            step_id = str(uuid.uuid4())
            Repository.create_step(
                step_id=step_id,
                task_id=task_id,
                step_order=idx + 1,
                agent_id=p["agent_id"],
                agent_name=p["agent_name"],
                operation=p["operation"],
                input_data={"prompt": DemoService.DEMO_PROMPT}
            )

        # Launch async execution
        asyncio.create_task(DemoService._run_demo_background(task_id))
        return Repository.get_task(task_id)

    @staticmethod
    async def _run_demo_background(task_id: str) -> None:
        try:
            await orchestrator.execute_task(task_id)
        except Exception as e:
            Repository.update_task_status(task_id, status="failed", error_message=str(e))

