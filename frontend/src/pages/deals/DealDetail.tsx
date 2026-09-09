import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { dealsApi } from '../../lib/api'
import { formatDate, formatCurrency, getDealStageBadgeClass } from '../../lib/utils'
import { ArrowLeft } from 'lucide-react'

export default function DealDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: deal, isLoading } = useQuery({
    queryKey: ['deal', id],
    queryFn: () => dealsApi.get(id!).then(r => r.data),
    enabled: !!id,
  })

  if (isLoading) return <div className="card animate-pulse h-64" />
  if (!deal) return <div className="card"><p>Deal not found</p></div>

  return (
    <div className="space-y-5 fade-in">
      <div className="flex items-center gap-3">
        <Link to="/deals" className="btn-ghost h-8 w-8 p-0 flex items-center justify-center"><ArrowLeft size={16} /></Link>
        <div>
          <h1 className="page-title">{deal.name}</h1>
          <span className={`badge ${getDealStageBadgeClass(deal.stage)} capitalize mt-1`}>{deal.stage.replace('_', ' ')}</span>
        </div>
        <div className="ml-auto">
          <p className="text-3xl font-bold text-emerald-400">{formatCurrency(deal.value)}</p>
          <p className="text-xs text-[var(--text-muted)] text-right">{deal.probability}% probability</p>
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 card">
          <h3 className="text-sm font-semibold mb-4">Deal Information</h3>
          {deal.description && <p className="text-sm text-[var(--text-muted)] mb-4">{deal.description}</p>}
          {deal.lost_reason && <div className="badge badge-red mb-3">Lost: {deal.lost_reason}</div>}
        </div>
        <div className="card">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">Details</h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-[var(--text-muted)]">Weighted Value</dt><dd className="text-amber-400">{formatCurrency(deal.weighted_value)}</dd></div>
            <div className="flex justify-between"><dt className="text-[var(--text-muted)]">Currency</dt><dd>{deal.currency}</dd></div>
            <div className="flex justify-between"><dt className="text-[var(--text-muted)]">Expected Close</dt><dd>{formatDate(deal.expected_close_date)}</dd></div>
            {deal.actual_close_date && <div className="flex justify-between"><dt className="text-[var(--text-muted)]">Actual Close</dt><dd>{formatDate(deal.actual_close_date)}</dd></div>}
            <div className="flex justify-between"><dt className="text-[var(--text-muted)]">Created</dt><dd>{formatDate(deal.created_at)}</dd></div>
          </dl>
        </div>
      </div>
    </div>
  )
}
