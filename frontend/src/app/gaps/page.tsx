'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { gapsApi } from '@/lib/api/gaps'
import ProtectedRoute from '@/components/auth/ProtectedRoute'

export default function GapsPage() {
  return (
    <ProtectedRoute>
      <GapsContent />
    </ProtectedRoute>
  )
}

function GapsContent() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any>(null)
  const [activeTab, setActiveTab] = useState('orphaned')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const result = await gapsApi.getComprehensive()
      setData(result)
    } catch (error) {
      console.error('Failed to load gaps:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Analyzing gaps...</p>
        </div>
      </div>
    )
  }

  const summary = data?.summary || {}

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">🔍 Gap Analysis</h1>
            <p className="mt-2 text-gray-600">Find missing work, documentation gaps, and stale items</p>
          </div>
          <button
            onClick={() => router.push('/chat')}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            ← Back to Chat
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500">Orphaned Tickets</div>
            <div className="mt-2 text-3xl font-bold text-gray-900">{summary.total_orphaned || 0}</div>
            <div className="mt-1 text-xs text-gray-500">Tickets with no commits/PRs</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500">Undocumented</div>
            <div className="mt-2 text-3xl font-bold text-gray-900">{summary.total_undocumented || 0}</div>
            <div className="mt-1 text-xs text-gray-500">Commits without tickets</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500">Missing Decisions</div>
            <div className="mt-2 text-3xl font-bold text-gray-900">{summary.total_missing_decisions || 0}</div>
            <div className="mt-1 text-xs text-gray-500">Need decision analysis</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm font-medium text-gray-500">Stale Work</div>
            <div className="mt-2 text-3xl font-bold text-gray-900">{summary.total_stale || 0}</div>
            <div className="mt-1 text-xs text-gray-500">Not updated recently</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              {[
                { id: 'orphaned', label: '🎫 Orphaned Tickets' },
                { id: 'undocumented', label: '📝 Undocumented' },
                { id: 'decisions', label: '🧠 Missing Decisions' },
                { id: 'stale', label: '⏰ Stale Work' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-6 py-4 text-sm font-medium border-b-2 ${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'orphaned' && <OrphanedTickets data={data?.orphaned_tickets} />}
            {activeTab === 'undocumented' && <UndocumentedFeatures data={data?.undocumented_features} />}
            {activeTab === 'decisions' && <MissingDecisions data={data?.missing_decisions} />}
            {activeTab === 'stale' && <StaleWork data={data?.stale_work} />}
          </div>
        </div>
      </div>
    </div>
  )
}

function OrphanedTickets({ data }: { data: any }) {
  const tickets = data?.tickets || []
  const total = data?.total_orphaned || 0

  if (total === 0) {
    return <div className="text-center py-12 text-green-600">✅ No orphaned tickets found!</div>
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <h3 className="font-medium text-gray-900 mb-2">By Status</h3>
          {Object.entries(data?.by_status || {}).map(([status, count]: any) => (
            <div key={status} className="text-sm text-gray-600">• {status}: {count}</div>
          ))}
        </div>
        <div>
          <h3 className="font-medium text-gray-900 mb-2">By Priority</h3>
          {Object.entries(data?.by_priority || {}).map(([priority, count]: any) => (
            <div key={priority} className="text-sm text-gray-600">• {priority}: {count}</div>
          ))}
        </div>
      </div>

      {tickets.slice(0, 20).map((ticket: any) => (
        <div key={ticket.ticket_key} className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className="font-medium text-gray-900">{ticket.ticket_key}: {ticket.summary}</h4>
              <div className="mt-2 flex gap-4 text-sm text-gray-600">
                <span>Status: {ticket.status}</span>
                <span>Priority: {ticket.priority}</span>
                <span>Assignee: {ticket.assignee || 'Unassigned'}</span>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function UndocumentedFeatures({ data }: { data: any }) {
  const commits = data?.commits || []
  const total = data?.total_undocumented || 0

  if (total === 0) {
    return <div className="text-center py-12 text-green-600">✅ All commits are documented!</div>
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 rounded p-4">
          <div className="text-sm text-gray-500">Total Commits</div>
          <div className="text-2xl font-bold text-gray-900">{total}</div>
        </div>
        <div className="bg-gray-50 rounded p-4">
          <div className="text-sm text-gray-500">Code Changes</div>
          <div className="text-2xl font-bold text-gray-900">{data?.total_code_changes?.toLocaleString() || 0}</div>
        </div>
      </div>

      {commits.slice(0, 15).map((commit: any) => (
        <div key={commit.sha} className="border border-gray-200 rounded-lg p-4">
          <div className="font-mono text-sm text-gray-600">{commit.sha?.slice(0, 7)}</div>
          <div className="mt-1 text-gray-900">{commit.message?.split('\n')[0]}</div>
          <div className="mt-2 text-sm text-gray-600">
            {commit.author_name} • {new Date(commit.commit_date).toLocaleDateString()}
          </div>
        </div>
      ))}
    </div>
  )
}

function MissingDecisions({ data }: { data: any }) {
  const tickets = data?.tickets || []
  const total = data?.total_missing_decisions || 0

  if (total === 0) {
    return <div className="text-center py-12 text-green-600">✅ All tickets have decision analysis!</div>
  }

  return (
    <div className="space-y-4">
      {tickets.map((ticket: any) => (
        <div key={ticket.ticket_key} className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900">{ticket.ticket_key}: {ticket.summary}</h4>
          <div className="mt-2 flex gap-4 text-sm text-gray-600">
            <span>Type: {ticket.issue_type}</span>
            <span>Status: {ticket.status}</span>
            <span>Commits: {ticket.commit_count}</span>
            <span>PRs: {ticket.pr_count}</span>
          </div>
          <div className="mt-3 text-sm text-blue-600">💡 Has implementation but no decision analysis</div>
        </div>
      ))}
    </div>
  )
}

function StaleWork({ data }: { data: any }) {
  const tickets = data?.tickets || []
  const total = data?.total_stale || 0

  if (total === 0) {
    return <div className="text-center py-12 text-green-600">✅ No stale work found!</div>
  }

  return (
    <div className="space-y-4">
      {tickets.slice(0, 20).map((ticket: any) => {
        const days = ticket.days_since_update || 0
        const severity = days > 60 ? '🔴' : days > 30 ? '🟡' : '🟢'

        return (
          <div key={ticket.ticket_key} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900">
                  {severity} {ticket.ticket_key}: {ticket.summary}
                </h4>
                <div className="mt-2 flex gap-4 text-sm text-gray-600">
                  <span>Status: {ticket.status}</span>
                  <span>Priority: {ticket.priority}</span>
                  <span>Stale: {days} days</span>
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
