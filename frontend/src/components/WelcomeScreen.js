import React from 'react';

const WelcomeScreen = ({ user, onSuggestionClick }) => {
  const suggestions = [
    "What are my consumer rights?",
    "How to file a legal complaint?",
    "Employment law basics"
  ];

  return (
    <div className="text-center py-12">
      <div className="w-20 h-20 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl">
        <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253z"></path>
        </svg>
      </div>
      
      <h2 className="text-3xl font-bold text-cyan-50 mb-4">Welcome to Clegora</h2>
      <p className="text-cyan-200 mb-8 text-lg max-w-2xl mx-auto">
        Ask me anything about legal matters and I'll provide helpful information based on legal documents.
      </p>
      
      {user ? (
        <div className="flex flex-wrap justify-center gap-3">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => onSuggestionClick(suggestion)}
              className="bg-slate-800/60 backdrop-blur-sm border border-slate-600/50 rounded-full px-6 py-3 text-sm text-cyan-100 hover:bg-slate-700/60 hover:border-cyan-400/50 transition-all shadow-lg"
            >
              {suggestion}
            </button>
          ))}
        </div>
      ) : (
        <p className="text-slate-400">Please sign in to start chatting</p>
      )}
    </div>
  );
};

export default WelcomeScreen;
