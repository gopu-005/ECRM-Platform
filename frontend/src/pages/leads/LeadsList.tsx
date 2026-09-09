import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { leadsApi } from '../../lib/api'
import { formatDate, getLeadStatusBadge, getScoreBadgeClass } from '../../lib/utils'
import { Plus, Search, Filter, ChevronLeft, ChevronRight, Zap, Trash2, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

const STATUSES = ['new', 'contacted', 'qualified', 'unqualified', 'converted', 'lost']
const SOURCES = ['website', 'referral', 'cold_call', 'email', 'social_media', 'advertisement', 'trade_show', 'other']

export default function LeadsList() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['leads', page, search, status],
    queryFn: () => leadsApi.list({ page, page_size: 20, search: search || undefined, status: status || undefined }).then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: leadsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Lead deleted')
    },
    onError: () => toast.error('Failed to delete lead'),
  })

  const convertMutation = useMutation({
    mutationFn: leadsApi.convert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Lead converted to contact!')
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || 'Conversion failed'),
  })

  return (
    <div className="space-y-5 fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Leads</h1>
          <p className="text-sm text-[var(--text-muted)]">{data?.total ?? 0} total leads</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">
          <Plus size={14} /> Add Lead
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input
            className="input pl-8 h-8 text-xs"
            placeholder="Search leads..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          />
        </div>
        <select
          className="input h-8 text-xs w-36"
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1) }}
        >
          <option value="">All Statuses</option>
          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Company</th>
              <th>Email</th>
              <th>Status</th>
              <th>Score</th>
              <th>Source</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 10 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 8 }).map((_, j) => (
                    <td key={j}><div className="h-4 bg-[var(--surface-2)] rounded animate-pulse w-24" /></td>
                  ))}
                </tr>
              ))
            ) : (data?.items || []).map((lead: any) => (
              <tr key={lead.id}>
                <td>
                  <Link to={`/leads/${lead.id}`} className="font-medium text-primary-400 hover:text-primary-300 hover:underline">
                    {lead.full_name}
                  </Link>
                </td>
                <td className="text-[var(--text-muted)]">{lead.company || '—'}</td>
                <td className="text-[var(--text-muted)]">{lead.email || '—'}</td>
                <td>
                  <span className={`badge ${getLeadStatusBadge(lead.status)} capitalize`}>
                    {lead.status}
                  </span>
                </td>
                <td>
                  <span className={`badge ${getScoreBadgeClass(lead.score)}`}>{lead.score}</span>
                </td>
                <td className="text-[var(--text-muted)] capitalize">{lead.source?.replace('_', ' ') || '—'}</td>
                <td className="text-[var(--text-muted)]">{formatDate(lead.created_at)}</td>
                <td>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => convertMutation.mutate(lead.id)}
                      disabled={lead.status === 'converted'}
                      className="btn-ghost h-7 w-7 p-0 flex items-center justify-center text-emerald-400 hover:text-emerald-300 disabled:opacity-30"
                      title="Convert to contact"
                    >
                      <RefreshCw size={12} />
                    </button>
                    <button
                      onClick={() => deleteMutation.mutate(lead.id)}
                      className="btn-ghost h-7 w-7 p-0 flex items-center justify-center text-red-400 hover:text-red-300"
                      title="Delete"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-[var(--text-muted)]">
            Page {data.page} of {data.total_pages} ({data.total} total)
          </p>
          <div className="flex items-center gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={!data.has_prev} className="btn-secondary h-8 w-8 p-0 flex items-center justify-center">
              <ChevronLeft size={14} />
            </button>
            <button onClick={() => setPage(p => p + 1)} disabled={!data.has_next} className="btn-secondary h-8 w-8 p-0 flex items-center justify-center">
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Create Modal */}
      {showCreate && <CreateLeadModal onClose={() => setShowCreate(false)} />}
    </div>
  )
}

function CreateLeadModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', company: '', phone: '', status: 'new', source: '' })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await leadsApi.create({ ...form, source: form.source || undefined })
      queryClient.invalidateQueries({ queryKey: ['leads'] })
      toast.success('Lead created!')
      onClose()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create lead')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="card w-full max-w-md">
        <h2 className="text-lg font-bold text-[var(--text)] mb-5">Create Lead</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="input-label">First Name *</label>
              <input className="input" required value={form.first_name} onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))} />
            </div>
            <div>
              <label className="input-label">Last Name *</label>
              <input className="input" required value={form.last_name} onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))} />
            </div>
          </div>
          <div>
            <label className="input-label">Email</label>
            <input type="email" className="input" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
          </div>
          <div>
            <label className="input-label">Company</label>
            <input className="input" value={form.company} onChange={e => setForm(f => ({ ...f, company: e.target.value }))} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="input-label">Status</label>
              <select className="input" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
                {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="input-label">Source</label>
              <select className="input" value={form.source} onChange={e => setForm(f => ({ ...f, source: e.target.value }))}>
                <option value="">None</option>
                {SOURCES.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
              </select>
            </div>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1">{loading ? 'Creating...' : 'Create Lead'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
