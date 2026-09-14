import os
import sys
import time
import json
from pathlib import Path
import streamlit as st

# Add backend directory to sys.path so local Nexus AI modules can be loaded if present
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if BACKEND_DIR.exists() and str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# --- Page Configuration ---
st.set_page_config(
    page_title="Nexus AI — Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Modern Custom Styling ---
st.markdown("""
<style>
    .nexus-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
        margin-bottom: 0px;
    }
    .nexus-subtitle {
        font-size: 0.95rem;
        color: #94A3B8;
        margin-bottom: 1.2rem;
    }
    .agent-pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .trace-card {
        border-left: 3px solid #6366F1;
        padding: 6px 12px;
        background-color: rgba(99, 102, 241, 0.05);
        border-radius: 0 6px 6px 0;
        margin: 4px 0;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Agent Registry Definition ---
AGENTS_META = {
    "orchestrator": {"name": "Nexus Orchestrator", "icon": "⚡", "role": "Central intelligence, routing, multi-step synthesis"},
    "computer_agent": {"name": "Computer Controller", "icon": "🖥️", "role": "Screen capture, window control, system vitals"},
    "file_agent": {"name": "Filesystem Operator", "icon": "📁", "role": "File discovery, directory traversal, safe creation/deletion"},
    "web_agent": {"name": "Web Navigator", "icon": "🌐", "role": "Live web search, page scraping, online research"},
    "coding_agent": {"name": "Code Architect", "icon": "💻", "role": "Code analysis, AST syntax diagnostics, sandbox execution"},
    "productivity_agent": {"name": "Productivity Executive", "icon": "📅", "role": "Calendar scheduling, meeting briefs, agenda management"},
    "communication_agent": {"name": "Comms Dispatcher", "icon": "✉️", "role": "Drafting emails, announcements, notification dispatches"},
    "data_agent": {"name": "Data Scientist", "icon": "📊", "role": "Dataset analysis, calculations, data visualization"},
    "creative_agent": {"name": "Creative Studio", "icon": "🎨", "role": "Content creation, documentation, copywriting"}
}

# --- Sidebar Configuration ---
with st.sidebar:
    st.markdown("## ⚡ Nexus AI Control")
    
    execution_mode = st.radio(
        "Execution Engine",
        options=["Direct Gemini API", "Local Nexus Multi-Agent", "FastAPI Backend"],
        index=0,
        help="Select whether to communicate directly via Gemini API, via local Python agent modules, or via FastAPI endpoint."
    )
    
    st.divider()
    
    # API Key Configuration
    default_key = os.environ.get("GEMINI_API_KEY", "")
    if "GEMINI_API_KEY" in st.secrets:
        default_key = st.secrets["GEMINI_API_KEY"]
        
    api_key = st.text_input(
        "Google Gemini API Key",
        value=default_key,
        type="password",
        help="Required for Direct Gemini mode. Get a free key at https://aistudio.google.com/"
    )
    
    if execution_mode == "Direct Gemini API":
        model_name = st.selectbox(
            "Gemini Model",
            options=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"],
            index=0
        )
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.05)
        system_instruction = st.text_area(
            "System Instruction",
            value="You are Nexus AI, an intelligent desktop assistant with advanced capabilities in system control, research, coding, and productivity.",
            height=100
        )
    elif execution_mode == "Local Nexus Multi-Agent":
        selected_agent = st.selectbox(
            "Target Agent",
            options=list(AGENTS_META.keys()),
            format_func=lambda k: f"{AGENTS_META[k]['icon']} {AGENTS_META[k]['name']}"
        )
    else:  # FastAPI Backend
        backend_url = st.text_input("Backend API Base URL", value="http://localhost:8000")
        selected_agent = st.selectbox(
            "Target Agent",
            options=list(AGENTS_META.keys()),
            format_func=lambda k: f"{AGENTS_META[k]['icon']} {AGENTS_META[k]['name']}"
        )

    st.divider()
    
    # Clear conversation button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- Top Navigation Tabs ---
tab_chat, tab_agents, tab_system = st.tabs(["💬 Command Chat", "🤖 Autonomous Agents", "📊 System Vitals"])

# ==========================================
# TAB 1: Chat Interface
# ==========================================
with tab_chat:
    st.markdown('<div class="nexus-title">NEXUS AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="nexus-subtitle">Intelligent Desktop Operating Layer & Autonomous Multi-Agent System</div>', unsafe_allow_html=True)

    # Initialize session state for messages
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "👋 Greetings! I am **Nexus AI**. I can assist with software engineering, file management, web research, data processing, and system operations.",
                "agent": "orchestrator",
                "traces": []
            }
        ]

    # Render Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            # Display Agent badge if available
            agent_key = msg.get("agent", "orchestrator")
            if msg["role"] == "assistant" and agent_key in AGENTS_META:
                meta = AGENTS_META[agent_key]
                st.caption(f"{meta['icon']} **{meta['name']}**")
            
            st.markdown(msg["content"])
            
            # If there are activity traces or security tickets, render them in an expander
            if msg.get("traces"):
                with st.expander(f"🔍 View Execution Trace ({len(msg['traces'])} steps)", expanded=False):
                    for trace in msg["traces"]:
                        action = trace.get("action", "Operation")
                        detail = trace.get("detail", "")
                        status = trace.get("status", "info")
                        st.markdown(f"**[{status.upper()}]** {action}\n\n`{detail}`")
            
            if msg.get("security_ticket"):
                ticket = msg["security_ticket"]
                st.warning(f"🛡️ **Security Gate Ticket Issued:** `{ticket.get('id', 'N/A')}`\n\n**Action:** `{ticket.get('action')}`\n\n**Target:** `{ticket.get('target')}`")

    # Chat Input Box
    user_input = st.chat_input("Enter a command or ask Nexus AI...")

    if user_input:
        # Add user message to session
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Assistant Response Container
        with st.chat_message("assistant"):
            # ----------------------------------------------------
            # MODE 1: Direct Gemini API (Cloud / Standalone)
            # ----------------------------------------------------
            if execution_mode == "Direct Gemini API":
                if not api_key:
                    st.error("⚠️ Please enter a **Google Gemini API Key** in the sidebar to continue.")
                else:
                    placeholder = st.empty()
                    accumulated = ""
                    try:
                        # Try official google-genai SDK
                        try:
                            from google import genai
                            from google.genai import types

                            client = genai.Client(api_key=api_key)
                            response = client.models.generate_content_stream(
                                model=model_name,
                                contents=user_input,
                                config=types.GenerateContentConfig(
                                    system_instruction=system_instruction,
                                    temperature=temperature
                                )
                            )
                            for chunk in response:
                                if chunk.text:
                                    accumulated += chunk.text
                                    placeholder.markdown(accumulated + "▌")
                            placeholder.markdown(accumulated)

                        except ImportError:
                            # Fallback to legacy google-generativeai SDK
                            import google.generativeai as genai_legacy
                            genai_legacy.configure(api_key=api_key)
                            model = genai_legacy.GenerativeModel(
                                model_name=model_name,
                                system_instruction=system_instruction
                            )
                            response = model.generate_content(
                                user_input,
                                generation_config={"temperature": temperature},
                                stream=True
                            )
                            for chunk in response:
                                if chunk.text:
                                    accumulated += chunk.text
                                    placeholder.markdown(accumulated + "▌")
                            placeholder.markdown(accumulated)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": accumulated,
                            "agent": "orchestrator"
                        })
                    except Exception as e:
                        st.error(f"Gemini API Error: {str(e)}")

            # ----------------------------------------------------
            # MODE 2: Local Nexus Multi-Agent (In-Process Python)
            # ----------------------------------------------------
            elif execution_mode == "Local Nexus Multi-Agent":
                with st.spinner("Executing via Nexus Multi-Agent Orchestration..."):
                    try:
                        from app.agents import orchestrator, get_agent
                        target = selected_agent
                        if target == "orchestrator":
                            agent_result = orchestrator.execute(user_input)
                        else:
                            agent_instance = get_agent(target)
                            agent_result = agent_instance.execute(user_input, context={"target_agent": target})

                        st.markdown(agent_result.response)

                        if agent_result.activity_traces:
                            with st.expander("🔍 Execution Traces", expanded=True):
                                for trace in agent_result.activity_traces:
                                    st.markdown(f"- **{trace.get('action')}**: {trace.get('detail', '')}")

                        if agent_result.security_ticket:
                            t = agent_result.security_ticket
                            st.warning(f"🛡️ **Security Gate Ticket Triggered:** `{t.get('id')}`\n\nApproval required for `{t.get('action')}` on `{t.get('target')}`.")

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": agent_result.response,
                            "agent": agent_result.agent_role or selected_agent,
                            "traces": agent_result.activity_traces,
                            "security_ticket": agent_result.security_ticket
                        })
                    except ImportError as err:
                        st.error(f"Local backend modules could not be imported: {err}.\nMake sure backend dependencies are installed or switch to 'Direct Gemini API' mode.")
                    except Exception as err:
                        st.error(f"Execution failed: {err}")

            # ----------------------------------------------------
            # MODE 3: FastAPI Backend (REST API Endpoint)
            # ----------------------------------------------------
            else:
                with st.spinner("Querying Nexus Backend API..."):
                    try:
                        import httpx
                        endpoint = f"{backend_url.rstrip('/')}/api/chat"
                        payload = {
                            "message": user_input,
                            "target_agent": selected_agent
                        }
                        res = httpx.post(endpoint, json=payload, timeout=60.0)
                        if res.status_code == 200:
                            data = res.json()
                            content = data.get("content", "")
                            traces = data.get("activityTraces", [])
                            ticket_id = data.get("securityTicketId")

                            st.markdown(content)
                            if traces:
                                with st.expander("🔍 Execution Traces", expanded=True):
                                    for trace in traces:
                                        st.markdown(f"- **{trace.get('action')}**: {trace.get('detail', '')}")

                            if ticket_id:
                                st.warning(f"🛡️ Security ticket generated: `{ticket_id}`")

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": content,
                                "agent": data.get("agentRole", selected_agent),
                                "traces": traces,
                                "security_ticket": {"id": ticket_id} if ticket_id else None
                            })
                        else:
                            st.error(f"Backend returned status {res.status_code}: {res.text}")
                    except Exception as err:
                        st.error(f"Connection error to backend: {err}")

    # Export Chat Button in Sidebar
    if len(st.session_state.messages) > 1:
        with st.sidebar:
            chat_export = "\n\n".join([
                f"### {m['role'].upper()} ({m.get('agent', 'user')})\n{m['content']}"
                for m in st.session_state.messages
            ])
            st.download_button(
                "📥 Export Chat (.md)",
                data=chat_export,
                file_name="nexus_chat_history.md",
                mime="text/markdown",
                use_container_width=True
            )

# ==========================================
# TAB 2: Autonomous Agents Fleet
# ==========================================
with tab_agents:
    st.markdown("### 🤖 Nexus Agent Fleet")
    st.markdown("Nexus AI operates with 9 specialized autonomous agents coordinated by the central Orchestrator.")

    cols = st.columns(3)
    for idx, (key, info) in enumerate(AGENTS_META.items()):
        col = cols[idx % 3]
        with col:
            st.markdown(f"""
            <div style="border: 1px solid rgba(140, 140, 140, 0.2); border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                <h4 style="margin: 0;">{info['icon']} {info['name']}</h4>
                <p style="color: #6366F1; font-size: 0.8rem; font-weight: bold; margin: 4px 0;">{key}</p>
                <p style="font-size: 0.85rem; color: #CBD5E1;">{info['role']}</p>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# TAB 3: System Vitals
# ==========================================
with tab_system:
    st.markdown("### 📊 Hardware & System Telemetry")
    try:
        import psutil
        import platform

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CPU Usage", f"{psutil.cpu_percent()}%")
        mem = psutil.virtual_memory()
        c2.metric("RAM Used", f"{mem.percent}%", f"{round(mem.used / (1024**3), 1)} / {round(mem.total / (1024**3), 1)} GB")
        disk = psutil.disk_usage("/")
        c3.metric("Disk Used", f"{disk.percent}%", f"{round(disk.used / (1024**3), 1)} GB")
        c4.metric("Platform", platform.system(), platform.release())

        st.divider()
        st.markdown("#### System Details")
        st.json({
            "OS": platform.platform(),
            "Python Version": platform.python_version(),
            "CPU Logical Cores": psutil.cpu_count(logical=True),
            "CPU Physical Cores": psutil.cpu_count(logical=False),
        })
    except Exception as e:
        st.info(f"System vitals telemetry unavailable: {e}")
