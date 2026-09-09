import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number, currency = 'USD') {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatNumber(value: number) {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`
  return value.toString()
}

export function formatDate(date: string | null | undefined) {
  if (!date) return '—'
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export function formatDateTime(date: string | null | undefined) {
  if (!date) return '—'
  return new Date(date).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function timeAgo(date: string | null | undefined) {
  if (!date) return '—'
  const diff = Date.now() - new Date(date).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export function getScoreBadgeClass(score: number) {
  if (score >= 70) return 'badge-green'
  if (score >= 40) return 'badge-yellow'
  return 'badge-red'
}

export function getDealStageBadgeClass(stage: string) {
  const map: Record<string, string> = {
    prospecting: 'badge-gray',
    qualification: 'badge-blue',
    proposal: 'badge-yellow',
    negotiation: 'badge-purple',
    closed_won: 'badge-green',
    closed_lost: 'badge-red',
  }
  return map[stage] || 'badge-gray'
}

export function getLeadStatusBadge(status: string) {
  const map: Record<string, string> = {
    new: 'badge-blue',
    contacted: 'badge-purple',
    qualified: 'badge-green',
    unqualified: 'badge-gray',
    converted: 'badge-green',
    lost: 'badge-red',
  }
  return map[status] || 'badge-gray'
}
