import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dealsApi } from '../../lib/api'
import { formatCurrency, getDealStageBadgeClass } from '../../lib/utils'
import { DndContext, DragEndEvent, closestCenter } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import toast from 'react-hot-toast'
import { TrendingUp } from 'lucide-react'

const STAGES = [
  { key: 'prospecting', label: 'Prospecting', color: 'border-gray-500' },
  { key: 'qualification', label: 'Qualification', color: 'border-blue-500' },
  { key: 'proposal', label: 'Proposal', color: 'border-amber-500' },
  { key: 'negotiation', label: 'Negotiation', color: 'border-violet-500' },
  { key: 'closed_won', label: 'Closed Won ✓', color: 'border-emerald-500' },
  { key: 'closed_lost', label: 'Closed Lost ✗', color: 'border-red-500' },
]

export default function DealsPipeline() {
  const queryClient = useQueryClient()
  const { data: pipeline, isLoading } = useQuery({
    queryKey: ['deals-pipeline'],
    queryFn: () => dealsApi.pipeline().then(r => r.data),
  })

  const stageMutation = useMutation({
    mutationFn: ({ id, stage }: { id: string; stage: string }) =>
      dealsApi.updateStage(id, { stage }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deals-pipeline'] })
      toast.success('Deal stage updated!')
    },
    onError: () => toast.error('Failed to update stage'),
  })

  if (isLoading) return (
    <div className="space-y-5 fade-in">
      <div className="page-header"><h1 className="page-title">Pipeline</h1></div>
      <div className="flex gap-4 overflow-x-auto pb-4">
        {STAGES.map(s => <div key={s.key} className="min-w-64 w-64 card h-96 animate-pulse" />)}
      </div>
    </div>
  )

  const totalValue = STAGES.filter(s => !s.key.includes('closed')).reduce((sum, s) => {
    return sum + (pipeline?.[s.key] || []).reduce((a: number, d: any) => a + d.value, 0)
  }, 0)

  return (
    <div className="space-y-5 fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Deal Pipeline</h1>
          <p className="text-sm text-[var(--text-muted)]">
            Total pipeline: <span className="text-emerald-400 font-semibold">{formatCurrency(totalValue)}</span>
          </p>
        </div>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-4">
        {STAGES.map(({ key, label, color }) => {
          const deals: any[] = pipeline?.[key] || []
          const stageValue = deals.reduce((sum: number, d: any) => sum + d.value, 0)
          return (
            <div key={key} className={`min-w-64 w-64 flex-shrink-0`}>
              <div className={`card border-t-2 ${color} mb-3`}>
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">{label}</h3>
                  <span className="badge badge-gray text-[10px]">{deals.length}</span>
                </div>
                <p className="text-sm font-bold text-[var(--text)] mt-1">{formatCurrency(stageValue)}</p>
              </div>
              <div className="space-y-2">
                {deals.map((deal: any) => (
                  <div key={deal.id} className="card-hover p-3 cursor-pointer">
                    <p className="text-xs font-medium text-[var(--text)] truncate">{deal.name}</p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs font-bold text-emerald-400">{formatCurrency(deal.value)}</span>
                      <span className="text-[10px] text-[var(--text-muted)]">{deal.probability}%</span>
                    </div>
                    <div className="flex items-center gap-1 mt-2 flex-wrap">
                      {STAGES.filter(s => s.key !== key).map(s => (
                        <button
                          key={s.key}
                          onClick={() => stageMutation.mutate({ id: deal.id, stage: s.key })}
                          className="text-[9px] px-1.5 py-0.5 rounded bg-[var(--surface-2)] hover:bg-primary-600/20 text-[var(--text-muted)] hover:text-primary-400 transition-colors"
                        >
                          → {s.label.split(' ')[0]}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
                {deals.length === 0 && (
                  <div className="h-20 flex items-center justify-center border-2 border-dashed border-[var(--border)] rounded-xl">
                    <p className="text-xs text-[var(--text-muted)]">No deals</p>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
