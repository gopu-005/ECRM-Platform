import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { activitiesApi } from '../../lib/api'
import { timeAgo } from '../../lib/utils'
import { Activity, ChevronLeft, ChevronRight } from 'lucide-react'

export default function ActivityFeed() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQuery({
    queryKey: ['activities', page],
    queryFn: () => activitiesApi.list({ page, page_size: 20 }).then(r => r.data),
  })

  const typeColors: Record<string, string> = {
    call: 'text-blue-400 bg-blue-400/10',
    email: 'text-violet-400 bg-violet-400/10',
    meeting: 'text-emerald-400 bg-emerald-400/10',
    note: 'text-amber-400 bg-amber-400/10',
    task: 'text-cyan-400 bg-cyan-400/10',
    deal_stage_change: 'text-orange-400 bg-orange-400/10',
    lead_converted: 'text-green-400 bg-green-400/10',
    system: 'text-gray-400 bg-gray-400/10',
  }

  return (
    <div className="space-y-5 fade-in">
      <div className="page-header">
        <div><h1 className="page-title">Activity Feed</h1><p className="text-sm text-[var(--text-muted)]">{data?.total ?? 0} activities</p></div>
      </div>

      <div className="space-y-3">
        {isLoading ? Array.from({ length: 10 }).map((_, i) => <div key={i} className="card h-16 animate-pulse" />) :
          (data?.items || []).map((act: any) => (
            <div key={act.id} className="card flex items-start gap-4">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${typeColors[act.type] || 'bg-gray-400/10 text-gray-400'}`}>
                <Activity size={14} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[var(--text)]">{act.title}</p>
                {act.description && <p className="text-xs text-[var(--text-muted)] mt-0.5">{act.description}</p>}
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--surface-2)] text-[var(--text-muted)] capitalize">{act.type.replace('_', ' ')}</span>
                  <span className="text-xs text-[var(--text-muted)]">{timeAgo(act.created_at)}</span>
                </div>
              </div>
            </div>
          ))}
      </div>

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-[var(--text-muted)]">Page {data.page} of {data.total_pages}</p>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={!data.has_prev} className="btn-secondary h-8 w-8 p-0 flex items-center justify-center"><ChevronLeft size={14} /></button>
            <button onClick={() => setPage(p => p + 1)} disabled={!data.has_next} className="btn-secondary h-8 w-8 p-0 flex items-center justify-center"><ChevronRight size={14} /></button>
          </div>
        </div>
      )}
    </div>
  )
}
