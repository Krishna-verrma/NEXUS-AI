-- NEXUS AI Database Schema (SQLite)

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    user_prompt TEXT NOT NULL,
    status TEXT NOT NULL, -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    complexity TEXT DEFAULT 'moderate', -- 'simple', 'moderate', 'complex'
    is_demo INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds REAL DEFAULT 0,
    error_message TEXT,
    final_result TEXT
);

CREATE TABLE IF NOT EXISTS task_steps (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_order INTEGER NOT NULL,
    agent_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    status TEXT NOT NULL, -- 'waiting', 'planning', 'running', 'completed', 'failed', 'needs_review'
    operation TEXT,
    input_data TEXT, -- JSON
    output_data TEXT, -- JSON
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds REAL DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT NOT NULL,
    role TEXT NOT NULL,
    description TEXT NOT NULL,
    capabilities TEXT NOT NULL, -- JSON array
    is_enabled INTEGER DEFAULT 1,
    is_system INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    status TEXT NOT NULL,
    output_preview TEXT,
    full_output TEXT,
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY(step_id) REFERENCES task_steps(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    role TEXT NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    metadata TEXT, -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    original_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    task_id TEXT,
    status TEXT DEFAULT 'ready', -- 'uploading', 'ready', 'processing', 'error'
    metadata TEXT, -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    executive_summary TEXT,
    methodology TEXT,
    key_findings TEXT, -- JSON
    analysis TEXT,
    risks TEXT, -- JSON
    recommendations TEXT, -- JSON
    conclusion TEXT,
    full_markdown TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS connected_accounts (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL, -- 'google', 'microsoft'
    account_email TEXT NOT NULL,
    account_name TEXT,
    status TEXT DEFAULT 'connected', -- 'connected', 'disconnected', 'needs_reauth'
    scopes TEXT, -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS oauth_tokens (
    account_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    encrypted_access_token TEXT NOT NULL,
    encrypted_refresh_token TEXT,
    expires_at TIMESTAMP,
    token_type TEXT DEFAULT 'Bearer',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(account_id) REFERENCES connected_accounts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS calendar_events (
    id TEXT PRIMARY KEY,
    provider_event_id TEXT,
    title TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    timezone TEXT DEFAULT 'Asia/Kolkata',
    organizer TEXT,
    organizer_email TEXT,
    attendees TEXT, -- JSON array of attendees
    location TEXT,
    description TEXT,
    category TEXT DEFAULT 'meeting', -- 'meeting', 'task', 'review'
    source TEXT DEFAULT 'google', -- 'google', 'outlook', 'local'
    priority TEXT DEFAULT 'normal', -- 'normal', 'medium', 'high'
    join_url TEXT,
    platform TEXT, -- 'google_meet', 'teams', 'zoom', 'in_person'
    conference_data TEXT, -- JSON
    is_important INTEGER DEFAULT 0,
    status TEXT DEFAULT 'MY_MEETING', -- 'MY_MEETING', 'INVITED', 'OPTIONAL', 'ORGANIZER', 'NOT_MY_MEETING', 'EMAIL_ONLY', 'CANCELLED', 'RESCHEDULED'
    ownership_role TEXT DEFAULT 'attendee', -- 'organizer', 'attendee', 'invited', 'optional', 'copied', 'external', 'mentioned'
    is_conflict INTEGER DEFAULT 0,
    conflict_with_id TEXT,
    discrepancy_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_metadata (
    id TEXT PRIMARY KEY, -- Message ID
    provider TEXT NOT NULL, -- 'google', 'microsoft'
    thread_id TEXT,
    subject TEXT NOT NULL,
    sender TEXT,
    sender_email TEXT,
    snippet TEXT,
    received_at TIMESTAMP,
    is_read INTEGER DEFAULT 0,
    is_important INTEGER DEFAULT 0,
    intent_tag TEXT DEFAULT 'work', -- 'invitation', 'cancellation', 'reschedule', 'work', 'other'
    related_event_title TEXT,
    suggested_time TEXT,
    raw_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS meeting_links (
    id TEXT PRIMARY KEY,
    event_id TEXT,
    url TEXT NOT NULL,
    provider TEXT NOT NULL, -- 'google_meet', 'teams', 'zoom'
    conference_id TEXT,
    transcript_available INTEGER DEFAULT 0,
    recording_url TEXT,
    metadata TEXT, -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(event_id) REFERENCES calendar_events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sync_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    execution_id TEXT,
    name TEXT NOT NULL,
    artifact_type TEXT NOT NULL, -- 'markdown', 'json', 'code', 'patch', 'report'
    path TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

