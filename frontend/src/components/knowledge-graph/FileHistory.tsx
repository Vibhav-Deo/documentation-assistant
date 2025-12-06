'use client'

import { useState } from 'react'
import { knowledgeGraphApi } from '@/lib/api/knowledge-graph'

export default function FileHistory() {
  const [filePath, setFilePath] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<any>(null)

  const handleSearch = async () => {
    if (!filePath.trim()) {
      setError('Please enter a file path')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await knowledgeGraphApi.getFileHistory(filePath.trim())
      setData(response)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load file history')
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
          📁 File History
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          Enter a file path to see related commits, tickets, and developers
        </p>

        <div className="flex gap-3">
          <input
            type="text"
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="src/components/Example.tsx"
            className="flex-1 rounded-md border border-gray-300 px-4 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
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
        <div className="grid grid-cols-2 gap-6">
          {/* File Info */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">File Info</h3>
            {data.file && (
              <div className="space-y-2">
                <div>
                  <div className="text-sm text-gray-600">Path</div>
                  <div className="font-mono text-sm">{data.file.file_path}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Language</div>
                  <div>{data.file.language}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Size</div>
                  <div>{(data.file.size / 1024).toFixed(1)} KB</div>
                </div>
              </div>
            )}
          </div>

          {/* Stats */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Activity</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Commits</span>
                <span className="font-bold">{data.commits?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Related Tickets</span>
                <span className="font-bold">{data.tickets?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Contributors</span>
                <span className="font-bold">{data.developers?.length || 0}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
