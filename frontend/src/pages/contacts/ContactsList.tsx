import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { contactsApi } from '../../lib/api'
import { formatDate } from '../../lib/utils'
import { Plus, Search, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ContactsList() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['contacts', page, search],
    queryFn: () => contactsApi.list({ page, page_size: 20, search: search || undefined }).then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: contactsApi.delete,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['contacts'] }); toast.success('Contact deleted') },
    onError: () => toast.error('Failed to delete'),
  })

  return (
    <div className="space-y-5 fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Contacts</h1>
          <p className="text-sm text-[var(--text-muted)]">{data?.total ?? 0} total contacts</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary"><Plus size={14} /> Add Contact</button>
      </div>

      <div className="card p-4">
        <div className="relative max-w-sm">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input className="input pl-8 h-8 text-xs" placeholder="Search contacts..." value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} />
        </div>
      </div>

      <div className="table-wrapper">
        <table className="table">
          <thead>
            <tr><th>Name</th><th>Email</th><th>Phone</th><th>Title</th><th>Department</th><th>Created</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {isLoading ? Array.from({ length: 8 }).map((_, i) => (
              <tr key={i}>{Array.from({ length: 7 }).map((_, j) => <td key={j}><div className="h-4 bg-[var(--surface-2)] rounded animate-pulse w-24" /></td>)}</tr>
            )) : (data?.items || []).map((c: any) => (
              <tr key={c.id}>
                <td><Link to={`/contacts/${c.id}`} className="font-medium text-primary-400 hover:underline">{c.full_name}</Link></td>
                <td className="text-[var(--text-muted)]">{c.email || '—'}</td>
                <td className="text-[var(--text-muted)]">{c.phone || '—'}</td>
                <td className="text-[var(--text-muted)]">{c.title || '—'}</td>
                <td className="text-[var(--text-muted)]">{c.department || '—'}</td>
                <td className="text-[var(--text-muted)]">{formatDate(c.created_at)}</td>
                <td><button onClick={() => deleteMutation.mutate(c.id)} className="btn-ghost h-7 w-7 p-0 flex items-center justify-center text-red-400"><Trash2 size={12} /></button></td>
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

      {showCreate && <CreateContactModal onClose={() => setShowCreate(false)} />}
    </div>
  )
}

function CreateContactModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', phone: '', title: '', department: '' })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true)
    try {
      await contactsApi.create(form)
      queryClient.invalidateQueries({ queryKey: ['contacts'] })
      toast.success('Contact created!')
      onClose()
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Failed') }
    finally { setLoading(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="card w-full max-w-md">
        <h2 className="text-lg font-bold text-[var(--text)] mb-5">Create Contact</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="input-label">First Name *</label><input className="input" required value={form.first_name} onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))} /></div>
            <div><label className="input-label">Last Name *</label><input className="input" required value={form.last_name} onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))} /></div>
          </div>
          <div><label className="input-label">Email</label><input type="email" className="input" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} /></div>
          <div><label className="input-label">Phone</label><input className="input" value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="input-label">Title</label><input className="input" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} /></div>
            <div><label className="input-label">Department</label><input className="input" value={form.department} onChange={e => setForm(f => ({ ...f, department: e.target.value }))} /></div>
          </div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1">{loading ? 'Creating...' : 'Create'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
