'use client'

import { useState, useEffect } from 'react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import HeroMetrics from '@/components/demo/HeroMetrics'
import InteractiveExamples from '@/components/demo/InteractiveExamples'
import PerformanceCharts from '@/components/demo/PerformanceCharts'
import AIShowcase from '@/components/demo/AIShowcase'

export default function DemoPage() {
  return (
    <ProtectedRoute>
      <DemoContent />
    </ProtectedRoute>
  )
}

function DemoContent() {
  const [activeSection, setActiveSection] = useState('overview')

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                🚀 Enterprise RAG Platform Demo
              </h1>
              <p className="mt-2 text-lg text-gray-600">
                AI-powered development intelligence with predictive analytics
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                ✅ Demo Ready
              </div>
              <div className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                v1.0.0
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {[
              { id: 'overview', label: '📊 Overview', desc: 'Key metrics' },
              { id: 'examples', label: '🎮 Interactive', desc: 'Live demos' },
              { id: 'performance', label: '📈 Analytics', desc: 'Performance' },
              { id: 'ai', label: '🤖 AI Showcase', desc: 'AI capabilities' },
            ].map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeSection === section.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div>{section.label}</div>
                <div className="text-xs text-gray-400">{section.desc}</div>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeSection === 'overview' && <HeroMetrics />}
        {activeSection === 'examples' && <InteractiveExamples />}
        {activeSection === 'performance' && <PerformanceCharts />}
        {activeSection === 'ai' && <AIShowcase />}
      </div>

      {/* Footer */}
      <div className="bg-gray-50 border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Ready to Transform Your Development Workflow?
            </h3>
            <p className="text-gray-600 mb-6">
              Join leading teams using AI-powered development intelligence
            </p>
            <div className="flex justify-center gap-4">
              <button className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium">
                Start Free Trial
              </button>
              <button className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium">
                Schedule Demo
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}