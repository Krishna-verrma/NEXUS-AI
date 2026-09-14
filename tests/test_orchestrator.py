import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.agents.orchestrator import NexusOrchestrator

@pytest.mark.asyncio
async def test_dynamic_workflow_coding_task():
    orchestrator = NexusOrchestrator()
    plan = await orchestrator.plan_workflow(
        prompt="Debug this C++ function and fix memory leak",
        files=[]
    )
    agent_ids = [p["agent_id"] for p in plan]
    assert "coding" in agent_ids
    assert "reviewer" in agent_ids
    # Data analyst should NOT be included for a pure coding task
    assert "data_analyst" not in agent_ids

@pytest.mark.asyncio
async def test_dynamic_workflow_document_task():
    orchestrator = NexusOrchestrator()
    plan = await orchestrator.plan_workflow(
        prompt="Summarize this legal brief and extract key clauses",
        files=[{"file_type": "pdf", "file_path": "contract.pdf"}]
    )
    agent_ids = [p["agent_id"] for p in plan]
    assert "document" in agent_ids
    assert "reviewer" in agent_ids

@pytest.mark.asyncio
async def test_dynamic_workflow_sales_and_report_task():
    orchestrator = NexusOrchestrator()
    plan = await orchestrator.plan_workflow(
        prompt="Analyze this sales dataset, research market trends, identify risks and create a report",
        files=[{"file_type": "csv", "file_path": "sales.csv"}]
    )
    agent_ids = [p["agent_id"] for p in plan]
    assert "data_analyst" in agent_ids
    assert "research" in agent_ids
    assert "risk" in agent_ids
    assert "reviewer" in agent_ids
    assert "report" in agent_ids
