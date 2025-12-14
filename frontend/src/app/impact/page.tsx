'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { impactApi } from '@/lib/api/impact'
import { predictionsApi } from '@/lib/api/predictions'
import ProtectedRoute from '@/components/auth/ProtectedRoute'

export default function ImpactPage() {
  return (
    <ProtectedRoute>
      <ImpactContent />
    </ProtectedRoute>
  )
}

function ImpactContent() {
  const router = useRouter()
  const [analysisType, setAnalysisType] = useState<'file' | 'ticket' | 'commit' | 'reviewers'>('file')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">🎯 Impact Analysis</h1>
            <p className="mt-2 text-gray-600">Predict the impact of changes before they happen</p>
          </div>
          <button
            onClick={() => router.push('/chat')}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            ← Back to Chat
          </button>
        </div>

        {/* Analysis Type Selector */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="grid grid-cols-4 gap-0">
            {[
              { id: 'file', label: '📄 File Impact', desc: 'Analyze file changes' },
              { id: 'ticket', label: '🎫 Ticket Impact', desc: 'Estimate scope' },
              { id: 'commit', label: '💻 Commit Impact', desc: 'Risk assessment' },
              { id: 'reviewers', label: '👥 Reviewers', desc: 'Suggest reviewers' },
            ].map((type) => (
              <button
                key={type.id}
                onClick={() => setAnalysisType(type.id as any)}
                className={`p-6 text-left border-b-4 transition-colors ${
                  analysisType === type.id
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-transparent hover:bg-gray-50'
                }`}
              >
                <div className="font-medium text-gray-900">{type.label}</div>
                <div className="mt-1 text-sm text-gray-500">{type.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Analysis Content */}
        <div className="bg-white rounded-lg shadow p-6">
          {analysisType === 'file' && <FileImpact />}
          {analysisType === 'ticket' && <TicketImpact />}
          {analysisType === 'commit' && <CommitImpact />}
          {analysisType === 'reviewers' && <ReviewerSuggestions />}
        </div>
      </div>
    </div>
  )
}

function FileImpact() {
  const [filePath, setFilePath] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string>('')

  const analyze = async () => {
    if (!filePath) return
    try {
      setLoading(true)
      setError('')
      const data = await impactApi.analyzeFile(filePath)
      setResult(data)
    } catch (error: any) {
      setError(error?.message || 'Failed to analyze file')
      console.error('Failed to analyze:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">File Impact Analysis</h2>
        <p className="text-gray-600 mb-6">Analyze what would be affected if you change a specific file</p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">File Path</label>
            <input
              type="text"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              placeholder="e.g., src/auth/oauth.ts"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          <button
            onClick={analyze}
            disabled={!filePath || loading}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Analyzing...' : '🔍 Analyze Impact'}
          </button>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="mt-8 space-y-6">
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-500">Total Commits</div>
              <div className="text-2xl font-bold text-gray-900">{result.total_commits || 0}</div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-500">Related Tickets</div>
              <div className="text-2xl font-bold text-gray-900">{result.related_tickets?.length || 0}</div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-500">Developers</div>
              <div className="text-2xl font-bold text-gray-900">{result.top_developers?.length || 0}</div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-500">Co-changed Files</div>
              <div className="text-2xl font-bold text-gray-900">{result.frequently_changed_with?.length || 0}</div>
            </div>
          </div>

          <div>
            <h3 className="font-medium text-gray-900 mb-3">Top Developers</h3>
            <div className="space-y-2">
              {result.top_developers?.slice(0, 5).map((dev: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <span className="text-gray-900">{dev.email}</span>
                  <span className="text-sm text-gray-600">{dev.commit_count} commits</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function TicketImpact() {
  const [ticketKey, setTicketKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string>('')
  const [riskAssessment, setRiskAssessment] = useState<any>(null)
  const [riskLoading, setRiskLoading] = useState(false)

  const analyze = async () => {
    if (!ticketKey) return
    try {
      setLoading(true)
      setError('')
      const data = await impactApi.analyzeTicket(ticketKey)
      setResult(data)
      
      // Also load risk assessment
      loadRiskAssessment(ticketKey)
    } catch (error: any) {
      setError(error?.message || 'Failed to analyze ticket')
      console.error('Failed to analyze:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadRiskAssessment = async (key: string) => {
    try {
      setRiskLoading(true)
      const risk = await predictionsApi.assessTicketRisk({ ticket_key: key })
      setRiskAssessment(risk)
    } catch (error) {
      console.error('Failed to load risk:', error)
    } finally {
      setRiskLoading(false)
    }
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Ticket Impact Analysis</h2>
      <p className="text-gray-600 mb-6">Estimate the scope and impact of implementing a ticket</p>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Ticket Key</label>
          <input
            type="text"
            value={ticketKey}
            onChange={(e) => setTicketKey(e.target.value.toUpperCase())}
            placeholder="e.g., AUTH-101"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>

        <button
          onClick={analyze}
          disabled={!ticketKey || loading}
          className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Analyzing...' : '🔍 Analyze Impact'}
        </button>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="mt-8 space-y-6">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="font-medium text-blue-900">{result.ticket_key}</div>
            <div className="text-sm text-blue-700 mt-1">{result.summary}</div>
          </div>

          {/* Risk Assessment Panel */}
          {riskAssessment && (
            <div className={`p-4 rounded-lg border ${
              riskAssessment.risk_level === 'High' ? 'bg-red-50 border-red-300' :
              riskAssessment.risk_level === 'Medium' ? 'bg-yellow-50 border-yellow-300' :
              'bg-green-50 border-green-300'
            }`}>
              <div className="flex items-start gap-3">
                <div className="text-2xl">
                  {riskAssessment.risk_level === 'High' ? '🔴' :
                   riskAssessment.risk_level === 'Medium' ? '🟡' : '🟢'}
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 mb-2">
                    Risk Assessment: {riskAssessment.risk_score}/100 ({riskAssessment.risk_level})
                  </h3>
                  {riskAssessment.risk_factors && riskAssessment.risk_factors.length > 0 && (
                    <div className="mb-3">
                      <div className="text-sm font-medium text-gray-700 mb-1">Risk Factors:</div>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {riskAssessment.risk_factors.map((factor: string, i: number) => (
                          <li key={i}>• {factor}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {riskAssessment.mitigation_suggestions && riskAssessment.mitigation_suggestions.length > 0 && (
                    <div>
                      <div className="text-sm font-medium text-gray-700 mb-1">Mitigation Suggestions:</div>
                      <ul className="text-sm text-gray-600 space-y-1">
                        {riskAssessment.mitigation_suggestions.map((suggestion: string, i: number) => (
                          <li key={i}>• {suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-500">Files Affected</div>
              <div className="text-2xl font-bold text-gray-900">{result.file_count || 0}</div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-500">Total Changes</div>
              <div className="text-2xl font-bold text-gray-900">{result.total_changes?.toLocaleString() || 0}</div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-500">Similar Tickets</div>
              <div className="text-2xl font-bold text-gray-900">{result.similar_tickets?.length || 0}</div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-500">Dependencies</div>
              <div className="text-2xl font-bold text-gray-900">{result.dependent_tickets?.length || 0}</div>
            </div>
          </div>

          {result.blast_radius && (
            <div className={`p-4 rounded-lg ${
              result.blast_radius.includes('Small') ? 'bg-green-50 border border-green-200' :
              result.blast_radius.includes('Medium') ? 'bg-yellow-50 border border-yellow-200' :
              'bg-red-50 border border-red-200'
            }`}>
              <div className="font-medium">📊 Blast Radius: {result.blast_radius}</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function CommitImpact() {
  const [sha, setSha] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string>('')

  const analyze = async () => {
    if (!sha) return
    try {
      setLoading(true)
      setError('')
      const data = await impactApi.analyzeCommit(sha)
      setResult(data)
    } catch (error: any) {
      setError(error?.message || 'Failed to analyze commit')
      console.error('Failed to analyze:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Commit Impact Analysis</h2>
      <p className="text-gray-600 mb-6">Analyze the impact and risk of a specific commit</p>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Commit SHA</label>
          <input
            type="text"
            value={sha}
            onChange={(e) => setSha(e.target.value)}
            placeholder="e.g., abc123def456"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>

        <button
          onClick={analyze}
          disabled={!sha || loading}
          className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Analyzing...' : '🔍 Analyze Impact'}
        </button>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="mt-8 space-y-6">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="font-mono text-sm text-gray-600">{result.sha?.slice(0, 7)}</div>
            <div className="mt-1 text-gray-900">{result.message?.split('\n')[0]}</div>
            <div className="mt-2 text-sm text-gray-600">{result.author} • {new Date(result.date).toLocaleDateString()}</div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-500">Files Changed</div>
              <div className="text-2xl font-bold text-gray-900">{result.file_count || 0}</div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-500">Lines Changed</div>
              <div className="text-2xl font-bold text-gray-900">+{result.additions || 0} -{result.deletions || 0}</div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-sm text-gray-500">Risk Score</div>
              <div className="text-2xl font-bold text-gray-900">{result.risk_score || 0}/100</div>
            </div>
          </div>

          {result.risk_level && (
            <div className={`p-4 rounded-lg ${
              result.risk_level === 'Low' ? 'bg-green-50 border border-green-200' :
              result.risk_level === 'Medium' ? 'bg-yellow-50 border border-yellow-200' :
              'bg-red-50 border border-red-200'
            }`}>
              <div className="font-medium">Risk Level: {result.risk_level}</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ReviewerSuggestions() {
  const [files, setFiles] = useState(['', ''])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string>('')

  const suggest = async () => {
    const validFiles = files.filter(f => f.trim())
    if (validFiles.length === 0) return

    try {
      setLoading(true)
      setError('')
      const data = await impactApi.suggestReviewers(validFiles)
      setResult(data)
    } catch (error: any) {
      setError(error?.message || 'Failed to suggest reviewers')
      console.error('Failed to suggest:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Suggest Code Reviewers</h2>
      <p className="text-gray-600 mb-6">Get reviewer recommendations based on file history</p>

      <div className="space-y-4">
        {files.map((file, i) => (
          <div key={i}>
            <label className="block text-sm font-medium text-gray-700 mb-2">File {i + 1}</label>
            <input
              type="text"
              value={file}
              onChange={(e) => {
                const newFiles = [...files]
                newFiles[i] = e.target.value
                setFiles(newFiles)
              }}
              placeholder="e.g., src/auth/oauth.ts"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>
        ))}

        <button
          onClick={() => setFiles([...files, ''])}
          className="text-sm text-indigo-600 hover:text-indigo-700"
        >
          + Add another file
        </button>

        <button
          onClick={suggest}
          disabled={files.filter(f => f.trim()).length === 0 || loading}
          className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Finding reviewers...' : '👥 Suggest Reviewers'}
        </button>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="mt-8 space-y-4">
          <h3 className="font-medium text-gray-900">Suggested Reviewers</h3>
          {result.suggested_reviewers?.map((reviewer: any, i: number) => (
            <div key={i} className={`p-4 rounded-lg border ${i < 3 ? 'border-indigo-200 bg-indigo-50' : 'border-gray-200'}`}>
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-medium text-gray-900">
                    {i < 3 && '⭐ '}#{i + 1} {reviewer.author_name}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">{reviewer.author_email}</div>
                  <div className="text-sm text-gray-600 mt-1">
                    {reviewer.commit_count} commits • Last: {new Date(reviewer.last_commit_date).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
