'use client'

import { useState } from 'react'
import { knowledgeGraphApi } from '@/lib/api/knowledge-graph'
import RelationshipGraph from './RelationshipGraph'
import type { TicketRelationship } from '@/types'

export default function TicketRelationships() {
  const [ticketKey, setTicketKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<TicketRelationship | null>(null)

  const handleSearch = async () => {
    if (!ticketKey.trim()) {
      setError('Please enter a ticket key')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await knowledgeGraphApi.getTicketRelationships(ticketKey.trim())
      setData(response)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load ticket relationships')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="space-y-6">
      {/* Search Input */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          🎫 Explore Ticket Relationships
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          Enter a ticket key to see all related commits, PRs, code files, and developers
        </p>

        <div className="flex gap-3">
          <input
            type="text"
            value={ticketKey}
            onChange={(e) => setTicketKey(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="e.g., JIRA-123, SCRUM-45"
            className="flex-1 rounded-md border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Loading...' : '🔍 Explore'}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}
      </div>

      {/* Results */}
      {data && (
        <div className="space-y-6">
          {/* Summary Metrics */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Commits</div>
              <div className="text-2xl font-bold text-gray-900">
                {data.commits?.length || 0}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Pull Requests</div>
              <div className="text-2xl font-bold text-gray-900">
                {data.pull_requests?.length || 0}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Code Files</div>
              <div className="text-2xl font-bold text-gray-900">
                {data.code_files?.length || 0}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-4">
              <div className="text-sm text-gray-600">Developers</div>
              <div className="text-2xl font-bold text-gray-900">
                {data.developers?.length || 0}
              </div>
            </div>
          </div>

          {/* Graph Visualization */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Relationship Graph
            </h3>
            <RelationshipGraph data={data} ticketKey={data.ticket_key} />
          </div>

          {/* Details Tables */}
          <div className="grid grid-cols-2 gap-6">
            {/* Commits */}
            {data.commits && data.commits.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  💾 Commits ({data.commits.length})
                </h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {data.commits.map((commit, idx) => (
                    <div key={idx} className="border-l-4 border-purple-500 pl-3 py-2">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {commit.message}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {commit.author} • {new Date(commit.date).toLocaleDateString()}
                      </div>
                      {commit.commit_hash && (
                        <div className="text-xs text-gray-500 font-mono mt-1">
                          {commit.commit_hash.substring(0, 8)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Pull Requests */}
            {data.pull_requests && data.pull_requests.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  🔀 Pull Requests ({data.pull_requests.length})
                </h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {data.pull_requests.map((pr, idx) => (
                    <div key={idx} className="border-l-4 border-green-500 pl-3 py-2">
                      <div className="text-sm font-medium text-gray-900">
                        #{pr.pr_number}: {pr.title}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {pr.author} • {pr.state}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(pr.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Code Files */}
            {data.code_files && data.code_files.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  📝 Code Files ({data.code_files.length})
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {data.code_files.map((file, idx) => (
                    <div key={idx} className="border-l-4 border-orange-500 pl-3 py-2">
                      <div className="text-sm font-medium text-gray-900 font-mono truncate">
                        {file.file_path}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {file.language} • {(file.size / 1024).toFixed(1)} KB
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Developers */}
            {data.developers && data.developers.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  👨‍💻 Developers ({data.developers.length})
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {data.developers.map((dev, idx) => (
                    <div key={idx} className="border-l-4 border-blue-500 pl-3 py-2">
                      <div className="text-sm font-medium text-gray-900">{dev.name}</div>
                      <div className="text-xs text-gray-600 mt-1">{dev.email}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {dev.commits_count} commits
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
