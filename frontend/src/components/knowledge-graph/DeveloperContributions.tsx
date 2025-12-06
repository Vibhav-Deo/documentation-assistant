'use client'

import { useState } from 'react'
import { knowledgeGraphApi } from '@/lib/api/knowledge-graph'

export default function DeveloperContributions() {
  const [developerEmail, setDeveloperEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<any>(null)

  const handleSearch = async () => {
    if (!developerEmail.trim()) {
      setError('Please enter a developer email')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await knowledgeGraphApi.getDeveloperContributions(
        developerEmail.trim()
      )
      setData(response)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load developer contributions')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Search Input */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          👨‍💻 Developer Contributions
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          Enter a developer email to see their tickets, commits, and pull requests
        </p>

        <div className="flex gap-3">
          <input
            type="email"
            value={developerEmail}
            onChange={(e) => setDeveloperEmail(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="developer@company.com"
            className="flex-1 rounded-md border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 font-medium"
          >
            {loading ? 'Loading...' : '🔍 Search'}
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
        <div className="grid grid-cols-3 gap-6">
          {/* Developer Info */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Developer Info</h3>
            <div className="space-y-2">
              <div>
                <div className="text-sm text-gray-600">Name</div>
                <div className="font-medium">{data.developer?.name || 'N/A'}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Email</div>
                <div className="text-sm">{data.developer?.email || 'N/A'}</div>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Statistics</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Commits</span>
                <span className="font-bold">{data.commits?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Pull Requests</span>
                <span className="font-bold">{data.pull_requests?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tickets</span>
                <span className="font-bold">{data.tickets?.length || 0}</span>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow p-6 text-white">
            <h3 className="text-lg font-semibold mb-2">Total Contributions</h3>
            <div className="text-4xl font-bold">
              {(data.commits?.length || 0) +
                (data.pull_requests?.length || 0) +
                (data.tickets?.length || 0)}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
