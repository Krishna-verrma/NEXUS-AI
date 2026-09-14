import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { Home } from './pages/Home/Home';
import { Chat } from './pages/Chat/Chat';
import { Agents } from './pages/Agents/Agents';
import { Tasks } from './pages/Tasks/Tasks';
import { Files } from './pages/Files/Files';
import { Automations } from './pages/Automations/Automations';
import { Calendar } from './pages/Calendar/Calendar';
import { Activity } from './pages/Activity/Activity';
import { Settings } from './pages/Settings/Settings';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<string>('home');
  const [initialChatPrompt, setInitialChatPrompt] = useState<string>('');
  const [initialChatAgent, setInitialChatAgent] = useState<string | undefined>(undefined);
  const [pendingTickets, setPendingTickets] = useState<number>(0);

  const handleQuickAction = (prompt: string, targetAgent?: string) => {
    setInitialChatPrompt(prompt);
    setInitialChatAgent(targetAgent);
    setActivePage('chat');
  };

  const handleRunAgentDirect = (agentRole: string) => {
    setInitialChatPrompt(`Hello, activate direct execution mode for ${agentRole}.`);
    setInitialChatAgent(agentRole);
    setActivePage('chat');
  };

  const renderActivePage = () => {
    switch (activePage) {
      case 'home':
        return <Home onQuickAction={handleQuickAction} onNavigate={setActivePage} />;
      case 'chat':
        return (
          <Chat
            initialPrompt={initialChatPrompt}
            initialAgent={initialChatAgent}
            onClearInitialPrompt={() => {
              setInitialChatPrompt('');
              setInitialChatAgent(undefined);
            }}
            onPendingTicketsChange={setPendingTickets}
          />
        );
      case 'agents':
        return <Agents onRunAgent={handleRunAgentDirect} />;
      case 'tasks':
        return <Tasks />;
      case 'files':
        return <Files />;
      case 'automations':
        return <Automations />;
      case 'calendar':
        return <Calendar />;
      case 'activity':
        return <Activity />;
      case 'settings':
        return <Settings />;
      default:
        return <Home onQuickAction={handleQuickAction} onNavigate={setActivePage} />;
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-nexus-bg text-slate-100 font-sans">
      {/* Top Bar */}
      <Navbar
        activePage={activePage}
        onNavigate={setActivePage}
        pendingTicketCount={pendingTickets}
      />

      {/* Main App Body */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activePage={activePage}
          onNavigate={setActivePage}
          pendingTicketCount={pendingTickets}
        />
        <main className="flex-1 overflow-hidden relative">
          {renderActivePage()}
        </main>
      </div>
    </div>
  );
};
