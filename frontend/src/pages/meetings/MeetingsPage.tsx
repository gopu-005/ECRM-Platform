import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { meetingsApi } from '../../lib/api'
import { formatDateTime } from '../../lib/utils'
import { Plus, Calendar, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'

export default function MeetingsPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [showCreate, setShowCreate] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['meetings', page],
    queryFn: () => meetingsApi.list({ page, page_size: 20 }).then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: meetingsApi.delete,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['meetings'] }); toast.success('Meeting deleted') },
  })

  return (
    <div className="space-y-5 fade-in">
      <div className="page-header">
        <div><h1 className="page-title">Meetings</h1><p className="text-sm text-[var(--text-muted)]">{data?.total ?? 0} total</p></div>
        <button onClick={() => setShowCreate(true)} className="btn-primary"><Plus size={14} /> Schedule Meeting</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? Array.from({ length: 6 }).map((_, i) => <div key={i} className="card h-32 animate-pulse" />) :
          (data?.items || []).map((m: any) => (
            <div key={m.id} className="card-hover group">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">{m.title}</p>
                  <div className="flex items-center gap-1.5 mt-1 text-xs text-[var(--text-muted)]">
                    <Calendar size={11} />
                    <span>{formatDateTime(m.start_time)}</span>
                  </div>
                  {m.location && <p className="text-xs text-[var(--text-muted)] mt-1">📍 {m.location}</p>}
                  <span className={`badge mt-2 text-[10px] ${m.status === 'scheduled' ? 'badge-blue' : m.status === 'completed' ? 'badge-green' : 'badge-gray'}`}>{m.status}</span>
                </div>
                <button onClick={() => deleteMutation.mutate(m.id)} className="btn-ghost h-7 w-7 p-0 flex items-center justify-center text-red-400 opacity-0 group-hover:opacity-100"><Trash2 size={12} /></button>
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

      {showCreate && <CreateMeetingModal onClose={() => setShowCreate(false)} />}
    </div>
  )
}

function CreateMeetingModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ title: '', start_time: '', end_time: '', location: '', meeting_url: '' })
  const [loading, setLoading] = useState(false)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true)
    try {
      await meetingsApi.create({ ...form, start_time: new Date(form.start_time).toISOString(), end_time: new Date(form.end_time).toISOString() })
      queryClient.invalidateQueries({ queryKey: ['meetings'] }); toast.success('Meeting scheduled!'); onClose()
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Failed') }
    finally { setLoading(false) }
  }
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="card w-full max-w-md">
        <h2 className="text-lg font-bold mb-5">Schedule Meeting</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div><label className="input-label">Title *</label><input className="input" required value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="input-label">Start Time *</label><input type="datetime-local" className="input" required value={form.start_time} onChange={e => setForm(f => ({ ...f, start_time: e.target.value }))} /></div>
            <div><label className="input-label">End Time *</label><input type="datetime-local" className="input" required value={form.end_time} onChange={e => setForm(f => ({ ...f, end_time: e.target.value }))} /></div>
          </div>
          <div><label className="input-label">Location</label><input className="input" value={form.location} onChange={e => setForm(f => ({ ...f, location: e.target.value }))} /></div>
          <div><label className="input-label">Meeting URL</label><input className="input" placeholder="https://meet.google.com/..." value={form.meeting_url} onChange={e => setForm(f => ({ ...f, meeting_url: e.target.value }))} /></div>
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1">{loading ? 'Scheduling...' : 'Schedule'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
