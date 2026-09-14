import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.agents.data_analyst import DataAnalystAgent
from app.agents.research import ResearchAgent
from app.agents.coding import CodingAgent
from app.agents.document import DocumentAgent
from app.agents.risk import RiskAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.report import ReportAgent
from app.core.config import DATA_DIR

@pytest.mark.asyncio
async def test_data_analyst_agent_with_demo_csv():
    agent = DataAnalystAgent()
    demo_csv = DATA_DIR / "demo_sales.csv"
    assert demo_csv.exists()

    context = {
        "prompt": "Analyze sales dataset and identify why revenue declined",
        "files": [{"file_path": str(demo_csv)}]
    }
    result = await agent.run(context)
    assert result.success is True
    assert result.agent_id == "data_analyst"
    assert "statistics" in result.output
    assert "Revenue" in result.output["statistics"]
    assert result.output["statistics"]["Revenue"]["total"] > 0
    assert "trend_timeline" in result.output
    assert len(result.output["trend_timeline"]) >= 10
    assert "anomalies" in result.output

@pytest.mark.asyncio
async def test_research_agent():
    agent = ResearchAgent()
    context = {"prompt": "Research enterprise cloud software market trends 2025"}
    result = await agent.run(context)
    assert result.success is True
    assert result.agent_id == "research"
    assert "verified_facts" in result.output
    assert "strategic_assumptions" in result.output
    assert len(result.output["verified_facts"]) > 0

@pytest.mark.asyncio
async def test_coding_agent_safety():
    agent = CodingAgent()
    context = {"prompt": "Write an optimized SQL query for sales aggregations"}
    result = await agent.run(context)
    assert result.success is True
    assert result.agent_id == "coding"
    assert "code" in result.output
    # Ensure safe review model
    assert result.metrics.get("requires_permission_to_run") is True

@pytest.mark.asyncio
async def test_risk_agent():
    agent = RiskAgent()
    context = {"prompt": "Evaluate business and technical risks of customer churn"}
    result = await agent.run(context)
    assert result.success is True
    assert result.agent_id == "risk"
    assert "risks" in result.output
    assert len(result.output["risks"]) >= 3
    # Check severity, probability, mitigation schema
    for r in result.output["risks"]:
        assert "severity" in r
        assert "probability" in r
        assert "mitigation" in r

@pytest.mark.asyncio
async def test_reviewer_agent():
    agent = ReviewerAgent()
    context = {
        "prompt": "Audit sales analysis",
        "upstream_outputs": {
            "data_analyst": {"summary": "Calculated $1.2M decline"},
            "research": {"verified_facts": ["Market contracted 28%"]}
        }
    }
    result = await agent.run(context)
    assert result.success is True
    assert result.agent_id == "reviewer"
    assert "approved" in result.output
    assert "confidence" in result.output

@pytest.mark.asyncio
async def test_report_agent():
    import uuid
    from app.database.repository import Repository
    tid = str(uuid.uuid4())
    Repository.create_task(tid, "Test Title", "Prompt", "moderate", False)
    agent = ReportAgent()
    context = {
        "prompt": "Strategic sales turnaround proposal",
        "task_id": tid,
        "upstream_outputs": {
            "data_analyst": {"summary": "Sales analysis"},
            "research": {"sources": ["Gartner"]},
            "risk": {"risks": [{"title": "Churn", "severity": "High", "mitigation": "SWAT"}]}
        }
    }
    result = await agent.run(context)
    assert result.success is True
    assert result.agent_id == "report"
    assert "executive_summary" in result.output
    assert "full_markdown" in result.output
    assert "report_id" in result.output
