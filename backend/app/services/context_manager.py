import uuid
from pathlib import Path
from typing import Any, Optional
from app.database.repository import Repository
from app.core.config import DATA_DIR

ARTIFACTS_DIR = DATA_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

class ContextManager:
    """Central context and memory manager for multi-agent execution."""

    @staticmethod
    def get_conversation_context(conversation_id: Optional[str], limit: int = 10) -> list[dict[str, Any]]:
        if not conversation_id:
            return []
        return Repository.get_messages(task_id=conversation_id, limit=limit)

    @staticmethod
    def get_task_context(task_id: str) -> Optional[dict[str, Any]]:
        return Repository.get_task(task_id)

    @staticmethod
    def get_file_context(task_id: str) -> list[dict[str, Any]]:
        return Repository.list_files(task_id=task_id) or []

    @staticmethod
    def get_artifacts(task_id: str) -> list[dict[str, Any]]:
        return Repository.list_artifacts(task_id=task_id)

    @staticmethod
    def save_artifact(
        task_id: str,
        name: str,
        content: str,
        artifact_type: str = "markdown",
        execution_id: Optional[str] = None
    ) -> dict[str, Any]:
        """Saves an artifact both to disk and to the database."""
        task_dir = ARTIFACTS_DIR / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        file_path = task_dir / name
        file_path.write_text(content, encoding="utf-8")

        artifact_id = str(uuid.uuid4())
        return Repository.create_artifact(
            artifact_id=artifact_id,
            task_id=task_id,
            execution_id=execution_id,
            name=name,
            artifact_type=artifact_type,
            content=content,
            path=str(file_path)
        )

    @staticmethod
    def build_agent_context(
        task_id: str,
        agent_id: str,
        prompt: str,
        upstream_outputs: dict[str, Any],
        step_task: Optional[str] = None,
        files: Optional[list[dict[str, Any]]] = None,
        retry_count: int = 0,
        required_changes: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """Constructs focused, non-bloated execution context for a specific agent step."""
        artifacts = Repository.list_artifacts(task_id=task_id)
        attached_files = files if files is not None else (Repository.list_files(task_id=task_id) or [])

        return {
            "task_id": task_id,
            "agent_id": agent_id,
            "prompt": prompt,
            "user_prompt": prompt,
            "step_task": step_task or prompt,
            "upstream_outputs": upstream_outputs,
            "artifacts": {a["name"]: a["content"] for a in artifacts},
            "files": attached_files,
            "retry_count": retry_count,
            "required_changes": required_changes or []
        }

context_manager = ContextManager()
