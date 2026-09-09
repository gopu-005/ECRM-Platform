import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { accountsApi } from '../../lib/api'
import { formatDate, formatCurrency } from '../../lib/utils'
import { ArrowLeft, Globe, Building2 } from 'lucide-react'

export default function AccountDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: account, isLoading } = useQuery({
    queryKey: ['account', id],
    queryFn: () => accountsApi.get(id!).then(r => r.data),
    enabled: !!id,
  })

  if (isLoading) return <div className="card animate-pulse h-64" />
  if (!account) return <div className="card"><p>Account not found</p></div>

  return (
    <div className="space-y-5 fade-in">
      <div className="flex items-center gap-3">
        <Link to="/accounts" className="btn-ghost h-8 w-8 p-0 flex items-center justify-center"><ArrowLeft size={16} /></Link>
        <div><h1 className="page-title">{account.name}</h1><p className="text-sm text-[var(--text-muted)]">{account.industry || 'No industry'}</p></div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 card">
          <h3 className="text-sm font-semibold mb-4">Account Information</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            {account.domain && <div className="flex items-center gap-2"><Globe size={14} className="text-[var(--text-muted)]" /><span>{account.domain}</span></div>}
            {account.website && <div className="flex items-center gap-2"><Globe size={14} className="text-[var(--text-muted)]" /><a href={account.website} target="_blank" rel="noopener noreferrer" className="text-primary-400">{account.website}</a></div>}
            {account.country && <div><span className="text-[var(--text-muted)]">Country:</span> {account.country}</div>}
            {account.description && <div className="col-span-2 text-[var(--text-muted)]">{account.description}</div>}
          </div>
        </div>
        <div className="card">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">Financials</h3>
          <dl className="space-y-2 text-sm">
            {account.annual_revenue && <div className="flex justify-between"><dt className="text-[var(--text-muted)]">Annual Revenue</dt><dd className="text-emerald-400">{formatCurrency(account.annual_revenue)}</dd></div>}
            {account.employee_count && <div className="flex justify-between"><dt className="text-[var(--text-muted)]">Employees</dt><dd>{account.employee_count.toLocaleString()}</dd></div>}
            <div className="flex justify-between"><dt className="text-[var(--text-muted)]">Created</dt><dd>{formatDate(account.created_at)}</dd></div>
          </dl>
        </div>
      </div>
    </div>
  )
}
