'use client'

import { useEffect, useState } from 'react'
import { adminApi } from '@/lib/api/admin'

export default function SystemHealth() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [health, setHealth] = useState<any>(null)
  const [metrics, setMetrics] = useState<any>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)

    try {
      const [healthData, metricsData] = await Promise.all([
        adminApi.getSystemHealth(),
        adminApi.getSystemMetrics(),
      ])
      setHealth(healthData)
      setMetrics(metricsData)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load system health')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading system health...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
        <button
          onClick={loadData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!health) return null

  const isHealthy = health.status === 'healthy'
  const services = health.services || {}

  return (
    <div className="space-y-6">
      {/* Overall Status */}
      <div className="grid grid-cols-3 gap-4">
        <div className={`rounded-lg shadow p-6 ${isHealthy ? 'bg-green-500' : 'bg-red-500'} text-white`}>
          <div className="text-sm opacity-90">Overall Status</div>
          <div className="text-3xl font-bold mt-2 capitalize">
            {isHealthy ? '✅ Healthy' : '❌ Unhealthy'}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600">Healthy Services</div>
          <div className="text-3xl font-bold text-gray-900 mt-2">
            {Object.values(services).filter((s: any) => s.status === 'healthy').length}/
            {Object.keys(services).length}
          </div>
        </div>

        {metrics && (
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600">CPU Usage</div>
            <div className={`text-3xl font-bold mt-2 ${
              metrics.cpu_percent > 80 ? 'text-red-600' : 'text-gray-900'
            }`}>
              {metrics.cpu_percent?.toFixed(1) || 0}%
            </div>
          </div>
        )}
      </div>

      {/* Service Status Cards */}
      <div className="grid grid-cols-2 gap-6">
        {Object.entries(services).map(([serviceName, serviceData]: [string, any]) => (
          <div
            key={serviceName}
            className={`rounded-lg shadow p-6 border-l-4 ${
              serviceData.status === 'healthy'
                ? 'bg-white border-green-500'
                : 'bg-red-50 border-red-500'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 capitalize">
                  {serviceName}
                </h3>
                <p className={`text-sm mt-1 ${
                  serviceData.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {serviceData.status === 'healthy' ? '✅ Operational' : '❌ Down'}
                </p>
              </div>
              <div className="text-right">
                {serviceData.status === 'healthy' ? (
                  <div className="text-3xl">✅</div>
                ) : (
                  <div className="text-3xl">❌</div>
                )}
              </div>
            </div>

            {serviceData.error && (
              <div className="mt-3 p-2 bg-red-100 rounded text-xs text-red-800">
                <strong>Error:</strong> {serviceData.error}
              </div>
            )}

            {serviceData.version && (
              <div className="mt-2 text-xs text-gray-500">
                Version: {serviceData.version}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* System Metrics */}
      {metrics && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Metrics</h3>
          <div className="grid grid-cols-3 gap-6">
            {/* CPU */}
            <div>
              <div className="text-sm text-gray-600 mb-2">CPU Usage</div>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className={`h-4 rounded-full ${
                    metrics.cpu_percent > 80
                      ? 'bg-red-600'
                      : metrics.cpu_percent > 60
                      ? 'bg-yellow-500'
                      : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(metrics.cpu_percent, 100)}%` }}
                />
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {metrics.cpu_percent?.toFixed(1)}%
              </div>
            </div>

            {/* Memory */}
            {metrics.memory_percent && (
              <div>
                <div className="text-sm text-gray-600 mb-2">Memory Usage</div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className={`h-4 rounded-full ${
                      metrics.memory_percent > 80
                        ? 'bg-red-600'
                        : metrics.memory_percent > 60
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(metrics.memory_percent, 100)}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {metrics.memory_percent?.toFixed(1)}%
                </div>
              </div>
            )}

            {/* Disk */}
            {metrics.disk_percent && (
              <div>
                <div className="text-sm text-gray-600 mb-2">Disk Usage</div>
                <div className="w-full bg-gray-200 rounded-full h-4">
                  <div
                    className={`h-4 rounded-full ${
                      metrics.disk_percent > 80
                        ? 'bg-red-600'
                        : metrics.disk_percent > 60
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(metrics.disk_percent, 100)}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {metrics.disk_percent?.toFixed(1)}%
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
