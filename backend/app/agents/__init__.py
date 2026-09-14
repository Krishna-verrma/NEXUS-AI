from app.agents.base import BaseAgent, AgentResult
from app.agents.orchestrator.agent import OrchestratorAgent
from app.agents.computer_agent.agent import ComputerAgent
from app.agents.file_agent.agent import FileAgent
from app.agents.web_agent.agent import WebAgent
from app.agents.coding_agent.agent import CodingAgent
from app.agents.productivity_agent.agent import ProductivityAgent
from app.agents.communication_agent.agent import CommunicationAgent
from app.agents.data_agent.agent import DataAgent
from app.agents.creative_agent.agent import CreativeAgent

# Shared singleton orchestrator
orchestrator = OrchestratorAgent()

AGENT_REGISTRY = {
    "orchestrator": orchestrator,
    **orchestrator.sub_agents
}

def get_agent(role: str) -> BaseAgent:
    return AGENT_REGISTRY.get(role, orchestrator)
