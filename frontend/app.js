// Firebase configuration
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js';
import { getAuth, signInWithPopup, GoogleAuthProvider, signOut, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js';

// Firebase config - replace with your actual config
const firebaseConfig = {
    apiKey: "your-api-key",
    authDomain: "your-auth-domain",
    projectId: "your-project-id",
    storageBucket: "your-storage-bucket",
    messagingSenderId: "your-sender-id",
    appId: "your-app-id"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

// API Configuration
const API_BASE_URL = 'http://localhost:8001';

// Global state
let currentUser = null;
let conversationId = null;
let isProcessing = false;

// DOM Elements
const signInBtn = document.getElementById('sign-in-btn');
const signOutBtn = document.getElementById('sign-out-btn');
const userInfo = document.getElementById('user-info');
const userEmail = document.getElementById('user-email');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const chatContainer = document.getElementById('chat-container');
const welcomeMessage = document.getElementById('welcome-message');
const loadingOverlay = document.getElementById('loading-overlay');

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    setupAuthStateListener();
});

function setupEventListeners() {
    // Auth buttons
    signInBtn.addEventListener('click', signIn);
    signOutBtn.addEventListener('click', handleSignOut);
    
    // Message input
    messageInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            sendMessage();
        }
    });
    
    sendBtn.addEventListener('click', sendMessage);
    
    // Suggestion buttons
    document.querySelectorAll('.suggestion-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (currentUser) {
                messageInput.value = btn.textContent.trim();
                sendMessage();
            }
        });
    });
}

function setupAuthStateListener() {
    onAuthStateChanged(auth, (user) => {
        currentUser = user;
        updateUI();
    });
}

async function signIn() {
    try {
        loadingOverlay.classList.remove('hidden');
        const result = await signInWithPopup(auth, provider);
        console.log('Signed in:', result.user.email);
    } catch (error) {
        console.error('Sign in error:', error);
        alert('Failed to sign in. Please try again.');
    } finally {
        loadingOverlay.classList.add('hidden');
    }
}

async function handleSignOut() {
    try {
        await signOut(auth);
        conversationId = null;
        chatContainer.innerHTML = '';
        chatContainer.classList.add('hidden');
        welcomeMessage.classList.remove('hidden');
    } catch (error) {
        console.error('Sign out error:', error);
    }
}

function updateUI() {
    if (currentUser) {
        // User is signed in
        signInBtn.classList.add('hidden');
        userInfo.classList.remove('hidden');
        userEmail.textContent = currentUser.email;
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.placeholder = "Ask me anything about legal matters...";
        document.querySelector('.mt-2.text-xs').textContent = "Press Ctrl+Enter to send";
    } else {
        // User is signed out
        signInBtn.classList.remove('hidden');
        userInfo.classList.add('hidden');
        messageInput.disabled = true;
        sendBtn.disabled = true;
        messageInput.placeholder = "Please sign in to start chatting...";
        document.querySelector('.mt-2.text-xs').textContent = "Press Ctrl+Enter to send • Please sign in to start chatting";
    }
}

async function sendMessage() {
    if (!currentUser || isProcessing || !messageInput.value.trim()) {
        return;
    }
    
    const message = messageInput.value.trim();
    messageInput.value = '';
    isProcessing = true;
    sendBtn.disabled = true;
    
    // Hide welcome message and show chat
    welcomeMessage.classList.add('hidden');
    chatContainer.classList.remove('hidden');
    
    // Add user message
    addMessage(message, 'user');
    
    // Add assistant message placeholder
    const assistantMessageId = addMessage('', 'assistant', true);
    
    try {
        await streamResponse(message, assistantMessageId);
    } catch (error) {
        console.error('Error sending message:', error);
        updateMessage(assistantMessageId, 'Sorry, I encountered an error. Please try again.', false);
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
    }
}

function addMessage(content, sender, isTyping = false) {
    const messageId = 'msg-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} mb-4`;
    
    const avatar = sender === 'user' 
        ? `<div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium ml-3">${currentUser?.email?.[0]?.toUpperCase() || 'U'}</div>`
        : `<div class="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center text-white text-sm font-medium mr-3">AI</div>`;
    
    const messageContent = isTyping 
        ? `<div class="flex space-x-1 p-2"><div class="typing-indicator"></div><div class="typing-indicator"></div><div class="typing-indicator"></div></div>`
        : `<div class="message-content">${content}</div>`;
    
    messageDiv.innerHTML = `
        <div class="flex max-w-3xl ${sender === 'user' ? 'flex-row-reverse' : 'flex-row'}">
            ${avatar}
            <div class="mx-3 p-3 rounded-lg ${sender === 'user' ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200'} shadow-sm">
                ${messageContent}
                <div class="sources-container mt-2 hidden"></div>
            </div>
        </div>
    `;
    
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return messageId;
}

function updateMessage(messageId, content, isTyping = false, sources = []) {
    const messageDiv = document.getElementById(messageId);
    if (!messageDiv) return;
    
    const contentDiv = messageDiv.querySelector('.message-content') || messageDiv.querySelector('.flex.space-x-1');
    if (contentDiv) {
        if (isTyping) {
            contentDiv.innerHTML = `<div class="flex space-x-1 p-2"><div class="typing-indicator"></div><div class="typing-indicator"></div><div class="typing-indicator"></div></div>`;
        } else {
            contentDiv.innerHTML = content;
            contentDiv.className = 'message-content';
        }
    }
    
    // Add sources if provided
    if (sources && sources.length > 0) {
        const sourcesContainer = messageDiv.querySelector('.sources-container');
        if (sourcesContainer) {
            sourcesContainer.classList.remove('hidden');
            sourcesContainer.innerHTML = `
                <div class="mt-3 pt-3 border-t border-gray-100">
                    <div class="text-xs text-gray-500 mb-2">Sources:</div>
                    <div class="space-y-2">
                        ${sources.map(source => `
                            <div class="source-card bg-gray-50 p-2 rounded text-xs">
                                <div class="font-medium text-gray-700">${source.title}</div>
                                <div class="text-gray-500">${source.source} • Relevance: ${(source.similarity * 100).toFixed(1)}%</div>
                                <div class="text-gray-600 mt-1">${source.content_preview}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
    }
    
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

async function streamResponse(message, messageId) {
    try {
        const token = await currentUser.getIdToken();
        
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
                userId: currentUser.uid,
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
                            // Keep showing typing indicator
                            continue;
                        } else if (parsed.type === 'token') {
                            updateMessage(messageId, parsed.content, false);
                        } else if (parsed.type === 'complete') {
                            updateMessage(messageId, parsed.content, false, parsed.sources);
                            conversationId = parsed.conversationId;
                            return;
                        } else if (parsed.type === 'error') {
                            updateMessage(messageId, `Error: ${parsed.content}`, false);
                            return;
                        }
                    } catch (e) {
                        // Handle non-JSON data as plain text
                        if (data.trim()) {
                            updateMessage(messageId, data, false);
                        }
                    }
                }
            }
        }
    } catch (error) {
        console.error('Streaming error:', error);
        throw error;
    }
}
