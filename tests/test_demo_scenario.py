import pytest
import sys
import asyncio
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.demo_service import DemoService
from app.database.repository import Repository

@pytest.mark.asyncio
async def test_demo_scenario_full_pipeline():
    task = await DemoService.start_demo_task()
    task_id = task["id"]
    assert task["is_demo"] is True
    assert len(task["steps"]) == 5

    # Wait for completion (simulated execution takes ~1 second)
    for _ in range(30):
        await asyncio.sleep(0.2)
        current = Repository.get_task(task_id)
        if current["status"] in ("completed", "failed"):
            break

    final_task = Repository.get_task(task_id)
    assert final_task["status"] == "completed"
    assert final_task["final_result"] is not None
    assert len(final_task["final_result"]) > 100

    # Verify all steps completed successfully
    for step in final_task["steps"]:
        assert step["status"] == "completed"
        assert step["output_data"] is not None

    # Verify report was generated in database
    reports = Repository.list_reports()
    assert len(reports) > 0
    demo_report = next((r for r in reports if r.get("task_id") == task_id), None)
    assert demo_report is not None
    assert len(demo_report["key_findings"]) > 0
    assert len(demo_report["recommendations"]) > 0
