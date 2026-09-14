import json
import logging
import time
from typing import Any, Optional
from app.agents.base import BaseAgent, AgentResult
from app.core.ai_client import ai_client
from app.tools import tool_registry
from app.services.context_manager import context_manager

logger = logging.getLogger("nexus.agents.data")


class DataAgent(BaseAgent):
    """
    Autonomous data analysis agent.
    Reads and parses real files, computes real statistics,
    and uses the LLM to synthesize meaningful business insights.
    """
    def __init__(self, agent_id: str = "data_agent"):
        super().__init__(
            agent_id=agent_id,
            name="Data Agent",
            role="Quantitative Data Analyst & Scientist"
        )
        self.capabilities = [
            "CSV/JSON/Excel File Parsing (Real Files)",
            "Descriptive Statistics & Outlier Detection",
            "Trend & Correlation Identification",
            "LLM-Powered Business Insight Synthesis",
            "Structured Data Artifact Export"
        ]
        self.allowed_tools = [
            "documents:parse_document",
            "filesystem:read_file",
            "filesystem:list_directory",
        ]
        self.system_prompt = (
            "You are the NEXUS Data Analysis Agent.\n"
            "You will be given real parsed data from a file (CSV, JSON, or Excel).\n"
            "Your job is to:\n"
            "1. Identify key patterns, trends, and anomalies from the actual values.\n"
            "2. Compute descriptive statistics if not already provided.\n"
            "3. Extract actionable business insights grounded in the real data.\n"
            "4. Highlight any data quality issues you observe.\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            "  \"summary\": \"string\",\n"
            "  \"key_insights\": [\"string\"],\n"
            "  \"statistics\": { \"rows\": int, \"columns\": int, \"numeric_fields\": [...], "
            "\"missing_values\": int },\n"
            "  \"anomalies\": [\"string\"],\n"
            "  \"recommendations\": [\"string\"]\n"
            "}"
        )
        self.execution_state = "idle"

    async def run(self, context: dict[str, Any]) -> AgentResult:
        self.execution_state = "running"
        start_time = time.time()
        task_id = context.get("task_id", "default")
        prompt = context.get("prompt") or context.get("user_prompt") or context.get("step_task") or ""
        files = context.get("files", [])

        # === STEP 1: Identify target file(s) ===
        target_file_path = self._pick_target_file(files, prompt)

        # === STEP 2: Parse the file ===
        parsed_data: Optional[dict[str, Any]] = None
        raw_content = ""
        file_parse_error = ""

        if target_file_path:
            parse_res = await tool_registry.execute_tool(
                name="documents:parse_document",
                allowed_tools=self.allowed_tools,
                file_path=target_file_path,
                include_statistics=True
            )
            if parse_res.success:
                parsed_data = parse_res.data
            else:
                file_parse_error = f"documents:parse_document failed: {parse_res.error}"
                logger.warning(f"DataAgent: {file_parse_error}. Trying direct read.")
                # Fallback: read raw file content
                read_res = await tool_registry.execute_tool(
                    name="filesystem:read_file",
                    allowed_tools=self.allowed_tools,
                    path=target_file_path
                )
                if read_res.success:
                    raw_content = read_res.data.get("content", "")

        # === STEP 3: Build data context for LLM ===
        data_context = self._build_data_context(parsed_data, raw_content, target_file_path)

        # === STEP 4: LLM synthesizes insights from real data ===
        output = None
        if ai_client.is_configured():
            user_message = (
                f"Analyze this data from '{target_file_path or 'workspace file'}':\n\n"
                f"{data_context}\n\n"
                f"User Goal: {prompt}"
            )
            llm_result = await ai_client.generate(
                system_prompt=self.system_prompt,
                user_message=user_message,
                max_tokens=2000,
                temperature=0.2
            )
            if llm_result.get("success") and llm_result.get("content"):
                output = self._parse_llm_response(llm_result["content"])

        # === FALLBACK: Build output from parsed_data without LLM ===
        if not output:
            output = self._build_offline_analysis(parsed_data, raw_content, target_file_path)
        else:
            if parsed_data:
                if "statistics" not in output or not output["statistics"]:
                    output["statistics"] = parsed_data.get("statistics", {})
                elif "statistics" in parsed_data:
                    for k, v in parsed_data["statistics"].items():
                        if k not in output["statistics"]:
                            output["statistics"][k] = v
                if "trend_timeline" not in output:
                    output["trend_timeline"] = parsed_data.get("trend_timeline", [])
                if "anomalies" not in output:
                    output["anomalies"] = parsed_data.get("anomalies", [])

        # === STEP 5: Save analysis artifacts ===
        report_md = self._format_markdown_report(output, target_file_path, prompt)
        context_manager.save_artifact(
            task_id=task_id,
            name="data-analysis.md",
            content=report_md,
            artifact_type="markdown"
        )
        context_manager.save_artifact(
            task_id=task_id,
            name="data-analysis.json",
            content=json.dumps(output, indent=2),
            artifact_type="json"
        )

        duration = round(time.time() - start_time, 2)
        self.execution_state = "completed"
        insights = output.get("key_insights", [])
        stats = output.get("statistics", {})

        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            success=True,
            output=output,
            preview=self.format_preview(
                f"Data analysis complete: {stats.get('rows', '?')} rows, "
                f"{len(insights)} insights extracted from {target_file_path or 'workspace'}."
            ),
            confidence=0.90 if ai_client.is_configured() else 0.65,
            metrics={
                "rows": stats.get("rows", 0),
                "columns": stats.get("columns", 0),
                "insights_count": len(insights),
                "source_file": target_file_path
            },
            duration_seconds=duration
        )

    def _pick_target_file(self, files: list[dict[str, Any]], prompt: str) -> Optional[str]:
        """Pick the most relevant file for analysis from attached files or prompt hints."""
        if files:
            for f in files:
                fp = f.get("file_path") or f.get("path") or f.get("filename")
                if fp and any(fp.endswith(ext) for ext in [".csv", ".xlsx", ".xls", ".json", ".parquet"]):
                    return fp
            # Take first file regardless
            fp = files[0].get("file_path") or files[0].get("path") or files[0].get("filename")
            if fp:
                return fp

        # Hint from prompt
        import re
        path_match = re.search(r"[\w/\\:\-]+\.(?:csv|xlsx|xls|json|parquet)", prompt)
        if path_match:
            return path_match.group(0)

        return None

    def _build_data_context(
        self,
        parsed_data: Optional[dict[str, Any]],
        raw_content: str,
        file_path: Optional[str]
    ) -> str:
        """Build a concise text representation of the parsed data for the LLM."""
        if parsed_data:
            rows = parsed_data.get("row_count") or parsed_data.get("rows") or 0
            cols = parsed_data.get("column_count") or parsed_data.get("columns") or 0
            headers = parsed_data.get("headers") or parsed_data.get("column_names") or []
            sample = parsed_data.get("sample_rows") or parsed_data.get("rows_data") or []
            stats = parsed_data.get("statistics") or {}

            lines = [
                f"File: {file_path or 'unknown'}",
                f"Dimensions: {rows} rows × {cols} columns",
                f"Headers: {headers[:20]}",
            ]
            if stats:
                lines.append(f"Column Statistics: {json.dumps(stats, default=str)[:800]}")
            if sample:
                lines.append(f"Sample Rows (first 5): {json.dumps(sample[:5], default=str)[:600]}")
            return "\n".join(lines)

        if raw_content:
            return f"Raw file content (first 1500 chars):\n{raw_content[:1500]}"

        return "No file data available."

    def _parse_llm_response(self, content: str) -> dict[str, Any]:
        """Safely parse LLM JSON response."""
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
                "summary": str(data.get("summary", "")),
                "key_insights": list(data.get("key_insights", [])),
                "statistics": data.get("statistics", {}),
                "anomalies": list(data.get("anomalies", [])),
                "recommendations": list(data.get("recommendations", []))
            }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"DataAgent LLM parse failed: {e}")
            return self._build_offline_analysis(None, content, None)

    def _build_offline_analysis(
        self,
        parsed_data: Optional[dict[str, Any]],
        raw_content: str,
        file_path: Optional[str]
    ) -> dict[str, Any]:
        """Build an analysis from parsed_data or raw_content without LLM."""
        if parsed_data:
            rows = parsed_data.get("row_count") or 0
            cols = parsed_data.get("column_count") or 0
            headers = parsed_data.get("headers") or []
            stats_data = parsed_data.get("statistics") or {}

            insights = [f"Dataset contains {rows} rows and {cols} columns."]
            if headers:
                insights.append(f"Detected fields: {', '.join(str(h) for h in headers[:10])}.")
            if stats_data:
                for col, col_stats in list(stats_data.items())[:3]:
                    if isinstance(col_stats, dict):
                        mean_val = col_stats.get("mean")
                        if mean_val is not None:
                            insights.append(f"Column '{col}': mean = {mean_val:.2f}.")

            merged_stats = dict(stats_data)
            merged_stats["rows"] = rows
            merged_stats["columns"] = cols
            merged_stats["numeric_fields"] = [h for h in headers if isinstance(h, str)]
            merged_stats["missing_values"] = parsed_data.get("missing_count", 0)

            for col, cs in stats_data.items():
                if isinstance(cs, dict) and "total" not in cs:
                    cs["total"] = cs.get("sum", cs.get("total", 0))

            return {
                "summary": f"Analyzed {rows}×{cols} dataset from '{file_path or 'file'}'.",
                "key_insights": insights,
                "statistics": merged_stats,
                "trend_timeline": parsed_data.get("trend_timeline", []),
                "anomalies": parsed_data.get("anomalies", []),
                "recommendations": [
                    "Monitor key performance indicators across numeric dimensions.",
                    "Review column statistics and trend variance for anomaly signals."
                ]
            }

        # Fallback: can't even parse the file
        return {
            "summary": f"Data file '{file_path or 'unknown'}' could not be fully parsed.",
            "key_insights": [
                "File was located and partially read.",
                "Configure AI_API_KEY for intelligent data analysis synthesis."
            ],
            "statistics": {"rows": 0, "columns": 0, "numeric_fields": [], "missing_values": 0},
            "anomalies": ["File parsing incomplete — check format compatibility."],
            "recommendations": [
                "Ensure file is in CSV, JSON, or Excel format.",
                "Configure an AI provider for full analysis synthesis."
            ]
        }

    def _format_markdown_report(
        self,
        output: dict[str, Any],
        file_path: Optional[str],
        prompt: str
    ) -> str:
        lines = [
            f"# Data Analysis Report\n",
            f"**Source:** `{file_path or 'workspace data'}`",
            f"**Goal:** {prompt[:150]}\n",
            f"## Summary\n{output.get('summary', '')}\n",
            "## Key Insights\n"
        ]
        for i in output.get("key_insights", []):
            lines.append(f"- {i}")

        stats = output.get("statistics", {})
        if stats:
            lines.append("\n## Dataset Statistics\n")
            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| Rows | {stats.get('rows', '?')} |")
            lines.append(f"| Columns | {stats.get('columns', '?')} |")
            lines.append(f"| Missing Values | {stats.get('missing_values', '?')} |")

        anomalies = output.get("anomalies", [])
        if anomalies:
            lines.append("\n## Anomalies Detected\n")
            for a in anomalies:
                lines.append(f"- ⚠️ {a}")

        recs = output.get("recommendations", [])
        if recs:
            lines.append("\n## Recommendations\n")
            for r in recs:
                lines.append(f"- {r}")

        return "\n".join(lines)
