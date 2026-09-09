import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { leadsApi } from '../../lib/api'
import { formatDate, formatCurrency, getLeadStatusBadge, getScoreBadgeClass } from '../../lib/utils'
import { ArrowLeft, Mail, Phone, Building2, MapPin, Star } from 'lucide-react'

export default function LeadDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: lead, isLoading } = useQuery({
    queryKey: ['lead', id],
    queryFn: () => leadsApi.get(id!).then(r => r.data),
    enabled: !!id,
  })

  if (isLoading) return <div className="card animate-pulse h-64" />
  if (!lead) return <div className="card"><p className="text-[var(--text-muted)]">Lead not found</p></div>

  return (
    <div className="space-y-5 fade-in">
      <div className="flex items-center gap-3 mb-2">
        <Link to="/leads" className="btn-ghost h-8 w-8 p-0 flex items-center justify-center">
          <ArrowLeft size={16} />
        </Link>
        <div>
          <h1 className="page-title">{lead.full_name}</h1>
          <p className="text-sm text-[var(--text-muted)]">{lead.company || 'No company'}</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className={`badge ${getLeadStatusBadge(lead.status)} capitalize`}>{lead.status}</span>
          <span className={`badge ${getScoreBadgeClass(lead.score)}`}>Score: {lead.score}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 space-y-5">
          <div className="card">
            <h3 className="text-sm font-semibold text-[var(--text)] mb-4">Contact Information</h3>
            <div className="grid grid-cols-2 gap-4">
              {lead.email && (
                <div className="flex items-center gap-2 text-sm">
                  <Mail size={14} className="text-[var(--text-muted)]" />
                  <a href={`mailto:${lead.email}`} className="text-primary-400 hover:underline">{lead.email}</a>
                </div>
              )}
              {lead.phone && (
                <div className="flex items-center gap-2 text-sm">
                  <Phone size={14} className="text-[var(--text-muted)]" />
                  <span className="text-[var(--text)]">{lead.phone}</span>
                </div>
              )}
              {lead.company && (
                <div className="flex items-center gap-2 text-sm">
                  <Building2 size={14} className="text-[var(--text-muted)]" />
                  <span className="text-[var(--text)]">{lead.company}</span>
                </div>
              )}
              {(lead.city || lead.country) && (
                <div className="flex items-center gap-2 text-sm">
                  <MapPin size={14} className="text-[var(--text-muted)]" />
                  <span className="text-[var(--text)]">{[lead.city, lead.country].filter(Boolean).join(', ')}</span>
                </div>
              )}
            </div>
            {lead.description && (
              <div className="mt-4 pt-4 border-t border-[var(--border)]">
                <p className="text-sm text-[var(--text-muted)]">{lead.description}</p>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="card">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">Details</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-[var(--text-muted)]">Source</dt>
                <dd className="capitalize">{lead.source?.replace('_', ' ') || '—'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-[var(--text-muted)]">Industry</dt>
                <dd>{lead.industry || '—'}</dd>
              </div>
              {lead.annual_revenue && (
                <div className="flex justify-between">
                  <dt className="text-[var(--text-muted)]">Annual Revenue</dt>
                  <dd className="text-emerald-400">{formatCurrency(lead.annual_revenue)}</dd>
                </div>
              )}
              {lead.employee_count && (
                <div className="flex justify-between">
                  <dt className="text-[var(--text-muted)]">Employees</dt>
                  <dd>{lead.employee_count.toLocaleString()}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-[var(--text-muted)]">Created</dt>
                <dd>{formatDate(lead.created_at)}</dd>
              </div>
              {lead.converted_at && (
                <div className="flex justify-between">
                  <dt className="text-[var(--text-muted)]">Converted</dt>
                  <dd className="text-emerald-400">{formatDate(lead.converted_at)}</dd>
                </div>
              )}
            </dl>
          </div>

          <div className="card">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">Lead Score</h3>
            <div className="flex items-center gap-3">
              <div className={`text-3xl font-bold ${lead.score >= 70 ? 'text-emerald-400' : lead.score >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
                {lead.score}
              </div>
              <div>
                <p className="text-xs text-[var(--text-muted)]">out of 100</p>
                <p className="text-xs font-medium">
                  {lead.score >= 70 ? '🔥 Hot Lead' : lead.score >= 40 ? '⚡ Warm Lead' : '🧊 Cold Lead'}
                </p>
              </div>
            </div>
            <div className="mt-3 h-2 bg-[var(--surface-2)] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${lead.score >= 70 ? 'bg-emerald-400' : lead.score >= 40 ? 'bg-amber-400' : 'bg-red-400'}`}
                style={{ width: `${lead.score}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
