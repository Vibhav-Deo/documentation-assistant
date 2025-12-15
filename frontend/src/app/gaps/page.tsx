'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { gapsApi } from '@/lib/api/gaps'
import { predictionsApi } from '@/lib/api/predictions'
import { autoTagApi } from '@/lib/api/autoTag'
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
  const [predictionsData, setPredictionsData] = useState<any>(null)
  const [predictionsLoading, setPredictionsLoading] = useState(false)

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

  const loadPredictions = async () => {
    try {
      setPredictionsLoading(true)
      const [hotspots, bottlenecks] = await Promise.all([
        predictionsApi.getCodeHotspots(90),
        predictionsApi.forecastResourceBottlenecks(30)
      ])
      setPredictionsData({ hotspots, bottlenecks })
    } catch (error) {
      console.error('Failed to load predictions:', error)
    } finally {
      setPredictionsLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'predictions' && !predictionsData && !predictionsLoading) {
      loadPredictions()
    }
  }, [activeTab])

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
                { id: 'predictions', label: '🔮 Predictions' },
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
            {activeTab === 'orphaned' && <OrphanedTickets data={data?.comprehensive_analysis?.orphaned_tickets} />}
            {activeTab === 'undocumented' && <UndocumentedFeatures data={data?.comprehensive_analysis?.undocumented_commits} />}
            {activeTab === 'decisions' && <MissingDecisions data={data?.comprehensive_analysis?.missing_decisions} />}
            {activeTab === 'stale' && <StaleWork data={data?.comprehensive_analysis?.stale_tickets} />}
            {activeTab === 'predictions' && (
              <PredictionsTab 
                data={predictionsData} 
                loading={predictionsLoading}
                onRefresh={loadPredictions}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function OrphanedTickets({ data }: { data: any }) {
  const tickets = data?.items || []
  const total = data?.count || 0
  const [riskScores, setRiskScores] = useState<Record<string, any>>({})
  const [loadingRisk, setLoadingRisk] = useState<Record<string, boolean>>({})

  const loadRiskScore = async (ticketKey: string) => {
    if (riskScores[ticketKey] || loadingRisk[ticketKey]) return
    
    try {
      setLoadingRisk(prev => ({ ...prev, [ticketKey]: true }))
      const risk = await predictionsApi.assessTicketRisk({ ticket_key: ticketKey })
      setRiskScores(prev => ({ ...prev, [ticketKey]: risk }))
    } catch (error) {
      console.error(`Failed to load risk for ${ticketKey}:`, error)
    } finally {
      setLoadingRisk(prev => ({ ...prev, [ticketKey]: false }))
    }
  }

  if (total === 0) {
    return <div className="text-center py-12 text-green-600">✅ No orphaned tickets found!</div>
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <h3 className="font-medium text-gray-900 mb-2">By Status</h3>
          {Object.entries(data?.statistics?.by_status || {}).map(([status, count]: any) => (
            <div key={status} className="text-sm text-gray-600">• {status}: {count}</div>
          ))}
        </div>
        <div>
          <h3 className="font-medium text-gray-900 mb-2">By Priority</h3>
          {Object.entries(data?.statistics?.by_priority || {}).map(([priority, count]: any) => (
            <div key={priority} className="text-sm text-gray-600">• {priority}: {count}</div>
          ))}
        </div>
      </div>

      {tickets.slice(0, 20).map((ticket: any) => {
        const risk = riskScores[ticket.ticket_key]
        const loading = loadingRisk[ticket.ticket_key]
        
        return (
          <div key={ticket.ticket_key} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900">{ticket.ticket_key}: {ticket.summary}</h4>
                <div className="mt-2 flex gap-4 text-sm text-gray-600">
                  <span>Status: {ticket.status}</span>
                  <span>Priority: {ticket.priority}</span>
                  <span>Assignee: {ticket.assignee || 'Unassigned'}</span>
                </div>
                
                {risk && (
                  <div className={`mt-3 inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
                    risk.risk_level === 'High' ? 'bg-red-100 text-red-800' :
                    risk.risk_level === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    <span className="font-medium">Risk: {risk.risk_score}/100 ({risk.risk_level})</span>
                  </div>
                )}
              </div>
              
              <button
                onClick={() => loadRiskScore(ticket.ticket_key)}
                disabled={loading || !!risk}
                className="ml-4 px-3 py-1 text-sm text-indigo-600 hover:text-indigo-700 disabled:opacity-50"
              >
                {loading ? '...' : risk ? '✓' : '🔮 Assess Risk'}
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function UndocumentedFeatures({ data }: { data: any }) {
  const commits = data?.items || []
  const total = data?.count || 0

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
          <div className="text-2xl font-bold text-gray-900">{data?.statistics?.total_code_changes?.toLocaleString() || 0}</div>
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
  const tickets = data?.items || []
  const total = data?.count || 0

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
  const tickets = data?.items || []
  const total = data?.count || 0

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

function PredictionsTab({ data, loading, onRefresh }: { data: any, loading: boolean, onRefresh: () => void }) {
  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading predictions...</p>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="text-center py-12">
        <button
          onClick={onRefresh}
          className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          🔮 Load Predictions
        </button>
      </div>
    )
  }

  const hotspots = data.hotspots || []
  const bottlenecks = data.bottlenecks || []

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">🔮 Predictive Analytics</h2>
          <p className="mt-1 text-sm text-gray-600">ML-powered insights to prevent future issues</p>
        </div>
        <button
          onClick={onRefresh}
          className="px-4 py-2 text-sm text-indigo-600 hover:text-indigo-700"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Code Hotspots */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">🔥 Code Hotspots</h3>
        <p className="text-sm text-gray-600 mb-4">
          Files that change frequently and are likely to cause issues
        </p>
        
        {hotspots.length === 0 ? (
          <div className="text-center py-8 text-green-600">✅ No hotspots detected!</div>
        ) : (
          <div className="space-y-3">
            {hotspots.slice(0, 10).map((hotspot: any, i: number) => (
              <div 
                key={i} 
                className={`border rounded-lg p-4 ${
                  hotspot.risk_level === 'High' ? 'border-red-300 bg-red-50' :
                  hotspot.risk_level === 'Medium' ? 'border-yellow-300 bg-yellow-50' :
                  'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-mono text-sm text-gray-900">{hotspot.file_path}</div>
                    <div className="mt-2 flex gap-4 text-sm text-gray-600">
                      <span>Changes: {hotspot.change_frequency}</span>
                      <span>Predicted (30d): {hotspot.predicted_changes_next_30_days}</span>
                      <span className={`font-medium ${
                        hotspot.risk_level === 'High' ? 'text-red-600' :
                        hotspot.risk_level === 'Medium' ? 'text-yellow-600' :
                        'text-green-600'
                      }`}>
                        Risk: {hotspot.risk_level}
                      </span>
                    </div>
                    {hotspot.contributors && hotspot.contributors.length > 0 && (
                      <div className="mt-2 text-xs text-gray-500">
                        Contributors: {hotspot.contributors.slice(0, 3).join(', ')}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Resource Bottlenecks */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">⚠️ Resource Bottlenecks</h3>
        <p className="text-sm text-gray-600 mb-4">
          Developers who may be overloaded in the next 30 days
        </p>
        
        {bottlenecks.length === 0 ? (
          <div className="text-center py-8 text-green-600">✅ No bottlenecks predicted!</div>
        ) : (
          <div className="space-y-3">
            {bottlenecks.map((bottleneck: any, i: number) => (
              <div 
                key={i} 
                className={`border rounded-lg p-4 ${
                  bottleneck.bottleneck_severity === 'High' ? 'border-red-300 bg-red-50' :
                  bottleneck.bottleneck_severity === 'Medium' ? 'border-yellow-300 bg-yellow-50' :
                  'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{bottleneck.developer}</div>
                    <div className="mt-2 flex gap-4 text-sm text-gray-600">
                      <span>Current: {bottleneck.current_workload} tickets</span>
                      <span>Predicted: {bottleneck.predicted_workload} tickets</span>
                      <span className={`font-medium ${
                        bottleneck.bottleneck_severity === 'High' ? 'text-red-600' :
                        bottleneck.bottleneck_severity === 'Medium' ? 'text-yellow-600' :
                        'text-green-600'
                      }`}>
                        Severity: {bottleneck.bottleneck_severity}
                      </span>
                    </div>
                    {bottleneck.suggested_actions && bottleneck.suggested_actions.length > 0 && (
                      <div className="mt-3 space-y-1">
                        <div className="text-xs font-medium text-gray-700">Suggested Actions:</div>
                        {bottleneck.suggested_actions.map((action: string, j: number) => (
                          <div key={j} className="text-xs text-gray-600">• {action}</div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
