import asyncio
import uuid
import time
import logging
from typing import Any, Optional
from app.database.repository import Repository
from app.agents.orchestrator import orchestrator
from app.core.event_bus import event_bus

logger = logging.getLogger("nexus.task_service")


class TaskService:
    @staticmethod
    async def create_and_run_task(
        prompt: str,
        file_ids: list[str] = None,
        is_demo: bool = False
    ) -> dict[str, Any]:
        task_id = str(uuid.uuid4())
        title = prompt[:45] + "..." if len(prompt) > 45 else prompt
        task = Repository.create_task(
            task_id=task_id,
            title=title,
            user_prompt=prompt,
            complexity="moderate",
            is_demo=is_demo
        )

        # Link uploaded files to this task (fixed: get_file returns dict, not context manager)
        if file_ids:
            for fid in file_ids:
                try:
                    f = Repository.get_file(fid)
                    if f:
                        Repository.update_file_task(file_id=fid, task_id=task_id)
                except Exception as e:
                    logger.warning(f"Could not link file {fid} to task {task_id}: {e}")

        # Launch background execution
        asyncio.create_task(TaskService._run_task_background(task_id))
        return Repository.get_task(task_id)

    @staticmethod
    async def _run_task_background(task_id: str) -> None:
        try:
            await orchestrator.execute_task(task_id)
        except Exception as e:
            logger.error(f"Task {task_id} failed with exception: {e}", exc_info=True)
            Repository.update_task_status(task_id, status="failed", error_message=str(e))
            await event_bus.publish(task_id, {
                "type": "task_error",
                "task_id": task_id,
                "error": str(e)
            })

    @staticmethod
    def get_task(task_id: str) -> Optional[dict[str, Any]]:
        return Repository.get_task(task_id)

    @staticmethod
    def list_tasks(limit: int = 50) -> list[dict[str, Any]]:
        return Repository.list_tasks(limit)

    @staticmethod
    async def cancel_task(task_id: str) -> dict[str, Any]:
        Repository.update_task_status(task_id, status="cancelled")
        await event_bus.publish(task_id, {
            "type": "task_status",
            "task_id": task_id,
            "status": "cancelled"
        })
        return Repository.get_task(task_id)
