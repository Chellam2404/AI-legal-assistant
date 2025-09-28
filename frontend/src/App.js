import React, { useState, useEffect, useRef } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signOut, onAuthStateChanged } from 'firebase/auth';
import ChatMessage from './components/ChatMessage';
import MessageInput from './components/MessageInput';
import Header from './components/Header';
import WelcomeScreen from './components/WelcomeScreen';
import AuthScreen from './components/AuthScreen';

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyA3zW4kZ_dT5jIKPI4qI5FyqgXb0ZSVxAM",
  authDomain: "clegora.firebaseapp.com",
  projectId: "clegora",
  storageBucket: "clegora.firebasestorage.app",
  messagingSenderId: "325502068501",
  appId: "1:325502068501:web:21d8d0ac71f017b22deb1c",
  measurementId: "G-JT7PG2KS5T"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

const API_BASE_URL = 'http://localhost:8001';

function App() {
  const [user, setUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [showAuthScreen, setShowAuthScreen] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      if (user) {
        setShowAuthScreen(false);
      }
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSignIn = async () => {
    setShowAuthScreen(true);
  };

  const handleSignOut = async () => {
    try {
      await signOut(auth);
      setMessages([]);
      setConversationId(null);
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  const handleSendMessage = async (message) => {
    if (!user || isLoading) return;

    // Add user message
    const userMessage = {
      id: Date.now(),
      content: message,
      sender: 'user',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    // Add assistant placeholder
    const assistantMessage = {
      id: Date.now() + 1,
      content: '',
      sender: 'assistant',
      timestamp: new Date(),
      isTyping: true,
      isStreaming: false,
      sources: []
    };
    setMessages(prev => [...prev, assistantMessage]);

    setIsLoading(true);

    try {
      await streamResponse(message, assistantMessage.id);
    } catch (error) {
      console.error('Error sending message:', error);
      updateMessage(assistantMessage.id, {
        content: 'Sorry, I encountered an error. Please try again.',
        isTyping: false
      });
    } finally {
      setIsLoading(false);
    }
  };

  const updateMessage = (messageId, updates) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, ...updates } : msg
    ));
  };

  const streamResponse = async (message, messageId) => {
    try {
      const token = await user.getIdToken();
      
      const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache',
        },
        body: JSON.stringify({
          query: message,
          userId: user.uid,
          conversationId: conversationId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            
            if (data === '[DONE]') {
              return;
            }

            try {
              const parsed = JSON.parse(data);
              
              if (parsed.type === 'status') {
                // Initial status message
                updateMessage(messageId, {
                  content: parsed.content,
                  isTyping: false,
                  isStreaming: true
                });
              } else if (parsed.type === 'token') {
                // Streaming token updates
                updateMessage(messageId, {
                  content: parsed.content,
                  isTyping: false,
                  isStreaming: true
                });
              } else if (parsed.type === 'sources') {
                // Sources received
                updateMessage(messageId, {
                  sources: parsed.sources || []
                });
              } else if (parsed.type === 'complete') {
                // Final complete message
                updateMessage(messageId, {
                  content: parsed.content,
                  isTyping: false,
                  isStreaming: false,
                  sources: parsed.sources || []
                });
                setConversationId(parsed.conversationId);
                return;
              } else if (parsed.type === 'error') {
                updateMessage(messageId, {
                  content: `Error: ${parsed.content}`,
                  isTyping: false,
                  isStreaming: false
                });
                return;
              }
            } catch (e) {
              // Handle non-JSON data
              if (data.trim()) {
                updateMessage(messageId, {
                  content: data,
                  isTyping: false,
                  isStreaming: false
                });
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      throw error;
    }
  };

  const handleSuggestionClick = (suggestion) => {
    if (user) {
      handleSendMessage(suggestion);
    }
  };

  const handleAuthSuccess = () => {
    setShowAuthScreen(false);
  };

  // Show auth screen if user is not logged in or explicitly requested
  if (!user || showAuthScreen) {
    return (
      <AuthScreen 
        auth={auth}
        provider={provider}
        onAuthSuccess={handleAuthSuccess}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      <Header 
        user={user} 
        onSignIn={handleSignIn} 
        onSignOut={handleSignOut}
        isLoading={isLoading}
      />
      
      <main className="flex-1 max-w-4xl mx-auto px-4 py-6 pb-20 overflow-y-auto">
        {messages.length === 0 ? (
          <WelcomeScreen 
            user={user} 
            onSuggestionClick={handleSuggestionClick}
          />
        ) : (
          <div className="space-y-6 mb-6">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>
      
      {/* Floating minimal input */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 w-full max-w-2xl px-4">
        <MessageInput 
          onSendMessage={handleSendMessage}
          disabled={!user || isLoading}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}

export default App;
