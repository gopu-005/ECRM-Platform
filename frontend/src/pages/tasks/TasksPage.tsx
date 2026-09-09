import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tasksApi } from '../../lib/api'
import { formatDate } from '../../lib/utils'
import { Plus, CheckSquare, Square, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '../../lib/utils'
import toast from 'react-hot-toast'

const statusColors: Record<string, string> = {
  todo: 'badge-blue',
  in_progress: 'badge-yellow',
  completed: 'badge-green',
  cancelled: 'badge-gray',
}

const priorityColors: Record<string, string> = {
  low: 'text-gray-400',
  medium: 'text-blue-400',
  high: 'text-amber-400',
  urgent: 'text-red-400',
}

export default function TasksPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [filterStatus, setFilterStatus] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['tasks', page, filterStatus],
    queryFn: () => tasksApi.list({ page, page_size: 20, status: filterStatus || undefined }).then(r => r.data),
  })

  const deleteMutation = useMutation({
    mutationFn: tasksApi.delete,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['tasks'] }); toast.success('Task deleted') },
  })

  const completeMutation = useMutation({
    mutationFn: (id: string) => tasksApi.update(id, { status: 'completed' }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['tasks'] }); toast.success('Task completed!') },
  })

  return (
    <div className="space-y-5 fade-in">
      <div className="page-header">
        <div><h1 className="page-title">Tasks</h1><p className="text-sm text-[var(--text-muted)]">{data?.total ?? 0} tasks</p></div>
        <button onClick={() => setShowCreate(true)} className="btn-primary"><Plus size={14} /> Add Task</button>
      </div>

      <div className="card p-4 flex gap-3">
        {['', 'todo', 'in_progress', 'completed', 'cancelled'].map(s => (
          <button key={s} onClick={() => { setFilterStatus(s); setPage(1) }}
            className={cn('btn text-xs h-7 px-3', filterStatus === s ? 'btn-primary' : 'btn-secondary')}>
            {s ? s.replace('_', ' ') : 'All'}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {isLoading ? Array.from({ length: 8 }).map((_, i) => <div key={i} className="card h-14 animate-pulse" />) :
          (data?.items || []).map((task: any) => (
            <div key={task.id} className={cn('card flex items-center gap-3 py-3', task.status === 'completed' && 'opacity-60')}>
              <button onClick={() => task.status !== 'completed' && completeMutation.mutate(task.id)} className="flex-shrink-0 text-[var(--text-muted)] hover:text-emerald-400 transition-colors">
                {task.status === 'completed' ? <CheckSquare size={16} className="text-emerald-400" /> : <Square size={16} />}
              </button>
              <div className="flex-1 min-w-0">
                <p className={cn('text-sm font-medium', task.status === 'completed' && 'line-through text-[var(--text-muted)]')}>{task.title}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className={`badge ${statusColors[task.status] || 'badge-gray'} text-[10px]`}>{task.status.replace('_', ' ')}</span>
                  <span className={`text-[10px] font-medium capitalize ${priorityColors[task.priority]}`}>{task.priority}</span>
                  {task.due_date && <span className="text-[10px] text-[var(--text-muted)]">Due: {formatDate(task.due_date)}</span>}
                </div>
              </div>
              <button onClick={() => deleteMutation.mutate(task.id)} className="btn-ghost h-7 w-7 p-0 flex items-center justify-center text-red-400 flex-shrink-0"><Trash2 size={12} /></button>
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

      {showCreate && <CreateTaskModal onClose={() => setShowCreate(false)} />}
    </div>
  )
}

function CreateTaskModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState({ title: '', description: '', priority: 'medium', due_date: '' })
  const [loading, setLoading] = useState(false)
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true)
    try {
      await tasksApi.create({ ...form, due_date: form.due_date || undefined })
      queryClient.invalidateQueries({ queryKey: ['tasks'] }); toast.success('Task created!'); onClose()
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Failed') }
    finally { setLoading(false) }
  }
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="card w-full max-w-md">
        <h2 className="text-lg font-bold mb-5">Create Task</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div><label className="input-label">Title *</label><input className="input" required value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} /></div>
          <div><label className="input-label">Description</label><textarea className="input" rows={2} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="input-label">Priority</label>
              <select className="input" value={form.priority} onChange={e => setForm(f => ({ ...f, priority: e.target.value }))}>
                {['low', 'medium', 'high', 'urgent'].map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div><label className="input-label">Due Date</label><input type="datetime-local" className="input" value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} /></div>
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
