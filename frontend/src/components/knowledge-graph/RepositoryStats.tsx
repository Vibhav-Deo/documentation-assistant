'use client'

import { useEffect, useState } from 'react'
import { knowledgeGraphApi } from '@/lib/api/knowledge-graph'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function RepositoryStats() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<any>(null)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await knowledgeGraphApi.getRepositoryStats()
      setStats(response)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load repository stats')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading repository stats...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    )
  }

  if (!stats) return null

  // Prepare language distribution data for chart
  const languageData = Object.entries(stats.language_distribution || {}).map(
    ([name, value]) => ({
      name,
      files: value,
    })
  )

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow p-6 text-white">
          <div className="text-sm opacity-90">Total Commits</div>
          <div className="text-3xl font-bold mt-2">{stats.total_commits || 0}</div>
        </div>
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow p-6 text-white">
          <div className="text-sm opacity-90">Code Files</div>
          <div className="text-3xl font-bold mt-2">{stats.total_files || 0}</div>
        </div>
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow p-6 text-white">
          <div className="text-sm opacity-90">Pull Requests</div>
          <div className="text-3xl font-bold mt-2">{stats.total_prs || 0}</div>
        </div>
        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg shadow p-6 text-white">
          <div className="text-sm opacity-90">Contributors</div>
          <div className="text-3xl font-bold mt-2">
            {stats.top_contributors?.length || 0}
          </div>
        </div>
      </div>

      {/* Language Distribution Chart */}
      {languageData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Language Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={languageData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="files" fill="#4f46e5" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Top Contributors */}
      {stats.top_contributors && stats.top_contributors.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Top Contributors
          </h3>
          <div className="space-y-3">
            {stats.top_contributors.slice(0, 10).map((contributor: any, idx: number) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center font-bold">
                    {idx + 1}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">
                      {contributor.name || 'Unknown'}
                    </div>
                    <div className="text-sm text-gray-600">{contributor.email}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-gray-900">
                    {contributor.commit_count || 0}
                  </div>
                  <div className="text-xs text-gray-500">commits</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
