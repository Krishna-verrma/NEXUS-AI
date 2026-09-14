from typing import Dict, Any, List

def plan_workflow(query: str, target_agent: str = None) -> Dict[str, Any]:
    """Decompose user query into multi-agent execution steps."""
    q = query.lower()

    if target_agent and target_agent != "orchestrator":
        return {
            "intent": "direct_agent_delegation",
            "primaryAgent": target_agent,
            "steps": [
                {"agent": target_agent, "action": f"Execute direct task: {query}"}
            ]
        }

    # Computer control intents
    if any(k in q for k in ["launch", "open app", "open chrome", "open calc", "open notepad", "screenshot", "screen capture", "system vitals", "hardware", "cpu usage"]):
        return {
            "intent": "computer_control",
            "primaryAgent": "computer_agent",
            "steps": [
                {"agent": "computer_agent", "action": f"Control desktop/system: {query}"}
            ]
        }

    # Filesystem intents
    if any(k in q for k in ["file", "directory", "folder", "search file", "find file", "delete", "remove file", "create file", "write file"]):
        return {
            "intent": "filesystem_operation",
            "primaryAgent": "file_agent",
            "steps": [
                {"agent": "file_agent", "action": f"Execute filesystem action: {query}"}
            ]
        }

    # Web search intents
    if any(k in q for k in ["search web", "browse", "google", "look up", "http://", "https://", "latest news", "find online"]):
        return {
            "intent": "web_research",
            "primaryAgent": "web_agent",
            "steps": [
                {"agent": "web_agent", "action": f"Research online sources: {query}"}
            ]
        }

    # Coding / Programming intents
    if any(k in q for k in ["code", "python", "typescript", "bug", "syntax", "refactor", "function", "class", "execute code", "run code"]):
        return {
            "intent": "code_engineering",
            "primaryAgent": "coding_agent",
            "steps": [
                {"agent": "coding_agent", "action": f"Analyze and execute code task: {query}"}
            ]
        }

    # Productivity / Calendar intents
    if any(k in q for k in ["calendar", "schedule", "meeting", "agenda", "appointment", "remind", "todo"]):
        return {
            "intent": "productivity_scheduling",
            "primaryAgent": "productivity_agent",
            "steps": [
                {"agent": "productivity_agent", "action": f"Manage schedule and agenda: {query}"}
            ]
        }

    # Communication / Email intents
    if any(k in q for k in ["email", "draft", "slack", "message", "announcement", "notify"]):
        return {
            "intent": "communication_drafting",
            "primaryAgent": "communication_agent",
            "steps": [
                {"agent": "communication_agent", "action": f"Draft communication dispatch: {query}"}
            ]
        }

    # Data intents
    if any(k in q for k in ["data", "csv", "excel", "dataset", "statistics", "metric", "chart", "numbers"]):
        return {
            "intent": "data_analysis",
            "primaryAgent": "data_agent",
            "steps": [
                {"agent": "data_agent", "action": f"Analyze dataset & calculate metrics: {query}"}
            ]
        }

    # Creative intents
    if any(k in q for k in ["write", "story", "creative", "brainstorm", "document", "article", "essay", "pitch"]):
        return {
            "intent": "creative_studio",
            "primaryAgent": "creative_agent",
            "steps": [
                {"agent": "creative_agent", "action": f"Draft creative presentation/document: {query}"}
            ]
        }

    # Compound default: Search files then synthesize
    return {
        "intent": "general_orchestration",
        "primaryAgent": "creative_agent",
        "steps": [
            {"agent": "creative_agent", "action": f"Synthesize response: {query}"}
        ]
    }
