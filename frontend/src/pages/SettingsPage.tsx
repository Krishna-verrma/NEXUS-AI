import React, { useState, useEffect, useRef } from 'react';
import { 
  Key, 
  Cpu, 
  Sliders, 
  Globe, 
  ShieldCheck, 
  Check, 
  Calendar, 
  Mail, 
  HardDrive, 
  RefreshCw, 
  ExternalLink, 
  Info, 
  Upload, 
  Eye, 
  EyeOff, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle,
  FolderOpen,
  Zap,
  Trash2,
  GitBranch,
  GitPullRequest,
  Copy
} from 'lucide-react';
import { Settings, ConnectorsStatusResponse, AuthStatusResponse } from '../types';
import { api } from '../services/api';

interface SettingsPageProps {
  settings: Settings | null;
  onSaveSettings: (settings: Partial<Settings>) => Promise<void>;
  loading: boolean;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({
  settings,
  onSaveSettings,
  loading
}) => {
  // AI Settings
  const [provider, setProvider] = useState('openai');
  const [apiKey, setApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [baseUrl, setBaseUrl] = useState('https://api.openai.com/v1');
  const [model, setModel] = useState('gpt-4o-mini');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2048);

  // App Connections
  const [googleCalendarUrl, setGoogleCalendarUrl] = useState('');
  const [outlookCalendarUrl, setOutlookCalendarUrl] = useState('');
  const [githubToken, setGithubToken] = useState('');
  const [showGithubToken, setShowGithubToken] = useState(false);
  const [githubRepo, setGithubRepo] = useState('');
  const [syncingGithub, setSyncingGithub] = useState(false);
  const [testingGithub, setTestingGithub] = useState(false);
  const [autoScanPc, setAutoScanPc] = useState(true);
  const [webSearch, setWebSearch] = useState(false);
  const [webSearchApiKey, setWebSearchApiKey] = useState('');
  const [demoMode, setDemoMode] = useState(true);

  // OAuth Credentials state
  const [authStatus, setAuthStatus] = useState<AuthStatusResponse | null>(null);
  const [googleClientId, setGoogleClientId] = useState('');
  const [googleClientSecret, setGoogleClientSecret] = useState('');
  const [showGoogleConfig, setShowGoogleConfig] = useState(false);
  const [showGmailConfig, setShowGmailConfig] = useState(false);
  const [showGoogleSecret, setShowGoogleSecret] = useState(false);
  const [copiedRedirectUri, setCopiedRedirectUri] = useState(false);
  const [msClientId, setMsClientId] = useState('');
  const [msClientSecret, setMsClientSecret] = useState('');
  const [showMsConfig, setShowMsConfig] = useState(false);
  const [isOAuthActionLoading, setIsOAuthActionLoading] = useState(false);

  // Navigation filter / category
  const [activeTab, setActiveTab] = useState<'all' | 'ai' | 'google' | 'gmail' | 'outlook' | 'github' | 'pc' | 'web'>('all');

  // Status & Feedback state
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [syncingGoogle, setSyncingGoogle] = useState(false);
  const [syncingOutlook, setSyncingOutlook] = useState(false);
  const [scanningPc, setScanningPc] = useState(false);
  const [syncNotice, setSyncNotice] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [connectors, setConnectors] = useState<ConnectorsStatusResponse | null>(null);
  const [testingAi, setTestingAi] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; latency_ms?: number } | null>(null);
  const [testingGmail, setTestingGmail] = useState(false);
  const [gmailTestResult, setGmailTestResult] = useState<{ success: boolean; count: number; message: string; messages?: any[] } | null>(null);
  const [clearingSamples, setClearingSamples] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadAuthStatus = async () => {
    try {
      const data = await api.getAuthStatus();
      setAuthStatus(data);
      if (data?.google?.client_id && !googleClientId) {
        setGoogleClientId(data.google.client_id);
      }
      if (data?.microsoft?.client_id && !msClientId) {
        setMsClientId(data.microsoft.client_id);
      }
    } catch {
      // ignore
    }
  };

  const handleTestGmail = async () => {
    setTestingGmail(true);
    setGmailTestResult(null);
    try {
      const res = await api.testGmailConnection();
      setGmailTestResult(res);
      if (res.success) {
        showNotification('success', res.message || `Gmail verified! Found ${res.count} messages.`);
      } else {
        showNotification('error', res.message || 'Failed to query Gmail messages.');
      }
    } catch (err: any) {
      const msg = err.message || 'Error querying Gmail.';
      setGmailTestResult({ success: false, count: 0, message: msg });
      showNotification('error', msg);
    } finally {
      setTestingGmail(false);
    }
  };

  const handleCopyRedirectUri = (uri: string) => {
    navigator.clipboard.writeText(uri);
    setCopiedRedirectUri(true);
    showNotification('success', 'Redirect URI copied to clipboard!');
    setTimeout(() => setCopiedRedirectUri(false), 3000);
  };

  useEffect(() => {
    loadAuthStatus();
  }, []);

  useEffect(() => {
    if (settings) {
      const prov = settings.ai_provider || 'openai';
      setProvider(prov);
      setApiKey(settings.ai_api_key || '');
      
      let effectiveBaseUrl = settings.ai_base_url;
      let effectiveModel = settings.ai_model;
      if (prov === 'gemini') {
        if (!effectiveBaseUrl || effectiveBaseUrl.includes('api.openai.com')) {
          effectiveBaseUrl = 'https://generativelanguage.googleapis.com/v1beta';
        }
        if (!effectiveModel || effectiveModel.startsWith('gpt-')) {
          effectiveModel = 'gemini-2.5-flash';
        }
      } else if (prov === 'openai') {
        if (!effectiveBaseUrl || effectiveBaseUrl.includes('googleapis.com')) {
          effectiveBaseUrl = 'https://api.openai.com/v1';
        }
        if (!effectiveModel || effectiveModel.startsWith('gemini-')) {
          effectiveModel = 'gpt-4o-mini';
        }
      }
      setBaseUrl(effectiveBaseUrl || (prov === 'gemini' ? 'https://generativelanguage.googleapis.com/v1beta' : 'https://api.openai.com/v1'));
      setModel(effectiveModel || (prov === 'gemini' ? 'gemini-2.5-flash' : 'gpt-4o-mini'));
      setTemperature(settings.ai_temperature ?? 0.7);
      setMaxTokens(settings.ai_max_tokens ?? 2048);
      setDemoMode(settings.demo_mode ?? true);
      setWebSearch(settings.enable_web_search ?? false);
      setGoogleCalendarUrl(settings.google_calendar_url || '');
      setOutlookCalendarUrl(settings.outlook_calendar_url || '');
      setGithubToken(settings.github_token || '');
      setGithubRepo(settings.github_repo || '');
      setAutoScanPc(settings.auto_scan_pc ?? true);
      setWebSearchApiKey(settings.web_search_api_key || '');
    }
    loadConnectors();
  }, [settings]);

  const loadConnectors = async () => {
    try {
      const data = await api.getCalendarConnectors();
      setConnectors(data);
    } catch {
      // ignore
    }
  };

  const handleConnectOAuth = async (prov: 'google' | 'microsoft') => {
    setIsOAuthActionLoading(true);
    try {
      const res = await api.getOAuthLoginUrl(prov);
      if (res.url) {
        window.open(res.url, '_blank', 'width=600,height=700');
        showNotification('success', `Opened ${prov === 'google' ? 'Google' : 'Microsoft'} OAuth login window.`);
      }
    } catch (err: any) {
      showNotification('error', err.message || `Failed to initiate ${prov} OAuth.`);
    } finally {
      setIsOAuthActionLoading(false);
    }
  };

  const handleDisconnectOAuth = async (prov: 'google' | 'microsoft') => {
    setIsOAuthActionLoading(true);
    try {
      const res = await api.disconnectOAuth(prov);
      showNotification('success', res.message || `Disconnected ${prov}.`);
      await loadAuthStatus();
      await loadConnectors();
    } catch (err: any) {
      showNotification('error', err.message || `Failed to disconnect ${prov}.`);
    } finally {
      setIsOAuthActionLoading(false);
    }
  };

  const handleSaveOAuthConfig = async (prov: 'google' | 'microsoft') => {
    const cId = prov === 'google' ? googleClientId : msClientId;
    const cSec = prov === 'google' ? googleClientSecret : msClientSecret;
    if (!cId.trim()) {
      showNotification('error', 'Please enter a Client ID.');
      return;
    }
    setIsOAuthActionLoading(true);
    try {
      const res = await api.configureOAuth(prov, { client_id: cId.trim(), client_secret: cSec.trim() });
      showNotification('success', res.message || `Saved ${prov} OAuth credentials.`);
      await loadAuthStatus();
    } catch (err: any) {
      showNotification('error', err.message || `Failed to save ${prov} credentials.`);
    } finally {
      setIsOAuthActionLoading(false);
    }
  };

  const handleManualWorkspaceSync = async () => {
    setIsOAuthActionLoading(true);
    try {
      const res = await api.triggerCalendarSync();
      showNotification('success', res.message || 'Workspaces & calendar synchronized!');
      await loadAuthStatus();
      await loadConnectors();
    } catch (err: any) {
      showNotification('error', err.message || 'Sync failed.');
    } finally {
      setIsOAuthActionLoading(false);
    }
  };

  const showNotification = (type: 'success' | 'error', message: string) => {
    setSyncNotice({ type, message });
    setTimeout(() => setSyncNotice(null), 4000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSaveSettings({
      ai_provider: provider,
      ai_api_key: apiKey,
      ai_base_url: baseUrl,
      ai_model: model,
      ai_temperature: Number(temperature),
      ai_max_tokens: Number(maxTokens),
      demo_mode: demoMode,
      enable_web_search: webSearch,
      google_calendar_url: googleCalendarUrl,
      outlook_calendar_url: outlookCalendarUrl,
      github_token: githubToken,
      github_repo: githubRepo,
      auto_scan_pc: autoScanPc,
      web_search_api_key: webSearchApiKey
    });
    setSavedSuccess(true);
    await loadConnectors();
    setTimeout(() => setSavedSuccess(false), 3500);
  };

  const handleTestGithub = async () => {
    setTestingGithub(true);
    try {
      const res = await api.testGithubConnection(githubToken);
      if (res.success) {
        showNotification('success', res.message || 'GitHub authenticated successfully!');
      } else {
        showNotification('error', res.message || 'Failed to authenticate with GitHub.');
      }
    } catch (err: any) {
      showNotification('error', err.message || 'Error testing GitHub connection.');
    } finally {
      setTestingGithub(false);
    }
  };

  const handleSyncGithub = async () => {
    setSyncingGithub(true);
    try {
      const res = await api.syncGithub(githubToken, githubRepo);
      if (res.success) {
        showNotification('success', res.message || `Indexed ${res.count} GitHub deliverables!`);
        await loadConnectors();
      } else {
        showNotification('error', res.message || 'Failed to sync GitHub issues.');
      }
    } catch (err: any) {
      showNotification('error', err.message || 'Error syncing GitHub.');
    } finally {
      setSyncingGithub(false);
    }
  };
 
  const handleTestAiConnection = async () => {
    setTestingAi(true);
    setTestResult(null);
    try {
      const res = await api.testAiConnection({
        provider,
        api_key: apiKey,
        base_url: baseUrl,
        model
      });
      setTestResult(res);
      if (res.success) {
        showNotification('success', res.message || 'AI Connection verified successfully!');
        if (demoMode) {
          setDemoMode(false);
        }
      } else {
        showNotification('error', res.message || res.error || 'Connection failed.');
      }
    } catch (err: any) {
      const msg = err.message || 'Failed to connect to AI provider.';
      setTestResult({ success: false, message: msg });
      showNotification('error', msg);
    } finally {
      setTestingAi(false);
    }
  };

  const handleClearSampleEvents = async () => {
    setClearingSamples(true);
    try {
      const res = await api.clearSampleCalendarEvents();
      showNotification('success', res.message || 'Demo sample meetings cleared! Only your real calendar events will show.');
      await loadConnectors();
    } catch (err: any) {
      showNotification('error', err.message || 'Failed to clear sample events.');
    } finally {
      setClearingSamples(false);
    }
  };

  const handleSyncGoogle = async () => {
    if (!googleCalendarUrl.trim()) {
      showNotification('error', 'Please enter your Google Calendar iCal URL first.');
      return;
    }
    setSyncingGoogle(true);
    try {
      const res = await api.syncCalendarUrl(googleCalendarUrl.trim(), 'google_calendar');
      if (res.success) {
        showNotification('success', `Google Calendar connected! Synced ${res.count} events.`);
        await loadConnectors();
      } else {
        showNotification('error', res.error || 'Failed to sync Google Calendar.');
      }
    } catch (err: any) {
      showNotification('error', err.message || 'Error syncing Google Calendar.');
    } finally {
      setSyncingGoogle(false);
    }
  };

  const handleSyncOutlook = async () => {
    if (!outlookCalendarUrl.trim()) {
      showNotification('error', 'Please enter your Outlook Webcal URL first.');
      return;
    }
    setSyncingOutlook(true);
    try {
      const res = await api.syncCalendarUrl(outlookCalendarUrl.trim(), 'outlook');
      if (res.success) {
        showNotification('success', `Outlook Calendar synced! Imported ${res.count} events.`);
        await loadConnectors();
      } else {
        showNotification('error', res.error || 'Failed to sync Outlook URL.');
      }
    } catch (err: any) {
      showNotification('error', err.message || 'Error syncing Outlook.');
    } finally {
      setSyncingOutlook(false);
    }
  };

  const handleScanDesktopOutlook = async () => {
    setSyncingOutlook(true);
    try {
      const res = await api.scanPcCalendar();
      if (res.success) {
        showNotification('success', `Scanned local PC & Outlook! Found ${res.imported_events} total events.`);
        await loadConnectors();
      } else {
        showNotification('error', 'Could not scan local Outlook application.');
      }
    } catch (err: any) {
      showNotification('error', err.message || 'Error scanning Outlook.');
    } finally {
      setSyncingOutlook(false);
    }
  };

  const handleScanPcFiles = async () => {
    setScanningPc(true);
    try {
      const res = await api.scanPcCalendar();
      if (res.success) {
        showNotification('success', `Local scan complete! Indexed ${res.imported_events} events from ${res.found_files?.length || 0} files.`);
        await loadConnectors();
      } else {
        showNotification('error', 'Error scanning PC folders.');
      }
    } catch (err: any) {
      showNotification('error', err.message || 'Error scanning PC.');
    } finally {
      setScanningPc(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const res = await api.importCalendarIcs(text, file.name);
      showNotification('success', `Uploaded ${file.name}! Imported ${res.count} events.`);
      await loadConnectors();
    } catch (err: any) {
      showNotification('error', err.message || 'Failed to import ICS file.');
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 max-w-5xl mx-auto space-y-7 animate-in fade-in duration-300">
      {/* Soft Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <Sparkles className="w-5 h-5" />
            </span>
            <h2 className="text-2xl font-bold text-white tracking-tight">App & API Connections</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Connect your calendar, email, local PC files, and AI models into Nexus. Each application operates in its own isolated, secure block.
          </p>
        </div>

        {/* Status Pill */}
        <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 px-3.5 py-1.5 rounded-2xl text-xs">
          <span className={`w-2 h-2 rounded-full ${demoMode ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'}`} />
          <span className="text-slate-300 font-medium">
            {demoMode ? 'Sandbox Demo Mode Active' : 'Live Production Mode'}
          </span>
        </div>
      </div>

      {/* Floating Notification Banner */}
      {syncNotice && (
        <div className={`p-4 rounded-2xl border flex items-center justify-between gap-3 text-xs shadow-lg animate-in slide-in-from-top duration-300 ${
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

      {/* Soft Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        {[
          { id: 'all', label: 'All Connections', icon: Sparkles },
          { id: 'ai', label: 'AI Brain & Models', icon: Cpu },
          { id: 'google', label: 'Google Calendar', icon: Calendar },
          { id: 'gmail', label: 'Google Gmail', icon: Mail },
          { id: 'outlook', label: 'Microsoft Outlook', icon: Mail },
          { id: 'github', label: 'GitHub Workspace', icon: GitBranch },
          { id: 'pc', label: 'Local PC & Files', icon: HardDrive },
          { id: 'web', label: 'Web Search', icon: Globe }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl font-medium transition-all flex-shrink-0 ${
                isActive
                  ? 'bg-blue-600/20 text-blue-300 border border-blue-500/40 shadow-sm'
                  : 'bg-slate-900/50 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-slate-800/60'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">

        {/* ======================================================== */}
        {/* BLOCK 1: AI Model & Inference Brain                      */}
        {/* ======================================================== */}
        {(activeTab === 'all' || activeTab === 'ai') && (
          <div className="bg-slate-900/50 backdrop-blur-md p-6 rounded-3xl border border-slate-800/80 shadow-lg space-y-5 transition-all hover:border-slate-700/80">
            <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-2xl bg-gradient-to-br from-blue-500/20 to-indigo-500/10 border border-blue-500/30 text-blue-400">
                  <Cpu className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">AI Model Engine (Brain)</h3>
                  <p className="text-xs text-slate-400">
                    Powers autonomous reasoning, synthesis, calendar analysis, and workflow execution.
                  </p>
                </div>
              </div>

              <span className={`px-3 py-1 rounded-xl text-[11px] font-medium border flex items-center gap-1.5 ${
                testResult?.success || (settings?.is_configured && !testResult)
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${testResult?.success || (settings?.is_configured && !testResult) ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                {testResult?.success ? (testResult.latency_ms ? `AI Ready (${testResult.latency_ms}ms)` : 'AI Ready') : settings?.is_configured ? 'Key Configured' : 'Key Needed or Demo'}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="space-y-1.5">
                <label className="text-slate-300 font-medium">Provider Architecture</label>
                <select
                  value={provider}
                  onChange={(e) => {
                    const val = e.target.value;
                    setProvider(val);
                    if (val === 'gemini') {
                      setBaseUrl('https://generativelanguage.googleapis.com/v1beta');
                      setModel('gemini-2.5-flash');
                    } else if (val === 'openai') {
                      setBaseUrl('https://api.openai.com/v1');
                      setModel('gpt-4o-mini');
                    } else if (val === 'groq') {
                      setBaseUrl('https://api.groq.com/openai/v1');
                      setModel('llama-3.1-70b-versatile');
                    } else if (val === 'ollama') {
                      setBaseUrl('http://localhost:11434/v1');
                      setModel('llama3');
                    } else if (val === 'openrouter') {
                      setBaseUrl('https://openrouter.ai/api/v1');
                      setModel('anthropic/claude-3.5-sonnet');
                    }
                  }}
                  className="w-full bg-slate-950/70 border border-slate-800 rounded-2xl px-3.5 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
                >
                  <option value="gemini">Google Gemini (Recommended - Free Tier Available)</option>
                  <option value="openai">OpenAI (GPT-4o, GPT-4o-mini)</option>
                  <option value="groq">Groq (Ultra-Fast Llama 3 - Free API)</option>
                  <option value="openrouter">OpenRouter (Claude, Llama, Mistral)</option>
                  <option value="ollama">Ollama (100% Offline Local PC LLMs - No Key)</option>
                  <option value="custom">Custom OpenAI-Compatible Endpoint</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-slate-300 font-medium">Model Name</label>
                <input
                  type="text"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="e.g. gemini-1.5-flash or gpt-4o-mini"
                  className="w-full bg-slate-950/70 border border-slate-800 rounded-2xl px-3.5 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs transition-colors"
                />
              </div>

              <div className="space-y-1.5 md:col-span-2">
                <div className="flex items-center justify-between">
                  <label className="text-slate-300 font-medium">AI API Key</label>
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] text-emerald-400 flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" /> Stored locally in SQLite
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="text-slate-400 hover:text-slate-200 text-[11px] flex items-center gap-1 transition-colors"
                    >
                      {showApiKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      <span>{showApiKey ? 'Hide' : 'Show'}</span>
                    </button>
                  </div>
                </div>
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => {
                    const val = e.target.value;
                    setApiKey(val);
                    if (val.trim() && !val.startsWith('***') && demoMode) {
                      setDemoMode(false);
                    }
                  }}
                  placeholder={
                    provider === 'gemini' ? 'Paste Google Gemini API Key (starts with AIzaSy...)' :
                    provider === 'groq' ? 'Paste Groq API Key (starts with gsk_...)' :
                    provider === 'ollama' ? 'No key required for local Ollama' :
                    'Paste your API Key (starts with sk-...)'
                  }
                  className="w-full bg-slate-950/70 border border-slate-800 rounded-2xl px-3.5 py-2.5 text-slate-200 focus:outline-none focus:border-blue-500 font-mono text-xs transition-colors"
                />
                <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400 pt-1">
                  <span>Nexus encrypts and holds keys strictly on your local PC.</span>
                  <a
                    href={
                      provider === 'gemini' ? 'https://aistudio.google.com/app/apikey' :
                      provider === 'groq' ? 'https://console.groq.com/keys' :
                      provider === 'openai' ? 'https://platform.openai.com/api-keys' :
                      'https://openrouter.ai/keys'
                    }
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-400 hover:underline flex items-center gap-1"
                  >
                    <span>Get free {provider === 'gemini' ? 'Gemini' : provider === 'groq' ? 'Groq' : 'API'} key</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>

              {/* Endpoint URL */}
              <div className="space-y-1.5 md:col-span-2">
                <label className="text-slate-400 text-[11px]">Base API Endpoint URL</label>
                <input
                  type="text"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="https://api.openai.com/v1"
                  className="w-full bg-slate-950/70 border border-slate-800 rounded-2xl px-3.5 py-2 text-slate-300 font-mono text-xs focus:outline-none focus:border-blue-500"
                />
              </div>

              {/* Test AI Connection Bar */}
              <div className="md:col-span-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-slate-200">Verify AI Model Connectivity</span>
                    {testResult && (
                      <span className={`text-[11px] px-2 py-0.5 rounded-lg border font-medium ${
                        testResult.success
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      }`}>
                        {testResult.success ? `Connected (${testResult.latency_ms}ms)` : 'Test Failed'}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400">
                    {testResult 
                      ? testResult.message 
                      : `Pings ${provider.toUpperCase()} (${model}) to verify that your key is valid and response generation is ready.`}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleTestAiConnection}
                  disabled={testingAi || (!apiKey.trim() && !settings?.is_configured)}
                  className="px-4 py-2 bg-gradient-to-r from-blue-600/30 to-indigo-600/30 hover:from-blue-600/40 hover:to-indigo-600/40 text-blue-300 border border-blue-500/40 rounded-xl font-medium transition-all text-xs flex items-center gap-1.5 flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                >
                  <Zap className={`w-3.5 h-3.5 text-blue-400 ${testingAi ? 'animate-bounce' : ''}`} />
                  <span>{testingAi ? 'Testing Key...' : 'Test AI Connection'}</span>
                </button>
              </div>
            </div>

            {/* Sliders */}
            <div className="pt-2 grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-slate-800/80 text-xs">
              <div className="space-y-1.5">
                <div className="flex justify-between text-slate-300">
                  <span>Creativity (Temperature)</span>
                  <span className="font-mono text-blue-400">{temperature}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1.2"
                  step="0.05"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full accent-blue-500 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-500">
                  <span>0.0 Focused / Precise</span>
                  <span>1.0 Highly Creative</span>
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-slate-300">
                  <span>Max Response Length</span>
                  <span className="font-mono text-blue-400">{maxTokens} tokens</span>
                </div>
                <input
                  type="number"
                  min="512"
                  max="8192"
                  step="256"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                  className="w-full bg-slate-950/70 border border-slate-800 rounded-2xl px-3.5 py-1.5 text-slate-200 font-mono text-xs"
                />
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* BLOCK 2: Google Workspace (Calendar, Gmail, Meet)        */}
        {/* ======================================================== */}
        {(activeTab === 'all' || activeTab === 'google') && (
          <div className="bg-slate-900/50 backdrop-blur-md p-6 rounded-3xl border border-slate-800/80 shadow-lg space-y-5 transition-all hover:border-slate-700/80">
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-2xl bg-gradient-to-br from-red-500/20 via-yellow-500/10 to-green-500/10 border border-emerald-500/30 text-emerald-400">
                  <Calendar className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Google Workspace Connection</h3>
                  <p className="text-xs text-slate-400">
                    Real Google OAuth 2.0 integration for Google Calendar, Gmail invitations/cancellations, and Google Meet conferences.
                  </p>
                </div>
              </div>

              <span className={`px-3 py-1 rounded-xl text-xs font-semibold border flex items-center gap-1.5 self-start ${
                authStatus?.google?.connected
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
              }`}>
                <span>{authStatus?.google?.connected ? '🟢' : '🔴'}</span>
                <span>
                  {authStatus?.google?.connected 
                    ? `Connected (${authStatus.google.email || 'Google Account'})` 
                    : 'Not Connected'}
                </span>
              </span>
            </div>

            {/* Sub-services status grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="font-semibold text-slate-200">Google Calendar</span>
                  <p className="text-[10px] text-slate-400">Events, attendees, organizers</p>
                </div>
                <span className="text-xs font-mono font-bold">
                  {authStatus?.google?.connected || connectors?.google_calendar?.connected ? '🟢' : '🔴'}
                </span>
              </div>

              <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="font-semibold text-slate-200">Gmail</span>
                  <p className="text-[10px] text-slate-400">Invites, changes, cancellations</p>
                </div>
                <span className="text-xs font-mono font-bold">
                  {authStatus?.google?.connected ? '🟢' : '🔴'}
                </span>
              </div>

              <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="font-semibold text-slate-200">Google Meet</span>
                  <p className="text-[10px] text-slate-400">Direct join URLs & conferences</p>
                </div>
                <span className="text-xs font-mono font-bold">
                  {authStatus?.google?.connected ? '🟢' : '🔴'}
                </span>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
              {authStatus?.google?.connected ? (
                <button
                  type="button"
                  onClick={() => handleDisconnectOAuth('google')}
                  disabled={isOAuthActionLoading}
                  className="px-4 py-2 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 rounded-xl font-medium transition-all"
                >
                  Disconnect Google Account
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => handleConnectOAuth('google')}
                  disabled={isOAuthActionLoading}
                  className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold shadow-md transition-all flex items-center gap-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Connect Google Account</span>
                </button>
              )}

              <button
                type="button"
                onClick={handleManualWorkspaceSync}
                disabled={isOAuthActionLoading}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl font-medium transition-all flex items-center gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isOAuthActionLoading ? 'animate-spin' : ''}`} />
                <span>Sync Now</span>
              </button>

              <button
                type="button"
                onClick={() => setShowGoogleConfig(!showGoogleConfig)}
                className="px-3 py-2 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 rounded-xl font-medium transition-all"
              >
                {showGoogleConfig ? 'Hide OAuth Credentials' : 'Configure OAuth Credentials'}
              </button>

              <button
                type="button"
                onClick={handleClearSampleEvents}
                disabled={clearingSamples}
                className="px-3 py-2 bg-slate-950/70 hover:bg-rose-950/40 text-slate-400 hover:text-rose-300 border border-slate-800 rounded-xl font-medium transition-all flex items-center gap-1.5 ml-auto"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Clear Demo Events</span>
              </button>
            </div>

            {/* Expandable OAuth Credentials Form */}
            {showGoogleConfig && (
              <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3 text-xs animate-in fade-in">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">Custom Google Cloud OAuth 2.0 Client</span>
                  <span className="text-[11px] text-slate-500 font-mono">Redirect: http://127.0.0.1:8000/api/auth/callback/google</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-slate-400 text-[11px]">Client ID</label>
                    <input
                      type="text"
                      value={googleClientId}
                      onChange={(e) => setGoogleClientId(e.target.value)}
                      placeholder="xxxx.apps.googleusercontent.com"
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-slate-400 text-[11px]">Client Secret</label>
                    <input
                      type="password"
                      value={googleClientSecret}
                      onChange={(e) => setGoogleClientSecret(e.target.value)}
                      placeholder="GOCSPX-xxxxxxxx"
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleSaveOAuthConfig('google')}
                  disabled={isOAuthActionLoading}
                  className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors"
                >
                  Save Credentials
                </button>
              </div>
            )}

            {/* iCal feed fallback */}
            <div className="space-y-1.5 pt-2 border-t border-slate-800/60 text-xs">
              <label className="text-slate-400 text-[11px]">Optional iCal Web Feed Fallback URL</label>
              <div className="flex gap-2">
                <input
                  type="url"
                  value={googleCalendarUrl}
                  onChange={(e) => setGoogleCalendarUrl(e.target.value)}
                  placeholder="https://calendar.google.com/calendar/ical/your_email/private-.../basic.ics"
                  className="flex-1 bg-slate-950/70 border border-slate-800 rounded-xl px-3.5 py-2 text-slate-200 font-mono text-xs focus:outline-none focus:border-blue-500"
                />
                <button
                  type="button"
                  onClick={handleSyncGoogle}
                  disabled={syncingGoogle}
                  className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium"
                >
                  Sync URL
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* BLOCK 2B: Google Gmail (Live OAuth 2.0 & Email Brain)    */}
        {/* ======================================================== */}
        {(activeTab === 'all' || activeTab === 'gmail') && (
          <div className="bg-slate-900/50 backdrop-blur-md p-6 rounded-3xl border border-slate-800/80 shadow-lg space-y-5 transition-all hover:border-slate-700/80">
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-2xl bg-gradient-to-br from-red-500/20 via-rose-500/15 to-amber-500/10 border border-red-500/30 text-red-400">
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-white">Google Gmail Connection</h3>
                    <span className="px-2 py-0.5 rounded-lg text-[10px] font-semibold bg-red-500/10 text-red-300 border border-red-500/20">
                      OAuth 2.0
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Connect Google Gmail to read important communications, track meeting invites, detect agenda changes, and empower the autonomous Gmail Agent.
                  </p>
                </div>
              </div>

              <span className={`px-3 py-1 rounded-xl text-xs font-semibold border flex items-center gap-1.5 self-start ${
                authStatus?.google?.connected || authStatus?.gmail?.connected
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
              }`}>
                <span>{authStatus?.google?.connected || authStatus?.gmail?.connected ? '🟢' : '🔴'}</span>
                <span>
                  {authStatus?.google?.connected || authStatus?.gmail?.connected 
                    ? `Connected (${authStatus?.google?.account_email || authStatus?.google?.email || authStatus?.gmail?.account_email || 'Gmail Account'})` 
                    : 'Not Connected'}
                </span>
              </span>
            </div>

            {/* Sub-services / Capabilities Status Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="font-semibold text-slate-200">Gmail Inbox & Threads</span>
                  <p className="text-[10px] text-slate-400">Search messages via Gmail REST API</p>
                </div>
                <span className="text-xs font-mono font-bold">
                  {authStatus?.google?.connected ? '🟢' : '🔴'}
                </span>
              </div>

              <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="font-semibold text-slate-200">Meeting Invites & RSVPs</span>
                  <p className="text-[10px] text-slate-400">Extract schedules and cancellations</p>
                </div>
                <span className="text-xs font-mono font-bold">
                  {authStatus?.google?.connected ? '🟢' : '🔴'}
                </span>
              </div>

              <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="font-semibold text-slate-200">Gmail Agent</span>
                  <p className="text-[10px] text-slate-400">Autonomous email specialist</p>
                </div>
                <span className="text-xs font-mono font-bold">
                  {authStatus?.google?.connected ? '🟢' : '🔴'}
                </span>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
              {authStatus?.google?.connected ? (
                <button
                  type="button"
                  onClick={() => handleDisconnectOAuth('google')}
                  disabled={isOAuthActionLoading}
                  className="px-4 py-2 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 rounded-xl font-medium transition-all"
                >
                  Disconnect Gmail
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => handleConnectOAuth('google')}
                  disabled={isOAuthActionLoading}
                  className="px-4 py-2.5 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white rounded-xl font-semibold shadow-md transition-all flex items-center gap-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Connect Google Gmail (OAuth 2.0)</span>
                </button>
              )}

              <button
                type="button"
                onClick={handleTestGmail}
                disabled={testingGmail || (!authStatus?.google?.connected && !authStatus?.gmail?.connected)}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl font-medium transition-all flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Zap className={`w-3.5 h-3.5 text-red-400 ${testingGmail ? 'animate-bounce' : ''}`} />
                <span>{testingGmail ? 'Testing Gmail API...' : 'Test Gmail Connection'}</span>
              </button>

              <button
                type="button"
                onClick={() => setShowGmailConfig(!showGmailConfig)}
                className="px-3 py-2 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 rounded-xl font-medium transition-all"
              >
                {showGmailConfig ? 'Hide OAuth Credentials' : 'Configure OAuth Credentials'}
              </button>
            </div>

            {/* Test Result Message Box */}
            {gmailTestResult && (
              <div className={`p-4 rounded-2xl border text-xs space-y-2 animate-in fade-in duration-200 ${
                gmailTestResult.success 
                  ? 'bg-emerald-950/30 border-emerald-500/30 text-emerald-200' 
                  : 'bg-rose-950/30 border-rose-500/30 text-rose-200'
              }`}>
                <div className="flex items-center justify-between font-semibold">
                  <span className="flex items-center gap-1.5">
                    {gmailTestResult.success ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertCircle className="w-4 h-4 text-rose-400" />}
                    <span>{gmailTestResult.message}</span>
                  </span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900/60 border border-slate-700">
                    {gmailTestResult.count} Messages Found
                  </span>
                </div>
                {gmailTestResult.messages && gmailTestResult.messages.length > 0 && (
                  <div className="space-y-1.5 pt-2 border-t border-slate-800/60">
                    <span className="text-[11px] text-slate-400 font-medium">Recent communications indexed from Gmail:</span>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {gmailTestResult.messages.slice(0, 5).map((m: any, idx: number) => (
                        <div key={idx} className="p-2 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-[11px]">
                          <div className="truncate mr-2">
                            <span className="font-semibold text-slate-200">{m.subject || '(No subject)'}</span>
                            <span className="text-slate-400 ml-2 text-[10px]">from: {m.from}</span>
                          </div>
                          <span className="text-slate-500 text-[10px] whitespace-nowrap">{m.date?.slice(0, 16)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Expandable OAuth Credentials Form */}
            {showGmailConfig && (
              <div className="p-5 rounded-2xl bg-slate-950/90 border border-slate-800 space-y-4 text-xs animate-in fade-in">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                  <div>
                    <h4 className="font-semibold text-slate-100 flex items-center gap-2">
                      <Key className="w-4 h-4 text-red-400" />
                      <span>Google Cloud OAuth 2.0 Client Credentials</span>
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Enter the OAuth 2.0 Web Application credentials from your Google Cloud Console project.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleCopyRedirectUri('http://127.0.0.1:8000/api/auth/callback/google')}
                    className="px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-[11px] text-slate-300 flex items-center gap-1 self-start sm:self-auto transition-colors"
                  >
                    <Copy className="w-3 h-3 text-red-400" />
                    <span>{copiedRedirectUri ? 'Copied URI!' : 'Copy Redirect URI'}</span>
                  </button>
                </div>

                {/* Redirect URI Notification Box */}
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="space-y-0.5">
                    <span className="text-[11px] font-semibold text-slate-300">Authorized Redirect URI for Google Cloud Console:</span>
                    <p className="font-mono text-[11px] text-red-300 select-all">http://127.0.0.1:8000/api/auth/callback/google</p>
                  </div>
                  <span className="text-[10px] text-slate-500">
                    Also accepts: <code className="font-mono text-slate-400">http://localhost:8000/api/auth/google/callback</code>
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-slate-300 text-[11px] font-medium">Google Client ID</label>
                    <input
                      type="text"
                      value={googleClientId}
                      onChange={(e) => setGoogleClientId(e.target.value)}
                      placeholder="xxxx.apps.googleusercontent.com"
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-red-500"
                    />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <label className="text-slate-300 text-[11px] font-medium">Google Client Secret</label>
                      <button
                        type="button"
                        onClick={() => setShowGoogleSecret(!showGoogleSecret)}
                        className="text-[10px] text-slate-400 hover:text-slate-200 flex items-center gap-0.5"
                      >
                        {showGoogleSecret ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                        <span>{showGoogleSecret ? 'Hide' : 'Show'}</span>
                      </button>
                    </div>
                    <input
                      type={showGoogleSecret ? 'text' : 'password'}
                      value={googleClientSecret}
                      onChange={(e) => setGoogleClientSecret(e.target.value)}
                      placeholder="GOCSPX-xxxxxxxx"
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-red-500"
                    />
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                  <button
                    type="button"
                    onClick={() => handleSaveOAuthConfig('google')}
                    disabled={isOAuthActionLoading || !googleClientId.trim()}
                    className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-semibold shadow transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Save OAuth Credentials
                  </button>

                  <a
                    href="https://console.cloud.google.com/apis/credentials"
                    target="_blank"
                    rel="noreferrer"
                    className="text-red-400 hover:underline text-[11px] flex items-center gap-1"
                  >
                    <span>Open Google Cloud Console</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>

                {/* 5-Step Instructions */}
                <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/80 space-y-2 text-[11px] text-slate-300">
                  <div className="flex items-center gap-1.5 text-red-400 font-semibold">
                    <Info className="w-3.5 h-3.5" />
                    <span>How to set up Google Cloud OAuth for Gmail:</span>
                  </div>
                  <ol className="list-decimal list-inside space-y-1 text-slate-400 pl-1">
                    <li>Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noreferrer" className="text-red-400 underline">Google Cloud Console</a> and create or select your project.</li>
                    <li>In <strong>APIs & Services &gt; Library</strong>, search for and enable <strong>Gmail API</strong> (and <strong>Google Calendar API</strong>).</li>
                    <li>Under <strong>OAuth consent screen</strong>, set user type to <em>External</em> or <em>Internal</em> and add scope: <code className="text-red-300 font-mono">https://www.googleapis.com/auth/gmail.readonly</code>.</li>
                    <li>Under <strong>Credentials</strong>, click <strong>Create Credentials &gt; OAuth client ID</strong> (choose <em>Web application</em>).</li>
                    <li>Under <strong>Authorized redirect URIs</strong>, paste: <code className="text-red-300 font-mono">http://127.0.0.1:8000/api/auth/callback/google</code>.</li>
                    <li>Copy your <strong>Client ID</strong> and <strong>Client Secret</strong> into the fields above, click <strong>Save OAuth Credentials</strong>, then click <strong>Connect Google Gmail</strong>.</li>
                  </ol>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ======================================================== */}
        {/* BLOCK 3: Microsoft 365 (Outlook Mail, Calendar, Teams)   */}
        {/* ======================================================== */}
        {(activeTab === 'all' || activeTab === 'outlook') && (
          <div className="bg-slate-900/50 backdrop-blur-md p-6 rounded-3xl border border-slate-800/80 shadow-lg space-y-5 transition-all hover:border-slate-700/80">
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-2xl bg-gradient-to-br from-blue-600/20 to-cyan-500/10 border border-blue-500/30 text-blue-400">
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Microsoft 365 & Outlook Connection</h3>
                  <p className="text-xs text-slate-400">
                    Microsoft Graph OAuth 2.0 integration for Outlook Mail, Outlook Calendar, and Microsoft Teams meetings.
                  </p>
                </div>
              </div>

              <span className={`px-3 py-1 rounded-xl text-xs font-semibold border flex items-center gap-1.5 self-start ${
                authStatus?.microsoft?.connected
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
              }`}>
                <span>{authStatus?.microsoft?.connected ? '🟢' : '🔴'}</span>
                <span>
                  {authStatus?.microsoft?.connected 
                    ? `Connected (${authStatus.microsoft.email || 'Microsoft Account'})` 
                    : 'Not Connected'}
                </span>
              </span>
            </div>

            {/* Sub-services status grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="font-semibold text-slate-200">Outlook Mail</span>
                  <p className="text-[10px] text-slate-400">Messages, RSVPs, changes</p>
                </div>
                <span className="text-xs font-mono font-bold">
                  {authStatus?.microsoft?.connected ? '🟢' : '🔴'}
                </span>
              </div>

              <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="font-semibold text-slate-200">Outlook Calendar</span>
                  <p className="text-[10px] text-slate-400">Calendar schedule & invites</p>
                </div>
                <span className="text-xs font-mono font-bold">
                  {authStatus?.microsoft?.connected || connectors?.outlook?.connected ? '🟢' : '🔴'}
                </span>
              </div>

              <div className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="font-semibold text-slate-200">Microsoft Teams</span>
                  <p className="text-[10px] text-slate-400">Online Teams video meetings</p>
                </div>
                <span className="text-xs font-mono font-bold">
                  {authStatus?.microsoft?.connected ? '🟢' : '🔴'}
                </span>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
              {authStatus?.microsoft?.connected ? (
                <button
                  type="button"
                  onClick={() => handleDisconnectOAuth('microsoft')}
                  disabled={isOAuthActionLoading}
                  className="px-4 py-2 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 rounded-xl font-medium transition-all"
                >
                  Disconnect Microsoft Account
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => handleConnectOAuth('microsoft')}
                  disabled={isOAuthActionLoading}
                  className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold shadow-md transition-all flex items-center gap-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Connect Microsoft Account</span>
                </button>
              )}

              <button
                type="button"
                onClick={handleManualWorkspaceSync}
                disabled={isOAuthActionLoading}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl font-medium transition-all flex items-center gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isOAuthActionLoading ? 'animate-spin' : ''}`} />
                <span>Sync Now</span>
              </button>

              <button
                type="button"
                onClick={() => setShowMsConfig(!showMsConfig)}
                className="px-3 py-2 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 rounded-xl font-medium transition-all"
              >
                {showMsConfig ? 'Hide OAuth Credentials' : 'Configure OAuth Credentials'}
              </button>
            </div>

            {/* Expandable OAuth Credentials Form */}
            {showMsConfig && (
              <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3 text-xs animate-in fade-in">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">Custom Microsoft Entra ID (Azure) Client</span>
                  <span className="text-[11px] text-slate-500 font-mono">Redirect: http://127.0.0.1:8000/api/auth/callback/microsoft</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-slate-400 text-[11px]">Application (client) ID</label>
                    <input
                      type="text"
                      value={msClientId}
                      onChange={(e) => setMsClientId(e.target.value)}
                      placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-slate-400 text-[11px]">Client Secret Value</label>
                    <input
                      type="password"
                      value={msClientSecret}
                      onChange={(e) => setMsClientSecret(e.target.value)}
                      placeholder="Client secret string"
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleSaveOAuthConfig('microsoft')}
                  disabled={isOAuthActionLoading}
                  className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors"
                >
                  Save Credentials
                </button>
              </div>
            )}

            {/* Desktop Windows Outlook 1-Click Scanner Fallback */}
            <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs">
              <div>
                <span className="font-semibold text-slate-200">1-Click Desktop Outlook COM Scanner</span>
                <p className="text-[11px] text-slate-400">Directly scans installed Microsoft Outlook without cloud login</p>
              </div>
              <button
                type="button"
                onClick={handleScanDesktopOutlook}
                disabled={syncingOutlook}
                className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl font-medium"
              >
                Scan Desktop Outlook
              </button>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* BLOCK 4: GitHub Developer & Workspace Connection         */}
        {/* ======================================================== */}
        {(activeTab === 'all' || activeTab === 'github') && (
          <div className="bg-slate-900/50 backdrop-blur-md p-6 rounded-3xl border border-slate-800/80 shadow-lg space-y-5 transition-all hover:border-slate-700/80">
            <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-2xl bg-gradient-to-br from-slate-700/30 to-purple-600/20 border border-purple-500/30 text-purple-300">
                  <GitBranch className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">GitHub Workspace Connection</h3>
                  <p className="text-xs text-slate-400">
                    Connect GitHub to index open pull requests, issues, and repositories so AI agents can assist with code and task tracking.
                  </p>
                </div>
              </div>

              <span className={`px-3 py-1 rounded-xl text-[11px] font-medium border flex items-center gap-1.5 ${
                connectors?.github?.connected
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-slate-800/80 text-slate-400 border-slate-700'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${connectors?.github?.connected ? 'bg-emerald-400' : 'bg-slate-500'}`} />
                {connectors?.github?.connected 
                  ? `${connectors.github.status} • ${connectors.github.events_count} items` 
                  : 'Not Connected'}
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-slate-300 font-medium">GitHub Personal Access Token (PAT)</label>
                  <div className="relative">
                    <input
                      type={showGithubToken ? "text" : "password"}
                      value={githubToken}
                      onChange={(e) => setGithubToken(e.target.value)}
                      placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                      className="w-full bg-slate-950/70 border border-slate-800 rounded-2xl px-3.5 py-2.5 text-slate-200 font-mono text-xs focus:outline-none focus:border-purple-500 transition-colors pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowGithubToken(!showGithubToken)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                    >
                      {showGithubToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-slate-300 font-medium">Default Repository / Org (Optional)</label>
                  <input
                    type="text"
                    value={githubRepo}
                    onChange={(e) => setGithubRepo(e.target.value)}
                    placeholder="e.g. facebook/react or owner/repo (leave blank for user assigned)"
                    className="w-full bg-slate-950/70 border border-slate-800 rounded-2xl px-3.5 py-2.5 text-slate-200 font-mono text-xs focus:outline-none focus:border-purple-500 transition-colors"
                  />
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2 pt-1">
                <button
                  type="button"
                  onClick={handleTestGithub}
                  disabled={testingGithub}
                  className="px-4 py-2 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/40 rounded-2xl font-medium transition-all flex items-center gap-1.5 text-xs"
                >
                  <Zap className={`w-3.5 h-3.5 ${testingGithub ? 'animate-spin' : ''}`} />
                  <span>{testingGithub ? 'Verifying Token...' : 'Test GitHub Connection'}</span>
                </button>

                <button
                  type="button"
                  onClick={handleSyncGithub}
                  disabled={syncingGithub}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-2xl font-medium transition-all flex items-center gap-1.5 text-xs"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${syncingGithub ? 'animate-spin' : ''}`} />
                  <span>{syncingGithub ? 'Syncing...' : 'Sync Pull Requests & Issues'}</span>
                </button>
              </div>

              {/* 4-Step Setup Tip */}
              <div className="p-3.5 rounded-2xl bg-slate-950/40 border border-slate-800/80 space-y-2 text-[11px] text-slate-300 mt-2">
                <div className="flex items-center gap-2 text-purple-400 font-semibold">
                  <Info className="w-3.5 h-3.5" />
                  <span>How to generate a GitHub Personal Access Token (PAT):</span>
                </div>
                <ol className="list-decimal list-inside space-y-1 text-slate-400 pl-1">
                  <li>Open <a href="https://github.com/settings/tokens" target="_blank" rel="noreferrer" className="text-purple-400 underline">GitHub Token Settings</a> in your browser.</li>
                  <li>Click <strong>"Generate new token"</strong> &gt; <strong>"Generate new token (classic)"</strong>.</li>
                  <li>Check <strong>repo</strong> (Full control of private repositories) or <strong>read:user</strong>.</li>
                  <li>Generate and paste the token into the box above, then click <strong>"Sync Pull Requests & Issues"</strong>.</li>
                </ol>
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* BLOCK 5: Local PC Files & Deliverables                   */}
        {/* ======================================================== */}
        {(activeTab === 'all' || activeTab === 'pc') && (
          <div className="bg-slate-900/50 backdrop-blur-md p-6 rounded-3xl border border-slate-800/80 shadow-lg space-y-5 transition-all hover:border-slate-700/80">
            <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-2xl bg-gradient-to-br from-purple-500/20 to-indigo-500/10 border border-purple-500/30 text-purple-400">
                  <HardDrive className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Local PC Files & Deliverables</h3>
                  <p className="text-xs text-slate-400">
                    Index local schedule items, deadlines, and project files from your Windows Documents, Downloads, or Desktop.
                  </p>
                </div>
              </div>

              <span className="px-3 py-1 rounded-xl text-[11px] font-medium border bg-purple-500/10 text-purple-300 border-purple-500/30 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                {connectors?.local_pc?.events_count ?? 0} indexed items
              </span>
            </div>

            <div className="space-y-4 text-xs">
              <div className="flex items-center justify-between p-4 bg-slate-950/50 rounded-2xl border border-slate-800/80">
                <div>
                  <h4 className="font-semibold text-slate-200">Automatic PC Folder Scanner</h4>
                  <p className="text-slate-400 text-[11px] mt-0.5">
                    Scans Downloads, Documents, and Desktop for schedule .ics attachments and task items.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoScanPc}
                    onChange={(e) => setAutoScanPc(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={handleScanPcFiles}
                  disabled={scanningPc}
                  className="px-4 py-2.5 bg-slate-800/80 hover:bg-slate-800 text-slate-200 border border-slate-700/80 rounded-2xl font-medium transition-all flex items-center gap-2"
                >
                  <FolderOpen className="w-3.5 h-3.5 text-purple-400" />
                  <span>{scanningPc ? 'Scanning PC...' : 'Run Local PC Scan Now'}</span>
                </button>

                <input
                  type="file"
                  ref={fileInputRef}
                  accept=".ics"
                  onChange={handleFileUpload}
                  className="hidden"
                />

                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2.5 bg-slate-800/80 hover:bg-slate-800 text-slate-200 border border-slate-700/80 rounded-2xl font-medium transition-all flex items-center gap-2"
                >
                  <Upload className="w-3.5 h-3.5 text-blue-400" />
                  <span>Upload .ICS Calendar File</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* BLOCK 5: Live Web Search & Intelligence                  */}
        {/* ======================================================== */}
        {(activeTab === 'all' || activeTab === 'web') && (
          <div className="bg-slate-900/50 backdrop-blur-md p-6 rounded-3xl border border-slate-800/80 shadow-lg space-y-5 transition-all hover:border-slate-700/80">
            <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border border-emerald-500/30 text-emerald-400">
                  <Globe className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Live Web Search & Intelligence</h3>
                  <p className="text-xs text-slate-400">
                    Permits Research Agent to fetch up-to-date market trends, company news, and live web citations.
                  </p>
                </div>
              </div>

              <span className={`px-3 py-1 rounded-xl text-[11px] font-medium border flex items-center gap-1.5 ${
                webSearch
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-slate-800/80 text-slate-400 border-slate-700'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${webSearch ? 'bg-emerald-400' : 'bg-slate-500'}`} />
                {webSearch ? 'Search Enabled' : 'Search Off'}
              </span>
            </div>

            <div className="space-y-4 text-xs">
              <div className="flex items-center justify-between p-4 bg-slate-950/50 rounded-2xl border border-slate-800/80">
                <div>
                  <h4 className="font-semibold text-slate-200">Enable Live Web Search</h4>
                  <p className="text-slate-400 text-[11px] mt-0.5">
                    When enabled, agents can browse the live internet to enrich reports with fresh data.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={webSearch}
                    onChange={(e) => setWebSearch(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
                </label>
              </div>

              {webSearch && (
                <div className="space-y-1.5 animate-in fade-in duration-200">
                  <label className="text-slate-300 font-medium">Custom Search API Key (Optional)</label>
                  <input
                    type="password"
                    value={webSearchApiKey}
                    onChange={(e) => setWebSearchApiKey(e.target.value)}
                    placeholder="Optional Serper / Tavily / Google Search API key (Leave blank for default search)"
                    className="w-full bg-slate-950/70 border border-slate-800 rounded-2xl px-3.5 py-2.5 text-slate-200 font-mono text-xs focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                  <span className="text-[11px] text-slate-500">
                    If left empty, Nexus uses the built-in search retrieval engine.
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* BLOCK 6: Operational Sandbox & Demo Mode                 */}
        {/* ======================================================== */}
        {activeTab === 'all' && (
          <div className="bg-slate-900/50 backdrop-blur-md p-6 rounded-3xl border border-slate-800/80 shadow-lg space-y-4 transition-all hover:border-slate-700/80">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
              <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Operational Sandbox & Demo Mode</h3>
                <p className="text-[11px] text-slate-400">
                  Switch between offline zero-cost simulation and real live AI cloud execution.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 bg-slate-950/50 rounded-2xl border border-slate-800/80 text-xs">
              <div>
                <h4 className="font-semibold text-slate-200">Demo Mode (Offline Sandbox)</h4>
                <p className="text-slate-400 text-[11px] mt-0.5">
                  Allows 100% deterministic multi-agent execution on sample datasets without consuming external API credits.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={demoMode}
                  onChange={(e) => setDemoMode(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-amber-500"></div>
              </label>
            </div>
          </div>
        )}

        {/* ======================================================== */}
        {/* Save Bar                                                 */}
        {/* ======================================================== */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-3xl bg-slate-900/90 border border-slate-800/80 shadow-xl sticky bottom-4 backdrop-blur-md">
          {savedSuccess ? (
            <span className="flex items-center gap-2 text-xs text-emerald-400 font-medium">
              <Check className="w-4 h-4" /> All application connections and settings saved!
            </span>
          ) : (
            <span className="text-xs text-slate-400">
              Connections take effect immediately on next AI agent query.
            </span>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-7 py-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-500 hover:from-blue-500 hover:to-indigo-400 text-white text-xs font-semibold rounded-2xl shadow-lg shadow-blue-600/25 transition-all border border-blue-400/30 active:scale-[0.98]"
          >
            <Check className="w-4 h-4" />
            <span>Save All Configurations</span>
          </button>
        </div>
      </form>
    </div>
  );
};

