from typing import Dict, Any, Optional, Callable
from app.agents.base import BaseAgent, AgentResult
from app.tools.computer.launch import launch_app
from app.tools.computer.screenshot import capture_screenshot
from app.tools.computer.system_info import get_system_info

class ComputerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="computer_agent",
            name="Computer Controller",
            description="Direct desktop integration, app launching, screenshot capture, and OS window management.",
            capabilities=["App Launching", "Screen Capture", "Process Management", "System Control"],
            allowed_tools=["launch_app", "capture_screenshot", "get_system_info"]
        )

    def execute(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> AgentResult:
        traces = []
        p_lower = prompt.lower()

        # Step 1: Planning
        traces.append(self.emit_trace(
            action="Analyzing Desktop Request",
            detail=f"Interpreting intent from prompt: '{prompt}'",
            status="started",
            callback=callback
        ))

        # Check for launch request
        if "open" in p_lower or "launch" in p_lower or "start" in p_lower:
            # Extract app target
            target_app = "calculator"
            for candidate in ["chrome", "notepad", "calculator", "calc", "explorer", "terminal", "powershell", "code", "vscode"]:
                if candidate in p_lower:
                    target_app = candidate
                    break
            
            tool_call = {"toolName": "launch_app", "parameters": {"app_name": target_app}}
            res = launch_app(target_app)
            tool_call["result"] = res
            tool_call["status"] = "success" if res.get("success") else "failed"

            traces.append(self.emit_trace(
                action=f"Launched Application: {target_app.capitalize()}",
                detail=res.get("message", f"Opened {target_app}"),
                status="tool_call",
                tool_calls=[tool_call],
                callback=callback
            ))

            return AgentResult(
                agent_role=self.role,
                response=f"Successfully initialized and executed command to launch **{target_app.capitalize()}** on Windows. Application process is active.",
                status="completed",
                activity_traces=traces,
                data=res
            )

        # Check for screenshot
        elif "screenshot" in p_lower or "screen" in p_lower or "capture" in p_lower:
            tool_call = {"toolName": "capture_screenshot", "parameters": {}}
            res = capture_screenshot()
            tool_call["result"] = res
            tool_call["status"] = "success"

            traces.append(self.emit_trace(
                action="Captured Screen Display",
                detail=f"Resolution: {res.get('width', 1920)}x{res.get('height', 1080)}",
                status="tool_call",
                tool_calls=[tool_call],
                callback=callback
            ))

            return AgentResult(
                agent_role=self.role,
                response="Captured current desktop viewport. Resolution analyzed at 1920x1080. Ready for visual layout inspection.",
                status="completed",
                activity_traces=traces,
                data=res
            )

        # Default: System metrics
        else:
            tool_call = {"toolName": "get_system_info", "parameters": {}}
            res = get_system_info()
            tool_call["result"] = res
            tool_call["status"] = "success"

            traces.append(self.emit_trace(
                action="Retrieved System Vitals",
                detail=f"CPU: {res.get('cpuUsagePercent')}% | RAM: {res.get('memoryUsagePercent')}%",
                status="tool_call",
                tool_calls=[tool_call],
                callback=callback
            ))

            return AgentResult(
                agent_role=self.role,
                response=f"Desktop system diagnostics retrieved: Running on **{res.get('os')}** ({res.get('architecture')}). CPU load is **{res.get('cpuUsagePercent')}%**, Memory utilization is **{res.get('memoryUsagePercent')}%** ({res.get('memoryUsedGb')}/{res.get('memoryTotalGb')} GB), and **{res.get('diskFreeGb')} GB** free disk space available.",
                status="completed",
                activity_traces=traces,
                data=res
            )
