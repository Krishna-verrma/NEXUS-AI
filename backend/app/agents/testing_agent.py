import json
import logging
import re
import time
from typing import Any, Optional
from app.agents.base import BaseAgent, AgentResult
from app.tools import tool_registry
from app.services.context_manager import context_manager

logger = logging.getLogger("nexus.agents.testing")


class TestingAgent(BaseAgent):
    """
    Autonomous QA and test execution agent.
    Discovers real test files, runs pytest, parses actual output metrics,
    and produces verified test-results.json artifacts.
    """
    def __init__(self):
        super().__init__(
            agent_id="testing_agent",
            name="Testing Agent",
            role="Test Automation & Verification Engineer"
        )
        self.capabilities = [
            "Pytest Execution (Real Subprocess)",
            "Dynamic Test File Discovery",
            "Failure Inspection & Trace Parsing",
            "Regression Testing",
            "Execution Metrics Reporting"
        ]
        self.allowed_tools = [
            "terminal:run_command",
            "filesystem:read_file",
            "filesystem:write_file",
            "filesystem:list_directory"
        ]
        self.input_schema = {
            "step_task": "string (optional test target from planner)",
            "context": "dict"
        }
        self.output_schema = {
            "tests_run": "integer",
            "passed": "integer",
            "failed": "integer",
            "duration_seconds": "float",
            "stdout": "string",
            "test_results": "list of dict",
            "status": "string ('PASSED' | 'FAILED')",
            "suite": "string"
        }
        self.execution_state = "idle"

    async def run(self, context: dict[str, Any]) -> AgentResult:
        self.execution_state = "running"
        start_time = time.time()
        task_id = context.get("task_id", "default")
        prompt = context.get("prompt") or context.get("user_prompt") or context.get("step_task") or ""

        # === STEP 1: Discover real test files ===
        test_file = await self._discover_test_target(prompt)

        # === STEP 2: Run pytest on the discovered target ===
        term_res = await tool_registry.execute_tool(
            name="terminal:run_command",
            allowed_tools=self.allowed_tools,
            command=f"pytest {test_file} -v --tb=short",
            timeout_seconds=60
        )

        stdout = ""
        stderr = ""
        if term_res.success:
            stdout = term_res.data.get("stdout", "")
            stderr = term_res.data.get("stderr", "")
        else:
            stdout = term_res.error or "Test execution failed."

        # === STEP 3: Parse real pytest output metrics ===
        passed_count, failed_count, error_count, duration = self._parse_pytest_output(stdout + "\n" + stderr)
        total_run = passed_count + failed_count + error_count
        overall_status = "PASSED" if (failed_count == 0 and error_count == 0 and term_res.success) else "FAILED"

        # Extract individual test results from verbose output
        test_results = self._extract_test_results(stdout)

        # === STEP 4: Save results artifact ===
        test_data = {
            "suite": test_file,
            "tests_run": total_run,
            "passed": passed_count,
            "failed": failed_count,
            "errors": error_count,
            "status": overall_status,
            "stdout": stdout[:2000],
            "test_results": test_results[:20],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        context_manager.save_artifact(
            task_id=task_id,
            name="test-results.json",
            content=json.dumps(test_data, indent=2),
            artifact_type="json"
        )

        # Save readable markdown summary
        md_lines = [
            f"# Test Results — {overall_status}\n",
            f"- **Suite:** `{test_file}`",
            f"- **Tests Run:** {total_run}",
            f"- **Passed:** {passed_count} ✅",
            f"- **Failed:** {failed_count}" + (" ❌" if failed_count > 0 else ""),
            f"- **Errors:** {error_count}" + (" ⚠️" if error_count > 0 else ""),
            f"\n```\n{stdout[:1500]}\n```"
        ]
        context_manager.save_artifact(
            task_id=task_id,
            name="test-results.md",
            content="\n".join(md_lines),
            artifact_type="markdown"
        )

        agent_duration = round(time.time() - start_time, 2)
        self.execution_state = "completed"

        summary = f"Test suite '{test_file}': {passed_count} passed, {failed_count} failed in {agent_duration}s. Status: {overall_status}."
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            success=(overall_status == "PASSED"),
            output=test_data,
            preview=self.format_preview(summary),
            confidence=1.0 if overall_status == "PASSED" else 0.4,
            metrics={
                "tests_run": total_run,
                "passed": passed_count,
                "failed": failed_count,
                "suite": test_file
            },
            duration_seconds=agent_duration,
            error=term_res.error if not term_res.success else None
        )

    async def _discover_test_target(self, prompt: str) -> str:
        """
        Dynamically discover test files in the workspace.
        Returns the most appropriate target based on the prompt context.
        """
        lower = prompt.lower()

        # Prompt-based targeting
        if "calendar" in lower or "schedule" in lower:
            return "tests/test_calendar_agent.py"
        if "chat" in lower or "follow" in lower or "duplicat" in lower or "context" in lower:
            return "tests/test_followup_chat_context.py"
        if "tool" in lower or "registry" in lower:
            return "tests/test_tool_registry.py"
        if "intent" in lower or "classif" in lower:
            return "tests/test_intent_classifier.py"
        if "orchestrat" in lower:
            return "tests/test_orchestrator.py"
        if "agent" in lower:
            return "tests/test_agents.py"
        if "pipeline" in lower or "dynamic" in lower:
            return "tests/test_dynamic_pipeline.py"
        if "api" in lower or "endpoint" in lower:
            return "tests/test_api_endpoints.py"

        # Default: try to discover tests directory
        list_res = await tool_registry.execute_tool(
            name="filesystem:list_directory",
            allowed_tools=self.allowed_tools,
            path="tests"
        )
        if list_res.success:
            entries = list_res.data.get("entries", [])
            test_files = [
                e["name"] for e in entries
                if isinstance(e, dict) and e.get("name", "").startswith("test_") and e.get("name", "").endswith(".py")
            ]
            if test_files:
                # Run full suite if multiple test files found
                return "tests/"

        return "tests/test_tool_registry.py"

    def _parse_pytest_output(self, output: str) -> tuple[int, int, int, float]:
        """Parse real pytest stdout to extract pass/fail/error counts and duration."""
        passed = 0
        failed = 0
        errors = 0
        duration = 0.0

        # Pattern: "5 passed, 2 failed, 1 error in 3.45s"
        summary_match = re.search(
            r"(?:(\d+)\s+passed)?[,\s]*(?:(\d+)\s+failed)?[,\s]*(?:(\d+)\s+error)?[,\s]*in\s+([\d.]+)s",
            output
        )
        if summary_match:
            passed = int(summary_match.group(1) or 0)
            failed = int(summary_match.group(2) or 0)
            errors = int(summary_match.group(3) or 0)
            try:
                duration = float(summary_match.group(4))
            except (ValueError, TypeError):
                pass
            return passed, failed, errors, duration

        # Fallback patterns
        passed_matches = re.findall(r"(\d+)\s+passed", output)
        failed_matches = re.findall(r"(\d+)\s+failed", output)
        error_matches = re.findall(r"(\d+)\s+error", output)
        duration_matches = re.findall(r"in\s+([\d.]+)s", output)

        passed = int(passed_matches[-1]) if passed_matches else 0
        failed = int(failed_matches[-1]) if failed_matches else 0
        errors = int(error_matches[-1]) if error_matches else 0
        duration = float(duration_matches[-1]) if duration_matches else 0.0

        return passed, failed, errors, duration

    def _extract_test_results(self, stdout: str) -> list[dict[str, Any]]:
        """Extract individual test pass/fail lines from verbose pytest output."""
        results = []
        # Match lines like: "tests/test_foo.py::test_bar PASSED"
        for line in stdout.splitlines():
            line = line.strip()
            if " PASSED" in line or " FAILED" in line or " ERROR" in line or " SKIPPED" in line:
                parts = line.rsplit(" ", 1)
                if len(parts) == 2:
                    test_name = parts[0].strip()
                    status = parts[1].strip()
                    results.append({"test": test_name, "status": status})
        return results
