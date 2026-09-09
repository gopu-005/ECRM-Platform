import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { contactsApi } from '../../lib/api'
import { formatDate } from '../../lib/utils'
import { ArrowLeft, Mail, Phone, Building2 } from 'lucide-react'

export default function ContactDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: contact, isLoading } = useQuery({
    queryKey: ['contact', id],
    queryFn: () => contactsApi.get(id!).then(r => r.data),
    enabled: !!id,
  })

  if (isLoading) return <div className="card animate-pulse h-64" />
  if (!contact) return <div className="card"><p className="text-[var(--text-muted)]">Contact not found</p></div>

  return (
    <div className="space-y-5 fade-in">
      <div className="flex items-center gap-3">
        <Link to="/contacts" className="btn-ghost h-8 w-8 p-0 flex items-center justify-center"><ArrowLeft size={16} /></Link>
        <div>
          <h1 className="page-title">{contact.full_name}</h1>
          <p className="text-sm text-[var(--text-muted)]">{contact.title} {contact.department ? `· ${contact.department}` : ''}</p>
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 card">
          <h3 className="text-sm font-semibold mb-4">Contact Information</h3>
          <div className="grid grid-cols-2 gap-4">
            {contact.email && <div className="flex items-center gap-2 text-sm"><Mail size={14} className="text-[var(--text-muted)]" /><a href={`mailto:${contact.email}`} className="text-primary-400">{contact.email}</a></div>}
            {contact.phone && <div className="flex items-center gap-2 text-sm"><Phone size={14} className="text-[var(--text-muted)]" /><span>{contact.phone}</span></div>}
            {contact.linkedin_url && <div className="flex items-center gap-2 text-sm col-span-2"><span className="text-[var(--text-muted)] text-xs">LinkedIn:</span><a href={contact.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-primary-400 text-xs truncate">{contact.linkedin_url}</a></div>}
          </div>
        </div>
        <div className="card">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">Details</h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-[var(--text-muted)]">Location</dt><dd>{[contact.city, contact.country].filter(Boolean).join(', ') || '—'}</dd></div>
            <div className="flex justify-between"><dt className="text-[var(--text-muted)]">Created</dt><dd>{formatDate(contact.created_at)}</dd></div>
          </dl>
        </div>
      </div>
    </div>
  )
}
