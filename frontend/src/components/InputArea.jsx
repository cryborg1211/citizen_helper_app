import { useRef, useState } from 'react';
import { Paperclip, Send } from 'lucide-react';

export function InputArea({ onSend, disabled }) {
  const [value, setValue] = useState('');
  const [attachedFile, setAttachedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed && !attachedFile) return;
    onSend(trimmed, attachedFile);
    setValue('');
    setAttachedFile(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) setAttachedFile(file);
  };

  return (
    <div className="border-t border-gray-100 bg-white px-6 py-4 shrink-0">
      {/* Attachment indicator */}
      {attachedFile && (
        <div className="mb-2 flex items-center gap-2">
          <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs text-emerald-700">
            <Paperclip size={12} />
            <span className="max-w-48 truncate font-medium">{attachedFile.name}</span>
            <button
              onClick={() => setAttachedFile(null)}
              className="ml-1 text-emerald-500 hover:text-emerald-700 font-bold"
            >
              ×
            </button>
          </div>
        </div>
      )}

      <div className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3 shadow-sm focus-within:border-emerald-400 focus-within:bg-white focus-within:shadow-md transition-all">
        {/* Attachment button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex shrink-0 items-center justify-center rounded-lg p-1.5 text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 transition-colors"
          title="Đính kèm tài liệu"
          disabled={disabled}
        >
          <Paperclip size={20} />
        </button>
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          accept=".pdf,.doc,.docx,.txt"
          onChange={handleFileChange}
        />

        {/* Dynamic height textarea */}
        <textarea
          id="chat-input"
          rows={1}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            // Auto-resize logic
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px';
          }}
          onKeyDown={handleKeyDown}
          placeholder="Gửi tin nhắn của bạn..."
          disabled={disabled}
          className="flex-1 resize-none bg-transparent text-sm text-gray-800 placeholder-gray-400 outline-none disabled:opacity-60 leading-relaxed"
          style={{ maxHeight: '140px', overflowY: 'auto' }}
        />

        {/* Send message button */}
        <button
          id="send-btn"
          onClick={handleSend}
          disabled={disabled || (!value.trim() && !attachedFile)}
          className="send-btn flex shrink-0 items-center justify-center w-9 h-9 rounded-xl bg-emerald-500 text-white shadow-sm hover:bg-emerald-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-95"
          title="Gửi"
        >
          <Send size={16} className="-translate-x-px translate-y-px rotate-0" style={{ transform: 'rotate(-20deg)' }} />
        </button>
      </div>

      <p className="mt-2 text-center text-xs text-gray-400">
        Luật Sư AI có thể nhầm lẫn. Vui lòng kiểm tra lại các thông tin quan trọng với chuyên gia pháp lý.
      </p>
    </div>
  );
}
