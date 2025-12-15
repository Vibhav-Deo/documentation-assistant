'use client'

import { useState } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { useRouter } from 'next/navigation'
import { decisionsApi } from '@/lib/api/decisions'
import type { Decision } from '@/types'

export default function DecisionsPage() {
  const router = useRouter()
  const [ticketKey, setTicketKey] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [decision, setDecision] = useState<Decision | null>(null)
  const [searchResults, setSearchResults] = useState<Decision[]>([])

  const handleAnalyze = async () => {
    if (!ticketKey.trim()) {
      setError('Please enter a ticket key')
      return
    }

    setLoading(true)
    setError(null)
    setDecision(null)

    try {
      const response: any = await decisionsApi.analyzeTicket(ticketKey.trim())
      setDecision(response.enhanced_decision || response.decision)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze decision')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query')
      return
    }

    setLoading(true)
    setError(null)
    setSearchResults([])

    try {
      const results = await decisionsApi.searchDecisions(searchQuery.trim())
      setSearchResults(results)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to search decisions')
    } finally {
      setLoading(false)
    }
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  🧠 Decision Analysis
                </h1>
                <p className="text-sm text-gray-600 mt-1">
                  Extract and analyze decision rationale from tickets
                </p>
              </div>
              <button
                onClick={() => router.push('/chat')}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                ← Back to Chat
              </button>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
          {/* Analyze Ticket */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Analyze Ticket Decision
            </h2>
            <div className="flex gap-3">
              <input
                type="text"
                value={ticketKey}
                onChange={(e) => setTicketKey(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                placeholder="e.g., PROJ-123"
                className="flex-1 rounded-md border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button
                onClick={handleAnalyze}
                disabled={loading}
                className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 font-medium"
              >
                {loading ? 'Analyzing...' : '🚀 Analyze'}
              </button>
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {decision && (() => {
              const d = decision as any
              const summary = typeof d.decision_summary === 'string' ? d.decision_summary : d.decision_summary?.content || 'N/A'
              const problem = typeof d.problem_statement === 'string' ? d.problem_statement : d.problem_statement?.content || 'N/A'
              const approach = typeof d.chosen_approach === 'string' ? d.chosen_approach : d.chosen_approach?.content || 'N/A'
              const alternatives = typeof d.alternatives_considered === 'string' ? d.alternatives_considered : d.alternatives_considered?.content
              
              return (
                <div className="mt-6 space-y-4">
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Decision Summary</h3>
                    <p className="text-gray-700">{summary}</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Problem Statement</h3>
                    <p className="text-gray-700 whitespace-pre-wrap">{problem}</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Chosen Approach</h3>
                    <p className="text-gray-700 whitespace-pre-wrap">{approach}</p>
                  </div>
                  {alternatives && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">Alternatives Considered</h3>
                      <p className="text-gray-700 whitespace-pre-wrap">{alternatives}</p>
                    </div>
                  )}
                </div>
              )
            })()}
          </div>

          {/* Search Decisions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Search Decisions
            </h2>
            <div className="flex gap-3">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="authentication refactoring, database migration, etc."
                className="flex-1 rounded-md border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button
                onClick={handleSearch}
                disabled={loading}
                className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 font-medium"
              >
                {loading ? 'Searching...' : '🔍 Search'}
              </button>
            </div>

            {searchResults.length > 0 && (
              <div className="mt-6 space-y-4">
                {searchResults.map((result) => (
                  <div key={result.id} className="border-l-4 border-indigo-500 pl-4 py-2">
                    <div className="font-medium text-gray-900">{result.decision_summary}</div>
                    <div className="text-sm text-gray-600 mt-1">Ticket: {result.ticket_key}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </ProtectedRoute>
  )
}
