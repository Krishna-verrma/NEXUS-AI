from typing import Dict, Any, Optional, Callable, List
from app.agents.base import BaseAgent, AgentResult
from app.agents.orchestrator.planner import plan_workflow

# Specialized agents
from app.agents.computer_agent.agent import ComputerAgent
from app.agents.file_agent.agent import FileAgent
from app.agents.web_agent.agent import WebAgent
from app.agents.coding_agent.agent import CodingAgent
from app.agents.productivity_agent.agent import ProductivityAgent
from app.agents.communication_agent.agent import CommunicationAgent
from app.agents.data_agent.agent import DataAgent
from app.agents.creative_agent.agent import CreativeAgent

class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="orchestrator",
            name="Nexus Orchestrator",
            description="Central brain. Plans workflows, delegates to specialized agents, and synthesizes results.",
            capabilities=["Intent Classification", "Multi-Agent Planning", "Tool Synthesis", "Self-Correction"],
            allowed_tools=["planner", "delegator", "synthesizer"]
        )
        # Register specialized agent registry
        self.sub_agents: Dict[str, BaseAgent] = {
            "computer_agent": ComputerAgent(),
            "file_agent": FileAgent(),
            "web_agent": WebAgent(),
            "coding_agent": CodingAgent(),
            "productivity_agent": ProductivityAgent(),
            "communication_agent": CommunicationAgent(),
            "data_agent": DataAgent(),
            "creative_agent": CreativeAgent(),
        }

    def execute(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> AgentResult:
        traces: List[Dict[str, Any]] = []
        target_agent = context.get("target_agent") if context else None

        # Step 1: Orchestrator Intent & Planning Trace
        traces.append(self.emit_trace(
            action="Deconstructing User Intent",
            detail=f"Analyzing prompt: '{prompt}'",
            status="started",
            callback=callback
        ))

        plan = plan_workflow(prompt, target_agent=target_agent)
        primary_agent_role = plan["primaryAgent"]

        traces.append(self.emit_trace(
            action=f"Orchestration Plan Formulated: Assigning to {primary_agent_role}",
            detail=f"Classified intent: '{plan['intent']}'. Decomposed into {len(plan['steps'])} operational step(s).",
            status="step",
            callback=callback
        ))

        # Check if delegated sub-agent exists
        sub_agent = self.sub_agents.get(primary_agent_role)
        if not sub_agent:
            sub_agent = self.sub_agents["creative_agent"]

        # Step 2: Execute Delegated Sub-Agent
        sub_result = sub_agent.execute(prompt, context=context, callback=callback)

        # Merge traces
        traces.extend(sub_result.activity_traces)

        # Step 3: Synthesis
        traces.append(self.emit_trace(
            action="Synthesizing Agent Outputs",
            detail=f"Compiled telemetry from {sub_agent.name}",
            status="finished",
            callback=callback
        ))

        return AgentResult(
            agent_role=self.role,
            response=sub_result.response,
            status=sub_result.status,
            activity_traces=traces,
            security_ticket=sub_result.security_ticket,
            data=sub_result.data
        )
