import { useState, useRef, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { MessageList } from './components/MessageList';
import { InputArea } from './components/InputArea';
import { QuickActions } from './components/QuickActions';
import { initialMessages } from './data/initialMessages';

export default function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [messages, setMessages] = useState(initialMessages);
  const [isTyping, setIsTyping] = useState(false);
  const bottomRef = useRef(null);

  // Auto-scroll to bottom whenever a new message is added or when typing state changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  /**
   * Handles sending a new message to the AI backend.
   * Uses async/await to call the FastAPI endpoint deployed on Render.
   */
  const handleSend = useCallback(async (text, file) => {
    if (!text && !file) return;

    // Formatting attachment message for display
    const userMessageText = file ? `${text ? text + '\n' : ''}📎 Attachment: ${file.name}` : text;
    
    const userMessage = {
      id: Date.now(),
      role: 'user',
      text: userMessageText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    
    // Set loading indicator while waiting for API response
    setIsTyping(true);

    try {
      // POST request to the local backend AI endpoint
      const response = await fetch("https://citizen-helper-api.onrender.com/api/chat", {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: userMessageText }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();

      setIsTyping(false);
      
      // Update UI with the dynamic response from the AI engine
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          role: 'ai',
          text: data.response,
          chips: [], // Backend currently handles only text responses
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      console.error('API Error:', error);
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          role: 'ai',
          text: 'The legal assistant system is currently undergoing maintenance or experiencing a connection timeout. Please try again in a few moments.',
          chips: [],
          timestamp: new Date(),
        },
      ]);
    }
  }, []);

  const handleChipClick = useCallback((chip) => {
    handleSend(chip, null);
  }, [handleSend]);

  const handleActionClick = useCallback((actionLabel) => {
    handleSend(`Action required: ${actionLabel}`, null);
  }, [handleSend]);

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Navigation Sidebar */}
      <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed((v) => !v)} />

      {/* Main UI Layout */}
      <div className="flex flex-1 flex-col overflow-hidden min-w-0">
        {/* Top Header */}
        <Header />

        {/* Primary Content Panes */}
        <div className="flex flex-1 overflow-hidden">
          {/* Conversational Interface Area */}
          <main className="flex flex-1 flex-col overflow-hidden bg-gray-50">
            <MessageList
              messages={messages}
              isTyping={isTyping}
              onChipClick={handleChipClick}
              bottomRef={bottomRef}
            />
            <InputArea onSend={handleSend} disabled={isTyping} />
            <footer className="text-center py-3 text-xs text-gray-400 border-t border-gray-100 bg-white">
              © 2025 Luật Sư AI. All rights reserved.
            </footer>
          </main>

          {/* Quick Access Side Panel */}
          <QuickActions onActionClick={handleActionClick} />
        </div>
      </div>
    </div>
  );
}
