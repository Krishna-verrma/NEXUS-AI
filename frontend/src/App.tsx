import React, { useState, useEffect, useCallback } from 'react';
import { Bell, X, Video, Sparkles } from 'lucide-react';
import { Sidebar, NavPage } from './components/layout/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { AgentsPage } from './pages/AgentsPage';
import { FilesPage } from './pages/FilesPage';
import { HistoryPage } from './pages/HistoryPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';
import { Task, TaskSummary, Agent, FileItem, Report, Settings, CalendarEvent, TodayScheduleResponse } from './types';
import { api } from './services/api';
import { useTaskWebSocket } from './hooks/useWebSocket';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<NavPage>('dashboard');
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [recentTasks, setRecentTasks] = useState<TaskSummary[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [backendHealth, setBackendHealth] = useState({ status: 'offline', demo_mode: true });
  const [loading, setLoading] = useState(false);
  const [upcomingReminder, setUpcomingReminder] = useState<CalendarEvent | null>(null);
  const [dismissedReminderId, setDismissedReminderId] = useState<string | null>(null);

  // Initial Data Fetch
  useEffect(() => {
    loadInitialData();
    const interval = setInterval(checkHealth, 8000);
    return () => clearInterval(interval);
  }, []);

  // Keyboard Shortcuts (Ctrl+K, Esc)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCurrentPage('dashboard');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Proactive Meeting Reminder Poller
  useEffect(() => {
    const checkUpcomingReminders = () => {
      api.getTodaySchedule()
        .then((data: TodayScheduleResponse) => {
          if (data && data.next_meeting) {
            const m = data.next_meeting;
            if (m.starts_in_minutes !== undefined && m.starts_in_minutes >= 0 && m.starts_in_minutes <= 15) {
              if (m.id !== dismissedReminderId) {
                setUpcomingReminder(m);
              }
            } else {
              setUpcomingReminder(null);
            }
          }
        })
        .catch(() => {});
    };

    checkUpcomingReminders();
    const interval = setInterval(checkUpcomingReminders, 25000);
    return () => clearInterval(interval);
  }, [dismissedReminderId]);

  const checkHealth = async () => {
    try {
      const h = await api.checkHealth();
      setBackendHealth(h);
    } catch {
      setBackendHealth({ status: 'offline', demo_mode: true });
    }
  };

  const loadInitialData = async () => {
    setLoading(true);
    try {
      await checkHealth();
      const [tList, aList, fList, rList, sData] = await Promise.all([
        api.listTasks().catch(() => []),
        api.listAgents().catch(() => []),
        api.listFiles().catch(() => []),
        api.listReports().catch(() => []),
        api.getSettings().catch(() => null)
      ]);
      setRecentTasks(tList);
      setAgents(aList);
      setFiles(fList);
      setReports(rList);
      setSettings(sData);
    } catch (err) {
      console.error('Initial load error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Real-time WebSocket Event Handler
  const handleWebSocketMessage = useCallback((msg: any) => {
    if (msg.type === 'step_status') {
      setCurrentTask((prev) => {
        if (!prev || prev.id !== msg.task_id) return prev;
        const updatedSteps = prev.steps.map((s) => {
          if (s.id === msg.step_id || s.agent_id === msg.agent_id) {
            return {
              ...s,
              status: msg.status,
              operation: msg.operation || s.operation,
              duration_seconds: msg.duration_seconds ?? s.duration_seconds,
              output_data: msg.output || s.output_data
            };
          }
          return s;
        });
        return { ...prev, steps: updatedSteps };
      });
    } else if (msg.type === 'task_completed') {
      setCurrentTask((prev) => {
        if (!prev || prev.id !== msg.task_id) return prev;
        return {
          ...prev,
          status: 'completed',
          final_result: msg.final_result,
          duration_seconds: msg.duration_seconds
        };
      });
      // Refresh task history and reports
      api.listTasks().then(setRecentTasks).catch(() => {});
      api.listReports().then(setReports).catch(() => {});
    } else if (msg.type === 'workflow_planned') {
      setCurrentTask((prev) => {
        if (!prev || prev.id !== msg.task_id) return prev;
        return { ...prev, steps: msg.steps || prev.steps };
      });
    }
  }, []);

  const activeTaskId = currentTask && (currentTask.status === 'pending' || currentTask.status === 'running') ? currentTask.id : null;
  const { isConnected: isWebSocketConnected } = useTaskWebSocket(activeTaskId, handleWebSocketMessage);

  // Resilient Polling Fallback for active tasks
  useEffect(() => {
    if (!currentTask || currentTask.status === 'completed' || currentTask.status === 'failed' || currentTask.status === 'cancelled') {
      return;
    }
    const pollInterval = setInterval(async () => {
      try {
        const updated = await api.getTask(currentTask.id);
        if (updated) {
          setCurrentTask(updated);
          if (updated.status === 'completed' || updated.status === 'failed') {
            api.listTasks().then(setRecentTasks).catch(() => {});
            api.listReports().then(setReports).catch(() => {});
          }
        }
      } catch (err) {
        console.error('Task polling error:', err);
      }
    }, 1500);

    return () => clearInterval(pollInterval);
  }, [currentTask?.id, currentTask?.status]);

  const handleToggleDemoMode = async () => {
    const nextMode = !backendHealth.demo_mode;
    await handleSaveSettings({ demo_mode: nextMode });
  };

  // Actions
  const handleStartTask = async (prompt: string, attachedFiles: File[]) => {
    setLoading(true);
    try {
      const uploadedFileIds: string[] = [];
      for (const f of attachedFiles) {
        const uploaded = await api.uploadFile(f);
        uploadedFileIds.push(uploaded.id);
      }
      const task = await api.createTask(prompt, uploadedFileIds, settings?.demo_mode ?? false);
      setCurrentTask(task);
      setCurrentPage('workspace');
      api.listTasks().then(setRecentTasks).catch(() => {});
    } catch (err: any) {
      alert(`Failed to start task: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStartDemo = async () => {
    setLoading(true);
    try {
      const task = await api.startDemoTask();
      setCurrentTask(task);
      setCurrentPage('workspace');
      api.listTasks().then(setRecentTasks).catch(() => {});
    } catch (err: any) {
      alert(`Failed to start demo: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenTask = async (taskId: string) => {
    setLoading(true);
    try {
      const task = await api.getTask(taskId);
      setCurrentTask(task);
      setCurrentPage('workspace');
    } catch (err: any) {
      alert(`Failed to open task: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshCurrentTask = async () => {
    if (!currentTask) return;
    try {
      const updated = await api.getTask(currentTask.id);
      setCurrentTask(updated);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCancelTask = async () => {
    if (!currentTask) return;
    try {
      const updated = await api.cancelTask(currentTask.id);
      setCurrentTask(updated);
      api.listTasks().then(setRecentTasks).catch(() => {});
    } catch (err: any) {
      alert(`Error cancelling task: ${err.message}`);
    }
  };

  const handleToggleAgent = async (agentId: string, isEnabled: boolean) => {
    try {
      const updated = await api.toggleAgent(agentId, isEnabled);
      setAgents((prev) => prev.map((a) => (a.id === agentId ? updated : a)));
    } catch (err: any) {
      alert(`Error toggling agent: ${err.message}`);
    }
  };

  const handleUploadFile = async (file: File) => {
    try {
      const newFile = await api.uploadFile(file);
      setFiles((prev) => [newFile, ...prev]);
    } catch (err: any) {
      alert(`File upload failed: ${err.message}`);
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    try {
      await api.deleteFile(fileId);
      setFiles((prev) => prev.filter((f) => f.id !== fileId));
    } catch (err: any) {
      alert(`File deletion failed: ${err.message}`);
    }
  };

  const handleUseFileInTask = (file: FileItem) => {
    setCurrentPage('dashboard');
  };

  const handleRenameReport = async (reportId: string, title: string) => {
    try {
      const updated = await api.renameReport(reportId, title);
      setReports((prev) => prev.map((r) => (r.id === reportId ? updated : r)));
    } catch (err: any) {
      alert(`Rename failed: ${err.message}`);
    }
  };

  const handleDeleteReport = async (reportId: string) => {
    try {
      await api.deleteReport(reportId);
      setReports((prev) => prev.filter((r) => r.id !== reportId));
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleSaveSettings = async (newSettings: Partial<Settings>) => {
    setLoading(true);
    try {
      const updated = await api.updateSettings(newSettings);
      setSettings(updated);
      await checkHealth();
    } catch (err: any) {
      alert(`Settings update failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#07090e] text-slate-100 font-sans">
      {/* Primary Sidebar */}
      <Sidebar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        onNewTask={() => setCurrentPage('dashboard')}
        isDemoMode={backendHealth.demo_mode}
        isConnected={backendHealth.status === 'healthy'}
        activeTaskTitle={currentTask?.status === 'running' ? currentTask.title : null}
        onToggleDemoMode={handleToggleDemoMode}
      />

      {/* Main View Router */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Proactive Meeting Alert Banner */}
        {upcomingReminder && (
          <div className="bg-slate-900/95 border-b border-blue-500/30 p-3 px-5 text-white shadow-xl flex items-center justify-between gap-4 z-40 backdrop-blur-md animate-in slide-in-from-top duration-300">
            <div className="flex items-center gap-3">
              <span className="p-1.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300">
                <Bell className="w-4 h-4" />
              </span>
              <div className="flex items-center flex-wrap gap-2">
                <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/30 text-amber-300">
                  {upcomingReminder.starts_in_minutes === 0 ? 'Starting Now' : `Starts in ${upcomingReminder.starts_in_minutes}m`}
                </span>
                <span className="text-xs sm:text-sm font-semibold tracking-tight">{upcomingReminder.title}</span>
                <span className="text-xs text-slate-400 hidden md:inline">
                  • {upcomingReminder.start_time.slice(11, 16)} ({upcomingReminder.location || 'Online'})
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-shrink-0">
              {upcomingReminder.join_url && (
                <button
                  type="button"
                  onClick={() => {
                    if (window.nexusBridge && window.nexusBridge.openExternal) {
                      window.nexusBridge.openExternal(upcomingReminder.join_url!);
                    } else {
                      window.open(upcomingReminder.join_url!, '_blank');
                    }
                  }}
                  className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow transition-colors flex items-center gap-1.5"
                >
                  <Video className="w-3.5 h-3.5" />
                  <span>Join Call</span>
                </button>
              )}
              <button
                type="button"
                onClick={() => setDismissedReminderId(upcomingReminder.id)}
                className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg transition-colors"
                title="Dismiss reminder"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {currentPage === 'dashboard' && (
          <DashboardPage
            onStartTask={handleStartTask}
            onStartDemo={handleStartDemo}
            onOpenTask={handleOpenTask}
            recentTasks={recentTasks}
            loading={loading}
          />
        )}

        {currentPage === 'workspace' && (
          <WorkspacePage
            task={currentTask}
            onRefreshTask={handleRefreshCurrentTask}
            onCancelTask={handleCancelTask}
            isStreaming={isWebSocketConnected}
          />
        )}

        {currentPage === 'agents' && (
          <AgentsPage
            agents={agents}
            onToggleAgent={handleToggleAgent}
          />
        )}

        {currentPage === 'files' && (
          <FilesPage
            files={files}
            onUploadFile={handleUploadFile}
            onDeleteFile={handleDeleteFile}
            onUseInTask={handleUseFileInTask}
            loading={loading}
          />
        )}

        {currentPage === 'history' && (
          <HistoryPage
            tasks={recentTasks}
            onSelectTask={handleOpenTask}
          />
        )}

        {currentPage === 'reports' && (
          <ReportsPage
            reports={reports}
            onRenameReport={handleRenameReport}
            onDeleteReport={handleDeleteReport}
          />
        )}

        {currentPage === 'settings' && (
          <SettingsPage
            settings={settings}
            onSaveSettings={handleSaveSettings}
            loading={loading}
          />
        )}
      </main>
    </div>
  );
};
