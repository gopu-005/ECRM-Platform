import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { accountsApi } from '../../lib/api'
import { formatDate, formatCurrency } from '../../lib/utils'
import { Plus, Search, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function AccountsList() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['accounts', page, search],
    queryFn: () => accountsApi.list({ page, page_size: 20, search: search || undefined }).then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: accountsApi.delete,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['accounts'] }); toast.success('Account deleted') },
    onError: () => toast.error('Failed to delete'),
  })

  return (
    <div className="space-y-5 fade-in">
      <div className="page-header">
        <div><h1 className="page-title">Accounts</h1><p className="text-sm text-[var(--text-muted)]">{data?.total ?? 0} total accounts</p></div>
        <button onClick={() => setShowCreate(true)} className="btn-primary"><Plus size={14} /> Add Account</button>
      </div>
      <div className="card p-4">
        <div className="relative max-w-sm"><Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input className="input pl-8 h-8 text-xs" placeholder="Search accounts..." value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} />
        </div>
      </div>
      <div className="table-wrapper">
        <table className="table">
          <thead><tr><th>Name</th><th>Industry</th><th>Domain</th><th>Revenue</th><th>Employees</th><th>Created</th><th>Actions</th></tr></thead>
          <tbody>
            {isLoading ? Array.from({ length: 8 }).map((_, i) => <tr key={i}>{Array.from({ length: 7 }).map((_, j) => <td key={j}><div className="h-4 bg-[var(--surface-2)] rounded animate-pulse w-24" /></td>)}</tr>)
              : (data?.items || []).map((a: any) => (
                <tr key={a.id}>
                  <td><Link to={`/accounts/${a.id}`} className="font-medium text-primary-400 hover:underline">{a.name}</Link></td>
                  <td className="text-[var(--text-muted)]">{a.industry || '—'}</td>
                  <td className="text-[var(--text-muted)]">{a.domain || '—'}</td>
                  <td className="text-emerald-400">{a.annual_revenue ? formatCurrency(a.annual_revenue) : '—'}</td>
                  <td className="text-[var(--text-muted)]">{a.employee_count?.toLocaleString() || '—'}</td>
                  <td className="text-[var(--text-muted)]">{formatDate(a.created_at)}</td>
                  <td><button onClick={() => deleteMutation.mutate(a.id)} className="btn-ghost h-7 w-7 p-0 flex items-center justify-center text-red-400"><Trash2 size={12} /></button></td>
                </tr>
              ))}
          </tbody>
        </table>
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
      {showCreate && <CreateAccountModal onClose={() => setShowCreate(false)} />}
    </div>
  )
}

function CreateAccountModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ name: '', domain: '', industry: '', website: '', country: '' })
  const [loading, setLoading] = useState(false)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true)
    try { await accountsApi.create(form); queryClient.invalidateQueries({ queryKey: ['accounts'] }); toast.success('Account created!'); onClose() }
    catch (err: any) { toast.error(err.response?.data?.detail || 'Failed') }
    finally { setLoading(false) }
  }
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="card w-full max-w-md">
        <h2 className="text-lg font-bold mb-5">Create Account</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div><label className="input-label">Company Name *</label><input className="input" required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} /></div>
          <div><label className="input-label">Domain</label><input className="input" value={form.domain} onChange={e => setForm(f => ({ ...f, domain: e.target.value }))} /></div>
          <div><label className="input-label">Industry</label><input className="input" value={form.industry} onChange={e => setForm(f => ({ ...f, industry: e.target.value }))} /></div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1">{loading ? 'Creating...' : 'Create'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
