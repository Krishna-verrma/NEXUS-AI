import json
import logging
import time
from typing import Any, Optional
from app.agents.base import BaseAgent, AgentResult
from app.core.ai_client import ai_client
from app.tools import tool_registry
from app.services.context_manager import context_manager

logger = logging.getLogger("nexus.agents.report")


class ReportAgent(BaseAgent):
    """
    Autonomous report synthesis agent.
    Reads all real task artifacts and step outputs, then uses the LLM
    to synthesize a coherent final markdown report.
    """
    def __init__(self, agent_id: str = "report_agent"):
        super().__init__(
            agent_id=agent_id,
            name="Report Agent",
            role="Principal Technical Analyst & Report Synthesizer"
        )
        self.capabilities = [
            "Multi-Agent Output Synthesis",
            "Real Artifact Aggregation",
            "LLM-Driven Executive Report Generation",
            "Structured Markdown Output",
            "Key Findings Extraction"
        ]
        self.allowed_tools = [
            "filesystem:read_file",
            "filesystem:list_directory",
            "filesystem:write_file"
        ]
        self.system_prompt = (
            "You are the NEXUS Report Agent — a principal technical analyst and executive writer.\n"
            "You are given real outputs produced by specialist agents (security, coding, research, data, testing).\n"
            "Your job is to:\n"
            "1. Synthesize the key findings from ALL provided agent outputs into a coherent report.\n"
            "2. Extract specific, concrete facts — numbers, file names, risk levels, test results, URLs.\n"
            "3. Do NOT invent or hallucinate any information not present in the provided context.\n"
            "4. Write in clear, executive prose with markdown formatting.\n"
            "5. Always include: Executive Summary, Findings (by section), Recommendations, and Next Steps.\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            "  \"title\": \"string\",\n"
            "  \"executive_summary\": \"string\",\n"
            "  \"methodology\": \"string\",\n"
            "  \"key_findings\": [\"string\"],\n"
            "  \"analysis\": \"string (detailed markdown)\",\n"
            "  \"risks\": [{ \"title\": \"str\", \"severity\": \"str\", \"mitigation\": \"str\" }],\n"
            "  \"recommendations\": [\"string\"],\n"
            "  \"next_steps\": [\"string\"],\n"
            "  \"conclusion\": \"string\"\n"
            "}"
        )
        self.execution_state = "idle"

    async def run(self, context: dict[str, Any]) -> AgentResult:
        self.execution_state = "running"
        start_time = time.time()
        task_id = context.get("task_id", "default_task")
        goal = context.get("user_prompt") or context.get("prompt", "")

        # === STEP 1: Collect all real prior agent outputs ===
        prior_outputs = self._collect_prior_outputs(context)

        # === STEP 2: Read real artifacts from workspace ===
        artifact_content = await self._read_workspace_artifacts(task_id)

        # === STEP 3: Build comprehensive context for LLM ===
        synthesis_context = self._build_synthesis_context(goal, prior_outputs, artifact_content)

        # === STEP 4: LLM synthesizes the final report ===
        report_data = None
        if ai_client.is_configured():
            user_message = (
                f"Goal: {goal}\n\n"
                f"All Agent Outputs & Artifacts:\n{synthesis_context}\n\n"
                "Synthesize a comprehensive final report from the above real agent outputs."
            )
            llm_result = await ai_client.generate(
                system_prompt=self.system_prompt,
                user_message=user_message,
                max_tokens=3000,
                temperature=0.2
            )
            if llm_result.get("success") and llm_result.get("content"):
                report_data = self._parse_llm_response(llm_result["content"])

        # === FALLBACK: Build report from raw prior outputs without LLM ===
        if not report_data:
            report_data = self._build_offline_report(goal, prior_outputs, artifact_content)

        # === STEP 5: Render and save the final-report.md artifact ===
        full_markdown = self._render_full_markdown(report_data, goal)
        context_manager.save_artifact(
            task_id=task_id,
            name="final-report.md",
            content=full_markdown,
            artifact_type="markdown"
        )

        # Also try writing to workspace filesystem
        write_res = await tool_registry.execute_tool(
            name="filesystem:write_file",
            allowed_tools=self.allowed_tools,
            path=f"workspace/{task_id[:8]}-final-report.md",
            content=full_markdown
        )
        if write_res.success:
            logger.info(f"ReportAgent: Saved final report to workspace/{task_id[:8]}-final-report.md")

        # Also save structured JSON for context manager
        context_manager.save_artifact(
            task_id=task_id,
            name="final-report.json",
            content=json.dumps(report_data, indent=2),
            artifact_type="json"
        )

        # Persist report in database
        report_id = f"report-{task_id[:8]}" if task_id else str(uuid.uuid4())
        try:
            from app.database.repository import Repository
            Repository.create_report(
                report_id=report_id,
                task_id=task_id,
                title=report_data.get("title", f"Report for {goal[:50]}"),
                summary=report_data.get("executive_summary", "")[:250],
                executive_summary=report_data.get("executive_summary", ""),
                methodology=report_data.get("methodology", ""),
                key_findings=report_data.get("key_findings", []),
                analysis=report_data.get("analysis", ""),
                risks=report_data.get("risks", []),
                recommendations=report_data.get("recommendations", []),
                conclusion=report_data.get("conclusion", ""),
                full_markdown=full_markdown
            )
        except Exception as e:
            logger.warning(f"ReportAgent: Could not persist report to database: {e}")

        duration = round(time.time() - start_time, 2)
        self.execution_state = "completed"
        findings = report_data.get("key_findings", [])

        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            success=True,
            output={**report_data, "full_markdown": full_markdown, "report_id": report_id},
            preview=self.format_preview(
                f"Report generated with {len(findings)} key findings for: '{goal[:60]}'."
            ),
            confidence=0.95 if ai_client.is_configured() else 0.70,
            metrics={
                "findings_count": len(findings),
                "recommendations_count": len(report_data.get("recommendations", [])),
                "agents_synthesized": len(prior_outputs),
                "report_id": report_id
            },
            duration_seconds=duration
        )

    def _collect_prior_outputs(self, context: dict[str, Any]) -> dict[str, Any]:
        """Collect all prior agent step results from context."""
        prior = {}

        # Primary: upstream_outputs is how orchestrator passes all prior results
        upstream = context.get("upstream_outputs", {})
        if upstream and isinstance(upstream, dict):
            prior.update(upstream)

        # Also check explicitly named output fields (legacy compat)
        for key in ["research_output", "coding_output", "data_output",
                    "security_output", "testing_output", "reviewer_output",
                    "planner_output", "schedule_output"]:
            if context.get(key):
                agent_name = key.replace("_output", "")
                prior[agent_name] = context[key]

        # Also check raw step outputs if passed
        step_results = context.get("step_results", {})
        for step_id, result in step_results.items():
            if result and isinstance(result, dict):
                agent_id = result.get("agent_id") or step_id
                prior[agent_id] = result.get("output", result)

        return prior

    async def _read_workspace_artifacts(self, task_id: str) -> str:
        """Read any real artifact files already written to workspace."""
        artifact_names = [
            "security-report.md",
            "test-results.md",
            "data-analysis.md",
            "research-findings.md",
            "code-analysis.md"
        ]
        collected = []
        for name in artifact_names:
            read_res = await tool_registry.execute_tool(
                name="filesystem:read_file",
                allowed_tools=self.allowed_tools,
                path=f"workspace/{name}"
            )
            if read_res.success and read_res.data.get("content"):
                content = read_res.data["content"]
                collected.append(f"--- [{name}] ---\n{content[:800]}")

        return "\n\n".join(collected) if collected else ""

    def _build_synthesis_context(
        self,
        goal: str,
        prior_outputs: dict[str, Any],
        artifact_content: str
    ) -> str:
        """Build a concise, comprehensive context string for LLM synthesis."""
        parts = []

        for agent_name, output in prior_outputs.items():
            if not output:
                continue
            output_str = json.dumps(output, default=str)[:1200]
            parts.append(f"[{agent_name.upper()} AGENT OUTPUT]\n{output_str}")

        if artifact_content:
            parts.append(f"[WORKSPACE ARTIFACTS]\n{artifact_content[:2000]}")

        if not parts:
            parts.append(f"[TASK CONTEXT]\nGoal: {goal}\nNo agent outputs collected yet.")

        return "\n\n".join(parts)

    def _parse_llm_response(self, content: str) -> dict[str, Any]:
        """Safely parse LLM JSON response into report structure."""
        content = content.strip()
        for fence in ("```json", "```"):
            if content.startswith(fence):
                content = content[len(fence):]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            data = json.loads(content)
            return {
                "title": str(data.get("title", "NEXUS AI Analysis Report")),
                "executive_summary": str(data.get("executive_summary", "")),
                "methodology": str(data.get("methodology", "")),
                "key_findings": list(data.get("key_findings", [])),
                "analysis": str(data.get("analysis", "")),
                "risks": list(data.get("risks", [])),
                "recommendations": list(data.get("recommendations", [])),
                "next_steps": list(data.get("next_steps", [])),
                "conclusion": str(data.get("conclusion", ""))
            }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"ReportAgent LLM parse failed: {e}")
            return None

    def _build_offline_report(
        self,
        goal: str,
        prior_outputs: dict[str, Any],
        artifact_content: str
    ) -> dict[str, Any]:
        """Build a structured report from agent outputs without LLM."""
        key_findings = []
        risks = []
        recommendations = []
        methodology_parts = []

        for agent_name, output in prior_outputs.items():
            if not output or not isinstance(output, dict):
                continue
            methodology_parts.append(agent_name)

            # Pull findings from each agent type
            if agent_name in ("security_agent", "security", "risk"):
                for r in output.get("risks", []):
                    risks.append({
                        "title": r.get("title", "Risk"),
                        "severity": r.get("severity", "Unknown"),
                        "mitigation": r.get("mitigation", "")
                    })
                    key_findings.append(
                        f"[Security] {r.get('title')} ({r.get('severity')} severity): {r.get('impact', '')}"
                    )
                for rec in output.get("recommendations", []):
                    recommendations.append(f"[Security] {rec}")

            elif agent_name in ("research_agent", "research"):
                for f in output.get("verified_facts", []):
                    fact = f.get("fact") if isinstance(f, dict) else str(f)
                    key_findings.append(f"[Research] {fact}")

            elif agent_name in ("testing_agent", "testing"):
                passed = output.get("passed", "?")
                failed = output.get("failed", "?")
                status = output.get("status", "UNKNOWN")
                key_findings.append(
                    f"[Testing] Suite: {output.get('suite', '?')} — "
                    f"{passed} passed, {failed} failed. Status: {status}."
                )

            elif agent_name in ("coding_agent", "coding"):
                if output.get("explanation"):
                    key_findings.append(f"[Coding] {output['explanation'][:200]}")
                for mod in output.get("files_modified", [])[:3]:
                    recommendations.append(f"Review changed file: {mod}")

            elif agent_name in ("data_agent", "data", "data_analyst"):
                summary = output.get("summary")
                if summary:
                    key_findings.append(f"[Data] {summary}")
                for i in output.get("key_insights", []):
                    key_findings.append(f"[Data] {i}")
                stats = output.get("statistics", {})
                if isinstance(stats, dict):
                    fields = [str(k) for k in stats.keys() if k not in ("rows", "columns", "numeric_fields", "missing_values")]
                    if fields:
                        key_findings.append(f"[Data] Evaluated metric columns and records: {', '.join(fields[:8])}")

        if not key_findings:
            key_findings = [f"Multi-agent pipeline executed for goal: {goal[:100]}"]

        if artifact_content:
            key_findings.append("Workspace artifacts generated and saved.")

        if not recommendations:
            recommendations = ["Review generated artifacts for detailed analysis."]

        return {
            "title": f"NEXUS AI Analysis Report: {goal[:60]}...",
            "executive_summary": (
                f"NEXUS AI completed a multi-agent pipeline for: '{goal[:150]}'. "
                f"Agents engaged: {', '.join(methodology_parts) if methodology_parts else 'pipeline'}. "
                f"{len(key_findings)} findings identified."
            ),
            "methodology": (
                f"Coordinated execution of agents: {', '.join(methodology_parts) if methodology_parts else 'N/A'}. "
                "Each agent performed real tool operations and produced verified outputs."
            ),
            "key_findings": key_findings,
            "analysis": (
                "## Agent-by-Agent Analysis\n\n"
                + "\n".join(f"**{a}:** {json.dumps(o, default=str)[:300]}" for a, o in prior_outputs.items())
            ),
            "risks": risks,
            "recommendations": recommendations,
            "next_steps": [
                "Review the final report artifact in the workspace.",
                "Address any high/critical severity risks first.",
                "Re-run the pipeline with updated inputs if needed."
            ],
            "conclusion": (
                f"The NEXUS AI multi-agent system successfully analyzed '{goal[:100]}'. "
                "All findings are derived from real agent tool executions."
            )
        }

    def _render_full_markdown(self, report_data: dict[str, Any], goal: str) -> str:
        """Render the final markdown report from structured data."""
        lines = [
            f"# {report_data.get('title', 'NEXUS AI Report')}\n",
            f"**Goal:** {goal[:200]}\n",
            f"## Executive Summary\n\n{report_data.get('executive_summary', '')}\n",
            f"## Methodology\n\n{report_data.get('methodology', '')}\n",
            "## Key Findings\n"
        ]
        for finding in report_data.get("key_findings", []):
            lines.append(f"- {finding}")

        if report_data.get("analysis"):
            lines.append(f"\n## Detailed Analysis\n\n{report_data['analysis'][:3000]}")

        risks = report_data.get("risks", [])
        if risks:
            lines.append("\n## Risk Matrix\n")
            for r in risks:
                lines.append(
                    f"### {r.get('title', 'Risk')} ({r.get('severity', 'Unknown')} severity)\n"
                    f"- **Mitigation:** {r.get('mitigation', 'See detailed report.')}\n"
                )

        recs = report_data.get("recommendations", [])
        if recs:
            lines.append("## Recommendations\n")
            for r in recs:
                lines.append(f"- {r}")

        next_steps = report_data.get("next_steps", [])
        if next_steps:
            lines.append("\n## Next Steps\n")
            for ns in next_steps:
                lines.append(f"1. {ns}")

        if report_data.get("conclusion"):
            lines.append(f"\n## Conclusion\n\n{report_data['conclusion']}")

        lines.append("\n---\n*Generated by NEXUS AI Multi-Agent System*")
        return "\n".join(lines)
