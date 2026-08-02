import React, { useState, useRef, useEffect } from 'react';
import { Paperclip, Send } from 'lucide-react';

export default function InputDock({
  onSendMessage,
  onTriggerPdfUpload,
  activeMode,
  isGenerating
}) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isGenerating) return;
    onSendMessage(input.trim());
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [input]);

  return (
    <div className="input-dock glass-panel">
      <form onSubmit={handleSubmit} className="chat-form">
        <button
          type="button"
          className="icon-btn input-action-btn"
          onClick={onTriggerPdfUpload}
          title="Attach PDF Document"
        >
          <Paperclip size={18} />
        </button>

        <div className="textarea-wrapper">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask NexusAI anything or upload a document..."
            required
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary btn-icon-only"
          disabled={!input.trim() || isGenerating}
          aria-label="Send message"
        >
          <Send size={18} />
        </button>
      </form>

      <div className="input-footer-info">
        <span>Press <kbd>Enter</kbd> to send, <kbd>Shift + Enter</kbd> for line break</span>
        <span className="mode-badge-pill">Mode: {activeMode.toUpperCase()}</span>
      </div>
    </div>
  );
}
