from typing import Dict, Any, Optional, Callable
from app.agents.base import BaseAgent, AgentResult
from app.tools.code.analyzer import analyze_code_structure
from app.tools.code.executor import execute_code_sandbox

class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="coding_agent",
            name="Code Architect",
            description="Software engineering, syntax analysis, refactoring, code execution testing, and debugging.",
            capabilities=["Static Analysis", "Bug Diagnostics", "Code Generation", "Test Execution"],
            allowed_tools=["analyze_code_structure", "execute_code_sandbox"]
        )

    def execute(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> AgentResult:
        traces = []
        p_lower = prompt.lower()

        traces.append(self.emit_trace(
            action="Parsing Software Architecture Requirements",
            detail=f"Prompt: '{prompt}'",
            status="started",
            callback=callback
        ))

        # Check for code execution simulation
        if "run" in p_lower or "execute" in p_lower:
            sample_code = """
def compute_pipeline_metrics(batch_size=128):
    latencies = [12.4, 9.8, 15.2, 11.0, 8.9]
    avg_latency = sum(latencies) / len(latencies)
    throughput = (batch_size * 1000) / avg_latency
    print(f"Batch Size: {batch_size} | Avg Latency: {avg_latency:.2f}ms | Throughput: {throughput:.1f} req/s")
    return {"avg_latency": avg_latency, "throughput": throughput}

metrics = compute_pipeline_metrics()
"""
            tool_call = {"toolName": "execute_code_sandbox", "parameters": {"code": sample_code}}
            res = execute_code_sandbox(sample_code)
            tool_call["result"] = res
            tool_call["status"] = "success"

            traces.append(self.emit_trace(
                action="Executed Code in Secure Sandbox",
                detail=f"Completed in {res.get('durationMs')}ms with 0 fatal errors",
                status="tool_call",
                tool_calls=[tool_call],
                callback=callback
            ))

            return AgentResult(
                agent_role=self.role,
                response=f"### Code Execution Results\n\n```python\n{sample_code.strip()}\n```\n\n**Standard Output**:\n```text\n{res.get('output', '').strip()}\n```\nExecution finished in **{res.get('durationMs')}ms**.",
                status="completed",
                activity_traces=traces,
                data=res
            )
        else:
            # Code generation / analysis
            code_sample = """import asyncio
from typing import AsyncGenerator

async def stream_agent_events(session_id: str) -> AsyncGenerator[dict, None]:
    \"\"\"Stream telemetry events for active Nexus sub-agents.\"\"\"
    yield {"event": "start", "session": session_id, "status": "initializing"}
    await asyncio.sleep(0.05)
    yield {"event": "chunk", "content": "Nexus AI stream active"}
    yield {"event": "done", "status": "completed"}
"""
            tool_call = {"toolName": "analyze_code_structure", "parameters": {"language": "python"}}
            res = analyze_code_structure(code_sample, language="python")
            tool_call["result"] = res
            tool_call["status"] = "success"

            traces.append(self.emit_trace(
                action="Static Syntax & AST Inspection",
                detail=f"AST Verified: {res.get('functionCount')} functions, {res.get('lineCount')} lines",
                status="tool_call",
                tool_calls=[tool_call],
                callback=callback
            ))

            return AgentResult(
                agent_role=self.role,
                response=f"### Code Architecture & Solution\n\n```python\n{code_sample}\n```\n\n**Quality & AST Analysis**:\n- Syntax Valid: `{res.get('validSyntax')}`\n- Cyclomatic Complexity: `{res.get('complexity')}`\n- Functions Detected: `{', '.join(res.get('functions', []))}`",
                status="completed",
                activity_traces=traces,
                data=res
            )
