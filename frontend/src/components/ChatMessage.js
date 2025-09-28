import React, { useState, useEffect, useRef } from 'react';

const ChatMessage = ({ message }) => {
  const { content, sender, isTyping, sources, isStreaming } = message;
  const [displayedContent, setDisplayedContent] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const timeoutRef = useRef(null);
  
  const isUser = sender === 'user';

  // Simple markdown parser for bold text
  const parseMarkdown = (text) => {
    if (!text) return text;
    
    // Split text by **bold** patterns
    const parts = text.split(/\*\*(.*?)\*\*/g);
    
    return parts.map((part, index) => {
      // Every odd index is bold text (captured groups)
      if (index % 2 === 1) {
        return <strong key={index} className="font-bold">{part}</strong>;
      }
      return part;
    });
  };

  // Calculate typing speed based on character position
  const getTypingDelay = (index, totalLength) => {
    const firstLineChars = 100; // First ~100 characters (2 lines) are fast
    const secondLineChars = 200; // Next ~100 characters are medium speed
    
    if (index < firstLineChars) {
      return 15; // Fast typing for first couple lines
    } else if (index < secondLineChars) {
      return 25; // Medium speed for next lines
    } else {
      return 40; // Slower for remaining content
    }
  };

  // Handle content display based on streaming state
  useEffect(() => {
    if (isUser) {
      // For user messages, always show full content
      setDisplayedContent(content);
    } else if (isStreaming && content) {
      // For streaming bot messages with typing effect
      if (content.length > displayedContent.length) {
        // New content arrived, start/continue typing effect
        const typeNextChar = () => {
          setDisplayedContent(prev => {
            const nextIndex = prev.length;
            if (nextIndex < content.length) {
              const newContent = content.slice(0, nextIndex + 1);
              const delay = getTypingDelay(nextIndex, content.length);
              
              timeoutRef.current = setTimeout(typeNextChar, delay);
              return newContent;
            }
            return prev;
          });
        };
        
        // Clear any existing timeout
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        
        // Start typing if we're behind
        if (displayedContent.length < content.length) {
          const delay = getTypingDelay(displayedContent.length, content.length);
          timeoutRef.current = setTimeout(typeNextChar, delay);
        }
      }
    } else if (!isStreaming && content) {
      // For completed bot messages, show full content immediately
      setDisplayedContent(content);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    } else if (isTyping) {
      // For typing state, show empty content
      setDisplayedContent('');
      setCurrentIndex(0);
    }
  }, [content, isStreaming, isTyping, isUser, displayedContent.length]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`flex max-w-3xl w-full ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-semibold shadow-lg flex-shrink-0 ${
          isUser 
            ? 'bg-gradient-to-br from-cyan-400 to-blue-500 ml-3' 
            : 'bg-gradient-to-br from-slate-700 to-slate-800 mr-3 border-2 border-cyan-200'
        }`}>
          {isUser ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
        </div>
        
        {/* Message Content */}
        <div className={`flex-1 p-4 rounded-xl shadow-lg ${
          isUser 
            ? 'bg-gradient-to-br from-cyan-500 to-blue-600 text-white max-w-sm' 
            : 'bg-slate-800 text-cyan-50 border border-slate-700'
        }`}>
          {isTyping ? (
            <div className="flex space-x-1 p-2">
              <div className="typing-indicator"></div>
              <div className="typing-indicator"></div>
              <div className="typing-indicator"></div>
            </div>
          ) : (
            <div className="whitespace-pre-wrap">
              {isUser ? displayedContent : parseMarkdown(displayedContent)}
              {!isUser && isStreaming && displayedContent.length < content.length && (
                <span className="animate-pulse text-cyan-400">|</span>
              )}
            </div>
          )}
          
          {/* Sources */}
          {sources && sources.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-600">
              <div className="text-xs text-cyan-300 mb-2">Sources:</div>
              <div className="space-y-2">
                {sources.map((source, index) => (
                  <div key={index} className="bg-slate-700 p-2 rounded text-xs border border-slate-600">
                    <div className="font-medium text-cyan-200">{source.title}</div>
                    <div className="text-slate-300">
                      {source.source} • Relevance: {(source.similarity * 100).toFixed(1)}%
                    </div>
                    <div className="text-slate-400 mt-1">{source.content_preview}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
