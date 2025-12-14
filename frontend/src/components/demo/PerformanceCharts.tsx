'use client'

import { useState, useEffect } from 'react'

export default function PerformanceCharts() {
  const [timeRange, setTimeRange] = useState('7d')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => setLoading(false), 1000)
    return () => clearTimeout(timer)
  }, [timeRange])

  const metrics = {
    '7d': {
      queries: [120, 145, 132, 178, 165, 189, 201],
      responseTime: [1.2, 1.1, 1.3, 1.0, 1.1, 0.9, 1.2],
      accuracy: [94, 95, 93, 96, 97, 95, 98],
      users: [45, 52, 48, 61, 58, 67, 72]
    },
    '30d': {
      queries: [3200, 3450, 3680, 3920, 4100, 4350, 4580],
      responseTime: [1.3, 1.2, 1.1, 1.0, 1.1, 1.0, 0.9],
      accuracy: [92, 93, 94, 95, 96, 96, 97],
      users: [180, 195, 210, 225, 240, 255, 270]
    }
  }

  const currentMetrics = metrics[timeRange as keyof typeof metrics]
  const labels = timeRange === '7d' 
    ? ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    : ['Week 1', 'Week 2', 'Week 3', 'Week 4']

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading analytics...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Performance Analytics
          </h2>
          <p className="text-xl text-gray-600">
            Real-time insights into system performance and user engagement
          </p>
        </div>
        <div className="flex gap-2">
          {[
            { key: '7d', label: '7 Days' },
            { key: '30d', label: '30 Days' }
          ].map((range) => (
            <button
              key={range.key}
              onClick={() => setTimeRange(range.key)}
              className={`px-4 py-2 rounded-lg font-medium ${
                timeRange === range.key
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Avg Response Time</p>
              <p className="text-3xl font-bold text-gray-900">1.1s</p>
              <p className="text-sm text-green-600">↓ 15% faster</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-xl">⚡</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">AI Accuracy</p>
              <p className="text-3xl font-bold text-gray-900">96.5%</p>
              <p className="text-sm text-green-600">↑ 2.3% improvement</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-xl">🎯</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Active Users</p>
              <p className="text-3xl font-bold text-gray-900">267</p>
              <p className="text-sm text-green-600">↑ 18% growth</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <span className="text-xl">👥</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Uptime</p>
              <p className="text-3xl font-bold text-gray-900">99.9%</p>
              <p className="text-sm text-green-600">Enterprise SLA</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-xl">✅</span>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Query Volume Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Query Volume</h3>
          <div className="h-64 flex items-end justify-between gap-2">
            {currentMetrics.queries.map((value, index) => (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full bg-indigo-500 rounded-t transition-all duration-1000 ease-out"
                  style={{ height: `${(value / Math.max(...currentMetrics.queries)) * 200}px` }}
                ></div>
                <div className="text-xs text-gray-500 mt-2">{labels[index]}</div>
                <div className="text-xs font-medium text-gray-700">{value}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Response Time Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Response Time (seconds)</h3>
          <div className="h-64 flex items-end justify-between gap-2">
            {currentMetrics.responseTime.map((value, index) => (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full bg-green-500 rounded-t transition-all duration-1000 ease-out"
                  style={{ height: `${(value / Math.max(...currentMetrics.responseTime)) * 200}px` }}
                ></div>
                <div className="text-xs text-gray-500 mt-2">{labels[index]}</div>
                <div className="text-xs font-medium text-gray-700">{value}s</div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Accuracy Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Accuracy (%)</h3>
          <div className="h-64 flex items-end justify-between gap-2">
            {currentMetrics.accuracy.map((value, index) => (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full bg-blue-500 rounded-t transition-all duration-1000 ease-out"
                  style={{ height: `${((value - 90) / 10) * 200}px` }}
                ></div>
                <div className="text-xs text-gray-500 mt-2">{labels[index]}</div>
                <div className="text-xs font-medium text-gray-700">{value}%</div>
              </div>
            ))}
          </div>
        </div>

        {/* User Growth Chart */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Users</h3>
          <div className="h-64 flex items-end justify-between gap-2">
            {currentMetrics.users.map((value, index) => (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full bg-purple-500 rounded-t transition-all duration-1000 ease-out"
                  style={{ height: `${(value / Math.max(...currentMetrics.users)) * 200}px` }}
                ></div>
                <div className="text-xs text-gray-500 mt-2">{labels[index]}</div>
                <div className="text-xs font-medium text-gray-700">{value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Insights */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-2xl">🚀</span>
            </div>
            <h4 className="font-medium text-gray-900 mb-2">Optimized Performance</h4>
            <p className="text-sm text-gray-600">
              Response times improved by 15% through caching and query optimization
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-2xl">🧠</span>
            </div>
            <h4 className="font-medium text-gray-900 mb-2">AI Model Accuracy</h4>
            <p className="text-sm text-gray-600">
              Continuous learning from user feedback improves accuracy over time
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-2xl">📈</span>
            </div>
            <h4 className="font-medium text-gray-900 mb-2">Growing Adoption</h4>
            <p className="text-sm text-gray-600">
              User base growing 18% month-over-month with high engagement
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}