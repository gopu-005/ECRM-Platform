import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { dealsApi } from '../../lib/api'
import { formatDate, formatCurrency, getDealStageBadgeClass } from '../../lib/utils'
import { Plus, Search, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

const STAGES = ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost']

export default function DealsList() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [stage, setStage] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['deals', page, search, stage],
    queryFn: () => dealsApi.list({ page, page_size: 20, search: search || undefined, stage: stage || undefined }).then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: dealsApi.delete,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['deals'] }); toast.success('Deal deleted') },
    onError: () => toast.error('Failed'),
  })

  return (
    <div className="space-y-5 fade-in">
      <div className="page-header">
        <div><h1 className="page-title">Deals</h1><p className="text-sm text-[var(--text-muted)]">{data?.total ?? 0} total deals</p></div>
        <button onClick={() => setShowCreate(true)} className="btn-primary"><Plus size={14} /> Add Deal</button>
      </div>
      <div className="card p-4 flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-48"><Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input className="input pl-8 h-8 text-xs" placeholder="Search deals..." value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} /></div>
        <select className="input h-8 text-xs w-40" value={stage} onChange={e => { setStage(e.target.value); setPage(1) }}>
          <option value="">All Stages</option>
          {STAGES.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
        </select>
      </div>
      <div className="table-wrapper">
        <table className="table">
          <thead><tr><th>Name</th><th>Stage</th><th>Value</th><th>Probability</th><th>Weighted</th><th>Close Date</th><th>Actions</th></tr></thead>
          <tbody>
            {isLoading ? Array.from({ length: 8 }).map((_, i) => <tr key={i}>{Array.from({ length: 7 }).map((_, j) => <td key={j}><div className="h-4 bg-[var(--surface-2)] rounded animate-pulse w-24" /></td>)}</tr>)
              : (data?.items || []).map((d: any) => (
                <tr key={d.id}>
                  <td><Link to={`/deals/${d.id}`} className="font-medium text-primary-400 hover:underline">{d.name}</Link></td>
                  <td><span className={`badge ${getDealStageBadgeClass(d.stage)} capitalize`}>{d.stage.replace('_', ' ')}</span></td>
                  <td className="text-emerald-400 font-semibold">{formatCurrency(d.value)}</td>
                  <td className="text-[var(--text-muted)]">{d.probability}%</td>
                  <td className="text-amber-400">{formatCurrency(d.weighted_value)}</td>
                  <td className="text-[var(--text-muted)]">{formatDate(d.expected_close_date)}</td>
                  <td><button onClick={() => deleteMutation.mutate(d.id)} className="btn-ghost h-7 w-7 p-0 flex items-center justify-center text-red-400"><Trash2 size={12} /></button></td>
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
      {showCreate && <CreateDealModal onClose={() => setShowCreate(false)} />}
    </div>
  )
}

function CreateDealModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ name: '', stage: 'prospecting', value: '', probability: '10', currency: 'USD' })
  const [loading, setLoading] = useState(false)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true)
    try {
      await dealsApi.create({ ...form, value: Number(form.value), probability: Number(form.probability) })
      queryClient.invalidateQueries({ queryKey: ['deals'] }); queryClient.invalidateQueries({ queryKey: ['deals-pipeline'] })
      toast.success('Deal created!'); onClose()
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Failed') }
    finally { setLoading(false) }
  }
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="card w-full max-w-md">
        <h2 className="text-lg font-bold mb-5">Create Deal</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div><label className="input-label">Deal Name *</label><input className="input" required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="input-label">Stage</label>
              <select className="input" value={form.stage} onChange={e => setForm(f => ({ ...f, stage: e.target.value }))}>
                {STAGES.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
              </select>
            </div>
            <div><label className="input-label">Value (USD)</label><input type="number" className="input" min="0" value={form.value} onChange={e => setForm(f => ({ ...f, value: e.target.value }))} /></div>
          </div>
          <div><label className="input-label">Probability (%)</label><input type="number" className="input" min="0" max="100" value={form.probability} onChange={e => setForm(f => ({ ...f, probability: e.target.value }))} /></div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1">{loading ? 'Creating...' : 'Create'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
