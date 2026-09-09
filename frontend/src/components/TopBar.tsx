import { Search, Bell, Sun, Moon } from 'lucide-react'
import { useAuthStore, useUIStore } from '../stores/store'

export default function TopBar() {
  const user = useAuthStore((s) => s.user)
  const { theme, toggleTheme } = useUIStore()

  return (
    <header
      className="h-14 flex items-center justify-between px-6 border-b border-[var(--border)] flex-shrink-0"
      style={{ background: 'var(--surface)' }}
    >
      {/* Search */}
      <div className="relative flex-1 max-w-md">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
        <input
          type="text"
          placeholder="Search leads, contacts, deals..."
          className="input pl-9 h-8 text-xs w-full"
        />
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-3">
        <button
          onClick={toggleTheme}
          className="btn-ghost h-8 w-8 p-0 flex items-center justify-center rounded-lg"
        >
          {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
        </button>

        <button className="btn-ghost h-8 w-8 p-0 flex items-center justify-center rounded-lg relative">
          <Bell size={14} />
          <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-red-500 rounded-full" />
        </button>

        {/* Avatar */}
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary-500 to-violet-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
            {user?.first_name?.[0]}{user?.last_name?.[0]}
          </div>
          <div className="hidden sm:block">
            <p className="text-xs font-semibold text-[var(--text)] leading-none">{user?.full_name}</p>
            <p className="text-[10px] text-[var(--text-muted)] capitalize">{user?.role?.replace('_', ' ')}</p>
          </div>
        </div>
      </div>
    </header>
  )
}
