'use client'

import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import AISettings from './AISettings'
import SourceFilters from './SourceFilters'

export default function Sidebar() {
  const router = useRouter()
  const { user, organization, logout } = useAuthStore()
  const { clearMessages } = useChatStore()

  const handleClearChat = () => {
    clearMessages()
  }

  return (
    <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col h-full">
      {/* User Info */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-bold text-gray-900">Documentation Assistant</h2>
        </div>
        <div className="text-sm">
          <p className="font-medium text-gray-900">{user?.name}</p>
          <p className="text-gray-600">{user?.email}</p>
          <p className="text-xs text-gray-500 mt-1">{organization?.name}</p>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Source Filters */}
        <SourceFilters />

        {/* AI Settings */}
        <AISettings />

        {/* Navigation Buttons */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold text-gray-900 mb-3">📊 Features</h3>
          <div className="space-y-2">
            <button
              onClick={() => router.push('/sync')}
              className="w-full text-left px-3 py-2 rounded-md hover:bg-indigo-50 text-sm text-indigo-700 font-medium border border-indigo-200"
            >
              🔄 Sync Data Sources
            </button>
            <button
              onClick={() => router.push('/knowledge-graph')}
              className="w-full text-left px-3 py-2 rounded-md hover:bg-gray-100 text-sm text-gray-700"
            >
              🔗 Knowledge Graph
            </button>
            <button
              onClick={() => router.push('/decisions')}
              className="w-full text-left px-3 py-2 rounded-md hover:bg-gray-100 text-sm text-gray-700"
            >
              🧠 Decision Analysis
            </button>
            <button
              onClick={() => router.push('/gaps')}
              className="w-full text-left px-3 py-2 rounded-md hover:bg-gray-100 text-sm text-gray-700"
            >
              🔍 Gap Analysis
            </button>
            <button
              onClick={() => router.push('/impact')}
              className="w-full text-left px-3 py-2 rounded-md hover:bg-gray-100 text-sm text-gray-700"
            >
              🎯 Impact Analysis
            </button>
            {user?.role === 'admin' && (
              <button
                onClick={() => router.push('/admin')}
                className="w-full text-left px-3 py-2 rounded-md hover:bg-gray-100 text-sm text-gray-700"
              >
                🛠️ Admin Panel
              </button>
            )}
          </div>
        </div>

        {/* Usage Info */}
        {organization && organization.plan !== 'enterprise' && (
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold text-gray-900 mb-2">📊 Usage</h3>
            <div className="mb-2">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Requests</span>
                <span>
                  {organization.used_quota}/{organization.monthly_quota}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-indigo-600 h-2 rounded-full"
                  style={{
                    width: `${Math.min((organization.used_quota / organization.monthly_quota) * 100, 100)}%`,
                  }}
                />
              </div>
            </div>
            {organization.used_quota / organization.monthly_quota > 0.8 && (
              <p className="text-xs text-orange-600 mt-2">
                ⚠️ Approaching quota limit
              </p>
            )}
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="border-t border-gray-200 p-4 space-y-2 bg-white">
        <button
          onClick={handleClearChat}
          className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          🗑️ Clear Chat
        </button>
        <button
          onClick={logout}
          className="w-full px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
        >
          🚪 Logout
        </button>
      </div>
    </div>
  )
}
