import { quickActions } from '../data/initialMessages';
import { Icon } from './Icon';

export function QuickActions({ onActionClick }) {
  return (
    <aside className="hidden lg:flex flex-col w-72 shrink-0 border-l border-gray-100 bg-white overflow-y-auto">
      <div className="px-5 pt-6 pb-4 border-b border-gray-100">
        <h2 className="text-base font-bold text-gray-900">Hành động nhanh</h2>
        <p className="text-xs text-gray-400 mt-0.5">Chọn một nhiệm vụ để bắt đầu</p>
      </div>
      
      {/* Dynamic Action Grid */}
      <div className="flex flex-col gap-2 px-4 py-4">
        {quickActions.map((action) => (
          <button
            key={action.id}
            onClick={() => onActionClick(action.label)}
            className="quick-action-card flex items-center gap-3 rounded-xl border border-gray-100 bg-gray-50 px-4 py-3.5 text-left hover:border-emerald-200 hover:bg-emerald-50 group transition-all"
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white border border-gray-200 shadow-sm group-hover:border-emerald-300 group-hover:bg-emerald-50 transition-colors">
              <Icon
                name={action.icon}
                size={17}
                className="text-gray-500 group-hover:text-emerald-600 transition-colors"
              />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-gray-800 group-hover:text-emerald-800 leading-snug truncate">
                {action.label}
              </p>
              <p className="text-xs text-gray-400 group-hover:text-emerald-500 truncate mt-0.5">
                {action.description}
              </p>
            </div>
          </button>
        ))}
      </div>

      {/* Instructional Footer */}
      <div className="mt-auto px-5 py-4 border-t border-gray-100">
        <div className="rounded-xl bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100 p-4">
          <p className="text-xs font-semibold text-emerald-800">💡 Mẹo trong ngày</p>
          <p className="text-xs text-emerald-700 mt-1 leading-relaxed">
            Đính kèm tệp PDF hoặc Word để phân tích pháp lý chi tiết và tóm tắt nội dung quan trọng.
          </p>
        </div>
      </div>
    </aside>
  );
}
