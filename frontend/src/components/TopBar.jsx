import React from 'react';
import { Sliders, Wand2, MessageSquare, FileText, Database, Menu } from 'lucide-react';

const modes = [
  { id: 'auto', label: 'Auto', icon: Wand2, tip: 'Auto mode' },
  { id: 'chat', label: 'Chat', icon: MessageSquare, tip: 'Direct Gemini Chat' },
  { id: 'pdf', label: 'PDF', icon: FileText, tip: 'Gemini File API Grounding' },
  { id: 'rag', label: 'RAG', icon: Database, tip: 'ChromaDB Vector Retrieval' }
];

export default function TopBar({ currentMode, onModeChange, onToggleSidebar }) {
  return (
    <header className="top-bar glass-panel">
      <div className="top-bar-left">
        <button className="icon-btn mobile-only" onClick={onToggleSidebar} aria-label="Toggle navigation">
          <Menu size={20} />
        </button>

        <div className="mode-selector">
          <div className="mode-selector-label">
            <Sliders size={16} />
            <span>Mode:</span>
          </div>

          <div className="mode-pills">
            {modes.map(mode => {
              const Icon = mode.icon;
              const isActive = currentMode === mode.id;
              return (
                <button
                  key={mode.id}
                  className={`mode-pill ${isActive ? 'active' : ''}`}
                  onClick={() => onModeChange(mode.id)}
                  title={mode.tip}
                >
                  <Icon size={14} />
                  <span>{mode.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="top-bar-right">
        <div className="status-indicator">
          <span className="pulse-dot" />
          <span>Backend Healthy</span>
        </div>
      </div>
    </header>
  );
}
