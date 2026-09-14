import re
from typing import Any, Optional, Tuple


class IntentType:
    CALENDAR_QUERY = "CALENDAR_QUERY"
    CALENDAR_ACTION = "CALENDAR_ACTION"
    TASK_RELATED = "TASK_RELATED"
    TASK_FOLLOW_UP = "TASK_FOLLOW_UP"
    GENERAL_QUESTION = "GENERAL_QUESTION"
    NEW_TASK = "NEW_TASK"
    CLARIFICATION = "CLARIFICATION"


class IntentClassifier:
    """
    Classifies user chat messages to determine intent and whether
    active task context or tools should be invoked.
    """

    # ── CALENDAR_ACTION: Creating or mutating a calendar event ──
    CALENDAR_ACTION_PATTERNS = [
        r"^(create|schedule|book|add|set\s+up|make)\s+(a\s+|an\s+)?(meeting|event|call|appointment|sync|demo)\b",
        r"^create\s+.*(meeting|event|call|appointment)",
        r"^schedule\s+.*(tomorrow|today|at\s+\d+|on\s+\d+)",
        r"^book\s+(a\s+)?(meeting|slot|call)",
        r"^(reschedule|move|change|shift|postpone|delay|update)\s+(my\s+|the\s+)?(meeting|event|call|appointment)",
        r"\b(reschedule|move|shift|change)\s+.*?\bto\s+\d+",
        r"\b(reschedule|move|change)\s+my\s+meeting\b",
    ]

    # ── CALENDAR_QUERY: Inspecting or querying calendar schedule ──
    CALENDAR_QUERY_PATTERNS = [
        r"what(?:'s|\s+is)\s+on\s+(my\s+)?(google\s+)?calendar",
        r"what(?:'s|\s+is)\s+on\s+\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+",
        r"what(?:'s|\s+is)\s+on\s+[a-zA-Z]+\s+\d{1,2}",
        r"what(?:'s|\s+is)\s+on\s+(today|tomorrow|yesterday)",
        r"(do\s+i\s+have|are\s+there)\s+any\s+(meetings?|events?|appointments?|calls?)\s+(tomorrow|today|this\s+week|next\s+week|on\s+.*)?",
        r"do\s+i\s+have\s+any\s+meetings?",
        r"(check\s+|view\s+|show\s+|my\s+)(google\s+)?(calendar|schedule)",
        r"upcoming\s+(meetings?|events?|schedule|calls?)",
        r"what\s+meetings?\s+(do\s+i\s+have|are\s+coming|are\s+there|are\s+today|are\s+tomorrow)",
        r"am\s+i\s+free\s+(today|tomorrow|on\s+.*)?",
        r"any\s+meeting(s)?(\s+coming\s+ahead|\s+ahead|\s+today|\s+tomorrow)?",
        r"(do\s+i\s+have\s+)?work\s+today",
    ]

    # ── NEW_TASK: Commands to create and execute a real multi-agent pipeline ──
    NEW_TASK_PATTERNS = [
        # Data analysis
        r"^(analyze|analyse|audit|examine|evaluate)\s+.*?\b(csv|dataset|data|file|spreadsheet|sheet|numbers|table|metrics)\b",
        # Code writing / generation
        r"^(write|code|create|generate|implement|build|develop|program)\s+.*?\b(python|c\+\+|cpp|java|rust|javascript|typescript|api|backend|frontend|script|program|app|dockerfile|service|endpoint)\b",
        # Document / plan / report creation
        r"^(create|make|generate|draft|build|design|prepare)\s+.*?\b(business plan|pitch deck|strategy|roadmap|proposal|presentation|report|architecture|budget)\b",
        # Competitive / technology research
        r"^(research|investigate|explore|benchmark|compare)\s+.*?\b(nvidia|apple|google|microsoft|ai|market|competitor|llm|cloud|hardware|trend|startup|latest|recent|development)\b",
        # Web scraping / data ingestion
        r"^(scrape|download|fetch|clone|ingest)\s+",
        # Explicit task launch
        r"^(start|run|launch|execute)\s+(a\s+|new\s+)?task",
        # Self-inspection and codebase tasks
        r"^inspect\s+(your|my|the|nexus|this)\s+(project|codebase|backend|code|repo|repository|app|system|file)",
        r"^(find|identify|locate|detect)\s+(bug|error|issue|problem|duplicate|improvement|vulnerability|flaw)",
        r"^(fix|resolve|patch|correct|debug)\s+(the|a|this|my|our)?\s*(bug|error|issue|problem|crash|duplicate|failure|flaw)",
        r"^(implement|add|integrate|refactor|optimize|upgrade)\s+(feature|improvement|functionality|module|class|method|endpoint|support)",
        # Run tests explicitly
        r"^run\s+(the\s+)?(tests?|test\s+suite|pytest|unit\s+tests?|integration\s+tests?)",
        # Security audits
        r"^(audit|scan|check|review)\s+.*(security|vulnerability|vulnerabilities|risk|secret|credential|dependency|dependencies)",
        # Analysis requiring agents
        r"^analyze\s+(the\s+)?(codebase|project|repository|repo|backend|system)",
    ]

    # ── CLARIFICATION: Asking what the agent meant by something ──
    CLARIFICATION_PATTERNS = [
        r"what\s+did\s+you\s+mean\s+by",
        r"what\s+do\s+you\s+mean\s+by",
        r"what\s+does\s+.*mean",
        r"can\s+you\s+clarify",
        r"could\s+you\s+clarify",
        r"clarify\s+what\s+you\s+mean",
        r"what\s+is\s+meant\s+by",
        r"in\s+what\s+sense",
    ]

    # ── TASK_FOLLOW_UP: Drilling into current task outputs ──
    TASK_FOLLOW_UP_PATTERNS = [
        r"what\s+are\s+the\s+(most\s+)?important\s+points",
        r"what\s+are\s+the\s+key\s+(points|takeaways|deliverables|findings|highlights|metrics|actions)",
        r"what\s+were\s+the\s+key\s+(deliverables|findings|points|outputs)",
        r"what\s+should\s+we\s+do\s+next",
        r"what\s+are\s+the\s+next\s+steps",
        r"summarize\s+(everything\s+you\s+changed|the\s+changes|the\s+(findings|report|results|briefing|meeting|plan|analysis))",
        r"tell\s+me\s+more\s+about\s+the\s+(points|findings|risks|recommendations|changes|improvements)",
        r"give\s+me\s+more\s+details\s+on\s+the\s+(findings|recommendations|risks|points|improvements)",
        r"what\s+did\s+we\s+find",
        r"what\s+were\s+the\s+results",
        r"what\s+improvements?\s+(did\s+you|were)\s+(find|identify|detect|suggest)",
        r"why\s+did\s+(europe|sales|revenue|churn|customers?|growth)\s+decline",
        r"what\s+(changed|was\s+changed|did\s+you\s+change)",
        r"show\s+me\s+(the\s+)?(changes?|diff|patch|improvements?|results?|output|findings)",
        r"(give|show)\s+(me\s+)?a\s+summary",
        r"summarize\s+(everything|all|the)",
    ]

    # ── TASK_RELATED: Asking about active task specifics ──
    TASK_RELATED_PATTERNS = [
        r"why\s+is\s+this\s+(meeting|task|briefing|review|agenda)\s+important",
        r"why\s+is\s+it\s+important",
        r"why\s+do\s+we\s+need\s+this\s+(meeting|briefing|task)",
        r"who\s+is\s+attending(\s+this\s+meeting)?",
        r"who\s+is\s+in\s+this\s+meeting",
        r"what\s+is\s+the\s+purpose\s+of\s+this\s+(task|meeting|briefing)",
        r"prep(are)?\s+notes\s+for\s+this\s+meeting",
        r"which\s+meeting\s+is\s+scheduled",
        r"what\s+meeting\s+is\s+scheduled",
    ]

    # ── GENERAL_QUESTION: Pure factual / conceptual / direct questions ──
    GENERAL_QUESTION_PATTERNS = [
        r"^(who|how|what|where|when|why)\s+is\s+the\s+(pm|prime\s+minister|president|ceo|founder|leader|chancellor|king|queen)",
        r"^(who|how)\s+is\s+the\s+pm\s+of\s+[a-zA-Z\s]+",
        r"^who\s+is\s+[a-zA-Z\s]+(\?)?$",
        r"^what\s+is\s+the\s+capital\s+of\s+[a-zA-Z\s]+",
        r"^where\s+is\s+[a-zA-Z\s]+located",
        r"^what\s+is\s+(2\s*\+\s*2|[\d\s\+\-\*\/\(\)]+)(\?)?$",
        r"^what\s+is\s+nexus\s*(ai)?(\?)?$",
        r"^explain\s+(what\s+is\s+)?nexus\s*(ai)?(\?)?$",
        r"^what\s+is\s+(python|docker|kubernetes|c\+\+|cpp|rust|golang|html|css|linux|git|sql|ai|ml|gravity|quantum\s+computing|dna|photosynthesis)(\?)?$",
        r"^explain\s+(python|docker|kubernetes|c\+\+|rust|gravity|relativity|photosynthesis|the\s+internet|ai|machine\s+learning|neural\s+networks?)(\?)?$",
        r"^how\s+does\s+(photosynthesis|gravity|an\s+airplane|the\s+sun|a\s+car\s+engine|the\s+internet|docker|kubernetes)\s+work",
        r"^tell\s+me\s+a\s+joke",
        r"^(hello|hi|hey|good\s+morning|good\s+evening)(\s+there)?(!|\.)?$",
        r"^what\s+is\s+(the\s+)?time(\s+now)?(\?)?$",
        r"^what\s+(day|date)\s+is\s+it(\?)?$",
        r"^give\s+me\s+(today'?s\s+)?date(\?)?$",
        r"^who\s+(invented|created|founded|built|designed|discovered)\s+",
    ]

    @classmethod
    def classify(cls, message: str, task: Optional[dict[str, Any]] = None) -> Tuple[str, bool]:
        """
        Returns (intent, usedTaskContext).
        """
        clean = message.strip()
        lower = clean.lower()

        # If an active task is present, prioritize task context checks
        if task:
            # 1. NEW_TASK overrides task context
            for pattern in cls.NEW_TASK_PATTERNS:
                if re.search(pattern, lower):
                    return IntentType.NEW_TASK, False

            # 2. Pure GENERAL_QUESTION should NOT use task context
            for pattern in cls.GENERAL_QUESTION_PATTERNS:
                if re.search(pattern, lower):
                    return IntentType.GENERAL_QUESTION, False

            # 3. TASK_RELATED (e.g. "Why is this meeting important?", "Which meeting is scheduled today?")
            for pattern in cls.TASK_RELATED_PATTERNS:
                if re.search(pattern, lower):
                    return IntentType.TASK_RELATED, True

            # 4. TASK_FOLLOW_UP (e.g. "What are the most important points?", "Summarize the findings.")
            for pattern in cls.TASK_FOLLOW_UP_PATTERNS:
                if re.search(pattern, lower):
                    return IntentType.TASK_FOLLOW_UP, True

            # 5. CLARIFICATION
            for pattern in cls.CLARIFICATION_PATTERNS:
                if re.search(pattern, lower):
                    return IntentType.CLARIFICATION, True

            # 6. CALENDAR_ACTION
            for pattern in cls.CALENDAR_ACTION_PATTERNS:
                if re.search(pattern, lower):
                    return IntentType.CALENDAR_ACTION, False

            # 7. CALENDAR_QUERY
            for pattern in cls.CALENDAR_QUERY_PATTERNS:
                if re.search(pattern, lower):
                    return IntentType.CALENDAR_QUERY, False

            # 8. Anaphoric / demonstrative reference to active task
            task_demonstratives = [
                "this meeting", "the meeting", "this task", "the task", "this briefing",
                "the briefing", "these points", "the points", "the findings", "these findings",
                "the deliverables", "the report", "this report", "the analysis", "this analysis",
                "the code", "this code", "the function", "the algorithm", "the risks", "the data",
                "the changes", "the improvements", "the results", "the output"
            ]
            if any(d in lower for d in task_demonstratives):
                return IntentType.TASK_FOLLOW_UP, True

            # 9. Keyword overlap with active task
            task_prompt = (task.get("user_prompt") or "").lower()
            task_title = (task.get("title") or "").lower()
            stop_words = {
                "this", "that", "with", "from", "your", "have", "make", "what",
                "which", "will", "about", "prepare", "give", "tell", "want", "need"
            }
            task_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", f"{task_title} {task_prompt}")) - stop_words
            msg_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", lower)) - stop_words
            overlap = task_words.intersection(msg_words)

            if overlap:
                return IntentType.TASK_FOLLOW_UP, True

            return IntentType.GENERAL_QUESTION, False

        # If NO active task:
        for pattern in cls.CALENDAR_ACTION_PATTERNS:
            if re.search(pattern, lower):
                return IntentType.CALENDAR_ACTION, False

        for pattern in cls.CALENDAR_QUERY_PATTERNS:
            if re.search(pattern, lower):
                return IntentType.CALENDAR_QUERY, False

        for pattern in cls.NEW_TASK_PATTERNS:
            if re.search(pattern, lower):
                return IntentType.NEW_TASK, False

        for pattern in cls.GENERAL_QUESTION_PATTERNS:
            if re.search(pattern, lower):
                return IntentType.GENERAL_QUESTION, False

        if any(k in lower for k in ["meeting", "schedule", "calendar", "work today"]):
            return IntentType.CALENDAR_QUERY, False

        return IntentType.GENERAL_QUESTION, False
