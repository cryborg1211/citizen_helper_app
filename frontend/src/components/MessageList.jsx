import { Bot } from 'lucide-react';

function TypingIndicator() {
  return (
    <div className="flex items-end gap-3 message-enter">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100">
        <Bot size={16} className="text-emerald-600" />
      </div>
      <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-sm bg-white border border-gray-200 px-4 py-3 shadow-sm">
        <span className="typing-dot block w-2 h-2 rounded-full bg-emerald-400"></span>
        <span className="typing-dot block w-2 h-2 rounded-full bg-emerald-400"></span>
        <span className="typing-dot block w-2 h-2 rounded-full bg-emerald-400"></span>
      </div>
    </div>
  );
}

function AiMessage({ message, onChipClick }) {
  const paragraphs = message.text.split('\n').filter(Boolean);

  return (
    <div className="flex items-end gap-3 message-enter">
      {/* Bot Avatar */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100">
        <Bot size={16} className="text-emerald-600" />
      </div>
      <div className="flex flex-col gap-2 max-w-[75%]">
        {/* Message Bubble */}
        <div className="rounded-2xl rounded-bl-sm bg-white border border-gray-200 px-4 py-3 shadow-sm">
          <div className="text-sm text-gray-700 leading-relaxed space-y-1.5">
            {paragraphs.map((para, i) => {
              // Simple Markdown Bold Handling
              const parts = para.split(/(\*\*[^*]+\*\*)/g);
              return (
                <p key={i}>
                  {parts.map((part, j) =>
                    part.startsWith('**') && part.endsWith('**') ? (
                      <strong key={j} className="font-semibold text-gray-900">
                        {part.slice(2, -2)}
                      </strong>
                    ) : (
                      <span key={j}>{part}</span>
                    )
                  )}
                </p>
              );
            })}
          </div>
        </div>
        {/* Suggestion Chips */}
        {message.chips && message.chips.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.chips.map((chip) => (
              <button
                key={chip}
                onClick={() => onChipClick(chip)}
                className="chip rounded-full border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-600 shadow-sm transition-colors hover:border-emerald-400 hover:text-emerald-600"
              >
                {chip}
              </button>
            ))}
          </div>
        )}
        <span className="text-xs text-gray-400 pl-1">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
}

function UserMessage({ message }) {
  return (
    <div className="flex items-end justify-end gap-3 message-enter">
      <div className="flex flex-col items-end gap-1 max-w-[70%]">
        <div className="rounded-2xl rounded-br-sm bg-emerald-500 px-4 py-3 shadow-sm">
          <p className="text-sm text-white leading-relaxed">{message.text}</p>
        </div>
        <span className="text-xs text-gray-400 pr-1">
          {formatTime(message.timestamp)}
        </span>
      </div>
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 to-teal-600">
        <span className="text-white font-bold text-xs">U</span>
      </div>
    </div>
  );
}

function formatTime(date) {
  if (!date) return '';
  return date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
}

export function MessageList({ messages, isTyping, onChipClick, bottomRef }) {
  return (
    <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5">
      {/* Dynamic Conversation Header */}
      <div className="text-center mb-4">
        <h2 className="text-xl font-bold text-gray-800">Trò chuyện với AI Pháp lý</h2>
        <p className="text-sm text-gray-400 mt-1">Thông tin chỉ mang tính chất tham khảo</p>
      </div>

      {messages.map((msg) =>
        msg.role === 'ai' ? (
          <AiMessage key={msg.id} message={msg} onChipClick={onChipClick} />
        ) : (
          <UserMessage key={msg.id} message={msg} />
        )
      )}

      {isTyping && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}
