import pytest
from app.agents import AGENT_REGISTRY, orchestrator, get_agent

def test_all_agents_registered():
    expected_roles = [
        "orchestrator",
        "computer_agent",
        "file_agent",
        "web_agent",
        "coding_agent",
        "productivity_agent",
        "communication_agent",
        "data_agent",
        "creative_agent"
    ]
    for role in expected_roles:
        assert role in AGENT_REGISTRY, f"Missing agent: {role}"
        agent = get_agent(role)
        assert agent.name is not None
        assert len(agent.capabilities) > 0

def test_orchestrator_execution():
    result = orchestrator.execute("Show me CPU and system status")
    assert result.status == "completed"
    assert len(result.activity_traces) > 0
    assert result.agent_role == "orchestrator"
    assert "Windows" in result.response or "system" in result.response.lower()

def test_file_agent_security_gate():
    result = orchestrator.execute("Please delete old_cache.tmp from filesystem")
    # File deletion should trigger human-in-the-loop security ticket!
    assert result.security_ticket is not None
    assert result.security_ticket["operationName"] == "delete_file"
    assert result.security_ticket["riskLevel"] in ["high", "critical"]
