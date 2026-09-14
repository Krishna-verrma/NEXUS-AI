import time
import uuid
import logging
from typing import Any, Callable, Awaitable, Optional
from app.agents.base import BaseAgent, AgentResult
from app.agents.planner_agent import PlannerAgent
from app.agents.research_agent import ResearchAgent
from app.agents.coding_agent import CodingAgent
from app.agents.data_agent import DataAgent
from app.agents.testing_agent import TestingAgent
from app.agents.security_agent import SecurityAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.report_agent import ReportAgent
from app.agents.schedule import ScheduleAgent
from app.agents.document import DocumentAgent

from app.database.repository import Repository
from app.core.event_bus import event_bus
from app.services.context_manager import context_manager

logger = logging.getLogger("nexus.orchestrator")

class NexusOrchestrator(BaseAgent):
    """
    Central Intelligence Command Center.
    Orchestrates dynamic DAG planning, tool allocation, agent execution,
    state tracking, automated error recovery, and quality gate auditing.
    """
    def __init__(self):
        super().__init__(
            agent_id="orchestrator",
            name="Nexus Orchestrator",
            role="Central Intelligence"
        )
        self.planner = PlannerAgent()

        # Canonical single instances per agent type
        _data = DataAgent(agent_id="data_analyst")
        _research = ResearchAgent(agent_id="research")
        _coding = CodingAgent()
        _coding.agent_id = "coding"
        _testing = TestingAgent()
        _testing.agent_id = "testing"
        _security = SecurityAgent(agent_id="risk")
        _reviewer = ReviewerAgent(agent_id="reviewer")
        _report = ReportAgent(agent_id="report")
        _document = DocumentAgent()
        _document.agent_id = "document"
        _schedule = ScheduleAgent()
        _schedule.agent_id = "schedule"

        self.specialized_agents: dict[str, BaseAgent] = {
            # Planner
            "planner": self.planner,
            "planner_agent": self.planner,
            # Data
            "data_analyst": _data,
            "data_agent": _data,
            "data": _data,
            # Research
            "research": _research,
            "research_agent": _research,
            # Coding
            "coding": _coding,
            "coding_agent": _coding,
            "code": _coding,
            # Testing
            "testing": _testing,
            "testing_agent": _testing,
            # Security / Risk
            "security_agent": _security,
            "security": _security,
            "risk": _security,
            # Reviewer
            "reviewer": _reviewer,
            "reviewer_agent": _reviewer,
            # Report
            "report": _report,
            "report_agent": _report,
            # Extras
            "document": _document,
            "document_agent": _document,
            "schedule": _schedule,
            "schedule_agent": _schedule,
        }

    CANONICAL_AGENT_ID_MAP = {
        "coding_agent": "coding",
        "coding": "coding",
        "code": "coding",
        "data_agent": "data_analyst",
        "data_analyst": "data_analyst",
        "data": "data_analyst",
        "research_agent": "research",
        "research": "research",
        "security_agent": "risk",
        "security": "risk",
        "risk": "risk",
        "reviewer_agent": "reviewer",
        "reviewer": "reviewer",
        "report_agent": "report",
        "report": "report",
        "document_agent": "document",
        "document": "document",
        "schedule_agent": "schedule",
        "schedule": "schedule",
        "testing_agent": "testing",
        "testing": "testing",
        "planner_agent": "planner",
        "planner": "planner",
    }

    async def plan_workflow(self, prompt: str, files: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Dynamically determine task complexity and construct the agent execution pipeline.
        Always delegates to PlannerAgent first (LLM-driven), with deterministic fallback.
        """
        files = files or []
        dag = await self.planner.plan_dag(user_goal=prompt, files=files)
        dag_steps = dag.get("steps", [])

        plan = []
        for idx, s in enumerate(dag_steps):
            raw_agent_id = s.get("agent", "research")
            target_id = self.CANONICAL_AGENT_ID_MAP.get(raw_agent_id, raw_agent_id)
            agent_inst = self._resolve_agent(target_id)
            final_id = agent_inst.agent_id if agent_inst else target_id
            plan.append({
                "agent_id": final_id,
                "agent_name": agent_inst.name if agent_inst else final_id.replace("_", " ").title(),
                "operation": s.get("task", f"Executing {final_id}"),
                "step_order": idx + 1,
                "depends_on": s.get("dependsOn", [])
            })

        return plan

    def _resolve_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Resolve agent_id to a real agent instance with fuzzy fallback."""
        if agent_id in self.specialized_agents:
            return self.specialized_agents[agent_id]
        # Fuzzy matching
        lower = agent_id.lower()
        if "coding" in lower or "code" in lower:
            return self.specialized_agents["coding_agent"]
        if "test" in lower:
            return self.specialized_agents["testing_agent"]
        if "data" in lower:
            return self.specialized_agents["data_agent"]
        if "sec" in lower or "risk" in lower or "vuln" in lower:
            return self.specialized_agents["security_agent"]
        if "rev" in lower:
            return self.specialized_agents["reviewer_agent"]
        if "rep" in lower:
            return self.specialized_agents["report_agent"]
        if "doc" in lower:
            return self.specialized_agents["document"]
        if "sched" in lower or "cal" in lower:
            return self.specialized_agents["schedule"]
        # Default: research
        return self.specialized_agents["research_agent"]

    async def execute_task(
        self,
        task_id: str,
        on_step_update: Optional[Callable[[str, dict[str, Any]], Awaitable[None]]] = None
    ) -> dict[str, Any]:
        """Execute the planned multi-agent workflow with state transitions, reviewer loops, and event emission."""
        task = Repository.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        prompt = task["user_prompt"]
        files = Repository.list_files(task_id=task_id) or []
        start_overall = time.time()

        # Update task status to running
        Repository.update_task_status(task_id, status="running")
        await event_bus.publish(task_id, {
            "type": "task_status",
            "task_id": task_id,
            "status": "running",
            "message": "Understanding task requirements and constructing execution DAG..."
        })

        # Generate execution steps if not already created
        steps = task.get("steps", [])
        if not steps:
            plan = await self.plan_workflow(prompt, files)
            for p in plan:
                step_id = str(uuid.uuid4())
                Repository.create_step(
                    step_id=step_id,
                    task_id=task_id,
                    step_order=p["step_order"],
                    agent_id=p["agent_id"],
                    agent_name=p["agent_name"],
                    operation=p["operation"],
                    input_data={"prompt": prompt, "depends_on": p.get("depends_on", [])}
                )
            task = Repository.get_task(task_id)
            steps = task.get("steps", [])

        await event_bus.publish(task_id, {
            "type": "workflow_planned",
            "task_id": task_id,
            "steps": steps,
            "message": f"Dynamic execution DAG initialized with {len(steps)} specialized agent steps."
        })

        # Execute agents, respecting DAG dependencies
        upstream_outputs: dict[str, Any] = {}
        report_output: Optional[dict[str, Any]] = None

        # Build an ordered execution list respecting step_order
        ordered_steps = sorted(steps, key=lambda s: s.get("step_order", 0))

        for step in ordered_steps:
            step_id = step["id"]
            agent_id = step["agent_id"]
            agent = self._resolve_agent(agent_id)

            if not agent:
                logger.warning(f"No agent resolved for agent_id='{agent_id}', skipping step {step_id}")
                Repository.update_step_status(step_id, status="skipped", operation="Agent not found")
                await event_bus.publish(task_id, {
                    "type": "step_status",
                    "task_id": task_id,
                    "step_id": step_id,
                    "agent_id": agent_id,
                    "status": "skipped",
                    "operation": "Agent not resolved — step skipped."
                })
                continue

            # Execute with retry loop (max 3 attempts per step)
            max_retries = 3
            retry_count = step.get("retry_count", 0)

            while retry_count <= max_retries:
                # Update step status to running
                Repository.update_step_status(step_id, status="running", operation=f"Running {agent.name}...")
                await event_bus.publish(task_id, {
                    "type": "step_status",
                    "task_id": task_id,
                    "step_id": step_id,
                    "agent_id": agent.agent_id,
                    "status": "running",
                    "operation": f"Running {agent.name}..." + (f" (retry {retry_count}/{max_retries})" if retry_count > 0 else "")
                })

                # Build agent execution context
                context = context_manager.build_agent_context(
                    task_id=task_id,
                    agent_id=agent.agent_id,
                    prompt=prompt,
                    upstream_outputs=upstream_outputs,
                    step_task=step.get("operation") or prompt,
                    files=files,
                    retry_count=retry_count
                )

                # Execute agent
                res: AgentResult = await agent.run(context)

                # Quality Gate: Reviewer Agent — if not approved and retries remain, re-run failing agent
                if agent.agent_id in ("reviewer", "reviewer_agent") and not res.output.get("approved", True):
                    if retry_count < max_retries:
                        # Find and re-run the preceding non-reviewer agent
                        issues = res.output.get("issues", [])
                        required_changes = res.output.get("required_changes", [])

                        Repository.update_step_status(
                            step_id,
                            status="needs_review",
                            operation=f"Reviewer requested revision cycle {retry_count + 1}/{max_retries}",
                            output_data=res.output,
                            retry_count=retry_count + 1
                        )
                        await event_bus.publish(task_id, {
                            "type": "step_status",
                            "task_id": task_id,
                            "step_id": step_id,
                            "agent_id": agent.agent_id,
                            "status": "needs_review",
                            "operation": f"Revision required: {'; '.join(issues[:2]) if issues else 'Quality check failed'}",
                            "retry_count": retry_count + 1
                        })

                        # Re-run the last non-reviewer agent from upstream_outputs
                        # Find the most recently completed non-reviewer agent
                        last_non_reviewer_id = None
                        for s in reversed(ordered_steps):
                            if s["id"] == step_id:
                                continue
                            s_agent_id = s["agent_id"]
                            if s_agent_id not in ("reviewer", "reviewer_agent"):
                                last_non_reviewer_id = s_agent_id
                                break

                        if last_non_reviewer_id:
                            prev_agent = self._resolve_agent(last_non_reviewer_id)
                            if prev_agent:
                                logger.info(f"Re-running {prev_agent.name} due to reviewer rejection (cycle {retry_count + 1})")
                                retry_ctx = context_manager.build_agent_context(
                                    task_id=task_id,
                                    agent_id=prev_agent.agent_id,
                                    prompt=prompt,
                                    upstream_outputs=upstream_outputs,
                                    step_task=step.get("operation") or prompt,
                                    files=files,
                                    retry_count=retry_count + 1,
                                    required_changes=required_changes
                                )
                                prev_res = await prev_agent.run(retry_ctx)
                                upstream_outputs[prev_agent.agent_id] = prev_res.output

                        retry_count += 1
                        continue  # Re-run reviewer with updated upstream
                    else:
                        # Max retries exhausted — approve with warning
                        logger.warning(f"Reviewer max retries ({max_retries}) exhausted for task {task_id}. Proceeding with best effort.")

                # Step completed (or reviewer approved, or max retries hit)
                final_status = "completed" if res.success else "failed"
                Repository.update_step_status(
                    step_id,
                    status=final_status,
                    operation="Completed" if res.success else f"Failed: {res.error}",
                    output_data=res.output,
                    duration_seconds=res.duration_seconds,
                    error_message=res.error
                )
                await event_bus.publish(task_id, {
                    "type": "step_status",
                    "task_id": task_id,
                    "step_id": step_id,
                    "agent_id": agent.agent_id,
                    "status": final_status,
                    "operation": "Completed" if res.success else f"Failed: {res.error}",
                    "duration_seconds": res.duration_seconds,
                    "preview": res.preview,
                    "output": res.output
                })

                upstream_outputs[agent.agent_id] = res.output

                # Track report output for final summary
                if agent.agent_id in ("report", "report_agent"):
                    report_output = res.output

                break  # Exit retry loop — step done

        # Final Result Formulation — purely from real agent outputs, no hardcoded strings
        overall_duration = round(time.time() - start_overall, 2)
        final_summary = self._formulate_final_result(prompt, upstream_outputs, report_output)

        Repository.update_task_status(
            task_id=task_id,
            status="completed",
            final_result=final_summary,
            duration_seconds=overall_duration
        )

        await event_bus.publish(task_id, {
            "type": "task_completed",
            "task_id": task_id,
            "status": "completed",
            "final_result": final_summary,
            "duration_seconds": overall_duration,
            "report_id": (
                report_output.get("report_id") or report_output.get("id")
                if report_output else None
            )
        })

        return Repository.get_task(task_id)

    def _formulate_final_result(
        self,
        prompt: str,
        upstream: dict[str, Any],
        report_output: Optional[dict[str, Any]]
    ) -> str:
        """
        Compose clean final summary from REAL agent outputs only.
        No hardcoded answers. Every line of this output is derived from
        what agents actually returned.
        """
        parts = []

        # 1. If report_output was produced — use it as primary summary
        if report_output and isinstance(report_output, dict):
            title = report_output.get("title") or report_output.get("executive_summary", "")[:60]
            exec_sum = report_output.get("executive_summary", "")
            if title:
                parts.append(f"### {title}\n")
            if exec_sum:
                parts.append(exec_sum)

            findings = report_output.get("key_findings", [])
            if findings:
                parts.append("\n**Key Findings:**")
                for f in findings[:6]:
                    parts.append(f"- {f}")

            recs = report_output.get("recommendations", [])
            if recs:
                parts.append("\n**Strategic Recommendations:**")
                for i, r in enumerate(recs[:5]):
                    parts.append(f"{i+1}. {r}")

            return "\n".join(parts)

        # 2. Research Agent output (no report)
        res_out = upstream.get("research_agent") or upstream.get("research")
        if res_out and isinstance(res_out, dict):
            topic = res_out.get("topic", "Research Findings")
            exec_sum = res_out.get("executive_summary", "")
            parts.append(f"### {topic}\n")
            if exec_sum:
                parts.append(exec_sum)

            facts = res_out.get("verified_facts", [])
            if facts:
                parts.append("\n**Key Facts:**")
                for f in facts[:5]:
                    if isinstance(f, dict):
                        src = f.get("source_url") or f.get("source", "")
                        fact_text = f.get("fact", "")
                        parts.append(f"- {fact_text}" + (f" *(Source: {src})*" if src else ""))
                    else:
                        parts.append(f"- {f}")

            assumptions = res_out.get("strategic_assumptions", [])
            if assumptions:
                parts.append("\n**Key Considerations:**")
                for a in assumptions[:3]:
                    val = a.get("assumption") if isinstance(a, dict) else str(a)
                    parts.append(f"- {val}")

            return "\n".join(parts)

        # 3. Coding Agent output (no report)
        code_out = upstream.get("coding_agent") or upstream.get("coding")
        if code_out and isinstance(code_out, dict):
            lang = code_out.get("language", "Code")
            explanation = code_out.get("explanation", "")
            parts.append(f"### Solution ({lang})\n")
            if explanation:
                parts.append(explanation)

            code = code_out.get("code", "")
            if code:
                parts.append(f"\n```{lang.lower()}\n{code}\n```")

            opts = code_out.get("optimizations", [])
            if opts:
                parts.append("\n**Design Choices:**")
                for o in opts:
                    parts.append(f"- {o}")

            inspected = code_out.get("files_inspected", [])
            modified = code_out.get("files_modified", [])
            if inspected:
                parts.append(f"\n**Files Inspected:** {', '.join(inspected[:5])}")
            if modified:
                parts.append(f"**Files Modified:** {', '.join(modified[:5])}")

            return "\n".join(parts)

        # 4. Testing Agent output (no report)
        test_out = upstream.get("testing_agent") or upstream.get("testing")
        if test_out and isinstance(test_out, dict):
            suite = test_out.get("suite", "tests")
            status = test_out.get("status", "UNKNOWN")
            run = test_out.get("tests_run", 0)
            passed = test_out.get("passed", 0)
            failed = test_out.get("failed", 0)
            stdout = test_out.get("stdout", "")

            parts.append(f"### Test Results — {status}\n")
            parts.append(f"- **Suite:** `{suite}`")
            parts.append(f"- **Tests Run:** {run}")
            parts.append(f"- **Passed:** {passed} ✅")
            if failed > 0:
                parts.append(f"- **Failed:** {failed} ❌")
            if stdout:
                parts.append(f"\n**Output:**\n```\n{stdout[:1000]}\n```")

            return "\n".join(parts)

        # 5. Data Agent output (no report)
        data_out = upstream.get("data_agent") or upstream.get("data_analyst")
        if data_out and isinstance(data_out, dict):
            summary = data_out.get("summary", "")
            parts.append("### Quantitative Data Analysis\n")
            if summary:
                parts.append(summary)

            stats = data_out.get("statistics", {})
            if stats and isinstance(stats, dict):
                parts.append("\n**Computed Statistics:**")
                for metric, s in stats.items():
                    if isinstance(s, dict):
                        parts.append(
                            f"- **{metric}**: Total={s.get('total', s.get('sum', 0))}, "
                            f"Mean={s.get('mean', 0)}, Min={s.get('min', 0)}, Max={s.get('max', 0)}"
                        )
                    else:
                        parts.append(f"- **{metric}**: {s}")

            insights = data_out.get("key_insights", [])
            if insights:
                parts.append("\n**Key Metrics & Observations:**")
                for ins in insights:
                    parts.append(f"- {ins}")

            anomalies = data_out.get("anomalies", [])
            if anomalies:
                parts.append(f"\n**Anomalies Detected:** {len(anomalies)}")
                for a in anomalies[:3]:
                    parts.append(f"- Row {a.get('row')}: `{a.get('column')}` = {a.get('value')} (z={a.get('z_score')})")

            return "\n".join(parts)

        # 6. Security Agent output (no report)
        sec_out = upstream.get("security_agent") or upstream.get("risk")
        if sec_out and isinstance(sec_out, dict):
            level = sec_out.get("overall_risk_level", "Unknown")
            summary = sec_out.get("risk_summary", "")
            parts.append(f"### Security Audit — Risk Level: {level}\n")
            if summary:
                parts.append(summary)

            risks = sec_out.get("risks", [])
            if risks:
                parts.append("\n**Risk Findings:**")
                for r in risks[:5]:
                    parts.append(f"- **{r.get('title')}** ({r.get('severity')} severity): {r.get('impact', '')}")

            return "\n".join(parts)

        # 7. Schedule Agent output
        sc_out = upstream.get("schedule")
        if sc_out and isinstance(sc_out, dict):
            parts.append(f"### Daily Schedule — {sc_out.get('date', 'Today')}\n")
            if sc_out.get("summary"):
                parts.append(sc_out["summary"])

            meetings = sc_out.get("today_meetings", [])
            if meetings:
                parts.append("\n**Today's Meetings:**")
                for m in meetings:
                    t = m.get("start_time", "").split(" ")[-1]
                    parts.append(f"- **{t}** — {m.get('title')} *({m.get('location', 'Online')})*")

            return "\n".join(parts)

        # 8. Reviewer only (no preceding agent produced output)
        rev_out = upstream.get("reviewer_agent") or upstream.get("reviewer")
        if rev_out and isinstance(rev_out, dict):
            eval_sum = rev_out.get("evaluation_summary", "Quality audit completed.")
            parts.append(f"### Quality Review\n{eval_sum}")
            checks = rev_out.get("audit_checks", [])
            if checks:
                parts.append("\n**Audit Checks:**")
                for c in checks:
                    icon = "✅" if c.get("passed") else "❌"
                    parts.append(f"- {icon} **{c.get('check')}**: {c.get('notes', '')}")
            return "\n".join(parts)

        # 9. Fallback — no meaningful output was captured
        parts.append("### Task Completed\nAll agent steps executed. No specific output to display.")
        return "\n".join(parts)

orchestrator = NexusOrchestrator()
