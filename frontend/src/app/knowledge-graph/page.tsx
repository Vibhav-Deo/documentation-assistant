'use client'

import { useState } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { useRouter } from 'next/navigation'
import TicketRelationships from '@/components/knowledge-graph/TicketRelationships'
import DeveloperContributions from '@/components/knowledge-graph/DeveloperContributions'
import FileHistory from '@/components/knowledge-graph/FileHistory'
import RepositoryStats from '@/components/knowledge-graph/RepositoryStats'

type TabType = 'tickets' | 'developers' | 'files' | 'stats'

export default function KnowledgeGraphPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<TabType>('tickets')

  const tabs = [
    { id: 'tickets' as TabType, label: '🎫 Ticket Relationships', icon: '🎫' },
    { id: 'developers' as TabType, label: '👨‍💻 Developer Contributions', icon: '👨‍💻' },
    { id: 'files' as TabType, label: '📁 File History', icon: '📁' },
    { id: 'stats' as TabType, label: '📊 Repository Stats', icon: '📊' },
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
                  🔗 Knowledge Graph Explorer
                </h1>
                <p className="text-sm text-gray-600 mt-1">
                  Explore relationships between tickets, commits, code, and developers
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
          {activeTab === 'tickets' && <TicketRelationships />}
          {activeTab === 'developers' && <DeveloperContributions />}
          {activeTab === 'files' && <FileHistory />}
          {activeTab === 'stats' && <RepositoryStats />}
        </main>
      </div>
    </ProtectedRoute>
  )
}
