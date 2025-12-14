'use client'

import { useState, useEffect } from 'react'

interface Metric {
  label: string
  value: string
  change: string
  trend: 'up' | 'down' | 'stable'
  icon: string
}

export default function HeroMetrics() {
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate loading metrics
    const timer = setTimeout(() => {
      setMetrics([
        {
          label: 'Documents Indexed',
          value: '12,847',
          change: '+23% this month',
          trend: 'up',
          icon: '📚'
        },
        {
          label: 'Queries Processed',
          value: '45,231',
          change: '+18% this month',
          trend: 'up',
          icon: '🔍'
        },
        {
          label: 'AI Insights Generated',
          value: '8,934',
          change: '+31% this month',
          trend: 'up',
          icon: '🧠'
        },
        {
          label: 'Average Response Time',
          value: '1.2s',
          change: '-15% improvement',
          trend: 'up',
          icon: '⚡'
        },
        {
          label: 'Developer Hours Saved',
          value: '2,156',
          change: '+42% this month',
          trend: 'up',
          icon: '⏰'
        },
        {
          label: 'Code Hotspots Detected',
          value: '127',
          change: '23 resolved',
          trend: 'stable',
          icon: '🔥'
        }
      ])
      setLoading(false)
    }, 1000)

    return () => clearTimeout(timer)
  }, [])

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading system metrics...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">
          Platform Overview
        </h2>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Real-time metrics from our AI-powered development intelligence platform.
          See how we're transforming developer productivity with predictive analytics.
        </p>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {metrics.map((metric, index) => (
          <div
            key={index}
            className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow duration-300"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-2xl">{metric.icon}</span>
                  <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                    {metric.label}
                  </h3>
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  {metric.value}
                </div>
                <div className={`flex items-center gap-1 text-sm ${
                  metric.trend === 'up' ? 'text-green-600' :
                  metric.trend === 'down' ? 'text-red-600' :
                  'text-gray-600'
                }`}>
                  {metric.trend === 'up' && '↗️'}
                  {metric.trend === 'down' && '↘️'}
                  {metric.trend === 'stable' && '➡️'}
                  <span>{metric.change}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* System Health */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">System Health</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-2xl">✅</span>
            </div>
            <div className="text-sm font-medium text-gray-900">API Status</div>
            <div className="text-xs text-green-600">All systems operational</div>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-2xl">🚀</span>
            </div>
            <div className="text-sm font-medium text-gray-900">Performance</div>
            <div className="text-xs text-blue-600">99.9% uptime</div>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-2xl">🤖</span>
            </div>
            <div className="text-sm font-medium text-gray-900">AI Models</div>
            <div className="text-xs text-purple-600">3 models active</div>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-2xl">🔒</span>
            </div>
            <div className="text-sm font-medium text-gray-900">Security</div>
            <div className="text-xs text-yellow-600">Enterprise grade</div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Recent Activity</h3>
        <div className="space-y-4">
          {[
            { time: '2 minutes ago', action: 'Code hotspot detected in auth/oauth.ts', type: 'warning' },
            { time: '5 minutes ago', action: 'New decision extracted from PROJ-123', type: 'info' },
            { time: '8 minutes ago', action: 'Risk assessment completed for 3 tickets', type: 'success' },
            { time: '12 minutes ago', action: 'Auto-tagged 15 commits as "feature"', type: 'info' },
            { time: '18 minutes ago', action: 'Predicted bottleneck for developer@company.com', type: 'warning' },
          ].map((activity, index) => (
            <div key={index} className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50">
              <div className={`w-2 h-2 rounded-full mt-2 ${
                activity.type === 'warning' ? 'bg-yellow-400' :
                activity.type === 'success' ? 'bg-green-400' :
                'bg-blue-400'
              }`}></div>
              <div className="flex-1">
                <div className="text-sm text-gray-900">{activity.action}</div>
                <div className="text-xs text-gray-500">{activity.time}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}