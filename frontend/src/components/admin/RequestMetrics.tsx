'use client'

import { useEffect, useState } from 'react'
import { adminApi } from '@/lib/api/admin'

export default function RequestMetrics() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<any>(null)
  const [timePeriod, setTimePeriod] = useState(24)

  useEffect(() => {
    loadMetrics()
  }, [timePeriod])

  const loadMetrics = async () => {
    setLoading(true)
    setError(null)

    try {
      const data = await adminApi.getRequestMetrics(timePeriod)
      setMetrics(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load request metrics')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading request metrics...</p>
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

  if (!metrics) return null

  const timePeriods = [
    { value: 1, label: 'Last 1 hour' },
    { value: 6, label: 'Last 6 hours' },
    { value: 24, label: 'Last 24 hours' },
    { value: 168, label: 'Last 7 days' },
  ]

  return (
    <div className="space-y-6">
      {/* Time Period Selector */}
      <div className="bg-white rounded-lg shadow p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Time Period
        </label>
        <select
          value={timePeriod}
          onChange={(e) => setTimePeriod(Number(e.target.value))}
          className="w-full md:w-64 rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          {timePeriods.map((period) => (
            <option key={period.value} value={period.value}>
              {period.label}
            </option>
          ))}
        </select>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Total Requests</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">
            {metrics.total_requests || 0}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Avg Response Time</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">
            {metrics.avg_response_time?.toFixed(2) || 0}s
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Error Rate</div>
          <div className={`text-3xl font-bold mt-2 ${
            metrics.error_rate > 5 ? 'text-red-600' : 'text-gray-900'
          }`}>
            {metrics.error_rate?.toFixed(1) || 0}%
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Period</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">
            {timePeriod}h
          </div>
        </div>
      </div>

      {/* Status Code Distribution */}
      {metrics.status_codes && Object.keys(metrics.status_codes).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Status Code Distribution
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(metrics.status_codes).map(([code, count]: [string, any]) => (
              <div
                key={code}
                className={`p-4 rounded-lg border-2 ${
                  code.startsWith('2')
                    ? 'border-green-500 bg-green-50'
                    : code.startsWith('4')
                    ? 'border-yellow-500 bg-yellow-50'
                    : code.startsWith('5')
                    ? 'border-red-500 bg-red-50'
                    : 'border-gray-300 bg-gray-50'
                }`}
              >
                <div className="text-sm text-gray-600">HTTP {code}</div>
                <div className="text-2xl font-bold text-gray-900 mt-1">{count}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top Endpoints */}
      {metrics.top_endpoints && Object.keys(metrics.top_endpoints).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Top Endpoints (By Request Count)
          </h3>
          <div className="space-y-3">
            {Object.entries(metrics.top_endpoints)
              .slice(0, 10)
              .map(([endpoint, count]: [string, any], idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-indigo-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                      {idx + 1}
                    </div>
                    <div className="font-mono text-sm text-gray-900">{endpoint}</div>
                  </div>
                  <div className="text-lg font-bold text-gray-900">{count}</div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
