import { Hammer, Bell } from 'lucide-react';

export function Header() {
  return (
    <header className="flex items-center justify-between border-b border-gray-100 bg-white px-6 py-3.5 shrink-0">
      <div className="flex items-center gap-3">
        {/* Brand Icon */}
        <div className="flex items-center justify-center w-9 h-9 bg-emerald-500 rounded-xl shadow-sm">
          <Hammer size={18} className="text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-gray-900 leading-tight">Luật Sư AI</h1>
          <p className="text-xs text-emerald-600 font-medium">Trí Tuệ Pháp Lý Chuyên Nghiệp</p>
        </div>
      </div>
      
      {/* Utility Toolbar */}
      <div className="flex items-center gap-3">
        <button className="relative flex items-center justify-center w-9 h-9 rounded-full hover:bg-gray-100 transition-colors">
          <Bell size={18} className="text-gray-500" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-emerald-500 rounded-full border border-white"></span>
        </button>
        
        {/* User Account Avatar */}
        <div className="w-9 h-9 rounded-full overflow-hidden ring-2 ring-emerald-200 shadow-sm">
          <div className="w-full h-full bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">U</span>
          </div>
        </div>
      </div>
    </header>
  );
}
