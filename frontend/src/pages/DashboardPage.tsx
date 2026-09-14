import React, { useState, useRef, useEffect } from 'react';
import { 
  Sparkles, 
  Paperclip, 
  ArrowRight, 
  Play, 
  Clock, 
  FileText, 
  Calendar, 
  Video,
  RefreshCw,
  CheckCircle2, 
  X, 
  AlertCircle,
  AlertTriangle,
  Mail,
  Users,
  ExternalLink,
  Bot,
  Send,
  CalendarCheck,
  ChevronDown,
  ChevronUp,
  Sun,
  Sunset,
  Moon
} from 'lucide-react';
import { TaskSummary, TodayScheduleResponse, CalendarEvent, ChatMessage } from '../types';
import { api } from '../services/api';

interface DashboardPageProps {
  onStartTask: (prompt: string, files: File[]) => void;
  onStartDemo: () => void;
  onOpenTask: (taskId: string) => void;
  recentTasks: TaskSummary[];
  loading: boolean;
}

const QUICK_QUESTIONS = [
  "Do I have a meeting today?",
  "What is my next meeting?",
  "Show today's meetings",
  "Show tomorrow's meetings",
  "What's my schedule this week?",
  "Do I have any overlapping meetings?",
  "Who is attending my next meeting?",
  "Which meetings are Google Meet?",
  "Which meetings are Teams?",
  "Did anyone cancel my meeting?",
  "Did anyone reschedule my meeting?",
  "Show important emails related to today's meetings",
  "What's my next meeting and give me the join link"
];

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onStartTask,
  onStartDemo,
  onOpenTask,
  recentTasks,
  loading
}) => {
  const [prompt, setPrompt] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [scheduleData, setScheduleData] = useState<TodayScheduleResponse | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncNotice, setSyncNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [activeStepIndicators, setActiveStepIndicators] = useState<string[]>([]);
  const [showAllQuickChips, setShowAllQuickChips] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const fetchSchedule = async () => {
    try {
      const data = await api.getTodaySchedule();
      setScheduleData(data);
    } catch (err) {
      console.warn('Could not fetch schedule:', err);
    }
  };

  const loadInitialChat = async () => {
    try {
      const msgs = await api.getChatMessages();
      if (msgs && msgs.length > 0) {
        setChatMessages(msgs.slice(-8));
      }
    } catch (err) {
      console.warn('Could not load chat messages:', err);
    }
  };

  useEffect(() => {
    fetchSchedule();
    loadInitialChat();
  }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isChatLoading, activeStepIndicators]);

  const handleManualSync = async () => {
    setIsSyncing(true);
    try {
      const res = await api.triggerCalendarSync();
      setSyncNotice({ type: 'success', message: res.message || 'Workspaces & calendar synced!' });
      await fetchSchedule();
    } catch (err: any) {
      setSyncNotice({ type: 'error', message: err.message || 'Sync failed.' });
    } finally {
      setIsSyncing(false);
      setTimeout(() => setSyncNotice(null), 3500);
    }
  };

  const handleSendQuery = async (queryText: string) => {
    const clean = queryText.trim();
    if (!clean || isChatLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: clean,
      created_at: new Date().toISOString()
    };

    setChatMessages((prev) => [...prev, userMsg]);
    setPrompt('');
    setIsChatLoading(true);

    // Initial progressive visual indicator
    setActiveStepIndicators(['🔎 Checking Google Calendar...']);

    const timer1 = setTimeout(() => {
      setActiveStepIndicators(['🔎 Checking Google Calendar...', '✓ Calendar data retrieved']);
    }, 400);

    const timer2 = setTimeout(() => {
      setActiveStepIndicators([
        '🔎 Checking Google Calendar...',
        '✓ Calendar data retrieved',
        '🧠 Analyzing schedule...'
      ]);
    }, 800);

    try {
      const res = await api.sendChatMessage(clean);
      clearTimeout(timer1);
      clearTimeout(timer2);
      setActiveStepIndicators([]);

      const assistantMsg: ChatMessage = {
        id: res.id || `assistant-${Date.now()}`,
        role: 'assistant',
        content: res.content || res.answer || '',
        created_at: new Date().toISOString(),
        steps: res.steps || res.execution_steps || [],
        raw_tool_data: res.raw_tool_data,
        account_connected: res.account_connected
      };

      setChatMessages((prev) => [...prev, assistantMsg]);
      fetchSchedule();
    } catch (err: any) {
      clearTimeout(timer1);
      clearTimeout(timer2);
      setActiveStepIndicators([]);

      const errMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ Error executing query: ${err.message || 'Internal connection error.'}`,
        created_at: new Date().toISOString()
      };
      setChatMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleJoinCall = (url?: string | null) => {
    if (!url) return;
    if (window.nexusBridge && window.nexusBridge.openExternal) {
      window.nexusBridge.openExternal(url);
    } else {
      window.open(url, '_blank');
    }
  };

  const handlePrepMeeting = (m: CalendarEvent) => {
    const prepQuery = `Prepare an executive briefing for my upcoming meeting: "${m.title}" at ${m.start_time.slice(11, 16)}. Outline the goals, key discussion points, and suggested agenda.`;
    handleSendQuery(prepQuery);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      setAttachedFiles(files);
      if (!prompt.trim()) {
        setPrompt(`Please analyze the attached file (${files.map((f) => f.name).join(', ')}), summarize key insights, and identify risks.`);
      }
    }
  };

  // Time & Greeting
  const now = new Date();
  const hour = now.getHours();
  let greeting = scheduleData?.greeting || 'GOOD MORNING';
  let GreetingIcon = Sun;
  if (greeting.includes('AFTERNOON') || (hour >= 12 && hour < 17)) {
    greeting = 'GOOD AFTERNOON';
    GreetingIcon = Sunset;
  } else if (greeting.includes('EVENING') || hour >= 17) {
    greeting = 'GOOD EVENING';
    GreetingIcon = Moon;
  }

  const currentDateDisplay = scheduleData?.day_of_week && scheduleData?.date
    ? `${scheduleData.day_of_week}, ${scheduleData.date}`
    : now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

  const currentTimeDisplay = scheduleData?.current_time || now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  const meetings = scheduleData?.meetings || [];
  const totalMeetingsToday = scheduleData?.meetings_today_count ?? meetings.length;
  const unreadEmails = scheduleData?.unread_important_emails_count ?? 0;
  const upcomingMeetingsCount = scheduleData?.upcoming_meetings_count ?? 0;
  const activeTasksCount = scheduleData?.tasks_count ?? 0;
  const conflictsCount = scheduleData?.calendar_conflicts_count ?? (scheduleData?.conflicts?.length ?? 0);

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-8 max-w-6xl mx-auto space-y-6 animate-in fade-in duration-300">
      
      {/* ── COMMAND CENTER HEADER ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-blue-950/40 border border-slate-800/80 p-6 rounded-3xl shadow-xl backdrop-blur-md">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs font-semibold text-blue-400 tracking-wider uppercase">
            <GreetingIcon className="w-4 h-4 text-amber-400" />
            <span>Personal Workspace Command Center • Asia/Kolkata</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <span>{greeting}, Krishna</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 flex items-center gap-2">
            <span>{currentDateDisplay}</span>
            <span className="w-1 h-1 rounded-full bg-slate-600" />
            <span className="text-slate-300 font-mono">{currentTimeDisplay}</span>
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-shrink-0">
          <button
            type="button"
            onClick={handleManualSync}
            disabled={isSyncing}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/40 rounded-2xl text-xs font-medium transition-all shadow-sm active:scale-95"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin text-blue-400' : ''}`} />
            <span>{isSyncing ? 'Syncing...' : 'Sync Workspaces'}</span>
          </button>
          <button
            type="button"
            onClick={onStartDemo}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 rounded-2xl text-xs font-medium border border-slate-700 transition-colors"
          >
            <Play className="w-3.5 h-3.5 fill-current text-amber-400" />
            <span>Try AI Demo</span>
          </button>
        </div>
      </div>

      {/* Floating Notification */}
      {syncNotice && (
        <div className={`p-3.5 rounded-2xl border flex items-center justify-between gap-3 text-xs shadow-lg animate-in slide-in-from-top ${
          syncNotice.type === 'success' 
            ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-200' 
            : 'bg-rose-950/40 border-rose-500/30 text-rose-200'
        }`}>
          <div className="flex items-center gap-2.5">
            {syncNotice.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            )}
            <span>{syncNotice.message}</span>
          </div>
        </div>
      )}

      {/* ── TODAY'S OVERVIEW STAT CARDS ── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {/* Card 1: Meetings Today */}
        <div className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl flex flex-col justify-between space-y-2 hover:border-blue-500/30 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Meetings Today</span>
            <div className="p-1.5 rounded-xl bg-blue-500/10 text-blue-400">
              <Calendar className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{totalMeetingsToday}</span>
            <span className="text-[11px] text-slate-500 font-medium">scheduled</span>
          </div>
        </div>

        {/* Card 2: Unread Important Emails */}
        <div className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl flex flex-col justify-between space-y-2 hover:border-amber-500/30 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Important Emails</span>
            <div className="p-1.5 rounded-xl bg-amber-500/10 text-amber-400">
              <Mail className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{unreadEmails}</span>
            <span className="text-[11px] text-slate-500 font-medium">unread</span>
          </div>
        </div>

        {/* Card 3: Upcoming Meetings */}
        <div className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl flex flex-col justify-between space-y-2 hover:border-purple-500/30 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Upcoming (7d)</span>
            <div className="p-1.5 rounded-xl bg-purple-500/10 text-purple-400">
              <CalendarCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{upcomingMeetingsCount}</span>
            <span className="text-[11px] text-slate-500 font-medium">sessions</span>
          </div>
        </div>

        {/* Card 4: Tasks */}
        <div className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl flex flex-col justify-between space-y-2 hover:border-cyan-500/30 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Active Tasks</span>
            <div className="p-1.5 rounded-xl bg-cyan-500/10 text-cyan-400">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{activeTasksCount}</span>
            <span className="text-[11px] text-slate-500 font-medium">pending</span>
          </div>
        </div>

        {/* Card 5: Calendar Conflicts */}
        <div className={`p-4 rounded-2xl border flex flex-col justify-between space-y-2 transition-all ${
          conflictsCount > 0 
            ? 'bg-rose-950/20 border-rose-500/40 text-rose-300' 
            : 'bg-slate-900/60 border-slate-800/80 text-emerald-400 hover:border-emerald-500/30'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Conflicts</span>
            <div className={`p-1.5 rounded-xl ${conflictsCount > 0 ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
              {conflictsCount > 0 ? <AlertTriangle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{conflictsCount}</span>
            <span className="text-[11px] text-slate-500 font-medium">
              {conflictsCount === 0 ? 'Clean' : 'Overlap'}
            </span>
          </div>
        </div>
      </div>

      {/* ── TODAY'S MEETINGS SECTION ── */}
      <div className="bg-slate-900/50 border border-slate-800/80 p-5 rounded-3xl shadow-lg space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <Calendar className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
              Today's Meetings
            </h2>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/20 text-blue-300">
              {meetings.length} verified
            </span>
          </div>
          <span className="text-xs text-slate-400 font-medium">
            Ownership Verified (You are Organizer or Attendee)
          </span>
        </div>

        {meetings.length === 0 ? (
          <div className="py-10 text-center space-y-2">
            <div className="inline-flex p-3 rounded-full bg-slate-800/60 text-slate-400 mb-1">
              <CalendarCheck className="w-6 h-6 text-slate-500" />
            </div>
            <p className="text-sm font-semibold text-slate-300">No meetings scheduled for today</p>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              You are all caught up! You have no Google Calendar or Outlook meetings on your agenda today.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {meetings.map((m) => {
              const platformLabel = m.platform === 'google_meet' 
                ? 'Google Meet' 
                : m.platform === 'teams' 
                ? 'Microsoft Teams' 
                : (m.join_url && m.join_url.includes('meet.google.com') ? 'Google Meet' : (m.join_url && m.join_url.includes('teams.microsoft.com') ? 'Microsoft Teams' : 'In-person'));

              const isGoogleMeet = platformLabel === 'Google Meet';
              const isTeams = platformLabel === 'Microsoft Teams';
              const joinUrl = m.join_url || m.meeting_url;
              const organizer = m.organizer || 'Krishna';
              const statusTag = m.ownership_status || m.status || 'MY_MEETING';

              return (
                <div
                  key={m.id}
                  className="bg-slate-950/60 border border-slate-800/80 hover:border-slate-700/80 p-4 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all"
                >
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-mono font-bold text-blue-400">
                        {m.start_time.slice(11, 16)} - {m.end_time.slice(11, 16)}
                      </span>
                      <span className="text-[10px] text-slate-400 px-2 py-0.5 rounded-md bg-slate-800">
                        {m.duration || '30 mins'}
                      </span>
                      <span className={`text-[10px] font-medium px-2 py-0.5 rounded-md border ${
                        isGoogleMeet 
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                          : isTeams 
                          ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' 
                          : 'bg-slate-800 text-slate-300 border-slate-700'
                      }`}>
                        {platformLabel}
                      </span>
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/20">
                        {statusTag}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-white truncate">
                      {m.title}
                    </h3>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                      <span>Organizer: <strong className="text-slate-200">{organizer}</strong></span>
                      {m.attendees_count !== undefined && m.attendees_count > 0 && (
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3 text-slate-400" />
                          <span>{m.attendees_count} attendee{m.attendees_count !== 1 ? 's' : ''}</span>
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0 pt-2 sm:pt-0">
                    {joinUrl ? (
                      <button
                        type="button"
                        onClick={() => handleJoinCall(joinUrl)}
                        className={`inline-flex items-center gap-1.5 px-4 py-2 text-white rounded-xl text-xs font-bold shadow-md transition-all active:scale-95 ${
                          isGoogleMeet 
                            ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/20' 
                            : isTeams 
                            ? 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-600/20' 
                            : 'bg-blue-600 hover:bg-blue-500 shadow-blue-600/20'
                        }`}
                      >
                        <Video className="w-3.5 h-3.5" />
                        <span>Join Meeting</span>
                      </button>
                    ) : (
                      <span className="text-xs text-slate-500 italic px-2">In-person</span>
                    )}

                    <button
                      type="button"
                      onClick={() => handlePrepMeeting(m)}
                      className="inline-flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium border border-slate-700 transition-colors"
                      title="Generate executive talking points and prep notes"
                    >
                      <Sparkles className="w-3 h-3 text-amber-400" />
                      <span>Prep</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── ON-DASHBOARD INTERACTIVE NEXUS CHAT ── */}
      <div className="bg-slate-900/50 border border-slate-800/80 rounded-3xl shadow-xl backdrop-blur-md overflow-hidden flex flex-col">
        {/* Chat Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-xl bg-blue-500/10 text-blue-400">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Nexus Workspace Assistant
              </h2>
              <p className="text-[11px] text-slate-400">
                Direct on-dashboard intelligence • Powered by Groq AI & Real Provider Tools
              </p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Groq Brain Active
          </span>
        </div>

        {/* Quick Test Questions Bar */}
        <div className="p-3 bg-slate-950/20 border-b border-slate-800/60">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Quick Workspace Queries
            </span>
            <button
              type="button"
              onClick={() => setShowAllQuickChips(!showAllQuickChips)}
              className="text-[11px] text-blue-400 hover:underline flex items-center gap-1"
            >
              <span>{showAllQuickChips ? 'Show Less' : 'Show All 13 Test Cases'}</span>
              {showAllQuickChips ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {(showAllQuickChips ? QUICK_QUESTIONS : QUICK_QUESTIONS.slice(0, 5)).map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSendQuery(q)}
                className="px-3 py-1 bg-slate-800/70 hover:bg-blue-600/20 hover:border-blue-500/40 text-slate-300 hover:text-blue-200 text-xs rounded-xl border border-slate-700/60 transition-all text-left"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Message Thread Area */}
        <div className="p-4 sm:p-5 max-h-[380px] overflow-y-auto space-y-4">
          {chatMessages.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-500 space-y-1">
              <p>No messages yet. Ask Nexus about your meetings, schedule, or emails above.</p>
              <p className="text-[11px] text-slate-600">Try clicking one of the quick queries above for an instant test.</p>
            </div>
          ) : (
            chatMessages.map((msg) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={msg.id}
                  className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1.5`}
                >
                  <div className="flex items-center gap-2 text-[10px] text-slate-400 px-1">
                    <span className="font-semibold">{isUser ? 'You' : 'Nexus AI'}</span>
                    {msg.created_at && (
                      <span>
                        {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    )}
                  </div>

                  {/* Execution Steps Indicators for Assistant */}
                  {!isUser && msg.steps && msg.steps.length > 0 && (
                    <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-2.5 space-y-1 max-w-xl text-[11px] font-mono text-slate-300">
                      {msg.steps.map((st, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <span className="text-blue-400">›</span>
                          <span>{st}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Message Bubble */}
                  <div
                    className={`p-3.5 rounded-2xl text-xs sm:text-sm max-w-2xl leading-relaxed whitespace-pre-wrap ${
                      isUser
                        ? 'bg-blue-600 text-white rounded-br-xs shadow-md'
                        : 'bg-slate-950/90 text-slate-200 border border-slate-800 rounded-bl-xs shadow-sm'
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              );
            })
          )}

          {/* Active Tool Step Indicator while loading */}
          {isChatLoading && (
            <div className="flex flex-col items-start space-y-2 animate-in fade-in">
              <div className="text-[10px] text-blue-400 font-semibold uppercase tracking-wider">
                Nexus Tool Execution Pipeline
              </div>
              <div className="bg-slate-950 border border-blue-500/30 rounded-2xl p-3 space-y-1.5 font-mono text-xs text-slate-200 shadow-lg">
                {activeStepIndicators.map((step, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Input Bar */}
        <div className="p-3.5 bg-slate-950/80 border-t border-slate-800">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendQuery(prompt);
            }}
            className="flex items-center gap-2"
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileChange}
              className="hidden"
              accept=".csv,.xlsx,.json,.pdf,.docx,.txt,.py,.sql"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="p-2.5 text-slate-400 hover:text-white bg-slate-800/80 rounded-xl hover:bg-slate-700 transition-colors"
              title="Attach File"
            >
              <Paperclip className="w-4 h-4" />
            </button>

            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Ask Nexus about your schedule, meetings, emails, or tasks..."
              className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            />

            <button
              type="submit"
              disabled={!prompt.trim() || isChatLoading}
              className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white rounded-xl text-xs font-semibold shadow-md transition-all flex items-center gap-1.5"
            >
              <span>Ask Nexus</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>

          {attachedFiles.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-2">
              {attachedFiles.map((file, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-300"
                >
                  <Paperclip className="w-3 h-3 text-blue-400" />
                  {file.name}
                  <button
                    type="button"
                    onClick={() => setAttachedFiles(attachedFiles.filter((_, i) => i !== idx))}
                    className="ml-1 text-slate-400 hover:text-rose-400 font-bold"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── RECENT ACTIVITY ACCORDION ── */}
      {recentTasks.length > 0 && (
        <div className="bg-slate-900/40 border border-slate-800/60 p-4 rounded-3xl space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span className="font-bold uppercase tracking-wider">Recent Multi-Agent Tasks</span>
            <span>{recentTasks.length} recorded</span>
          </div>

          <div className="space-y-2">
            {recentTasks.slice(0, 3).map((t) => (
              <div
                key={t.id}
                onClick={() => onOpenTask(t.id)}
                className="bg-slate-950/50 border border-slate-800 hover:border-slate-700 p-3 rounded-xl flex items-center justify-between cursor-pointer transition-all text-xs"
              >
                <div className="flex items-center gap-2.5 truncate">
                  <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
                  <span className="font-medium text-slate-200 truncate max-w-sm sm:max-w-md">
                    {t.title}
                  </span>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${
                    t.status === 'completed' 
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                      : t.status === 'running' 
                      ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' 
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}>
                    {t.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
