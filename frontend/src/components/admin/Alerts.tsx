'use client'

import { useEffect, useState } from 'react'
import { adminApi } from '@/lib/api/admin'

export default function Alerts() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [alerts, setAlerts] = useState<any[]>([])

  useEffect(() => {
    loadAlerts()
  }, [])

  const loadAlerts = async () => {
    setLoading(true)
    setError(null)

    try {
      const response: any = await adminApi.getAlerts()
      // API returns data wrapped in {success, data: [...]} structure
      const data = response.data || response
      setAlerts(Array.isArray(data) ? data : [])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load alerts')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading alerts...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
        <button
          onClick={loadAlerts}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    )
  }

  if (alerts.length === 0) {
    return (
      <div className="bg-green-50 border-2 border-green-500 rounded-lg p-8 text-center">
        <div className="text-6xl mb-4">✅</div>
        <h3 className="text-2xl font-bold text-green-900 mb-2">All Clear!</h3>
        <p className="text-green-700">No active alerts at this time.</p>
      </div>
    )
  }

  const getAlertStyle = (type: string) => {
    switch (type) {
      case 'critical':
        return {
          container: 'bg-red-50 border-red-500',
          icon: '🚨',
          label: 'CRITICAL',
          labelClass: 'bg-red-600 text-white',
        }
      case 'warning':
        return {
          container: 'bg-yellow-50 border-yellow-500',
          icon: '⚠️',
          label: 'WARNING',
          labelClass: 'bg-yellow-600 text-white',
        }
      default:
        return {
          container: 'bg-blue-50 border-blue-500',
          icon: 'ℹ️',
          label: 'INFO',
          labelClass: 'bg-blue-600 text-white',
        }
    }
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            🚨 Active Alerts ({alerts.length})
          </h2>
          <button
            onClick={loadAlerts}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {alerts.map((alert, index) => {
        const style = getAlertStyle(alert.type)
        return (
          <div
            key={index}
            className={`rounded-lg border-l-4 p-6 ${style.container}`}
          >
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 text-3xl">{style.icon}</div>
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${style.labelClass}`}>
                    {style.label}
                  </span>
                  {alert.timestamp && (
                    <span className="text-xs text-gray-500">
                      {new Date(alert.timestamp).toLocaleString()}
                    </span>
                  )}
                </div>
                <p className="text-gray-900 font-medium">{alert.message}</p>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
