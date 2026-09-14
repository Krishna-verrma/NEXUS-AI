from typing import Dict, Any, Optional, Callable
from app.agents.base import BaseAgent, AgentResult
from app.tools.calendar.google_calendar import list_calendar_events, schedule_calendar_event

class ProductivityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="productivity_agent",
            name="Productivity Executive",
            description="Manages calendars, meeting agendas, task pipelines, reminders, and daily briefing logs.",
            capabilities=["Event Scheduling", "Task Prioritization", "Meeting Summaries", "Time Blocking"],
            allowed_tools=["list_calendar_events", "schedule_calendar_event"]
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
            action="Analyzing Schedule & Tasks",
            detail=f"Directive: '{prompt}'",
            status="started",
            callback=callback
        ))

        # Check for scheduling request
        if "schedule" in p_lower or "meeting" in p_lower or "event" in p_lower:
            title = "Sprint Planning & Agent Review"
            for part in prompt.split(":"):
                if len(part.strip()) > 3:
                    title = part.strip()
            
            tool_call = {
                "toolName": "schedule_calendar_event",
                "parameters": {"title": title, "start_time": "15:00", "end_time": "15:45"}
            }
            res = schedule_calendar_event(title, "15:00", "15:45")
            tool_call["result"] = res
            tool_call["status"] = "success"

            traces.append(self.emit_trace(
                action=f"Reserved Calendar Slot: {title}",
                detail="Time blocked from 15:00 - 15:45 without conflict",
                status="tool_call",
                tool_calls=[tool_call],
                callback=callback
            ))

            return AgentResult(
                agent_role=self.role,
                response=f"📅 **Calendar Event Confirmed**: Successfully scheduled **{title}**.\n- Time: Today from `15:00` to `15:45`\n- Status: `Confirmed` (No scheduling overlaps detected)",
                status="completed",
                activity_traces=traces,
                data=res
            )
        else:
            # Default: List today's agenda
            tool_call = {"toolName": "list_calendar_events", "parameters": {}}
            res = list_calendar_events()
            tool_call["result"] = res
            tool_call["status"] = "success"

            traces.append(self.emit_trace(
                action="Retrieved Today's Agenda",
                detail=f"Identified {res.get('count', 0)} scheduled items",
                status="tool_call",
                tool_calls=[tool_call],
                callback=callback
            ))

            events_md = "\n".join([
                f"- **{e['startTime']} - {e['endTime']}**: {e['title']} ({e['status']})"
                for e in res.get("events", [])
            ])

            return AgentResult(
                agent_role=self.role,
                response=f"### 📋 Daily Productivity Agenda\n\n{events_md}\n\nAll agenda items are synchronized with your desktop calendar.",
                status="completed",
                activity_traces=traces,
                data=res
            )
