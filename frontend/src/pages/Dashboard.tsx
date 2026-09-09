import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '../lib/api'
import { formatCurrency, formatNumber, timeAgo, getDealStageBadgeClass, getLeadStatusBadge } from '../lib/utils'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import {
  TrendingUp, Users, Building2, Zap, DollarSign,
  CheckSquare, Calendar, Activity, ArrowUpRight, ArrowDownRight, Minus
} from 'lucide-react'

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4']

function KPICard({ label, value, unit, icon: Icon, color = 'blue' }: any) {
  const colorMap: Record<string, string> = {
    blue: 'from-blue-500/20 to-blue-600/5 border-blue-500/20',
    green: 'from-emerald-500/20 to-emerald-600/5 border-emerald-500/20',
    purple: 'from-violet-500/20 to-violet-600/5 border-violet-500/20',
    amber: 'from-amber-500/20 to-amber-600/5 border-amber-500/20',
    red: 'from-red-500/20 to-red-600/5 border-red-500/20',
    cyan: 'from-cyan-500/20 to-cyan-600/5 border-cyan-500/20',
  }
  const iconColorMap: Record<string, string> = {
    blue: 'text-blue-400',
    green: 'text-emerald-400',
    purple: 'text-violet-400',
    amber: 'text-amber-400',
    red: 'text-red-400',
    cyan: 'text-cyan-400',
  }

  return (
    <div className={`card p-5 bg-gradient-to-br ${colorMap[color]} border relative overflow-hidden`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">{label}</p>
          <p className="text-2xl font-bold text-[var(--text)] mt-1">
            {unit === 'USD' ? formatCurrency(Number(value)) :
             unit === '%' ? `${value}%` :
             formatNumber(Number(value))}
          </p>
        </div>
        <div className={`p-2 rounded-lg bg-[var(--surface-2)] ${iconColorMap[color]}`}>
          <Icon size={18} />
        </div>
      </div>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="card py-2 px-3 text-xs">
      <p className="font-medium text-[var(--text)]">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} style={{ color: entry.color }}>
          {entry.name}: {typeof entry.value === 'number' && entry.name?.includes('revenue')
            ? formatCurrency(entry.value)
            : entry.value}
        </p>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'dashboard'],
    queryFn: () => analyticsApi.dashboard().then((r) => r.data),
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="card h-24 animate-pulse bg-[var(--surface-2)]" />
          ))}
        </div>
      </div>
    )
  }

  const kpis = data?.kpis || {}

  const kpiConfig = [
    { key: 'total_leads', icon: Zap, color: 'blue' },
    { key: 'total_contacts', icon: Users, color: 'cyan' },
    { key: 'total_accounts', icon: Building2, color: 'purple' },
    { key: 'total_deals', icon: TrendingUp, color: 'amber' },
    { key: 'pipeline_value', icon: DollarSign, color: 'green' },
    { key: 'win_rate', icon: TrendingUp, color: 'green' },
    { key: 'avg_deal_size', icon: DollarSign, color: 'blue' },
    { key: 'lead_conversion_rate', icon: Zap, color: 'amber' },
    { key: 'weighted_pipeline', icon: DollarSign, color: 'purple' },
    { key: 'open_tasks', icon: CheckSquare, color: 'red' },
    { key: 'upcoming_meetings', icon: Calendar, color: 'cyan' },
    { key: 'activities_this_week', icon: Activity, color: 'blue' },
  ]

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="text-sm text-[var(--text-muted)]">Your CRM performance at a glance</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="pulse-dot" />
          <span className="text-xs text-[var(--text-muted)]">Live data</span>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        {kpiConfig.map(({ key, icon, color }) => {
          const kpi = kpis[key]
          if (!kpi) return null
          return (
            <KPICard
              key={key}
              label={kpi.label}
              value={kpi.value}
              unit={kpi.unit}
              icon={icon}
              color={color}
            />
          )
        })}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Trend */}
        <div className="card lg:col-span-2">
          <h3 className="text-sm font-semibold text-[var(--text)] mb-4">Revenue Trend (6 Months)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data?.revenue_trend || []}>
              <defs>
                <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} tickFormatter={(v) => `$${(v/1000).toFixed(0)}K`} />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="revenue"
                name="Revenue"
                stroke="#3b82f6"
                fill="url(#colorRevenue)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Lead by Status */}
        <div className="card">
          <h3 className="text-sm font-semibold text-[var(--text)] mb-4">Leads by Status</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={data?.lead_by_status || []}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                dataKey="count"
                nameKey="status"
              >
                {(data?.lead_by_status || []).map((_: any, i: number) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend iconSize={8} wrapperStyle={{ fontSize: '11px', color: 'var(--text-muted)' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Deals by Stage */}
        <div className="card">
          <h3 className="text-sm font-semibold text-[var(--text)] mb-4">Pipeline by Stage</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data?.deal_by_stage || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="stage" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
              <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" name="Deals" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top Deals + Recent Activities */}
        <div className="card">
          <h3 className="text-sm font-semibold text-[var(--text)] mb-4">Top Open Deals</h3>
          <div className="space-y-3">
            {(data?.top_deals || []).slice(0, 5).map((deal: any) => (
              <div key={deal.id} className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[var(--text)] truncate">{deal.name}</p>
                  <span className={`${getDealStageBadgeClass(deal.stage)} badge text-[10px] mt-0.5`}>
                    {deal.stage.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-sm font-bold text-emerald-400 ml-3">{formatCurrency(deal.value)}</p>
              </div>
            ))}
            {(!data?.top_deals || data.top_deals.length === 0) && (
              <p className="text-sm text-[var(--text-muted)]">No deals yet</p>
            )}
          </div>
        </div>
      </div>

      {/* Recent Activities */}
      <div className="card">
        <h3 className="text-sm font-semibold text-[var(--text)] mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {(data?.recent_activities || []).slice(0, 8).map((act: any) => (
            <div key={act.id} className="flex items-start gap-3 pb-3 border-b border-[var(--border)] last:border-0 last:pb-0">
              <div className="w-7 h-7 rounded-full bg-primary-600/15 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Activity size={12} className="text-primary-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-[var(--text)]">{act.title}</p>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">{timeAgo(act.created_at)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
