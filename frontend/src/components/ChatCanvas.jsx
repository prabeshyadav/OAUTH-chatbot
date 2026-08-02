import React, { useEffect, useRef } from 'react';
import { Zap, Compass, FilePlus, Code, Bot, Cpu, Sliders, Copy, Check } from 'lucide-react';
import { marked } from 'marked';
import hljs from 'highlight.js';
import 'highlight.js/styles/atom-one-dark.css';

marked.setOptions({
  highlight: function (code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  },
  breaks: true
});

export default function ChatCanvas({
  user,
  messages,
  isGenerating,
  onSelectStarterPrompt
}) {
  const canvasRef = useRef(null);
  const [copiedIdx, setCopiedIdx] = React.useState(null);

  useEffect(() => {
    if (canvasRef.current) {
      canvasRef.current.scrollTop = canvasRef.current.scrollHeight;
    }
  }, [messages, isGenerating]);

  const handleCopyCode = (codeText, idx) => {
    navigator.clipboard.writeText(codeText).then(() => {
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 2000);
    });
  };

  const renderMessageContent = (content, isUser) => {
    if (isUser) {
      return <p>{content}</p>;
    }
    const html = marked.parse(content || '');
    return <div dangerouslySetInnerHTML={{ __html: html }} />;
  };

  return (
    <div className="chat-canvas scrollable" ref={canvasRef}>
      {messages.length === 0 ? (
        <div className="welcome-screen">
          <div className="hero-badge">
            <Zap size={14} />
            <span>Multimodal & RAG AI Engine</span>
          </div>

          <h1>What will we explore today?</h1>
          <p>
            Connect your documents, leverage Google OAuth security, and query Gemini 2.0 / 3.0 Preview models with high precision.
          </p>

          <div className="starter-cards">
            <div
              className="starter-card"
              onClick={() => onSelectStarterPrompt('What can you do? Explain your modes and features.')}
            >
              <div className="card-icon"><Compass size={20} /></div>
              <h3>Explore Capabilities</h3>
              <p>Learn about Auto, Direct PDF grounding, and ChromaDB RAG modes.</p>
            </div>

            <div
              className="starter-card"
              onClick={() => onSelectStarterPrompt('Upload a PDF file using the left sidebar to start document Q&A.')}
            >
              <div className="card-icon"><FilePlus size={20} /></div>
              <h3>Analyze PDF Files</h3>
              <p>Upload files to query complex documents and extract insights instantly.</p>
            </div>

            <div
              className="starter-card"
              onClick={() => onSelectStarterPrompt('Write a Python script for connecting FastAPI with OAuth2 JWT authentication.')}
            >
              <div className="card-icon"><Code size={20} /></div>
              <h3>Coding & Architecture</h3>
              <p>Generate clean code snippets, diagrams, and technical solutions.</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="messages-container">
          {messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            const userInitial = user ? user.charAt(0).toUpperCase() : 'U';

            return (
              <div key={idx} className={`message-row ${isUser ? 'user' : 'model'}`}>
                <div className={`avatar ${isUser ? 'user-avatar-msg' : 'bot-avatar'}`}>
                  {isUser ? userInitial : <Bot size={20} />}
                </div>

                <div className="message-bubble-wrapper">
                  {!isUser && msg.meta && (
                    <div className="message-meta">
                      <span className="meta-tag">
                        <Cpu size={12} /> {msg.meta.model || 'Gemini'}
                      </span>
                      <span className="meta-tag">
                        <Sliders size={12} /> {(msg.meta.mode || 'auto').toUpperCase()}
                      </span>
                    </div>
                  )}

                  <div className="message-bubble glass-panel">
                    {renderMessageContent(msg.content, isUser)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {isGenerating && (
        <div className="typing-indicator-wrapper" style={{ marginTop: 16 }}>
          <div className="avatar bot-avatar">
            <Bot size={20} />
          </div>
          <div className="typing-bubble glass-panel">
            <div className="typing-dots">
              <span />
              <span />
              <span />
            </div>
            <span className="typing-text">Gemini is thinking...</span>
          </div>
        </div>
      )}
    </div>
  );
}
