'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import ConfluenceSync from '@/components/sync/ConfluenceSync'
import JiraSync from '@/components/sync/JiraSync'
import RepositorySync from '@/components/sync/RepositorySync'

export default function SyncPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'confluence' | 'jira' | 'repository'>('confluence')

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Data Synchronization</h1>
              <p className="mt-2 text-gray-600">
                Sync your documentation, tickets, and code repositories to enhance AI responses
              </p>
            </div>
            <button
              onClick={() => router.push('/chat')}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              ← Back to Chat
            </button>
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-lg shadow">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex" aria-label="Tabs">
                <button
                  onClick={() => setActiveTab('confluence')}
                  className={`${
                    activeTab === 'confluence'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } w-1/3 py-4 px-1 text-center border-b-2 font-medium text-sm`}
                >
                  📄 Confluence
                </button>
                <button
                  onClick={() => setActiveTab('jira')}
                  className={`${
                    activeTab === 'jira'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } w-1/3 py-4 px-1 text-center border-b-2 font-medium text-sm`}
                >
                  🎫 Jira
                </button>
                <button
                  onClick={() => setActiveTab('repository')}
                  className={`${
                    activeTab === 'repository'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } w-1/3 py-4 px-1 text-center border-b-2 font-medium text-sm`}
                >
                  📁 Repository
                </button>
              </nav>
            </div>

            <div className="p-6">
              {activeTab === 'confluence' && <ConfluenceSync />}
              {activeTab === 'jira' && <JiraSync />}
              {activeTab === 'repository' && <RepositorySync />}
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}
