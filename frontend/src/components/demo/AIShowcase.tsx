'use client'

import { useState } from 'react'

export default function AIShowcase() {
  const [activeComparison, setActiveComparison] = useState('search')
  const [isRunning, setIsRunning] = useState(false)
  const [results, setResults] = useState<any>(null)

  const handleComparisonChange = (key: string) => {
    setActiveComparison(key)
    setResults(null)
    setIsRunning(false)
  }

  const comparisons = {
    search: {
      title: '🔍 Semantic vs Keyword Search',
      description: 'See how semantic understanding improves search relevance',
      query: 'authentication issues',
      keywordResults: [
        { title: 'AUTH-123: Fix login bug', relevance: 0.6, type: 'ticket' },
        { title: 'Authentication.java', relevance: 0.4, type: 'code' },
        { title: 'User auth documentation', relevance: 0.3, type: 'doc' }
      ],
      semanticResults: [
        { title: 'PROJ-456: OAuth 2.0 implementation', relevance: 0.95, type: 'ticket' },
        { title: 'Security Architecture Decision', relevance: 0.92, type: 'doc' },
        { title: 'JWT token validation fix', relevance: 0.88, type: 'commit' },
        { title: 'Authentication middleware', relevance: 0.85, type: 'code' }
      ]
    },
    models: {
      title: '🤖 Multi-Model AI Comparison',
      description: 'Compare responses from different AI models with automatic fallback',
      query: 'Explain the OAuth flow in our system',
      models: [
        {
          name: 'Mistral 7B',
          status: 'success',
          response: 'OAuth flow: 1) User clicks login 2) Redirect to provider 3) User authenticates 4) Authorization code returned 5) Exchange for access token 6) Access protected resources',
          responseTime: '1.2s',
          confidence: 0.94
        },
        {
          name: 'Llama2 13B',
          status: 'fallback',
          response: 'The OAuth 2.0 flow in your system follows the authorization code grant type. When a user initiates login, they are redirected to the OAuth provider...',
          responseTime: '2.1s',
          confidence: 0.91
        },
        {
          name: 'CodeLlama',
          status: 'available',
          response: 'Based on the code analysis, your OAuth implementation uses PKCE for security enhancement...',
          responseTime: '1.8s',
          confidence: 0.89
        }
      ]
    },
    streaming: {
      title: '⚡ Real-time Streaming',
      description: 'Experience real-time AI responses with token-by-token streaming',
      query: 'What are the benefits of microservices?',
      streamingText: 'Microservices architecture offers several key benefits: 1) **Scalability** - Each service can be scaled independently based on demand. 2) **Technology Diversity** - Teams can choose the best technology stack for each service. 3) **Fault Isolation** - Failures in one service don\'t bring down the entire system. 4) **Faster Development** - Teams can work independently on different services. 5) **Easier Maintenance** - Smaller codebases are easier to understand and modify.'
    }
  }

  const runComparison = async () => {
    setIsRunning(true)
    setResults(null)

    if (activeComparison === 'streaming') {
      // Simulate streaming
      const text = comparisons.streaming.streamingText
      let currentText = ''
      
      for (let i = 0; i <= text.length; i += 3) {
        currentText = text.slice(0, i)
        setResults({ streamingText: currentText })
        await new Promise(resolve => setTimeout(resolve, 50))
      }
    } else {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      setResults(comparisons[activeComparison as keyof typeof comparisons])
    }

    setIsRunning(false)
  }

  const currentComparison = comparisons[activeComparison as keyof typeof comparisons]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">
          AI Capabilities Showcase
        </h2>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Experience the power of our AI engine with semantic understanding, 
          multi-model support, and real-time streaming.
        </p>
      </div>

      {/* Comparison Selector */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(comparisons).map(([key, comparison]) => (
          <button
            key={key}
            onClick={() => handleComparisonChange(key)}
            className={`p-4 rounded-lg border-2 text-left transition-all ${
              activeComparison === key
                ? 'border-indigo-500 bg-indigo-50'
                : 'border-gray-200 hover:border-gray-300 bg-white'
            }`}
          >
            <div className="font-semibold text-gray-900 mb-2">{comparison.title}</div>
            <div className="text-sm text-gray-600">{comparison.description}</div>
          </button>
        ))}
      </div>

      {/* AI Showcase */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">{currentComparison.title}</h3>
          <p className="text-sm text-gray-600 mt-1">{currentComparison.description}</p>
        </div>

        <div className="p-6">
          {/* Query Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Query
            </label>
            <div className="flex gap-3">
              <input
                type="text"
                value={currentComparison.query}
                readOnly
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-700"
              />
              <button
                onClick={runComparison}
                disabled={isRunning}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {isRunning ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Running...
                  </div>
                ) : (
                  'Run Comparison'
                )}
              </button>
            </div>
          </div>

          {/* Results */}
          {activeComparison === 'search' && results && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Keyword Search Results */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">🔤 Keyword Search</h4>
                <div className="space-y-3">
                  {results.keywordResults.map((result: any, index: number) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-3">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{result.title}</div>
                          <div className="text-xs text-gray-500 mt-1">{result.type}</div>
                        </div>
                        <div className={`px-2 py-1 rounded text-xs ${
                          result.relevance > 0.5 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {(result.relevance * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 text-sm text-gray-600">
                  Average relevance: {((results.keywordResults.reduce((sum: number, r: any) => sum + r.relevance, 0) / results.keywordResults.length) * 100).toFixed(0)}%
                </div>
              </div>

              {/* Semantic Search Results */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-3">🧠 Semantic Search</h4>
                <div className="space-y-3">
                  {results.semanticResults.map((result: any, index: number) => (
                    <div key={index} className="border border-green-200 rounded-lg p-3 bg-green-50">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{result.title}</div>
                          <div className="text-xs text-gray-500 mt-1">{result.type}</div>
                        </div>
                        <div className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                          {(result.relevance * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 text-sm text-green-700 font-medium">
                  Average relevance: {((results.semanticResults.reduce((sum: number, r: any) => sum + r.relevance, 0) / results.semanticResults.length) * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          )}

          {activeComparison === 'models' && results && (
            <div className="space-y-4">
              {results.models.map((model: any, index: number) => (
                <div key={index} className={`border rounded-lg p-4 ${
                  model.status === 'success' ? 'border-green-200 bg-green-50' :
                  model.status === 'fallback' ? 'border-yellow-200 bg-yellow-50' :
                  'border-gray-200'
                }`}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <h4 className="font-semibold text-gray-900">{model.name}</h4>
                      <span className={`px-2 py-1 rounded text-xs ${
                        model.status === 'success' ? 'bg-green-100 text-green-800' :
                        model.status === 'fallback' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {model.status}
                      </span>
                    </div>
                    <div className="flex gap-4 text-sm text-gray-600">
                      <span>⏱️ {model.responseTime}</span>
                      <span>🎯 {(model.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="text-gray-700">{model.response}</div>
                </div>
              ))}
            </div>
          )}

          {activeComparison === 'streaming' && results && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-gray-700">Streaming Response</span>
              </div>
              <div className="prose prose-sm max-w-none">
                <div dangerouslySetInnerHTML={{ __html: results.streamingText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                {isRunning && <span className="inline-block w-2 h-4 bg-indigo-600 animate-pulse ml-1"></span>}
              </div>
            </div>
          )}

          {isRunning && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                <span className="text-blue-800">
                  {activeComparison === 'search' && 'Running semantic analysis and comparing with keyword search...'}
                  {activeComparison === 'models' && 'Querying multiple AI models and comparing responses...'}
                  {activeComparison === 'streaming' && 'Generating streaming response...'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* AI Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
            <span className="text-2xl">🧠</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Semantic Understanding</h3>
          <p className="text-gray-600 text-sm">
            Advanced NLP models understand context and meaning, not just keywords. 
            Delivers 40% more relevant results than traditional search.
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
            <span className="text-2xl">🔄</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Multi-Model Fallback</h3>
          <p className="text-gray-600 text-sm">
            Automatic failover between Mistral, Llama2, and CodeLlama ensures 
            99.9% availability and optimal responses for different query types.
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
          <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mb-4">
            <span className="text-2xl">⚡</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Real-time Streaming</h3>
          <p className="text-gray-600 text-sm">
            Server-Sent Events deliver responses token-by-token for immediate 
            feedback. Reduces perceived latency by 60%.
          </p>
        </div>
      </div>
    </div>
  )
}