import json
import logging
import time
from typing import Any, Optional
from app.agents.base import BaseAgent, AgentResult
from app.core.ai_client import ai_client
from app.tools import tool_registry

logger = logging.getLogger("nexus.agents.planner")

class PlannerAgent(BaseAgent):
    """
    Autonomous planning agent that evaluates user goals, file context, and available tools
    to construct a dynamic, optimal Directed Acyclic Graph (DAG) for multi-agent execution.
    """
    def __init__(self):
        super().__init__(
            agent_id="planner_agent",
            name="Planner Agent",
            role="Strategic Architect & DAG Planner"
        )
        self.capabilities = [
            "Goal Decomposition",
            "Dynamic DAG Planning",
            "Tool & Agent Allocation",
            "Dependency Graph Resolution",
            "Context Optimization"
        ]
        self.allowed_tools = ["filesystem:list_directory", "filesystem:read_file"]
        self.input_schema = {
            "user_goal": "string (the user's objective)",
            "available_files": "list of dict",
            "available_tools": "list of str",
            "conversation": "list of messages",
            "project_context": "dict"
        }
        self.output_schema = {
            "goal": "string",
            "strategy": "string",
            "steps": "list of { id: str, agent: str, task: str, dependsOn: list of str }"
        }
        self.execution_state = "idle"
        self.system_prompt = (
            "You are the NEXUS AI Master Planner Agent.\n"
            "Your responsibility is to analyze the user's goal, available workspace files, and tool capabilities, "
            "then decompose the problem into an optimal Directed Acyclic Graph (DAG) of specialized agent steps.\n"
            "Available Agents: research_agent, coding_agent, data_agent, testing_agent, security_agent, reviewer_agent, report_agent, schedule.\n"
            "CRITICAL RULES:\n"
            "1. NEVER use a rigid default five-agent pipeline. Adapt precisely to the task needs.\n"
            "2. Every step must have a unique 'id', a specialized 'agent', a clear 'task', and 'dependsOn' array.\n"
            "3. Always conclude workflows with reviewer_agent to verify quality and correctness.\n"
            "Format your output as valid JSON:\n"
            "{\n"
            "  \"goal\": \"...\",\n"
            "  \"strategy\": \"...\",\n"
            "  \"steps\": [\n"
            "    {\"id\": \"step1\", \"agent\": \"...\", \"task\": \"...\", \"dependsOn\": []}\n"
            "  ]\n"
            "}"
        )

    async def plan_dag(
        self,
        user_goal: str,
        files: Optional[list[dict[str, Any]]] = None,
        conversation: Optional[list[dict[str, Any]]] = None
    ) -> dict[str, Any]:
        """Construct dynamic execution DAG."""
        self.execution_state = "planning"
        start_time = time.time()
        files = files or []

        # Check if live LLM is configured
        if ai_client.is_configured():
            try:
                prompt_text = (
                    f"User Goal: {user_goal}\n"
                    f"Attached Files: {[f.get('filename') for f in files]}\n"
                    f"Available Tools: {[t['name'] for t in tool_registry.list_tools()]}\n"
                )
                msgs = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt_text}
                ]
                resp = await ai_client.complete(messages=msgs, response_format_json=True)
                parsed = json.loads(resp)
                if "steps" in parsed and isinstance(parsed["steps"], list) and len(parsed["steps"]) > 0:
                    self.execution_state = "completed"
                    return parsed
            except Exception as e:
                logger.warning(f"Live LLM planning failed, using deterministic planner: {e}")

        # Deterministic / Offline Dynamic Planner
        dag = self._deterministic_dag_planner(user_goal, files)
        self.execution_state = "completed"
        return dag

    def _deterministic_dag_planner(self, goal: str, files: list[dict[str, Any]]) -> dict[str, Any]:
        lower = goal.lower().strip()

        file_types = [f.get("file_type", "").lower() for f in files] + [
            f.get("filename", "").split(".")[-1].lower() for f in files if "." in f.get("filename", "")
        ]
        has_csv = any(ext in ("csv", "xlsx", "xls") for ext in file_types)
        has_code = any(ext in ("py", "cpp", "js", "ts", "java", "sql", "cs") for ext in file_types)
        has_doc = any(ext in ("pdf", "doc", "docx", "txt", "md") for ext in file_types)

        # 1. Document / Legal brief task
        if has_doc or any(k in lower for k in ["legal brief", "contract", "clauses", "summarize this legal", "summarize document", "summarize this pdf"]):
            steps = [
                {
                    "id": "step1",
                    "agent": "document",
                    "task": "Extract and parse document text, structure, and clauses",
                    "dependsOn": []
                },
                {
                    "id": "step2",
                    "agent": "reviewer",
                    "task": "Audit document summary accuracy and clause interpretation",
                    "dependsOn": ["step1"]
                }
            ]
            return {
                "goal": goal,
                "strategy": "Autonomous Document & Clause Analysis",
                "steps": steps
            }

        # 2. Coding, Debugging & Algorithm tasks
        if any(k in lower for k in [
            "debug", "c++", "cpp", "binary search", "memory leak", "fix the bug",
            "fix a bug", "write a binary", "code", "algorithm", "write python",
            "write a python", "function and fix"
        ]):
            steps = [
                {
                    "id": "step1",
                    "agent": "coding",
                    "task": "Analyze code/problem, design algorithmic solution or apply necessary fixes",
                    "dependsOn": []
                },
                {
                    "id": "step2",
                    "agent": "reviewer",
                    "task": "Audit code correctness, algorithm complexity, edge cases, and safety",
                    "dependsOn": ["step1"]
                }
            ]
            return {
                "goal": goal,
                "strategy": "Polyglot Software Engineering & Quality Review",
                "steps": steps
            }

        # 3. Calendar & Schedule queries
        if any(k in lower for k in ["meeting", "meetings", "schedule", "work today", "calendar"]):
            steps = [
                {
                    "id": "step1",
                    "agent": "schedule",
                    "task": "Inspect connected calendar feeds, today's schedule, and upcoming meetings",
                    "dependsOn": []
                },
                {
                    "id": "step2",
                    "agent": "reviewer",
                    "task": "Audit schedule briefing and confirm link and time validity",
                    "dependsOn": ["step1"]
                }
            ]
            return {
                "goal": goal,
                "strategy": "Calendar Synchronization & Daily Briefing",
                "steps": steps
            }

        # 4. Multi-agent Sales Analysis & Report Task (5 agents)
        if any(k in lower for k in ["research market trends", "identify risks and create a report", "market trends, identify risks"]) or (
            has_csv and any(k in lower for k in ["report", "research", "risk"])
        ):
            steps = [
                {
                    "id": "step1",
                    "agent": "data_analyst",
                    "task": "Parse tabular dataset, compute descriptive statistics, and identify anomalies",
                    "dependsOn": []
                },
                {
                    "id": "step2",
                    "agent": "research",
                    "task": "Research market trends and external industry benchmarks",
                    "dependsOn": ["step1"]
                },
                {
                    "id": "step3",
                    "agent": "risk",
                    "task": "Evaluate business, technical, and operational risks",
                    "dependsOn": ["step1", "step2"]
                },
                {
                    "id": "step4",
                    "agent": "reviewer",
                    "task": "Audit computed mathematical figures, facts, and consistency",
                    "dependsOn": ["step1", "step2", "step3"]
                },
                {
                    "id": "step5",
                    "agent": "report",
                    "task": "Synthesize executive findings, charts, and recommendations into final report",
                    "dependsOn": ["step4"]
                }
            ]
            return {
                "goal": goal,
                "strategy": "Quantitative Data Analysis, Research & Strategic Reporting",
                "steps": steps
            }

        # 5. General Tabular Data Analysis
        if has_csv or any(k in lower for k in ["analyze this csv", "analyze csv", "dataset", "statistics", "sales data", "server metrics"]):
            steps = [
                {
                    "id": "step1",
                    "agent": "data_analyst",
                    "task": "Parse tabular dataset, compute descriptive statistics, and identify anomalies",
                    "dependsOn": []
                },
                {
                    "id": "step2",
                    "agent": "risk",
                    "task": "Verify data integrity, compliance flags, and metric bounds",
                    "dependsOn": ["step1"]
                },
                {
                    "id": "step3",
                    "agent": "reviewer",
                    "task": "Audit computed mathematical figures and consistency against raw rows",
                    "dependsOn": ["step1", "step2"]
                },
                {
                    "id": "step4",
                    "agent": "report",
                    "task": "Synthesize executive findings, charts, and recommendations into final report",
                    "dependsOn": ["step3"]
                }
            ]
            return {
                "goal": goal,
                "strategy": "Quantitative Data Analysis & Quality Audit",
                "steps": steps
            }

        # 6. Self-Development Demo / General Project Inspection
        if any(k in lower for k in [
            "inspect your own project", "inspect project and identify",
            "identify three improvements", "three improvements",
            "inspect the project", "inspect the codebase", "inspect my",
            "inspect your", "analyze the codebase", "analyze the project",
            "review the codebase", "review the project"
        ]):
            steps = [
                {
                    "id": "step1",
                    "agent": "coding",
                    "task": "Inspect repository files, package dependencies, and system architecture",
                    "dependsOn": []
                },
                {
                    "id": "step2",
                    "agent": "risk",
                    "task": "Audit codebase for security configurations, secret exposure, and input sanitization",
                    "dependsOn": ["step1"]
                },
                {
                    "id": "step3",
                    "agent": "reviewer",
                    "task": "Prioritize and evaluate identified architectural and security improvements",
                    "dependsOn": ["step1", "step2"]
                },
                {
                    "id": "step4",
                    "agent": "report",
                    "task": "Generate comprehensive project improvement roadmap and actionable plan",
                    "dependsOn": ["step3"]
                }
            ]
            return {
                "goal": goal,
                "strategy": "Autonomous Repository & Architecture Improvement Inspection",
                "steps": steps
            }

        # 7. Pure Test Execution
        if any(k in lower for k in [
            "run the tests", "run test", "run tests", "execute tests",
            "pytest", "unit test", "run the test suite", "run all tests"
        ]):
            steps = [
                {
                    "id": "step1",
                    "agent": "testing",
                    "task": "Execute automated test suites across backend and report test execution metrics",
                    "dependsOn": []
                },
                {
                    "id": "step2",
                    "agent": "reviewer",
                    "task": "Validate test pass rates, failure traces, and execution timings",
                    "dependsOn": ["step1"]
                }
            ]
            return {
                "goal": goal,
                "strategy": "Automated Test Verification",
                "steps": steps
            }

        # 8. Research / Explanation Task: "Explain Docker", "Give me 3 startup ideas", etc.
        steps = [
            {
                "id": "step1",
                "agent": "research",
                "task": "Investigate topic, search verified sources, and extract empirical facts",
                "dependsOn": []
            },
            {
                "id": "step2",
                "agent": "reviewer",
                "task": "Cross-examine facts, verify source credibility, and check for hallucinations",
                "dependsOn": ["step1"]
            }
        ]
        return {
            "goal": goal,
            "strategy": "Verified Research & Synthesis",
            "steps": steps
        }

    async def run(self, context: dict[str, Any]) -> AgentResult:
        start_time = time.time()
        goal = context.get("prompt") or context.get("user_prompt", "")
        files = context.get("files", [])
        dag = await self.plan_dag(goal, files)
        duration = round(time.time() - start_time, 2)
        step_count = len(dag.get("steps", []))
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            success=True,
            output=dag,
            preview=self.format_preview(f"Constructed DAG with {step_count} steps: {dag.get('strategy', 'Planned execution')}"),
            confidence=0.99,
            metrics={"step_count": step_count, "strategy": dag.get("strategy")},
            duration_seconds=duration
        )
