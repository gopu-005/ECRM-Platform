import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Zap, Loader2 } from 'lucide-react'
import { authApi } from '../../lib/api'
import { useAuthStore } from '../../stores/store'
import toast from 'react-hot-toast'

const schema = z.object({
  org_name: z.string().min(2, 'Organization name required'),
  org_slug: z.string().min(2, 'Slug required').regex(/^[a-z0-9-]+$/, 'Only lowercase, numbers, hyphens'),
  first_name: z.string().min(1, 'Required'),
  last_name: z.string().min(1, 'Required'),
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'At least 8 characters'),
})

type FormData = z.infer<typeof schema>

export default function Register() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [loading, setLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setLoading(true)
    try {
      const { data: tokens } = await authApi.register(data)
      localStorage.setItem('access_token', tokens.access_token)
      localStorage.setItem('refresh_token', tokens.refresh_token)
      const { data: user } = await authApi.me()
      setAuth(user, tokens.access_token, tokens.refresh_token)
      toast.success('Organization created! Welcome to ECRM.')
      navigate('/dashboard')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'var(--bg)' }}>
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-violet-600 mb-4">
            <Zap size={28} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-[var(--text)]">Set up your CRM</h1>
          <p className="text-[var(--text-muted)] mt-1">Create your organization and admin account</p>
        </div>

        <div className="card p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="input-label">First Name</label>
                <input className="input" placeholder="Jane" {...register('first_name')} />
                {errors.first_name && <p className="text-xs text-red-400 mt-1">{errors.first_name.message}</p>}
              </div>
              <div>
                <label className="input-label">Last Name</label>
                <input className="input" placeholder="Doe" {...register('last_name')} />
                {errors.last_name && <p className="text-xs text-red-400 mt-1">{errors.last_name.message}</p>}
              </div>
            </div>

            <div>
              <label className="input-label">Organization Name</label>
              <input className="input" placeholder="Acme Corp" {...register('org_name')} />
              {errors.org_name && <p className="text-xs text-red-400 mt-1">{errors.org_name.message}</p>}
            </div>

            <div>
              <label className="input-label">Org Slug (unique ID)</label>
              <input className="input" placeholder="acme-corp" {...register('org_slug')} />
              {errors.org_slug && <p className="text-xs text-red-400 mt-1">{errors.org_slug.message}</p>}
            </div>

            <div>
              <label className="input-label">Work Email</label>
              <input type="email" className="input" placeholder="you@company.com" {...register('email')} />
              {errors.email && <p className="text-xs text-red-400 mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <label className="input-label">Password</label>
              <input type="password" className="input" placeholder="Min 8 characters" {...register('password')} />
              {errors.password && <p className="text-xs text-red-400 mt-1">{errors.password.message}</p>}
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full justify-center h-10 mt-2">
              {loading ? <Loader2 size={16} className="animate-spin" /> : 'Create Organization'}
            </button>
          </form>

          <p className="text-center text-sm text-[var(--text-muted)] mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
