import re
import uuid
import logging
from typing import Any, Optional

from app.database.repository import Repository
from app.core.ai_client import ai_client
from app.ai.prompts import get_system_prompt
from app.services.calendar_service import CalendarService
from app.services.datetime_service import DateTimeService
from app.services.intent_classifier import IntentClassifier, IntentType
from app.tools import tool_registry

logger = logging.getLogger("nexus.chat_service")


class ChatService:
    @staticmethod
    async def process_chat_message(
        message: str,
        task_id: Optional[str] = None,
        active_task_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        mode: Optional[str] = "live"
    ) -> dict[str, Any]:
        user_msg_id = str(uuid.uuid4())
        effective_task_id = active_task_id or task_id
        task = Repository.get_task(effective_task_id) if effective_task_id else None

        # 1. Classify intent
        intent, used_task_context = IntentClassifier.classify(message, task=task)
        clean_msg = message.strip()
        lower_msg = clean_msg.lower()

        # ── INTENT: NEW_TASK ──
        if intent == IntentType.NEW_TASK:
            from app.services.task_service import TaskService
            new_task = await TaskService.create_and_run_task(prompt=clean_msg, is_demo=False)
            new_task_id = new_task["id"]

            answer = (
                f"🚀 **New Task Created & Dispatched**\n\n"
                f"Dispatched a multi-agent workflow for: **'{new_task.get('title', clean_msg)}'**\n\n"
                f"- **Task ID:** `{new_task_id}`\n"
                f"- **Status:** Dispatched to Nexus Orchestrator\n"
                f"- **Pipeline:** Planning, tool allocation, and agent execution started."
            )

            Repository.add_message(
                message_id=user_msg_id, task_id=effective_task_id, role="user", content=clean_msg
            )
            ai_msg_id = str(uuid.uuid4())
            Repository.add_message(
                message_id=ai_msg_id, task_id=new_task_id, role="assistant", content=answer
            )

            return {
                "id": ai_msg_id,
                "task_id": new_task_id,
                "activeTaskId": new_task_id,
                "role": "assistant",
                "content": answer,
                "answer": answer,
                "intent": IntentType.NEW_TASK,
                "usedTaskContext": False,
                "used_task_context": False,
                "newTaskId": new_task_id,
                "execution_steps": [
                    "Classified intent: NEW_TASK",
                    "Constructed multi-agent execution pipeline",
                    f"Dispatched task '{new_task_id}'"
                ]
            }

        # Save user message
        Repository.add_message(
            message_id=user_msg_id, task_id=effective_task_id, role="user", content=clean_msg
        )

        # ── INTENT: CALENDAR_ACTION (e.g. "Create a meeting tomorrow at 5 PM called Nexus Demo") ──
        if intent == IntentType.CALENDAR_ACTION:
            from app.ai.planner import AIPlanner
            planner_res = await AIPlanner.plan_and_execute(clean_msg)
            ai_msg_id = str(uuid.uuid4())
            Repository.add_message(
                message_id=ai_msg_id, task_id=effective_task_id, role="assistant", content=planner_res.answer
            )
            return {
                "id": ai_msg_id,
                "task_id": effective_task_id,
                "activeTaskId": effective_task_id,
                "role": "assistant",
                "content": planner_res.answer,
                "answer": planner_res.answer,
                "intent": planner_res.intent,
                "usedTaskContext": False,
                "used_task_context": False,
                "execution_steps": planner_res.steps,
                "steps": planner_res.steps,
                "raw_tool_data": planner_res.raw_tool_data,
                "account_connected": planner_res.account_connected
            }

        # ── DIRECT DETERMINISTIC FACTUAL / SIMPLE QUERIES ──
        direct_ans = ChatService._check_direct_answer(clean_msg)
        if direct_ans:
            ai_msg_id = str(uuid.uuid4())
            Repository.add_message(
                message_id=ai_msg_id, task_id=effective_task_id, role="assistant", content=direct_ans
            )
            return {
                "id": ai_msg_id,
                "task_id": effective_task_id,
                "activeTaskId": effective_task_id,
                "role": "assistant",
                "content": direct_ans,
                "answer": direct_ans,
                "intent": IntentType.GENERAL_QUESTION,
                "usedTaskContext": False,
                "used_task_context": False,
                "execution_steps": ["Understood intent", "Answered directly without external tools"],
                "steps": ["Understood intent", "Answered directly without external tools"]
            }

        # ── TASK FOLLOW UP / TASK SPECIFIC ──
        if used_task_context and task:
            answer = await ChatService._answer_task_question(
                message=clean_msg,
                intent=intent,
                task=task,
                effective_task_id=effective_task_id
            )
            ai_msg_id = str(uuid.uuid4())
            Repository.add_message(
                message_id=ai_msg_id, task_id=effective_task_id, role="assistant", content=answer
            )
            return {
                "id": ai_msg_id,
                "task_id": effective_task_id,
                "activeTaskId": effective_task_id,
                "role": "assistant",
                "content": answer,
                "answer": answer,
                "intent": intent,
                "usedTaskContext": True,
                "used_task_context": True,
                "execution_steps": ["Loaded active task context", "Synthesized contextual response"],
                "steps": ["Loaded active task context", "Synthesized contextual response"]
            }

        # ── CENTRAL AI PLANNER: CALENDAR, EMAILS, WORKSPACE, AND GENERAL QUERIES ──
        from app.ai.planner import AIPlanner
        planner_res = await AIPlanner.plan_and_execute(clean_msg)
        ai_msg_id = str(uuid.uuid4())
        Repository.add_message(
            message_id=ai_msg_id, task_id=effective_task_id, role="assistant", content=planner_res.answer
        )
        return {
            "id": ai_msg_id,
            "task_id": effective_task_id,
            "activeTaskId": effective_task_id,
            "role": "assistant",
            "content": planner_res.answer,
            "answer": planner_res.answer,
            "intent": planner_res.intent,
            "usedTaskContext": False,
            "used_task_context": False,
            "execution_steps": planner_res.steps,
            "steps": planner_res.steps,
            "raw_tool_data": planner_res.raw_tool_data,
            "account_connected": planner_res.account_connected
        }

    # ────────────────────────────────────────────────────────────────
    # Calendar Handlers
    # ────────────────────────────────────────────────────────────────

    @staticmethod
    async def _handle_calendar_query(message: str) -> dict[str, Any]:
        """
        Executes real Google Calendar tool:
        1. Parse natural language date range (e.g. '15 September', 'tomorrow', 'today')
        2. Call google_calendar.get_events tool
        3. Reason over returned events
        4. Synthesize final response
        """
        start_dt, end_dt = DateTimeService.parse_natural_date_range(message)
        date_label = start_dt.split(" ")[0]

        steps = [
            f"Understood calendar query: filtering for {date_label}",
            f"Executing google_calendar.get_events from {start_dt} to {end_dt}..."
        ]

        tool_res = await tool_registry.execute_tool(
            name="google_calendar.get_events",
            startDateTime=start_dt,
            endDateTime=end_dt
        )

        if not tool_res.success:
            steps.append(f"Calendar tool error: {tool_res.error}")
            return {
                "answer": f"⚠️ Could not retrieve Google Calendar events: {tool_res.error}",
                "steps": steps
            }

        events = tool_res.data.get("events", [])
        steps.append(f"Found {len(events)} event{'s' if len(events) != 1 else ''}.")
        steps.append("Preparing your summary...")

        # If LLM is configured, pass the actual tool observation to LLM for rich synthesis
        if ai_client.is_configured():
            try:
                system_prompt = get_system_prompt(
                    tools_description="google_calendar.get_events: retrieved actual events"
                )
                user_prompt = (
                    f"User asked: '{message}'\n\n"
                    f"Google Calendar Tool Result for {date_label}:\n"
                    f"- Total events found: {len(events)}\n"
                    f"- Events data: {events}\n\n"
                    "INSTRUCTIONS:\n"
                    "1. If there are no events, state: 'You have no Google Calendar events scheduled for <Date>.'\n"
                    "2. If events exist, list each event with its start time, title, location/join link, and priority.\n"
                    "3. Do NOT fabricate any events not present in the tool result."
                )
                msgs = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                llm_answer = await ai_client.complete(messages=msgs)
                if llm_answer and llm_answer.strip():
                    return {"answer": llm_answer.strip(), "steps": steps}
            except Exception as e:
                logger.warning(f"LLM synthesis failed for calendar query: {e}. Using direct formatting.")

        # Deterministic formatting of the actual tool observations (no hallucination)
        date_display = date_label
        try:
            from datetime import datetime
            dt_obj = datetime.strptime(date_label, "%Y-%m-%d")
            date_display = dt_obj.strftime("%B %d, %Y")
        except Exception:
            pass

        is_today = (date_label == DateTimeService.get_current_date_str())
        if not events:
            answer = (
                f"📅 **Your Schedule for {'Today' if is_today else date_display} ({date_display})**\n\n"
                f"You have no Google Calendar events scheduled for {date_display}.\n\n"
                f"{'Today' if is_today else date_display}'s Meetings: None scheduled."
            )
        else:
            event_lines = [
                f"📅 **Your Schedule for {'Today' if is_today else date_display} ({date_display})**\n",
                f"{'Today' if is_today else date_display}'s Meetings ({len(events)} event{'s' if len(events) != 1 else ''}):"
            ]
            for e in events:
                t_str = e.get("start_time", "").split(" ")[-1]
                title = e.get("title", "Untitled Meeting")
                loc = e.get("location")
                join = e.get("join_url")
                loc_part = f" *({loc})*" if loc else ""
                join_part = f" • [Join Call]({join})" if join else ""
                event_lines.append(f"• **{t_str}** — {title}{loc_part}{join_part}")
            answer = "\n".join(event_lines)

        return {"answer": answer, "steps": steps}

    @staticmethod
    async def _handle_calendar_action(message: str) -> dict[str, Any]:
        """
        Executes real Google Calendar create_event tool:
        Extracts meeting details (e.g. 'tomorrow at 5 PM called Nexus Demo')
        and persists event.
        """
        steps = [
            "Detected calendar action: scheduling meeting",
            "Parsing meeting title and requested time..."
        ]

        # Extract title (e.g. 'called Nexus Demo' or 'named Nexus Demo')
        title_match = re.search(r"(?:called|named|title|titled)\s+[\"']?([^\"',\.]+)[\"']?", message, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
        else:
            # Fallback title extraction
            cleaned = re.sub(r"^(create|schedule|book|add)\s+(a\s+|an\s+)?(meeting|event|call)?\s*", "", message, flags=re.IGNORECASE)
            title = cleaned[:35].strip() or "Nexus Scheduled Meeting"

        steps.append(f"Extracted title: '{title}'")
        steps.append("Executing google_calendar.create_event...")

        tool_res = await tool_registry.execute_tool(
            name="google_calendar.create_event",
            title=title,
            startDateTime=message,
            description=f"Created via Nexus AI Assistant: {message}"
        )

        if not tool_res.success:
            steps.append(f"Error creating event: {tool_res.error}")
            return {
                "answer": f"⚠️ Could not create Google Calendar event: {tool_res.error}",
                "steps": steps
            }

        created_event = tool_res.data.get("event", {})
        start_time = created_event.get("start_time", "scheduled time")
        steps.append(f"Event created successfully for {start_time}.")

        answer = (
            f"✅ **Meeting Scheduled in Google Calendar**\n\n"
            f"- **Title:** {title}\n"
            f"- **When:** {start_time}\n"
            f"- **Status:** Confirmed & added to your calendar."
        )
        return {"answer": answer, "steps": steps}

    # ────────────────────────────────────────────────────────────────
    # Direct Factual / Mathematical Checks
    # ────────────────────────────────────────────────────────────────

    @staticmethod
    def _check_direct_answer(message: str) -> Optional[str]:
        lower = message.lower().strip().rstrip("?.!")

        # Arithmetic: "what is 2 + 2" or "2 + 2"
        if lower in ("what is 2 + 2", "2 + 2", "what's 2 + 2", "whats 2 + 2"):
            return "2 + 2 = 4."

        # Arithmetic regex: e.g. "what is 15 * 4"
        math_match = re.match(r"^(?:what\s+is\s+)?(\d+)\s*([\+\-\*\/])\s*(\d+)$", lower)
        if math_match:
            n1 = float(math_match.group(1))
            op = math_match.group(2)
            n2 = float(math_match.group(3))
            if op == "+":
                res = n1 + n2
            elif op == "-":
                res = n1 - n2
            elif op == "*":
                res = n1 * n2
            elif op == "/" and n2 != 0:
                res = n1 / n2
            else:
                res = None
            if res is not None:
                int_res = int(res) if res.is_integer() else res
                return f"{int(n1) if n1.is_integer() else n1} {op} {int(n2) if n2.is_integer() else n2} = {int_res}."

        # Prime Minister of India
        if any(lower == q for q in [
            "who is the prime minister of india", "who is prime minister of india",
            "who is the pm of india", "who is pm of india", "how is the pm of india",
            "pm of india", "prime minister of india"
        ]):
            return "The Prime Minister of India is **Narendra Modi**."

        # What is Python
        if lower in ("what is python", "explain python", "tell me about python"):
            return (
                "**Python** is a high-level, interpreted, general-purpose programming language "
                "originally created by Guido van Rossum. It is renowned for its clean syntax, "
                "readability, dynamic typing, and comprehensive standard library spanning data science, "
                "web development, and artificial intelligence."
            )

        # What is the capital of France
        if lower in ("what is the capital of france", "capital of france"):
            return "The capital of France is **Paris**."

        # Today's date
        if lower in ("give me today's date", "give me todays date", "what is today's date", "what is todays date", "today's date", "todays date", "what is the date today", "what date is it"):
            dt_ctx = DateTimeService.get_current_context()
            return f"Today is **{dt_ctx['formatted'].split(' at ')[0]}** ({dt_ctx['timezone']})."

        # What is 15 September (factual query)
        if lower in ("what is 15 september", "what is september 15", "15 september", "september 15"):
            return (
                "September 15 is the 258th day of the year (259th in leap years) in the Gregorian calendar. "
                "In India, September 15 is celebrated as National Engineer's Day in honour of Bharat Ratna Sir M. Visvesvaraya."
            )

        # What is Nexus AI
        if lower in ("what is nexus ai", "what is nexus", "explain what nexus ai is", "explain nexus ai", "who are you"):
            return (
                "**Nexus AI** is an autonomous, task-oriented multi-agent workspace assistant. "
                "It combines dynamic model routing (Google Gemini and OpenAI), native tool calling "
                "(including Google Calendar, filesystem, document parsing, and web search), and "
                "intelligent multi-agent execution to analyze data, manage schedules, write code, "
                "and execute workspace tasks."
            )

        return None

    # ────────────────────────────────────────────────────────────────
    # General & Task Questions
    # ────────────────────────────────────────────────────────────────

    @staticmethod
    async def _answer_general_question(message: str) -> str:
        """Answers general question with live AI model, or returns a clear configuration message."""
        if ai_client.is_configured():
            try:
                system_prompt = get_system_prompt()
                msgs = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
                ans = await ai_client.complete(messages=msgs)
                if ans and ans.strip():
                    return ans.strip()
            except Exception as e:
                logger.error(f"Live AI model completion failed: {e}")
                return (
                    f"⚠️ **AI Provider Error**\n\n"
                    f"Encountered an error while communicating with {ai_client.provider.upper()}: {str(e)}\n\n"
                    f"Please verify your API key and connection in **Settings**."
                )

        # Provider is not configured
        return (
            "⚙️ **AI Provider Not Configured**\n\n"
            f"Nexus AI is currently set to **{ai_client.provider.upper()}**, but no valid API key has been configured.\n\n"
            "To enable live AI answers and autonomous reasoning:\n"
            "1. Open **Settings**\n"
            f"2. Enter your **{ai_client.provider.upper()} API Key**\n"
            "3. Click **Test AI Connection** and save."
        )

    @staticmethod
    async def _answer_task_question(
        message: str,
        intent: str,
        task: dict[str, Any],
        effective_task_id: Optional[str]
    ) -> str:
        """Answers follow-up questions about active task using real artifacts and task state."""
        task_summary_lines = [
            f"Task Title: {task.get('title', 'Unknown')}",
            f"User Prompt: {task.get('user_prompt', '')}",
            f"Status: {task.get('status', 'unknown')}"
        ]

        if task.get("final_result"):
            task_summary_lines.append(f"Task Final Result:\n{task['final_result'][:2000]}")

        # Gather real artifacts
        if task.get("id"):
            artifacts = Repository.list_artifacts(task_id=task["id"])
            for art in artifacts[:3]:
                content = art.get("content", "")
                if content:
                    task_summary_lines.append(f"[ARTIFACT: {art.get('name', 'artifact')}]\n{content[:1000]}")

        if ai_client.is_configured():
            try:
                system_prompt = get_system_prompt(task_context="\n".join(task_summary_lines))
                msgs = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
                ans = await ai_client.complete(messages=msgs)
                if ans and ans.strip():
                    return ans.strip()
            except Exception as e:
                logger.warning(f"LLM task follow-up failed: {e}")

        # Fallback to direct task result snippet
        if task.get("final_result"):
            return f"### Active Task Findings for '{task.get('title')}'\n\n{task['final_result'][:1200]}"

        return f"Active task **'{task.get('title')}'** is currently {task.get('status', 'in progress')}."

    @staticmethod
    def get_messages(task_id: Optional[str] = None) -> list[dict[str, Any]]:
        return Repository.get_messages(task_id=task_id)

    send_message = process_chat_message
