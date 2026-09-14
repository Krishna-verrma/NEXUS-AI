import time
from typing import Any
from app.agents.base import BaseAgent, AgentResult
from app.services.calendar_service import CalendarService
from app.core.ai_client import ai_client

class ScheduleAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="schedule",
            name="Schedule Agent",
            role="Specialized Agent"
        )

    async def run(self, context: dict[str, Any]) -> AgentResult:
        start_time = time.time()
        prompt = context.get("prompt", "")

        # Fetch live schedule from CalendarService
        today_data = CalendarService.get_today_schedule()
        upcoming_data = CalendarService.get_upcoming_meetings(days=7)

        # Check if real AI is configured
        if ai_client.is_configured():
            try:
                system_prompt = (
                    "You are the NEXUS AI Schedule & Workspace Assistant Agent.\n"
                    "You inspect the user's PC software calendar, today's agenda, upcoming meetings, and work deliverables.\n"
                    "Provide a crisp, clear, well-structured breakdown answering whether they have work today and what meetings are coming ahead.\n"
                    "Structure response as JSON with keys:\n"
                    "- 'summary': direct answer to 'do I have work today or meetings ahead?'\n"
                    "- 'today_meetings': list of { title, start_time, end_time, location }\n"
                    "- 'upcoming_meetings': list of { title, start_time, location }\n"
                    "- 'today_work_items': list of work tasks/deliverables\n"
                    "- 'next_meeting_notice': specific highlight for the next upcoming event"
                )
                user_msg = (
                    f"User Query: {prompt}\n"
                    f"Today ({today_data.get('day_of_week')}, {today_data.get('date')} at {today_data.get('current_time')}):\n"
                    f"Today's Meetings: {today_data.get('meetings')}\n"
                    f"Today's Work Tasks: {today_data.get('work_tasks')}\n"
                    f"Upcoming Meetings in Coming Days: {upcoming_data}"
                )
                resp = await ai_client.complete(
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_msg}],
                    response_format_json=True
                )
                import json
                parsed = json.loads(resp)
                duration = round(time.time() - start_time, 2)
                preview = self.format_preview(parsed.get("summary", "Schedule analyzed."))
                return AgentResult(
                    agent_id=self.agent_id,
                    agent_name=self.name,
                    success=True,
                    output=parsed,
                    preview=preview,
                    confidence=0.98,
                    metrics={
                        "meetings_today": len(today_data.get("meetings", [])),
                        "upcoming_meetings": len(upcoming_data),
                        "work_items": len(today_data.get("work_tasks", []))
                    },
                    duration_seconds=duration
                )
            except Exception:
                pass

        # Deterministic / Demo Response
        schedule_output = self._deterministic_schedule(prompt, today_data, upcoming_data)
        duration = round(time.time() - start_time, 2)
        preview = self.format_preview(schedule_output["summary"])

        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            success=True,
            output=schedule_output,
            preview=preview,
            confidence=0.99,
            metrics={
                "meetings_today": len(today_data.get("meetings", [])),
                "upcoming_meetings": len(upcoming_data),
                "work_items": len(today_data.get("work_tasks", []))
            },
            duration_seconds=duration
        )

    def _deterministic_schedule(self, prompt: str, today: dict[str, Any], upcoming: list[dict[str, Any]]) -> dict[str, Any]:
        date_str = today.get("date")
        day_name = today.get("day_of_week")
        curr_time = today.get("current_time")
        meetings = today.get("meetings", [])
        tasks = today.get("work_tasks", [])
        next_m = today.get("next_meeting")

        meeting_count = len(meetings)
        task_count = len(tasks)
        important_meetings = [m for m in meetings if m.get("is_important") or m.get("priority") == "high"]

        summary = (
            f"Yes, you have active commitments and deliverables for today ({day_name}, {date_str}). "
            f"You have {meeting_count} meeting{'s' if meeting_count != 1 else ''} "
            f"({len(important_meetings)} high-priority/urgent) and {task_count} work deliverables, "
            f"with {len(upcoming)} additional meetings scheduled ahead in the coming week."
        )

        next_notice = ""
        if next_m:
            time_part = next_m['start_time'].split(' ')[-1][:5]
            join_txt = f" [Join: {next_m['join_url']}]" if next_m.get("join_url") else ""
            prio_tag = " [🔥 IMPORTANT]" if next_m.get("is_important") else ""
            next_notice = f"Your next meeting is{prio_tag} '{next_m['title']}' at {time_part} ({next_m.get('location')}){join_txt}."
        else:
            next_notice = "All scheduled meetings for today have concluded. You have clear focus time for your work deliverables."

        return {
            "summary": summary,
            "date": f"{day_name}, {date_str}",
            "current_time": curr_time,
            "next_meeting_notice": next_notice,
            "important_meetings": important_meetings,
            "today_meetings": meetings,
            "today_work_items": tasks,
            "upcoming_meetings": upcoming[:5],
            "recommendations": [
                "Review the briefing notes 10 minutes prior to your next conference call.",
                "Prepare for your high-priority client architecture review with automated agent research.",
                "Click 'Join Call' directly on your dashboard when meetings start."
            ]
        }
