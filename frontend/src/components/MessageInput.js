import React, { useState } from 'react';

const MessageInput = ({ onSendMessage, disabled, isLoading }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  return (
    <div className="bg-slate-800/90 backdrop-blur-sm rounded-full shadow-2xl border border-slate-600/50 p-2">
      <form onSubmit={handleSubmit} className="flex items-center space-x-2">
        <div className="flex-1">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? "Sign in to chat..." : "Ask me anything..."}
            className="w-full px-4 py-3 bg-transparent text-cyan-50 placeholder-slate-400 focus:outline-none"
            disabled={disabled}
          />
        </div>
        <button
          type="submit"
          disabled={disabled || !message.trim() || isLoading}
          className="w-10 h-10 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-full hover:from-cyan-600 hover:to-blue-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
            </svg>
          )}
        </button>
      </form>
    </div>
  );
};

export default MessageInput;
