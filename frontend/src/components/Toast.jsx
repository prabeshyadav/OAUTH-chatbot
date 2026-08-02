import React from 'react';
import { CheckCircle, AlertCircle, Info } from 'lucide-react';

export default function Toast({ toasts }) {
  return (
    <div className="toast-container">
      {toasts.map(toast => {
        let Icon = Info;
        if (toast.type === 'success') Icon = CheckCircle;
        if (toast.type === 'error') Icon = AlertCircle;

        return (
          <div key={toast.id} className={`toast toast-${toast.type}`}>
            <Icon size={18} />
            <span>{toast.message}</span>
          </div>
        );
      })}
    </div>
  );
}
