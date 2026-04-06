import { MessageSquare, Plus, History, Settings } from 'lucide-react';

export function Sidebar({ collapsed, onToggle }) {
  const navItems = [
    { icon: <MessageSquare size={18} />, label: 'Chat box', active: true },
    { icon: <History size={18} />, label: 'Lịch sử', active: false },
    { icon: <Plus size={18} />, label: 'Cuộc hội thoại mới', active: false },
  ];

  return (
    <aside
      className={`sidebar-transition flex flex-col border-r border-gray-100 bg-white ${
        collapsed ? 'w-16 min-w-16' : 'w-56 min-w-56'
      } relative shrink-0`}
    >
      {/* Toggle button */}
      <button
        onClick={onToggle}
        className="absolute -right-3 top-5 z-10 flex h-6 w-6 items-center justify-center rounded-full border border-gray-200 bg-white shadow-sm hover:bg-emerald-50 hover:border-emerald-300 transition-colors"
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? (
          <svg className="w-3 h-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        ) : (
          <svg className="w-3 h-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        )}
      </button>

      {/* Logo area */}
      <div className={`flex items-center gap-3 px-4 py-4 border-b border-gray-100 ${collapsed ? 'justify-center' : ''}`}>
        <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center shrink-0">
          <svg viewBox="0 0 24 24" fill="white" className="w-4 h-4">
            <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z" />
          </svg>
        </div>
        {!collapsed && (
          <span className="font-semibold text-gray-800 text-sm whitespace-nowrap">
            Luật Sư AI
          </span>
        )}
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-2 py-3 space-y-1">
        {navItems.map((item, idx) => (
          <button
            key={idx}
            className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
              item.active
                ? 'bg-emerald-50 text-emerald-700'
                : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
            } ${collapsed ? 'justify-center' : ''}`}
            title={collapsed ? item.label : ''}
          >
            <span className={item.active ? 'text-emerald-600' : ''}>{item.icon}</span>
            {!collapsed && <span className="truncate">{item.label}</span>}
          </button>
        ))}
      </nav>

      {/* Settings section */}
      <div className={`px-2 pb-4 border-t border-gray-100 pt-3`}>
        <button
          className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition-all ${
            collapsed ? 'justify-center' : ''
          }`}
          title={collapsed ? 'Settings' : ''}
        >
          <Settings size={18} />
          {!collapsed && <span>Cài đặt</span>}
        </button>
      </div>
    </aside>
  );
}
