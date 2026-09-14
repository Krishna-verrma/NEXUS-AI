from fastapi import APIRouter, HTTPException
from typing import List
from app.agents import AGENT_REGISTRY, get_agent
from app.schemas.agent import AgentResponse, AgentExecutionRequest

router = APIRouter(prefix="/api/agents", tags=["Agents"])

# Agent static metadata map
AGENT_META = {
    "orchestrator": {"avatar": "BrainCircuit", "color": "#00F0FF", "executions": 142},
    "computer_agent": {"avatar": "Monitor", "color": "#8B5CF6", "executions": 89},
    "file_agent": {"avatar": "FolderGit2", "color": "#3B82F6", "executions": 215},
    "web_agent": {"avatar": "Globe2", "color": "#10B981", "executions": 178},
    "coding_agent": {"avatar": "Terminal", "color": "#EC4899", "executions": 310},
    "productivity_agent": {"avatar": "CalendarCheck", "color": "#F59E0B", "executions": 94},
    "communication_agent": {"avatar": "MessageSquareShare", "color": "#14B8A6", "executions": 67},
    "data_agent": {"avatar": "BarChart3", "color": "#6366F1", "executions": 112},
    "creative_agent": {"avatar": "Sparkles", "color": "#A855F7", "executions": 83},
}

@router.get("", response_model=List[AgentResponse])
def list_agents():
    """List all specialized agents in the Nexus hive."""
    agents = []
    for role, agent_instance in AGENT_REGISTRY.items():
        meta = AGENT_META.get(role, {"avatar": "Bot", "color": "#00F0FF", "executions": 50})
        agents.append(AgentResponse(
            id=role,
            role=role,
            name=agent_instance.name,
            description=agent_instance.description,
            avatar=meta["avatar"],
            color=meta["color"],
            capabilities=agent_instance.capabilities,
            tools=agent_instance.allowed_tools,
            status="idle",
            totalExecutions=meta["executions"]
        ))
    return agents

@router.get("/{role}", response_model=AgentResponse)
def get_agent_details(role: str):
    if role not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Agent '{role}' not found")
    agent_instance = AGENT_REGISTRY[role]
    meta = AGENT_META.get(role, {"avatar": "Bot", "color": "#00F0FF", "executions": 50})
    return AgentResponse(
        id=role,
        role=role,
        name=agent_instance.name,
        description=agent_instance.description,
        avatar=meta["avatar"],
        color=meta["color"],
        capabilities=agent_instance.capabilities,
        tools=agent_instance.allowed_tools,
        status="idle",
        totalExecutions=meta["executions"]
    )

@router.post("/execute")
def execute_agent_directly(payload: AgentExecutionRequest):
    agent_instance = get_agent(payload.agent_role)
    res = agent_instance.execute(payload.prompt)
    return res.to_dict()
