import uuid
import datetime
import re
import os
import glob
import json
import urllib.request
import urllib.error
import subprocess
from typing import Any, Optional
from app.database.connection import db_session
from app.database.repository import Repository

class CalendarService:
    @staticmethod
    def ensure_table():
        with db_session() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    location TEXT,
                    description TEXT,
                    category TEXT DEFAULT 'meeting',
                    source TEXT DEFAULT 'local',
                    priority TEXT DEFAULT 'normal',
                    join_url TEXT,
                    is_important INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Dynamic schema migrations for new columns
            cols = [col["name"] for col in conn.execute("PRAGMA table_info(calendar_events)").fetchall()]
            if "priority" not in cols:
                conn.execute("ALTER TABLE calendar_events ADD COLUMN priority TEXT DEFAULT 'normal'")
            if "join_url" not in cols:
                conn.execute("ALTER TABLE calendar_events ADD COLUMN join_url TEXT")
            if "is_important" not in cols:
                conn.execute("ALTER TABLE calendar_events ADD COLUMN is_important INTEGER DEFAULT 0")

    @staticmethod
    def evaluate_event_metadata(title: str, description: str = "", location: str = "") -> dict[str, Any]:
        """Detect importance level and extract direct conference join URLs."""
        combined_text = f"{title} {description} {location}".lower()

        # 1. Detect High-Priority / Important Indicators
        high_priority_keywords = [
            "urgent", "critical", "important", "imp", "board", "client", "investor", 
            "demo", "interview", "roadmap", "release", "deadline", "presentation", 
            "pitch", "keynote", "q3", "q4", "revenue", "contract", "decision"
        ]
        medium_priority_keywords = [
            "review", "sync", "triage", "planning", "architecture", "1:1", "standup"
        ]

        priority = "normal"
        is_important = 0

        if any(re.search(r'\b' + re.escape(kw) + r'\b', combined_text) for kw in high_priority_keywords):
            priority = "high"
            is_important = 1
        elif any(re.search(r'\b' + re.escape(kw) + r'\b', combined_text) for kw in medium_priority_keywords):
            priority = "medium"
            is_important = 0

        # 2. Extract Video Conference Links (Google Meet, Zoom, Teams, Webex)
        join_url = None
        platform = "in_person"

        full_raw_text = f"{location} {description} {title}"
        zoom_match = re.search(r'https?://[a-zA-Z0-9.-]*zoom\.us/j/[0-9?=&-_]+', full_raw_text, re.IGNORECASE)
        meet_match = re.search(r'https?://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}', full_raw_text, re.IGNORECASE)
        teams_match = re.search(r'https?://teams\.microsoft\.com/l/meetup-join/[^\s"<>]+', full_raw_text, re.IGNORECASE)
        webex_match = re.search(r'https?://[a-zA-Z0-9.-]*webex\.com/[^\s"<>]+', full_raw_text, re.IGNORECASE)

        if meet_match:
            join_url = meet_match.group(0)
            platform = "google_meet"
        elif zoom_match:
            join_url = zoom_match.group(0)
            platform = "zoom"
        elif teams_match:
            join_url = teams_match.group(0)
            platform = "teams"
        elif webex_match:
            join_url = webex_match.group(0)
            platform = "webex"
        elif "teams" in combined_text:
            platform = "teams"
        elif "zoom" in combined_text:
            platform = "zoom"
        elif "meet" in combined_text or "google" in combined_text:
            platform = "google_meet"

        return {
            "priority": priority,
            "is_important": is_important,
            "join_url": join_url,
            "platform": platform
        }

    @staticmethod
    def seed_default_events():
        """Ensure table exists and purge any obsolete demo/sample events."""
        CalendarService.ensure_table()
        # Clean up any legacy sample events
        CalendarService.clear_sample_events()

    @staticmethod
    def get_today_schedule() -> dict[str, Any]:
        CalendarService.seed_default_events()
        now = datetime.datetime.now()
        today_date = now.strftime("%Y-%m-%d")

        # 1. Fetch verified meetings for today
        raw_meetings = Repository.get_today_meetings(today_date)
        
        # Enrich and format meetings
        formatted_meetings = []
        for m in raw_meetings:
            e = dict(m)
            meta = CalendarService.evaluate_event_metadata(
                e.get("title", ""), e.get("description", "") or "", e.get("location", "") or ""
            )
            if not e.get("platform"):
                e["platform"] = meta["platform"]
            if not e.get("join_url") and meta["join_url"]:
                e["join_url"] = meta["join_url"]
            if not e.get("priority"):
                e["priority"] = meta["priority"]

            # Calculate duration string e.g. "30 mins", "1 hour"
            s_time = e.get("start_time", "")
            e_time = e.get("end_time", "")
            duration_str = "30 mins"
            if s_time and e_time:
                try:
                    dt1 = datetime.datetime.strptime(s_time[:19], "%Y-%m-%d %H:%M:%S")
                    dt2 = datetime.datetime.strptime(e_time[:19], "%Y-%m-%d %H:%M:%S")
                    diff_mins = int((dt2 - dt1).total_seconds() // 60)
                    if diff_mins > 0:
                        if diff_mins < 60:
                            duration_str = f"{diff_mins} mins"
                        elif diff_mins % 60 == 0:
                            duration_str = f"{diff_mins // 60} hour{'s' if diff_mins // 60 != 1 else ''}"
                        else:
                            duration_str = f"{diff_mins // 60}h {diff_mins % 60}m"
                except Exception:
                    pass
            e["duration"] = duration_str

            # Attendees count & list
            raw_att = e.get("attendees")
            attendees_list = []
            if raw_att:
                try:
                    attendees_list = json.loads(raw_att) if isinstance(raw_att, str) else raw_att
                except Exception:
                    pass
            e["attendees_count"] = len(attendees_list)
            e["attendees_list"] = attendees_list

            formatted_meetings.append(e)

        # 2. Next upcoming meeting
        next_meeting = None
        for m in formatted_meetings:
            start_dt_str = m["start_time"]
            try:
                start_dt = datetime.datetime.strptime(start_dt_str[:19], "%Y-%m-%d %H:%M:%S")
                if start_dt >= (now - datetime.timedelta(minutes=5)):
                    diff_mins = int((start_dt - now).total_seconds() // 60)
                    m_copy = dict(m)
                    m_copy["starts_in_minutes"] = diff_mins
                    next_meeting = m_copy
                    break
            except Exception:
                pass

        # 3. Overview metrics
        upcoming_meetings = Repository.get_upcoming_meetings(now.strftime("%Y-%m-%d %H:%M:%S"), limit=50)
        conflicts = Repository.get_calendar_conflicts()
        unread_emails = Repository.get_unread_emails_count()
        important_emails = Repository.get_important_emails(limit=5)

        with db_session() as conn:
            task_row = conn.execute("SELECT COUNT(*) as cnt FROM tasks WHERE status IN ('pending', 'running')").fetchone()
            active_tasks = task_row["cnt"] if task_row else 0

        # Contextual greeting based on hour in Asia/Kolkata
        hour = now.hour
        if hour < 12:
            greeting = "GOOD MORNING"
        elif hour < 17:
            greeting = "GOOD AFTERNOON"
        else:
            greeting = "GOOD EVENING"

        return {
            "date": today_date,
            "day_of_week": now.strftime("%A"),
            "current_time": now.strftime("%I:%M %p"),
            "greeting": greeting,
            "total_meetings_today": len(formatted_meetings),
            "meetings_today_count": len(formatted_meetings),
            "unread_important_emails_count": unread_emails,
            "upcoming_meetings_count": len(upcoming_meetings),
            "tasks_count": active_tasks,
            "calendar_conflicts_count": len(conflicts),
            "meetings": formatted_meetings,
            "upcoming_meetings": upcoming_meetings[:5],
            "conflicts": conflicts,
            "important_emails": important_emails,
            "work_tasks": [],
            "next_meeting": next_meeting
        }

    @staticmethod
    def get_upcoming_meetings(days: int = 365) -> list[dict[str, Any]]:
        CalendarService.seed_default_events()
        now = datetime.datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        end_date = (now + datetime.timedelta(days=days)).strftime("%Y-%m-%d 23:59:59")

        with db_session() as conn:
            rows = conn.execute("""
                SELECT * FROM calendar_events 
                WHERE start_time >= ? AND start_time <= ? AND category = 'meeting'
                ORDER BY start_time ASC
                LIMIT 50
            """, (now_str, end_date)).fetchall()

            events = [dict(r) for r in rows]

        for e in events:
            meta = CalendarService.evaluate_event_metadata(
                e.get("title", ""), e.get("description", "") or "", e.get("location", "") or ""
            )
            e["platform"] = meta["platform"]
            if not e.get("join_url") and meta["join_url"]:
                e["join_url"] = meta["join_url"]
            if not e.get("priority"):
                e["priority"] = meta["priority"]
            if e.get("is_important") is None:
                e["is_important"] = meta["is_important"]

        return events

    @staticmethod
    def clear_sample_events() -> int:
        """Remove demo/sample events so only the user's real connected calendar events remain."""
        CalendarService.ensure_table()
        with db_session() as conn:
            # Delete default seed events
            deleted = conn.execute("""
                DELETE FROM calendar_events 
                WHERE source IN ('sample', 'demo') 
                   OR title IN (
                       'Daily Engineering Sync & Sprint Standup',
                       'URGENT: Client Architecture & Cloud Integration Review',
                       'Client Architecture & Cloud Integration Review',
                       'Q3 Enterprise Strategy & Revenue Debrief',
                       'Deliverable: Complete database query optimization audit',
                       'Deliverable: Review and approve pull request #42',
                       'IMPORTANT: Product Roadmap & AI Agent Demo Session',
                       'Product Roadmap & AI Agent Demo Session',
                       'Cybersecurity & Data Governance Alignment'
                   )
            """).rowcount
            return deleted


    @staticmethod
    def import_ics_content(ics_text: str, source_name: str = "ics") -> int:
        """Parse standard iCalendar .ics format and insert events into SQLite with priority tagging."""
        CalendarService.ensure_table()
        lines = ics_text.splitlines()
        imported = 0
        current_event = None

        with db_session() as conn:
            for raw_line in lines:
                line = raw_line.strip()
                if line == "BEGIN:VEVENT":
                    current_event = {"id": str(uuid.uuid4()), "source": source_name, "category": "meeting"}
                elif line == "END:VEVENT" and current_event:
                    if current_event.get("title") and current_event.get("start_time"):
                        if not current_event.get("end_time"):
                            current_event["end_time"] = current_event["start_time"]
                        
                        meta = CalendarService.evaluate_event_metadata(
                            current_event.get("title", ""),
                            current_event.get("description", ""),
                            current_event.get("location", "")
                        )

                        conn.execute("""
                            INSERT INTO calendar_events (id, title, start_time, end_time, location, description, category, source, priority, join_url, is_important)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            current_event["id"],
                            current_event.get("title", "Meeting"),
                            current_event.get("start_time"),
                            current_event.get("end_time"),
                            current_event.get("location", ""),
                            current_event.get("description", ""),
                            current_event.get("category", "meeting"),
                            current_event.get("source", source_name),
                            meta["priority"],
                            meta["join_url"],
                            meta["is_important"]
                        ))
                        imported += 1
                    current_event = None
                elif current_event is not None:
                    if line.startswith("SUMMARY:"):
                        current_event["title"] = line[8:].strip()
                    elif line.startswith("LOCATION:"):
                        current_event["location"] = line[9:].strip()
                    elif line.startswith("DESCRIPTION:"):
                        current_event["description"] = line[12:].strip()
                    elif line.startswith("DTSTART"):
                        val = line.split(":")[-1].strip()
                        if len(val) >= 8:
                            formatted = f"{val[0:4]}-{val[4:6]}-{val[6:8]}"
                            if "T" in val and len(val) >= 15:
                                formatted += f" {val[9:11]}:{val[11:13]}:{val[13:15]}"
                            else:
                                formatted += " 09:00:00"
                            current_event["start_time"] = formatted
                    elif line.startswith("DTEND"):
                        val = line.split(":")[-1].strip()
                        if len(val) >= 8:
                            formatted = f"{val[0:4]}-{val[4:6]}-{val[6:8]}"
                            if "T" in val and len(val) >= 15:
                                formatted += f" {val[9:11]}:{val[11:13]}:{val[13:15]}"
                            else:
                                formatted += " 10:00:00"
                            current_event["end_time"] = formatted

        return imported

    @staticmethod
    def sync_ics_url(url: str, source_name: str = "google_calendar") -> dict[str, Any]:
        """Fetch and sync calendar from a public/private iCal URL (Google Calendar / Outlook Web)."""
        normalized_url = url.strip()
        if normalized_url.startswith("webcal://"):
            normalized_url = "https://" + normalized_url[9:]
        elif not (normalized_url.startswith("http://") or normalized_url.startswith("https://")):
            normalized_url = "https://" + normalized_url

        try:
            req = urllib.request.Request(
                normalized_url,
                headers={"User-Agent": "NEXUS-AI/1.0 (Windows NT 10.0; Win64; x64) Desktop/Agent"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode("utf-8", errors="ignore")
                count = CalendarService.import_ics_content(content, source_name=source_name)
                return {
                    "success": True,
                    "count": count,
                    "message": f"Successfully synchronized {count} events from {source_name}"
                }
        except Exception as e:
            return {
                "success": False,
                "count": 0,
                "error": f"Failed to sync calendar from URL: {str(e)}"
            }

    @staticmethod
    def scan_local_pc_calendars() -> dict[str, Any]:
        """Scan standard PC directories (Downloads, Documents, Desktop, Outlook) for .ics files."""
        CalendarService.ensure_table()
        user_home = os.path.expanduser("~")
        search_dirs = [
            os.path.join(user_home, "Downloads"),
            os.path.join(user_home, "Documents"),
            os.path.join(user_home, "Desktop"),
            os.path.join(user_home, "AppData", "Local", "Microsoft", "Outlook")
        ]

        found_files: list[str] = []
        total_imported = 0

        for sdir in search_dirs:
            if os.path.isdir(sdir):
                ics_pattern = os.path.join(sdir, "*.ics")
                for fpath in glob.glob(ics_pattern):
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            cnt = CalendarService.import_ics_content(f.read(), source_name="local_pc_file")
                            found_files.append(os.path.basename(fpath))
                            total_imported += cnt
                    except Exception:
                        pass

        # Also query Windows Outlook COM if available
        outlook_count = CalendarService.query_windows_outlook()
        total_imported += outlook_count

        return {
            "success": True,
            "found_files": found_files,
            "imported_events": total_imported,
            "outlook_synced": outlook_count > 0
        }

    @staticmethod
    def query_windows_outlook() -> int:
        """Query Microsoft Outlook desktop application on Windows via PowerShell MAPI script."""
        if os.name != "nt":
            return 0

        ps_script = """
        $ErrorActionPreference = 'SilentlyContinue'
        try {
            $outlook = New-Object -ComObject Outlook.Application
            if (-not $outlook) { exit 0 }
            $ns = $outlook.GetNamespace("MAPI")
            $calendar = $ns.GetDefaultFolder(9) # 9 = olFolderCalendar
            $items = $calendar.Items
            $items.IncludeRecurrences = $true
            $items.Sort("[Start]")
            $start = (Get-Date).ToString("yyyy-MM-dd 00:00:00")
            $end = (Get-Date).AddDays(7).ToString("yyyy-MM-dd 23:59:59")
            $filtered = $items.Restrict("[Start] >= '$start' and [Start] <= '$end'")
            
            $results = @()
            foreach ($item in $filtered) {
                $results += @{
                    title = $item.Subject
                    start = $item.Start.ToString("yyyy-MM-dd HH:mm:ss")
                    end = $item.End.ToString("yyyy-MM-dd HH:mm:ss")
                    location = $item.Location
                    body = $item.Body
                }
            }
            $results | ConvertTo-Json -Compress
        } catch {
            exit 0
        }
        """
        try:
            res = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=6
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                if isinstance(data, dict):
                    data = [data]
                imported = 0
                with db_session() as conn:
                    for item in data:
                        title = item.get("title")
                        start = item.get("start")
                        end = item.get("end") or start
                        if title and start:
                            meta = CalendarService.evaluate_event_metadata(
                                title, item.get("body", "") or "", item.get("location", "") or ""
                            )
                            conn.execute("""
                                INSERT INTO calendar_events (id, title, start_time, end_time, location, description, category, source, priority, join_url, is_important)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                str(uuid.uuid4()),
                                title,
                                start,
                                end,
                                item.get("location", ""),
                                item.get("body", "")[:300] if item.get("body") else "",
                                "meeting",
                                "outlook",
                                meta["priority"],
                                meta["join_url"],
                                meta["is_important"]
                            ))
                            imported += 1
                return imported
        except Exception:
            return 0
        return 0

    @staticmethod
    def get_connectors_status() -> dict[str, Any]:
        """Return connectivity health and indexed counts across Outlook, Google Calendar, and Local PC."""
        CalendarService.seed_default_events()
        with db_session() as conn:
            rows = conn.execute("""
                SELECT source, COUNT(*) as cnt FROM calendar_events GROUP BY source
            """).fetchall()

            counts = {r["source"]: r["cnt"] for r in rows}

        outlook_cnt = counts.get("outlook", 0)
        google_cnt = counts.get("google_calendar", 0) + counts.get("google", 0)
        local_cnt = counts.get("local", 0) + counts.get("ics", 0) + counts.get("local_pc_file", 0)
        github_cnt = counts.get("github", 0)

        db_settings = Repository.get_all_settings()
        gh_token = db_settings.get("github_token", "")
        gh_user = db_settings.get("github_username", "")
        gh_connected = bool(gh_token or github_cnt > 0)

        g_acc = Repository.get_connected_account_by_provider("google")
        g_tokens = Repository.get_oauth_tokens_by_provider("google") if g_acc else None
        gmail_connected = bool(g_acc and g_acc.get("status") == "connected" and g_tokens and g_tokens.get("access_token"))

        return {
            "outlook": {
                "name": "Microsoft Outlook",
                "connected": True if outlook_cnt > 0 else False,
                "events_count": outlook_cnt,
                "type": "Desktop Application / COM",
                "status": "Active" if outlook_cnt > 0 else "Ready"
            },
            "google_calendar": {
                "name": "Google Calendar",
                "connected": True if google_cnt > 0 else False,
                "events_count": google_cnt,
                "type": "iCal / Web Feed Sync",
                "status": "Active" if google_cnt > 0 else "Ready"
            },
            "gmail": {
                "name": "Google Gmail",
                "connected": gmail_connected,
                "events_count": 0,
                "type": "Google Cloud OAuth 2.0 / Gmail API",
                "status": f"Connected ({g_acc.get('account_email')})" if (gmail_connected and g_acc) else "Ready"
            },
            "github": {
                "name": "GitHub Workspace",
                "connected": gh_connected,
                "events_count": github_cnt,
                "type": "REST API v3 / Pull Requests & Issues",
                "status": f"Active (@{gh_user})" if (gh_connected and gh_user) else ("Active" if gh_connected else "Ready")
            },
            "local_pc": {
                "name": "Local PC Agenda & Files",
                "connected": True,
                "events_count": local_cnt,
                "type": "SQLite / Local .ICS Scanner",
                "status": "Indexed"
            }
        }

    @staticmethod
    def get_events(
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None,
        calendar_id: Optional[str] = None,
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """Retrieve calendar events within a specified datetime window."""
        CalendarService.seed_default_events()
        with db_session() as conn:
            query = "SELECT * FROM calendar_events WHERE 1=1"
            params = []

            if start_datetime and end_datetime:
                query += " AND ((start_time >= ? AND start_time <= ?) OR (date(start_time) >= date(?) AND date(start_time) <= date(?)))"
                params.extend([start_datetime, end_datetime, start_datetime, end_datetime])
            elif start_datetime:
                query += " AND (start_time >= ? OR date(start_time) >= date(?))"
                params.extend([start_datetime, start_datetime])
            elif end_datetime:
                query += " AND (start_time <= ? OR date(start_time) <= date(?))"
                params.extend([end_datetime, end_datetime])

            if calendar_id and calendar_id.lower() not in ("primary", "all", "default"):
                query += " AND source = ?"
                params.append(calendar_id)

            query += " ORDER BY start_time ASC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            events = [dict(r) for r in rows]

        for e in events:
            meta = CalendarService.evaluate_event_metadata(
                e.get("title", ""), e.get("description", "") or "", e.get("location", "") or ""
            )
            e["platform"] = meta["platform"]
            if not e.get("join_url") and meta["join_url"]:
                e["join_url"] = meta["join_url"]
            if not e.get("priority"):
                e["priority"] = meta["priority"]
            if e.get("is_important") is None:
                e["is_important"] = meta["is_important"]

        return events

    @staticmethod
    def get_event_by_id(event_id: str) -> Optional[dict[str, Any]]:
        CalendarService.ensure_table()
        with db_session() as conn:
            row = conn.execute("SELECT * FROM calendar_events WHERE id = ?", (event_id,)).fetchone()
            if not row:
                return None
            e = dict(row)
            meta = CalendarService.evaluate_event_metadata(
                e.get("title", ""), e.get("description", "") or "", e.get("location", "") or ""
            )
            e["platform"] = meta["platform"]
            if not e.get("join_url") and meta["join_url"]:
                e["join_url"] = meta["join_url"]
            return e

    @staticmethod
    async def create_event_async(
        title: str,
        start_time: str,
        end_time: Optional[str] = None,
        location: str = "",
        description: str = "",
        category: str = "meeting",
        source: str = "google_calendar"
    ) -> dict[str, Any]:
        """Create a real event in Google Calendar / Outlook and persist in SQLite repository."""
        CalendarService.ensure_table()
        from app.services.oauth.google_oauth import GoogleOAuthService
        from app.services.oauth.microsoft_oauth import MicrosoftOAuthService

        actual_end = end_time or start_time
        meta = CalendarService.evaluate_event_metadata(title, description, location)
        
        provider_event_id = None
        event_id = str(uuid.uuid4())
        join_url = meta.get("join_url")
        platform = meta.get("platform", "none")

        # Check connected providers
        google_acc = Repository.get_connected_account_by_provider("google")
        ms_acc = Repository.get_connected_account_by_provider("microsoft")

        if google_acc and source in ("google", "google_calendar", "local"):
            event_payload = {
                "title": title,
                "start_time": start_time,
                "end_time": actual_end,
                "location": location,
                "description": description,
                "add_meet": True
            }
            g_item = await GoogleOAuthService.create_calendar_event(event_payload)
            if g_item:
                provider_event_id = g_item.get("id")
                event_id = f"gcal_{provider_event_id}"
                source = "google"
                if g_item.get("hangoutLink"):
                    join_url = g_item.get("hangoutLink")
                    platform = "google_meet"
        elif ms_acc and source in ("outlook", "microsoft"):
            ms_item = await MicrosoftOAuthService.create_calendar_event({
                "title": title,
                "start_time": start_time,
                "end_time": actual_end,
                "location": location,
                "description": description
            })
            if ms_item:
                provider_event_id = ms_item.get("id")
                event_id = f"ms_{provider_event_id}"
                source = "outlook"
                if ms_item.get("onlineMeetingUrl"):
                    join_url = ms_item.get("onlineMeetingUrl")
                    platform = "teams"

        with db_session() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO calendar_events (
                    id, provider_event_id, title, start_time, end_time, location, 
                    description, category, source, priority, join_url, is_important, 
                    platform, status, ownership_role
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                provider_event_id,
                title,
                start_time,
                actual_end,
                location,
                description,
                category,
                source,
                meta["priority"],
                join_url,
                meta["is_important"],
                platform,
                "MY_MEETING",
                "organizer"
            ))

        return CalendarService.get_event_by_id(event_id)

    @staticmethod
    def create_event(
        title: str,
        start_time: str,
        end_time: Optional[str] = None,
        location: str = "",
        description: str = "",
        category: str = "meeting",
        source: str = "google_calendar"
    ) -> dict[str, Any]:
        """Synchronous create_event wrapper."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.create_task(CalendarService.create_event_async(
                title=title, start_time=start_time, end_time=end_time,
                location=location, description=description, category=category, source=source
            ))
            CalendarService.ensure_table()
            event_id = str(uuid.uuid4())
            actual_end = end_time or start_time
            meta = CalendarService.evaluate_event_metadata(title, description, location)
            with db_session() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO calendar_events (id, title, start_time, end_time, location, description, category, source, priority, join_url, is_important)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (event_id, title, start_time, actual_end, location, description, category, source, meta["priority"], meta["join_url"], meta["is_important"]))
            return CalendarService.get_event_by_id(event_id)
        else:
            return asyncio.run(CalendarService.create_event_async(
                title=title, start_time=start_time, end_time=end_time,
                location=location, description=description, category=category, source=source
            ))

    @staticmethod
    async def update_event_async(event_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        CalendarService.ensure_table()
        from app.services.oauth.google_oauth import GoogleOAuthService
        from app.services.oauth.microsoft_oauth import MicrosoftOAuthService

        # 1. Locate the existing event in SQLite
        existing = CalendarService.get_event_by_id(event_id)
        if not existing:
            # Try fuzzy search by title
            with db_session() as conn:
                row = conn.execute("SELECT * FROM calendar_events WHERE LOWER(title) LIKE ? LIMIT 1", (f"%{event_id.lower()}%",)).fetchone()
                if row:
                    existing = dict(row)

        if not existing:
            return None

        actual_id = existing.get("id")
        provider_event_id = existing.get("provider_event_id") or actual_id
        source = existing.get("source") or "google"

        # 2. Update remote Google Calendar if source is Google or Google is connected
        google_acc = Repository.get_connected_account_by_provider("google")
        if google_acc and (source in ("google", "google_calendar") or str(provider_event_id).startswith("gcal_") or not str(provider_event_id).startswith("ms_")):
            clean_g_id = provider_event_id
            if str(clean_g_id).startswith("gcal_"):
                clean_g_id = clean_g_id[5:]
            try:
                g_res = await GoogleOAuthService.update_calendar_event(clean_g_id, updates)
                if g_res:
                    # Update join_url / platform if Google Meet link was created or updated
                    if g_res.get("hangoutLink"):
                        updates["join_url"] = g_res.get("hangoutLink")
                        updates["platform"] = "google_meet"
            except Exception as e:
                pass

        # 3. Update Microsoft Graph if source is Outlook or Microsoft is connected
        ms_acc = Repository.get_connected_account_by_provider("microsoft")
        if ms_acc and (source in ("outlook", "microsoft") or str(provider_event_id).startswith("ms_")):
            clean_ms_id = provider_event_id
            if str(clean_ms_id).startswith("ms_"):
                clean_ms_id = clean_ms_id[3:]
            try:
                await MicrosoftOAuthService.update_calendar_event(clean_ms_id, updates)
            except Exception:
                pass

        # 4. Update local SQLite cache
        allowed = ["title", "start_time", "end_time", "location", "description", "category", "source", "priority", "join_url", "is_important", "status", "ownership_role"]
        set_clauses = []
        params = []
        for k, v in updates.items():
            if k in allowed:
                set_clauses.append(f"{k} = ?")
                params.append(v)

        if set_clauses:
            params.append(actual_id)
            with db_session() as conn:
                conn.execute(f"UPDATE calendar_events SET {', '.join(set_clauses)} WHERE id = ?", params)

        return CalendarService.get_event_by_id(actual_id)

    @staticmethod
    def update_event(event_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Synchronous update_event wrapper."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.create_task(CalendarService.update_event_async(event_id, updates))
            CalendarService.ensure_table()
            allowed = ["title", "start_time", "end_time", "location", "description", "category", "source", "priority", "join_url", "is_important", "status"]
            set_clauses = []
            params = []
            for k, v in updates.items():
                if k in allowed:
                    set_clauses.append(f"{k} = ?")
                    params.append(v)
            if set_clauses:
                params.append(event_id)
                with db_session() as conn:
                    conn.execute(f"UPDATE calendar_events SET {', '.join(set_clauses)} WHERE id = ?", params)
            return CalendarService.get_event_by_id(event_id)
        else:
            return asyncio.run(CalendarService.update_event_async(event_id, updates))

    @staticmethod
    async def delete_event_async(event_id: str) -> bool:
        CalendarService.ensure_table()
        from app.services.oauth.google_oauth import GoogleOAuthService
        from app.services.oauth.microsoft_oauth import MicrosoftOAuthService

        existing = CalendarService.get_event_by_id(event_id)
        if existing:
            prov_id = existing.get("provider_event_id") or existing.get("id")
            source = existing.get("source")
            if source in ("google", "google_calendar") or str(prov_id).startswith("gcal_"):
                await GoogleOAuthService.delete_calendar_event(prov_id)
            elif source in ("outlook", "microsoft") or str(prov_id).startswith("ms_"):
                await MicrosoftOAuthService.delete_calendar_event(prov_id)

        with db_session() as conn:
            res = conn.execute("DELETE FROM calendar_events WHERE id = ? OR provider_event_id = ?", (event_id, event_id))
            return res.rowcount > 0

    @staticmethod
    def delete_event(event_id: str) -> bool:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            asyncio.create_task(CalendarService.delete_event_async(event_id))
            with db_session() as conn:
                res = conn.execute("DELETE FROM calendar_events WHERE id = ? OR provider_event_id = ?", (event_id, event_id))
                return res.rowcount > 0
        else:
            return asyncio.run(CalendarService.delete_event_async(event_id))

