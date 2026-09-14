import React, { useState } from 'react';
import { Calendar as CalendarIcon, Clock, Plus, Users, CheckCircle2 } from 'lucide-react';

interface CalendarEvent {
  id: string;
  title: string;
  startTime: string;
  endTime: string;
  attendees: string[];
  status: string;
}

export const Calendar: React.FC = () => {
  const [events, setEvents] = useState<CalendarEvent[]>([
    {
      id: 'evt-1',
      title: 'Sprint Architecture Review & Agent Benchmarks',
      startTime: '10:00',
      endTime: '11:00',
      attendees: ['architect@nexus.dev', 'security@nexus.dev'],
      status: 'confirmed',
    },
    {
      id: 'evt-2',
      title: 'AI Multi-Agent Hive Synchronization',
      startTime: '14:00',
      endTime: '14:45',
      attendees: ['team@nexus.dev'],
      status: 'confirmed',
    },
    {
      id: 'evt-3',
      title: 'Production Deployment & Windows Packaging',
      startTime: '16:30',
      endTime: '17:15',
      attendees: ['lead@nexus.dev'],
      status: 'confirmed',
    },
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [start, setStart] = useState('11:30');
  const [end, setEnd] = useState('12:15');

  const handleAddEvent = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    const newEvt: CalendarEvent = {
      id: `evt-${Date.now()}`,
      title: title.trim(),
      startTime: start,
      endTime: end,
      attendees: ['you@nexus.local'],
      status: 'confirmed',
    };
    setEvents((prev) => [...prev, newEvt]);
    setTitle('');
    setIsModalOpen(false);
  };

  return (
    <div className="h-full overflow-y-auto px-8 py-8 space-y-8 bg-nexus-bg">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-nexus-border pb-6">
        <div>
          <div className="flex items-center space-x-2">
            <CalendarIcon className="w-5 h-5 text-nexus-cyan" />
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Productivity Agenda
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Autonomous schedule management with conflict resolution and meeting briefs.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-nexus-cyan to-nexus-indigo hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-bold text-xs shadow-cyan-glow self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Schedule Event</span>
        </button>
      </div>

      {/* Events Timeline */}
      <div className="space-y-4 max-w-4xl">
        {events.map((event) => (
          <div
            key={event.id}
            className="glass-panel p-5 rounded-2xl border border-nexus-border flex flex-col sm:flex-row sm:items-center justify-between gap-4"
          >
            <div className="flex items-start space-x-4">
              <div className="px-3 py-2 rounded-xl bg-nexus-card border border-nexus-border font-mono text-center shrink-0">
                <div className="text-xs font-bold text-nexus-cyan">{event.startTime}</div>
                <div className="text-[10px] text-slate-500">to {event.endTime}</div>
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-white tracking-wide">{event.title}</h3>
                <div className="flex items-center space-x-2 text-xs text-slate-400">
                  <Users className="w-3.5 h-3.5 text-slate-500" />
                  <span>{event.attendees.join(', ')}</span>
                </div>
              </div>
            </div>

            <span className="self-start sm:self-auto flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-nexus-emerald/15 border border-nexus-emerald/40 text-nexus-emerald text-[11px] font-semibold">
              <CheckCircle2 className="w-3 h-3" />
              <span className="uppercase">{event.status}</span>
            </span>
          </div>
        ))}
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleAddEvent} className="glass-panel w-full max-w-md rounded-2xl border border-nexus-cyan/40 p-6 space-y-4 shadow-cyan-glow">
            <h3 className="text-base font-bold text-white">Schedule Calendar Block</h3>
            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Event Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Nexus Multi-Agent Code Review"
                className="w-full px-3 py-2 rounded-xl bg-nexus-surface border border-nexus-border text-xs text-white focus:outline-none focus:border-nexus-cyan"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Start Time</label>
                <input
                  type="text"
                  value={start}
                  onChange={(e) => setStart(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-nexus-surface border border-nexus-border text-xs text-white font-mono focus:outline-none focus:border-nexus-cyan"
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">End Time</label>
                <input
                  type="text"
                  value={end}
                  onChange={(e) => setEnd(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-nexus-surface border border-nexus-border text-xs text-white font-mono focus:outline-none focus:border-nexus-cyan"
                  required
                />
              </div>
            </div>
            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-nexus-surface text-slate-300 border border-nexus-border text-xs"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-5 py-2 rounded-xl bg-nexus-cyan text-slate-950 font-bold text-xs shadow-cyan-glow"
              >
                Confirm Event
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
