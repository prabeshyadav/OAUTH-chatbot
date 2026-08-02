import React, { useRef } from 'react';
import { Cpu, Plus, FileText, Trash2, CheckCircle2, MessageSquare, LogOut, X } from 'lucide-react';
import { uploadPdfFile, deletePdfFile, clearChatHistory } from '../api';

export default function Sidebar({
  user,
  activePdf,
  setActivePdf,
  history,
  setHistory,
  isOpen,
  onClose,
  onNewChat,
  onLogout,
  showToast
}) {
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = React.useState(false);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.type !== 'application/pdf') {
      showToast('Only PDF files are allowed!', 'error');
      return;
    }

    setUploading(true);
    try {
      const data = await uploadPdfFile(file);
      setActivePdf({ filename: file.name, fileId: data.file_id });
      showToast('PDF Context Uploaded! RAG indexing active.', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleDeletePdf = async (e) => {
    e.stopPropagation();
    try {
      await deletePdfFile();
      setActivePdf(null);
      showToast('PDF removed successfully', 'info');
    } catch (err) {
      showToast('Failed to delete PDF', 'error');
    }
  };

  const handleClearHistory = async () => {
    if (!confirm('Are you sure you want to clear your chat history?')) return;
    try {
      await clearChatHistory();
      setHistory([]);
      showToast('Chat history cleared', 'success');
    } catch (err) {
      showToast('Failed to clear history', 'error');
    }
  };

  const userPrompts = history.filter(m => m.role === 'user');

  return (
    <aside className={`sidebar glass-panel ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <div className="brand">
          <div className="brand-logo">
            <Cpu size={22} />
          </div>
          <div className="brand-text">
            <h1>NexusAI</h1>
            <span className="version-tag">React + OAuth + RAG v2.0</span>
          </div>
        </div>
        <button className="icon-btn mobile-only" onClick={onClose} aria-label="Close sidebar">
          <X size={18} />
        </button>
      </div>

      <div className="sidebar-actions">
        <button className="btn btn-secondary btn-block" onClick={onNewChat}>
          <Plus size={16} />
          <span>New Chat</span>
        </button>
      </div>

      {/* Document Section */}
      <div className="document-section">
        <div className="section-title">
          <span>DOCUMENT ENGINE</span>
          <span className={`badge ${activePdf ? 'active-badge' : ''}`}>
            {activePdf ? '1 Active' : '0 Active'}
          </span>
        </div>

        <input
          type="file"
          ref={fileInputRef}
          accept="application/pdf"
          className="file-input-hidden"
          onChange={handleFileChange}
        />

        <div
          className="pdf-drop-zone"
          onClick={() => !activePdf && !uploading && fileInputRef.current.click()}
        >
          {uploading ? (
            <div className="drop-zone-uploading">
              <div className="spinner" />
              <span>Uploading & Indexing into ChromaDB...</span>
            </div>
          ) : activePdf ? (
            <div className="doc-card">
              <div className="doc-info">
                <FileText className="doc-icon" size={24} />
                <div className="doc-details">
                  <span className="doc-name">{activePdf.filename}</span>
                  <span className="doc-meta">
                    <CheckCircle2 size={12} /> RAG & PDF Grounded
                  </span>
                </div>
              </div>
              <button className="icon-btn danger" onClick={handleDeletePdf} title="Remove PDF">
                <Trash2 size={16} />
              </button>
            </div>
          ) : (
            <div className="drop-zone-content">
              <div className="drop-icon">
                <FileText size={28} />
              </div>
              <p className="drop-title">Upload PDF Context</p>
              <p className="drop-sub">Click or drag & drop PDF</p>
            </div>
          )}
        </div>
      </div>

      {/* History Section */}
      <div className="history-section">
        <div className="section-title">
          <span>CONVERSATION HISTORY</span>
          <button className="icon-btn text-muted" onClick={handleClearHistory} title="Clear History">
            <Trash2 size={14} />
          </button>
        </div>

        <div className="history-list scrollable">
          {userPrompts.length === 0 ? (
            <div className="history-empty">
              <MessageSquare size={24} />
              <p style={{ marginTop: 6 }}>No past messages yet</p>
            </div>
          ) : (
            userPrompts.map((msg, idx) => {
              const text = msg.parts ? msg.parts[0].text : 'Conversation';
              return (
                <div key={idx} className="history-item">
                  <MessageSquare size={14} />
                  <span>{text}</span>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* User Footer */}
      <div className="sidebar-footer">
        <div className="user-card">
          <div className="user-avatar">
            {user ? user.charAt(0).toUpperCase() : 'A'}
          </div>
          <div className="user-details">
            <span className="user-name">{user}</span>
            <span className="user-role">Authorized</span>
          </div>
          <button className="icon-btn" onClick={onLogout} title="Sign Out">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}
