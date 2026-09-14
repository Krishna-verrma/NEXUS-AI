import sqlite3
import json
from pathlib import Path
from typing import Generator
from contextlib import contextmanager
from app.core.config import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

def get_connection() -> sqlite3.Connection:
    """Create a new SQLite connection with foreign keys and Row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

@contextmanager
def db_session() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite database transactions."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db() -> None:
    """Initialize tables and default seed data."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db_session() as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        
        # Migrate existing calendar_events table columns if needed
        existing_cols = [r["name"] for r in conn.execute("PRAGMA table_info(calendar_events)").fetchall()]
        migrations = [
            ("provider_event_id", "TEXT"),
            ("timezone", "TEXT DEFAULT 'Asia/Kolkata'"),
            ("organizer", "TEXT"),
            ("organizer_email", "TEXT"),
            ("attendees", "TEXT"),
            ("priority", "TEXT DEFAULT 'normal'"),
            ("join_url", "TEXT"),
            ("platform", "TEXT"),
            ("conference_data", "TEXT"),
            ("is_important", "INTEGER DEFAULT 0"),
            ("status", "TEXT DEFAULT 'MY_MEETING'"),
            ("ownership_role", "TEXT DEFAULT 'attendee'"),
            ("is_conflict", "INTEGER DEFAULT 0"),
            ("conflict_with_id", "TEXT"),
            ("discrepancy_note", "TEXT"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        for col_name, col_type in migrations:
            if col_name not in existing_cols:
                try:
                    conn.execute(f"ALTER TABLE calendar_events ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass

        # Seed system agents ensuring all default agents are present
        seed_agents(conn)
        conn.execute("""
            UPDATE agents 
            SET name = 'Calendar & Assistant Agent', role = 'Personal AI Assistant'
            WHERE id = 'schedule'
        """)

def seed_agents(conn: sqlite3.Connection) -> None:
    """Populate default specialized agents."""
    agents_data = [
        (
            "orchestrator",
            "Nexus Orchestrator",
            "Brain",
            "Orchestrator",
            "Central planning intelligence that analyzes requirements, decomposes complex goals, delegates to specialized agents, and synthesizes final solutions.",
            json.dumps(["Dynamic Workflow Planning", "Agent Coordination", "Dependency Resolution", "Quality Gate Management"]),
            1, 1
        ),
        (
            "research",
            "Research Agent",
            "Search",
            "Specialized Agent",
            "Gathers external context, investigates market and technological trends, cites verified sources, and explicitly separates established facts from strategic hypotheses.",
            json.dumps(["External Information Search", "Fact Extraction", "Trend Synthesis", "Source Citation", "Fact vs Assumption Analysis"]),
            1, 1
        ),
        (
            "coding",
            "Coding Agent",
            "Code2",
            "Specialized Agent",
            "Analyzes, generates, and debugs code across C++, Python, Java, JS, TS, and SQL. Provides structured error analysis and optimizations without arbitrary auto-execution.",
            json.dumps(["Polyglot Code Generation", "Static Bug Detection", "SQL Optimization", "Architecture Refactoring", "Security Auditing"]),
            1, 1
        ),
        (
            "data_analyst",
            "Data Analyst",
            "BarChart3",
            "Specialized Agent",
            "Performs robust quantitative analysis on CSV, XLSX, and JSON datasets including summary statistics, correlations, anomalies, churn analysis, and visualization data generation.",
            json.dumps(["CSV/XLSX/JSON Processing", "Descriptive Statistics", "Anomaly Detection", "Correlation Analysis", "Chart Data Generation"]),
            1, 1
        ),
        (
            "document",
            "Document Agent",
            "FileText",
            "Specialized Agent",
            "Ingests and interprets unstructured documents (PDF, DOCX, TXT), extracting structural key points, executive summaries, and cross-document comparisons.",
            json.dumps(["PDF & DOCX Parsing", "Key Insight Extraction", "Long-form Summarization", "Contextual Document Q&A"]),
            1, 1
        ),
        (
            "risk",
            "Risk Agent",
            "AlertTriangle",
            "Specialized Agent",
            "Evaluates multi-dimensional risk surfaces including business, technical, operational, cybersecurity, and data compliance risks with severity, probability, and mitigation paths.",
            json.dumps(["Business Impact Analysis", "Technical Vulnerability Assessment", "Severity & Probability Matrix", "Actionable Mitigation Roadmaps"]),
            1, 1
        ),
        (
            "reviewer",
            "Reviewer Agent",
            "CheckCircle2",
            "Quality Assurance",
            "Critical quality gate that audits outputs from other agents for factual consistency, mathematical validity, logical rigor, and missing context before finalization.",
            json.dumps(["Factual Validation", "Completeness Audit", "Logical Consistency Checking", "Revision Request Generation"]),
            1, 1
        ),
        (
            "report",
            "Report Agent",
            "FileSpreadsheet",
            "Synthesis Agent",
            "Assembles comprehensive, publication-ready strategic reports with executive summaries, methodology, key findings, deep analysis, risk matrices, and prioritized recommendations.",
            json.dumps(["Executive Briefing", "Strategic Report Generation", "Markdown & Export Preparation", "Interactive Visualization Layout"]),
            1, 1
        ),
        (
            "schedule",
            "Calendar & Assistant Agent",
            "Calendar",
            "Personal AI Assistant",
            "Connects to your Google Calendar, Microsoft Outlook, and PC schedule. Checks upcoming meetings, prepares briefings, warns of conflicts, and gives direct video call links.",
            json.dumps(["Google Calendar Sync", "Microsoft Outlook Integration", "Meeting Urgency & Video Link Detection", "Daily Work Prioritization", "Executive Briefings"]),
            1, 1
        )
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO agents (id, name, icon, role, description, capabilities, is_enabled, is_system) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        agents_data
    )
