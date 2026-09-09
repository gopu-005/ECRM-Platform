import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Users, UserCheck, Building2, TrendingUp,
  CheckSquare, Calendar, Activity, Bell, BarChart3, LineChart,
  PieChart, Award, ShieldCheck, Settings, LogOut, ChevronLeft,
  Zap, Menu
} from 'lucide-react'
import { useAuthStore, useUIStore } from '../stores/store'
import { authApi } from '../lib/api'
import { cn } from '../lib/utils'
import toast from 'react-hot-toast'

const navGroups = [
  {
    label: 'Main',
    items: [
      { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    ],
  },
  {
    label: 'CRM',
    items: [
      { to: '/leads', icon: Zap, label: 'Leads' },
      { to: '/contacts', icon: UserCheck, label: 'Contacts' },
      { to: '/accounts', icon: Building2, label: 'Accounts' },
      { to: '/deals/pipeline', icon: TrendingUp, label: 'Pipeline' },
      { to: '/deals', icon: TrendingUp, label: 'Deals' },
    ],
  },
  {
    label: 'Productivity',
    items: [
      { to: '/tasks', icon: CheckSquare, label: 'Tasks' },
      { to: '/meetings', icon: Calendar, label: 'Meetings' },
      { to: '/activities', icon: Activity, label: 'Activities' },
      { to: '/notifications', icon: Bell, label: 'Notifications' },
    ],
  },
  {
    label: 'Analytics',
    items: [
      { to: '/analytics', icon: BarChart3, label: 'Overview' },
      { to: '/analytics/leads', icon: Zap, label: 'Lead Analytics' },
      { to: '/analytics/pipeline', icon: PieChart, label: 'Pipeline' },
      { to: '/analytics/revenue', icon: LineChart, label: 'Revenue' },
      { to: '/analytics/team', icon: Award, label: 'Team' },
    ],
  },
  {
    label: 'Admin',
    items: [
      { to: '/admin/users', icon: Users, label: 'Users' },
      { to: '/admin/audit-logs', icon: ShieldCheck, label: 'Audit Logs' },
      { to: '/settings', icon: Settings, label: 'Settings' },
    ],
  },
]

export default function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore()
  const { clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } catch {}
    clearAuth()
    navigate('/login')
    toast.success('Logged out successfully')
  }

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-full z-40 flex flex-col transition-all duration-300',
        'border-r border-[var(--border)]',
        sidebarOpen ? 'w-64' : 'w-16'
      )}
      style={{ background: 'var(--surface)' }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-[var(--border)]">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-violet-600 flex items-center justify-center flex-shrink-0">
          <Zap size={16} className="text-white" />
        </div>
        {sidebarOpen && (
          <span className="font-bold text-base text-[var(--text)] tracking-tight">
            ECRM<span className="text-primary-400">.</span>
          </span>
        )}
        <button
          onClick={toggleSidebar}
          className="ml-auto text-[var(--text-muted)] hover:text-[var(--text)] transition-colors"
        >
          {sidebarOpen ? <ChevronLeft size={16} /> : <Menu size={16} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-4">
        {navGroups.map((group) => (
          <div key={group.label}>
            {sidebarOpen && (
              <p className="px-3 mb-1 text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)]">
                {group.label}
              </p>
            )}
            <div className="space-y-0.5">
              {group.items.map(({ to, icon: Icon, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/dashboard'}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150',
                      isActive
                        ? 'bg-primary-600/15 text-primary-400 border border-primary-600/20'
                        : 'text-[var(--text-muted)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]',
                      !sidebarOpen && 'justify-center'
                    )
                  }
                  title={!sidebarOpen ? label : undefined}
                >
                  <Icon size={16} className="flex-shrink-0" />
                  {sidebarOpen && <span>{label}</span>}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Logout */}
      <div className="p-2 border-t border-[var(--border)]">
        <button
          onClick={handleLogout}
          className={cn(
            'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium w-full',
            'text-[var(--text-muted)] hover:bg-red-500/10 hover:text-red-400 transition-all duration-150',
            !sidebarOpen && 'justify-center'
          )}
        >
          <LogOut size={16} className="flex-shrink-0" />
          {sidebarOpen && <span>Logout</span>}
        </button>
      </div>
    </aside>
  )
}
