import React, { useState, useEffect } from 'react';
import AuthModal from './components/AuthModal';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import ChatCanvas from './components/ChatCanvas';
import InputDock from './components/InputDock';
import Toast from './components/Toast';
import {
  fetchChatHistory,
  sendChatMessage,
  fetchPdfStatus
} from './api';

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('nexus_access_token') || null);
  const [user, setUser] = useState(() => localStorage.getItem('nexus_user') || 'admin');
  const [currentMode, setCurrentMode] = useState('auto');
  const [activePdf, setActivePdf] = useState(null);
  const [history, setHistory] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toasts, setToasts] = useState([]);

  const showToast = (message, type = 'info', duration = 3500) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  };

  // OAuth Callback Handler
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const oauthToken = urlParams.get('access_token');
    if (oauthToken) {
      handleLoginSuccess(oauthToken, 'oauth_user');
      window.history.replaceState({}, document.title, window.location.pathname);
      showToast('Google OAuth Sign-in Successful!', 'success');
    }
  }, []);

  // Sync History & Active PDF when authenticated
  useEffect(() => {
    if (token) {
      loadHistory();
      loadPdfStatus();
    }
  }, [token]);

  const loadHistory = async () => {
    try {
      const data = await fetchChatHistory();
      const rawHist = data.history || [];
      setHistory(rawHist);

      // Convert raw history to chat messages format
      const formatted = rawHist.map(m => ({
        role: m.role,
        content: m.parts ? m.parts[0].text : ''
      }));
      setMessages(formatted);
    } catch (err) {
      console.error('Failed to load chat history', err);
    }
  };

  const loadPdfStatus = async () => {
    try {
      const data = await fetchPdfStatus();
      if (data.has_file) {
        setActivePdf({ filename: data.filename, fileId: data.file_id });
      } else {
        setActivePdf(null);
      }
    } catch (err) {
      setActivePdf(null);
    }
  };

  const handleLoginSuccess = (newToken, username) => {
    setToken(newToken);
    setUser(username || 'admin');
    localStorage.setItem('nexus_access_token', newToken);
    localStorage.setItem('nexus_user', username || 'admin');
  };

  const handleLogout = () => {
    setToken(null);
    setUser('admin');
    setHistory([]);
    setMessages([]);
    setActivePdf(null);
    localStorage.removeItem('nexus_access_token');
    localStorage.removeItem('nexus_user');
    showToast('Signed out', 'info');
  };

  const handleSendMessage = async (text) => {
    if (!text || isGenerating) return;

    setIsGenerating(true);

    // Optimistically add user message
    const newMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, newMsg]);

    try {
      const data = await sendChatMessage(text, currentMode);

      const botMsg = {
        role: 'model',
        content: data.bot,
        meta: { mode: data.mode, model: data.model }
      };

      setMessages(prev => [...prev, botMsg]);
      setHistory(prev => [
        ...prev,
        { role: 'user', parts: [{ text }] },
        { role: 'model', parts: [{ text: data.bot }] }
      ]);
    } catch (err) {
      showToast(err.message, 'error');
      setMessages(prev => [...prev, { role: 'model', content: `⚠️ **Error:** ${err.message}` }]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    showToast('Started new session', 'info');
  };

  return (
    <>
      <div className="glow-bg glow-bg-1" />
      <div className="glow-bg glow-bg-2" />
      <div className="glow-bg glow-bg-3" />

      <Toast toasts={toasts} />

      {!token && (
        <AuthModal
          onLoginSuccess={handleLoginSuccess}
          showToast={showToast}
        />
      )}

      <div className="app-layout">
        <Sidebar
          user={user}
          activePdf={activePdf}
          setActivePdf={setActivePdf}
          history={history}
          setHistory={setHistory}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          onNewChat={handleNewChat}
          onLogout={handleLogout}
          showToast={showToast}
        />

        <main className="chat-workspace">
          <TopBar
            currentMode={currentMode}
            onModeChange={(mode) => {
              setCurrentMode(mode);
              showToast(`Switched to ${mode.toUpperCase()} mode`, 'info');
            }}
            onToggleSidebar={() => setSidebarOpen(prev => !prev)}
          />

          <ChatCanvas
            user={user}
            messages={messages}
            isGenerating={isGenerating}
            onSelectStarterPrompt={(prompt) => handleSendMessage(prompt)}
          />

          <InputDock
            onSendMessage={handleSendMessage}
            onTriggerPdfUpload={() => {
              document.querySelector('.file-input-hidden')?.click();
            }}
            activeMode={currentMode}
            isGenerating={isGenerating}
          />
        </main>
      </div>
    </>
  );
}
