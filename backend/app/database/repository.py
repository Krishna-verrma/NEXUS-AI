import json
import sqlite3
import uuid
from typing import Any, Optional
from datetime import datetime
from app.database.connection import db_session

class Repository:
    # TASKS
    @staticmethod
    def create_task(task_id: str, title: str, user_prompt: str, complexity: str = "moderate", is_demo: bool = False) -> dict[str, Any]:
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO tasks (id, title, user_prompt, status, complexity, is_demo)
                VALUES (?, ?, ?, 'pending', ?, ?)
                """,
                (task_id, title, user_prompt, complexity, 1 if is_demo else 0)
            )
        return Repository.get_task(task_id)

    @staticmethod
    def get_task(task_id: str) -> Optional[dict[str, Any]]:
        with db_session() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                return None
            task = dict(row)
            task["is_demo"] = bool(task.get("is_demo", 0))
            # Fetch steps
            step_rows = conn.execute(
                "SELECT * FROM task_steps WHERE task_id = ? ORDER BY step_order ASC", (task_id,)
            ).fetchall()
            task["steps"] = [dict(s) for s in step_rows]
            for s in task["steps"]:
                if s.get("input_data") and isinstance(s["input_data"], str):
                    try:
                        s["input_data"] = json.loads(s["input_data"])
                    except Exception:
                        pass
                if s.get("output_data") and isinstance(s["output_data"], str):
                    try:
                        s["output_data"] = json.loads(s["output_data"])
                    except Exception:
                        pass
            return task

    @staticmethod
    def list_tasks(limit: int = 50) -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            tasks = []
            for r in rows:
                t = dict(r)
                t["is_demo"] = bool(t.get("is_demo", 0))
                # Count agents used
                step_cnt = conn.execute("SELECT COUNT(DISTINCT agent_id) as cnt FROM task_steps WHERE task_id = ?", (t["id"],)).fetchone()
                t["agents_count"] = step_cnt["cnt"] if step_cnt else 0
                tasks.append(t)
            return tasks

    @staticmethod
    def update_task_status(task_id: str, status: str, final_result: Optional[str] = None, error_message: Optional[str] = None, duration_seconds: Optional[float] = None) -> None:
        with db_session() as conn:
            updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
            params = [status]
            if final_result is not None:
                updates.append("final_result = ?")
                params.append(final_result)
            if error_message is not None:
                updates.append("error_message = ?")
                params.append(error_message)
            if duration_seconds is not None:
                updates.append("duration_seconds = ?")
                params.append(duration_seconds)
            if status in ("completed", "failed", "cancelled"):
                updates.append("completed_at = CURRENT_TIMESTAMP")
            params.append(task_id)
            conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params)

    # TASK STEPS
    @staticmethod
    def create_step(step_id: str, task_id: str, step_order: int, agent_id: str, agent_name: str, operation: str, input_data: Any = None) -> dict[str, Any]:
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO task_steps (id, task_id, step_order, agent_id, agent_name, status, operation, input_data)
                VALUES (?, ?, ?, ?, ?, 'waiting', ?, ?)
                """,
                (step_id, task_id, step_order, agent_id, agent_name, operation, json.dumps(input_data) if input_data else None)
            )
        return Repository.get_step(step_id)

    @staticmethod
    def get_step(step_id: str) -> Optional[dict[str, Any]]:
        with db_session() as conn:
            row = conn.execute("SELECT * FROM task_steps WHERE id = ?", (step_id,)).fetchone()
            if not row:
                return None
            res = dict(row)
            if res.get("input_data") and isinstance(res["input_data"], str):
                try:
                    res["input_data"] = json.loads(res["input_data"])
                except Exception:
                    pass
            if res.get("output_data") and isinstance(res["output_data"], str):
                try:
                    res["output_data"] = json.loads(res["output_data"])
                except Exception:
                    pass
            return res

    @staticmethod
    def update_step_status(
        step_id: str,
        status: str,
        operation: Optional[str] = None,
        output_data: Any = None,
        error_message: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        retry_count: Optional[int] = None
    ) -> None:
        with db_session() as conn:
            updates = ["status = ?"]
            params: list[Any] = [status]
            if operation is not None:
                updates.append("operation = ?")
                params.append(operation)
            if output_data is not None:
                updates.append("output_data = ?")
                params.append(json.dumps(output_data) if not isinstance(output_data, str) else output_data)
            if error_message is not None:
                updates.append("error_message = ?")
                params.append(error_message)
            if duration_seconds is not None:
                updates.append("duration_seconds = ?")
                params.append(duration_seconds)
            if retry_count is not None:
                updates.append("retry_count = ?")
                params.append(retry_count)
            if status == "running":
                updates.append("start_time = CURRENT_TIMESTAMP")
            elif status in ("completed", "failed"):
                updates.append("end_time = CURRENT_TIMESTAMP")
            params.append(step_id)
            conn.execute(f"UPDATE task_steps SET {', '.join(updates)} WHERE id = ?", params)

    # AGENTS
    @staticmethod
    def list_agents() -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("SELECT * FROM agents ORDER BY is_system DESC, name ASC").fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if item.get("capabilities"):
                    try:
                        item["capabilities"] = json.loads(item["capabilities"])
                    except Exception:
                        item["capabilities"] = []
                results.append(item)
            return results

    @staticmethod
    def toggle_agent(agent_id: str, is_enabled: bool) -> Optional[dict[str, Any]]:
        with db_session() as conn:
            conn.execute("UPDATE agents SET is_enabled = ? WHERE id = ?", (1 if is_enabled else 0, agent_id))
            row = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
            if not row:
                return None
            item = dict(row)
            if item.get("capabilities"):
                item["capabilities"] = json.loads(item["capabilities"])
            return item

    # FILES
    @staticmethod
    def create_file(file_id: str, filename: str, original_name: str, file_type: str, file_size: int, file_path: str, task_id: Optional[str] = None, metadata: Any = None) -> dict[str, Any]:
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO files (id, filename, original_name, file_type, file_size, file_path, task_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (file_id, filename, original_name, file_type, file_size, file_path, task_id, json.dumps(metadata) if metadata else None)
            )
        return Repository.get_file(file_id)

    @staticmethod
    def get_file(file_id: str) -> Optional[dict[str, Any]]:
        with db_session() as conn:
            row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
            if not row:
                return None
            item = dict(row)
            if item.get("metadata"):
                try:
                    item["metadata"] = json.loads(item["metadata"])
                except Exception:
                    pass
            return item

    @staticmethod
    def list_files(task_id: Optional[str] = None) -> list[dict[str, Any]]:
        with db_session() as conn:
            if task_id:
                rows = conn.execute("SELECT * FROM files WHERE task_id = ? ORDER BY created_at DESC", (task_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM files ORDER BY created_at DESC").fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if item.get("metadata"):
                    try:
                        item["metadata"] = json.loads(item["metadata"])
                    except Exception:
                        pass
                results.append(item)
            return results

    @staticmethod
    def delete_file(file_id: str) -> bool:
        with db_session() as conn:
            cur = conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
            return cur.rowcount > 0

    @staticmethod
    def update_file_task(file_id: str, task_id: str) -> None:
        """Link an uploaded file to a specific task."""
        with db_session() as conn:
            conn.execute(
                "UPDATE files SET task_id = ? WHERE id = ?",
                (task_id, file_id)
            )

    # REPORTS
    @staticmethod
    def create_report(
        report_id: str,
        task_id: Optional[str],
        title: str,
        summary: str,
        executive_summary: str,
        methodology: str,
        key_findings: list[str],
        analysis: str,
        risks: list[dict[str, Any]],
        recommendations: list[str],
        conclusion: str,
        full_markdown: str
    ) -> dict[str, Any]:
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO reports (
                    id, task_id, title, summary, executive_summary, methodology,
                    key_findings, analysis, risks, recommendations, conclusion, full_markdown
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id, task_id, title, summary, executive_summary, methodology,
                    json.dumps(key_findings), analysis, json.dumps(risks), json.dumps(recommendations),
                    conclusion, full_markdown
                )
            )
        return Repository.get_report(report_id)

    @staticmethod
    def get_report(report_id: str) -> Optional[dict[str, Any]]:
        with db_session() as conn:
            row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
            if not row:
                return None
            item = dict(row)
            for fld in ("key_findings", "risks", "recommendations"):
                if item.get(fld):
                    try:
                        item[fld] = json.loads(item[fld])
                    except Exception:
                        pass
            return item

    @staticmethod
    def list_reports(limit: int = 50) -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("SELECT * FROM reports ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                for fld in ("key_findings", "risks", "recommendations"):
                    if item.get(fld):
                        try:
                            item[fld] = json.loads(item[fld])
                        except Exception:
                            pass
                results.append(item)
            return results

    @staticmethod
    def update_report_title(report_id: str, new_title: str) -> Optional[dict[str, Any]]:
        with db_session() as conn:
            conn.execute("UPDATE reports SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_title, report_id))
        return Repository.get_report(report_id)

    @staticmethod
    def delete_report(report_id: str) -> bool:
        with db_session() as conn:
            cur = conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
            return cur.rowcount > 0

    # MESSAGES / CHAT
    @staticmethod
    def add_message(message_id: str, task_id: Optional[str], role: str, content: str, metadata: Any = None) -> dict[str, Any]:
        with db_session() as conn:
            conn.execute(
                "INSERT INTO messages (id, task_id, role, content, metadata) VALUES (?, ?, ?, ?, ?)",
                (message_id, task_id, role, content, json.dumps(metadata) if metadata else None)
            )
        return {"id": message_id, "task_id": task_id, "role": role, "content": content}

    @staticmethod
    def get_messages(task_id: Optional[str] = None, limit: int = 100) -> list[dict[str, Any]]:
        with db_session() as conn:
            if task_id:
                rows = conn.execute("SELECT * FROM messages WHERE task_id = ? ORDER BY created_at ASC LIMIT ?", (task_id, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM messages ORDER BY created_at ASC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    # SETTINGS
    @staticmethod
    def get_all_settings() -> dict[str, str]:
        with db_session() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            return {r["key"]: r["value"] for r in rows}

    @staticmethod
    def set_setting(key: str, value: str) -> None:
        with db_session() as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)", (key, value))

    # ARTIFACTS
    @staticmethod
    def create_artifact(
        artifact_id: str,
        task_id: str,
        name: str,
        artifact_type: str,
        content: str,
        path: Optional[str] = None,
        execution_id: Optional[str] = None
    ) -> dict[str, Any]:
        with db_session() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    task_id TEXT,
                    execution_id TEXT,
                    name TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    path TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            try:
                conn.execute(
                    """INSERT OR REPLACE INTO artifacts (id, task_id, execution_id, name, artifact_type, path, content)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (artifact_id, task_id, execution_id, name, artifact_type, path, content)
                )
            except Exception:
                # In case table was pre-created with FK, recreate without FK
                conn.execute("ALTER TABLE artifacts RENAME TO artifacts_old")
                conn.execute("""
                    CREATE TABLE artifacts (
                        id TEXT PRIMARY KEY,
                        task_id TEXT,
                        execution_id TEXT,
                        name TEXT NOT NULL,
                        artifact_type TEXT NOT NULL,
                        path TEXT,
                        content TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("INSERT OR IGNORE INTO artifacts SELECT * FROM artifacts_old")
                conn.execute("DROP TABLE artifacts_old")
                conn.execute(
                    """INSERT OR REPLACE INTO artifacts (id, task_id, execution_id, name, artifact_type, path, content)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (artifact_id, task_id, execution_id, name, artifact_type, path, content)
                )
        return {
            "id": artifact_id,
            "task_id": task_id,
            "execution_id": execution_id,
            "name": name,
            "artifact_type": artifact_type,
            "path": path,
            "content": content
        }

    @staticmethod
    def list_artifacts(task_id: str) -> list[dict[str, Any]]:
        with db_session() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    task_id TEXT,
                    execution_id TEXT,
                    name TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    path TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            rows = conn.execute("SELECT * FROM artifacts WHERE task_id = ? ORDER BY created_at ASC", (task_id,)).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_artifact_by_name(task_id: str, name: str) -> Optional[dict[str, Any]]:
        with db_session() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    task_id TEXT,
                    execution_id TEXT,
                    name TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    path TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            row = conn.execute("SELECT * FROM artifacts WHERE task_id = ? AND name = ?", (task_id, name)).fetchone()
            return dict(row) if row else None

    # ── Connected Accounts & OAuth Tokens ──

    @staticmethod
    def save_connected_account(
        provider: str,
        account_email: str,
        account_id: Optional[str] = None,
        account_name: Optional[str] = None,
        status: str = "connected",
        scopes: Optional[list[str]] = None
    ) -> dict[str, Any]:
        acc_id = account_id or str(uuid.uuid4())
        with db_session() as conn:
            conn.execute("""
                INSERT INTO connected_accounts (id, provider, account_email, account_name, status, scopes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    provider=excluded.provider,
                    account_email=excluded.account_email,
                    account_name=excluded.account_name,
                    status=excluded.status,
                    scopes=excluded.scopes,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                acc_id,
                provider,
                account_email,
                account_name,
                status,
                json.dumps(scopes or [])
            ))
            row = conn.execute("SELECT * FROM connected_accounts WHERE id = ?", (acc_id,)).fetchone()
            return dict(row) if row else {}

    @staticmethod
    def get_connected_account(account_id: str) -> Optional[dict[str, Any]]:
        with db_session() as conn:
            row = conn.execute("SELECT * FROM connected_accounts WHERE id = ?", (account_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_connected_account_by_provider(provider: str) -> Optional[dict[str, Any]]:
        with db_session() as conn:
            row = conn.execute("SELECT * FROM connected_accounts WHERE provider = ? AND status = 'connected' ORDER BY updated_at DESC LIMIT 1", (provider,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_connected_accounts() -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("SELECT * FROM connected_accounts ORDER BY created_at ASC").fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def delete_connected_account(account_id: str) -> bool:
        with db_session() as conn:
            conn.execute("DELETE FROM oauth_tokens WHERE account_id = ?", (account_id,))
            res = conn.execute("DELETE FROM connected_accounts WHERE id = ?", (account_id,))
            return res.rowcount > 0

    @staticmethod
    def delete_connected_accounts_by_provider(provider: str) -> bool:
        with db_session() as conn:
            conn.execute("DELETE FROM oauth_tokens WHERE provider = ?", (provider,))
            res = conn.execute("DELETE FROM connected_accounts WHERE provider = ?", (provider,))
            return res.rowcount > 0

    @staticmethod
    def save_oauth_tokens(
        account_id: str,
        provider: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[str] = None,
        token_type: str = "Bearer"
    ) -> None:
        from app.core.crypto import CryptoService
        enc_access = CryptoService.encrypt(access_token)
        enc_refresh = CryptoService.encrypt(refresh_token) if refresh_token else None

        with db_session() as conn:
            conn.execute("""
                INSERT INTO oauth_tokens (account_id, provider, encrypted_access_token, encrypted_refresh_token, expires_at, token_type, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(account_id) DO UPDATE SET
                    encrypted_access_token=excluded.encrypted_access_token,
                    encrypted_refresh_token=COALESCE(excluded.encrypted_refresh_token, oauth_tokens.encrypted_refresh_token),
                    expires_at=excluded.expires_at,
                    token_type=excluded.token_type,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                account_id,
                provider,
                enc_access,
                enc_refresh,
                expires_at,
                token_type
            ))

    @staticmethod
    def get_oauth_tokens(account_id: str) -> Optional[dict[str, Any]]:
        from app.core.crypto import CryptoService
        with db_session() as conn:
            row = conn.execute("SELECT * FROM oauth_tokens WHERE account_id = ?", (account_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            data["access_token"] = CryptoService.decrypt(data.get("encrypted_access_token", ""))
            data["refresh_token"] = CryptoService.decrypt(data.get("encrypted_refresh_token", "")) if data.get("encrypted_refresh_token") else None
            return data

    @staticmethod
    def get_oauth_tokens_by_provider(provider: str) -> Optional[dict[str, Any]]:
        from app.core.crypto import CryptoService
        with db_session() as conn:
            row = conn.execute("SELECT * FROM oauth_tokens WHERE provider = ? ORDER BY updated_at DESC LIMIT 1", (provider,)).fetchone()
            if not row:
                return None
            data = dict(row)
            data["access_token"] = CryptoService.decrypt(data.get("encrypted_access_token", ""))
            data["refresh_token"] = CryptoService.decrypt(data.get("encrypted_refresh_token", "")) if data.get("encrypted_refresh_token") else None
            return data

    # ── Normalized Calendar Events ──

    @staticmethod
    def upsert_calendar_event(event_data: dict[str, Any]) -> dict[str, Any]:
        with db_session() as conn:
            event_id = event_data.get("id") or str(uuid.uuid4())
            conn.execute("""
                INSERT INTO calendar_events (
                    id, provider_event_id, title, start_time, end_time, timezone,
                    organizer, organizer_email, attendees, location, description,
                    category, source, priority, join_url, platform, conference_data,
                    is_important, status, ownership_role, is_conflict, conflict_with_id,
                    discrepancy_note, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    provider_event_id=excluded.provider_event_id,
                    title=excluded.title,
                    start_time=excluded.start_time,
                    end_time=excluded.end_time,
                    timezone=excluded.timezone,
                    organizer=excluded.organizer,
                    organizer_email=excluded.organizer_email,
                    attendees=excluded.attendees,
                    location=excluded.location,
                    description=excluded.description,
                    category=excluded.category,
                    source=excluded.source,
                    priority=excluded.priority,
                    join_url=excluded.join_url,
                    platform=excluded.platform,
                    conference_data=excluded.conference_data,
                    is_important=excluded.is_important,
                    status=excluded.status,
                    ownership_role=excluded.ownership_role,
                    is_conflict=excluded.is_conflict,
                    conflict_with_id=excluded.conflict_with_id,
                    discrepancy_note=excluded.discrepancy_note,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                event_id,
                event_data.get("provider_event_id"),
                event_data.get("title", "Untitled Meeting"),
                event_data.get("start_time"),
                event_data.get("end_time"),
                event_data.get("timezone", "Asia/Kolkata"),
                event_data.get("organizer", ""),
                event_data.get("organizer_email", ""),
                json.dumps(event_data.get("attendees", [])) if isinstance(event_data.get("attendees"), (list, dict)) else event_data.get("attendees", "[]"),
                event_data.get("location", ""),
                event_data.get("description", ""),
                event_data.get("category", "meeting"),
                event_data.get("source", "google"),
                event_data.get("priority", "normal"),
                event_data.get("join_url"),
                event_data.get("platform"),
                json.dumps(event_data.get("conference_data", {})) if isinstance(event_data.get("conference_data"), (list, dict)) else event_data.get("conference_data"),
                event_data.get("is_important", 0),
                event_data.get("status", "MY_MEETING"),
                event_data.get("ownership_role", "attendee"),
                event_data.get("is_conflict", 0),
                event_data.get("conflict_with_id"),
                event_data.get("discrepancy_note")
            ))
            row = conn.execute("SELECT * FROM calendar_events WHERE id = ?", (event_id,)).fetchone()
            return dict(row) if row else {}

    save_calendar_event = upsert_calendar_event


    @staticmethod
    def get_calendar_events(
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None,
        source: Optional[str] = None,
        status_filter: Optional[list[str]] = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        with db_session() as conn:
            query = "SELECT * FROM calendar_events WHERE 1=1"
            params: list[Any] = []

            if start_datetime and end_datetime:
                query += " AND ((start_time >= ? AND start_time <= ?) OR (date(start_time) >= date(?) AND date(start_time) <= date(?)))"
                params.extend([start_datetime, end_datetime, start_datetime, end_datetime])
            elif start_datetime:
                query += " AND (start_time >= ? OR date(start_time) >= date(?))"
                params.extend([start_datetime, start_datetime])
            elif end_datetime:
                query += " AND (start_time <= ? OR date(start_time) <= date(?))"
                params.extend([end_datetime, end_datetime])

            if source and source.lower() not in ("all", "primary", "default"):
                query += " AND source = ?"
                params.append(source)

            if status_filter:
                placeholders = ",".join(["?"] * len(status_filter))
                query += f" AND status IN ({placeholders})"
                params.extend(status_filter)
            else:
                # By default, exclude EMAIL_ONLY and NOT_MY_MEETING from user schedule
                query += " AND status NOT IN ('EMAIL_ONLY', 'NOT_MY_MEETING')"

            query += " ORDER BY start_time ASC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_today_meetings(today_date: str) -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("""
                SELECT * FROM calendar_events
                WHERE date(start_time) = ?
                  AND category = 'meeting'
                  AND status IN ('MY_MEETING', 'INVITED', 'OPTIONAL', 'ORGANIZER')
                ORDER BY start_time ASC
            """, (today_date,)).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_upcoming_meetings(from_datetime: str, limit: int = 20) -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("""
                SELECT * FROM calendar_events
                WHERE start_time >= ?
                  AND category = 'meeting'
                  AND status IN ('MY_MEETING', 'INVITED', 'OPTIONAL', 'ORGANIZER')
                ORDER BY start_time ASC
                LIMIT ?
            """, (from_datetime, limit)).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_calendar_conflicts() -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("""
                SELECT * FROM calendar_events
                WHERE is_conflict = 1
                  AND status IN ('MY_MEETING', 'INVITED', 'OPTIONAL', 'ORGANIZER')
                ORDER BY start_time ASC
            """).fetchall()
            return [dict(r) for r in rows]

    # ── Email Metadata & Discovered Intelligence ──

    @staticmethod
    def save_email_metadata(email_data: dict[str, Any]) -> None:
        with db_session() as conn:
            conn.execute("""
                INSERT INTO email_metadata (
                    id, provider, thread_id, subject, sender, sender_email,
                    snippet, received_at, is_read, is_important, intent_tag,
                    related_event_title, suggested_time, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    subject=excluded.subject,
                    sender=excluded.sender,
                    sender_email=excluded.sender_email,
                    snippet=excluded.snippet,
                    is_read=excluded.is_read,
                    is_important=excluded.is_important,
                    intent_tag=excluded.intent_tag,
                    related_event_title=excluded.related_event_title,
                    suggested_time=excluded.suggested_time,
                    raw_json=excluded.raw_json
            """, (
                email_data["id"],
                email_data.get("provider", "google"),
                email_data.get("thread_id"),
                email_data.get("subject", ""),
                email_data.get("sender", ""),
                email_data.get("sender_email", ""),
                email_data.get("snippet", ""),
                email_data.get("received_at"),
                email_data.get("is_read", 0),
                email_data.get("is_important", 0),
                email_data.get("intent_tag", "work"),
                email_data.get("related_event_title"),
                email_data.get("suggested_time"),
                json.dumps(email_data.get("raw_json", {})) if isinstance(email_data.get("raw_json"), dict) else email_data.get("raw_json")
            ))

    @staticmethod
    def get_important_emails(limit: int = 15) -> list[dict[str, Any]]:
        with db_session() as conn:
            rows = conn.execute("""
                SELECT * FROM email_metadata
                WHERE is_important = 1 OR intent_tag IN ('invitation', 'cancellation', 'reschedule')
                ORDER BY received_at DESC LIMIT ?
            """, (limit,)).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_unread_emails_count() -> int:
        with db_session() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM email_metadata WHERE is_read = 0").fetchone()
            return row["cnt"] if row else 0

    # ── Sync State ──

    @staticmethod
    def get_sync_state(key: str) -> Optional[str]:
        with db_session() as conn:
            row = conn.execute("SELECT value FROM sync_state WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else None

    @staticmethod
    def set_sync_state(key: str, value: str) -> None:
        with db_session() as conn:
            conn.execute("""
                INSERT INTO sync_state (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """, (key, value))

