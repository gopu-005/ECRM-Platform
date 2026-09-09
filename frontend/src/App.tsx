import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/store'
import Layout from './components/Layout'

// Auth pages
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'

// CRM pages
import Dashboard from './pages/Dashboard'
import LeadsList from './pages/leads/LeadsList'
import LeadDetail from './pages/leads/LeadDetail'
import ContactsList from './pages/contacts/ContactsList'
import ContactDetail from './pages/contacts/ContactDetail'
import AccountsList from './pages/accounts/AccountsList'
import AccountDetail from './pages/accounts/AccountDetail'
import DealsPipeline from './pages/deals/DealsPipeline'
import DealsList from './pages/deals/DealsList'
import DealDetail from './pages/deals/DealDetail'
import TasksPage from './pages/tasks/TasksPage'
import MeetingsPage from './pages/meetings/MeetingsPage'
import ActivityFeed from './pages/activities/ActivityFeed'
import NotificationsPage from './pages/notifications/NotificationsPage'

// Analytics
import AnalyticsDashboard from './pages/analytics/AnalyticsDashboard'
import AnalyticsLeads from './pages/analytics/AnalyticsLeads'
import AnalyticsPipeline from './pages/analytics/AnalyticsPipeline'
import AnalyticsRevenue from './pages/analytics/AnalyticsRevenue'
import AnalyticsTeam from './pages/analytics/AnalyticsTeam'

// Admin
import AdminUsers from './pages/admin/AdminUsers'
import AdminAuditLogs from './pages/admin/AdminAuditLogs'
import SettingsPage from './pages/settings/SettingsPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

        {/* Protected with layout */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />

          {/* CRM */}
          <Route path="leads" element={<LeadsList />} />
          <Route path="leads/:id" element={<LeadDetail />} />
          <Route path="contacts" element={<ContactsList />} />
          <Route path="contacts/:id" element={<ContactDetail />} />
          <Route path="accounts" element={<AccountsList />} />
          <Route path="accounts/:id" element={<AccountDetail />} />
          <Route path="deals" element={<DealsList />} />
          <Route path="deals/pipeline" element={<DealsPipeline />} />
          <Route path="deals/:id" element={<DealDetail />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="meetings" element={<MeetingsPage />} />
          <Route path="activities" element={<ActivityFeed />} />
          <Route path="notifications" element={<NotificationsPage />} />

          {/* Analytics */}
          <Route path="analytics" element={<AnalyticsDashboard />} />
          <Route path="analytics/leads" element={<AnalyticsLeads />} />
          <Route path="analytics/pipeline" element={<AnalyticsPipeline />} />
          <Route path="analytics/revenue" element={<AnalyticsRevenue />} />
          <Route path="analytics/team" element={<AnalyticsTeam />} />

          {/* Admin */}
          <Route path="admin/users" element={<AdminUsers />} />
          <Route path="admin/audit-logs" element={<AdminAuditLogs />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
