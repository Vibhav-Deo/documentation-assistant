'use client'

import { useState } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/auth'
import OrganizationMetrics from '@/components/admin/OrganizationMetrics'
import SystemHealth from '@/components/admin/SystemHealth'
import RequestMetrics from '@/components/admin/RequestMetrics'
import Alerts from '@/components/admin/Alerts'

type TabType = 'organization' | 'health' | 'requests' | 'alerts'

export default function AdminPage() {
  const router = useRouter()
  const { user } = useAuthStore()
  const [activeTab, setActiveTab] = useState<TabType>('organization')

  // Check if user is admin
  if (user && user.role !== 'admin') {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="bg-white rounded-lg shadow-lg p-8 max-w-md">
            <h2 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h2>
            <p className="text-gray-600 mb-6">
              You need admin privileges to access this page.
            </p>
            <button
              onClick={() => router.push('/chat')}
              className="w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              Back to Chat
            </button>
          </div>
        </div>
      </ProtectedRoute>
    )
  }

  const tabs = [
    { id: 'organization' as TabType, label: '🏢 Organization', icon: '🏢' },
    { id: 'health' as TabType, label: '🏥 System Health', icon: '🏥' },
    { id: 'requests' as TabType, label: '📊 Request Metrics', icon: '📊' },
    { id: 'alerts' as TabType, label: '🚨 Alerts', icon: '🚨' },
  ]

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  🛠️ Admin Panel
                </h1>
                <p className="text-sm text-gray-600 mt-1">
                  System monitoring and organization management
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

        {/* Tabs */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav className="flex space-x-8" aria-label="Tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap
                    ${
                      activeTab === tab.id
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {activeTab === 'organization' && <OrganizationMetrics />}
          {activeTab === 'health' && <SystemHealth />}
          {activeTab === 'requests' && <RequestMetrics />}
          {activeTab === 'alerts' && <Alerts />}
        </main>
      </div>
    </ProtectedRoute>
  )
}
