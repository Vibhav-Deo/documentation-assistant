'use client'

import { useState } from 'react'

export default function InteractiveExamples() {
  const [activeExample, setActiveExample] = useState('decision')
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleExampleChange = (key: string) => {
    setActiveExample(key)
    setResult(null)
    setIsRunning(false)
  }

  const examples = {
    decision: {
      title: '🧠 Decision Extraction',
      description: 'Extract "why" behind decisions from tickets and documentation',
      input: 'PROJ-123: Implement OAuth 2.0 authentication',
      action: 'Extract Decision',
      mockResult: {
        decision: 'Use OAuth 2.0 for authentication',
        reasoning: 'OAuth 2.0 provides better security and user experience compared to basic auth',
        confidence: 0.92,
        sources: ['PROJ-123 description', 'Architecture doc section 4.2'],
        alternatives: ['Basic Auth', 'JWT only', 'SAML'],
        factors: ['Security requirements', 'User experience', 'Industry standards']
      }
    },
    gap: {
      title: '🔍 Gap Detection',
      description: 'Find orphaned tickets, undocumented features, and missing work',
      input: 'Analyze repository for gaps',
      action: 'Detect Gaps',
      mockResult: {
        orphaned_tickets: 12,
        undocumented_features: 8,
        missing_decisions: 5,
        stale_work: 15,
        details: [
          { type: 'orphaned', item: 'AUTH-456: Add 2FA support', days: 45 },
          { type: 'undocumented', item: 'commit abc123: New payment flow', files: 3 },
          { type: 'stale', item: 'UI-789: Redesign dashboard', days: 67 }
        ]
      }
    },
    impact: {
      title: '🎯 Impact Analysis',
      description: 'Predict the impact of changes before they happen',
      input: 'src/auth/oauth.ts',
      action: 'Analyze Impact',
      mockResult: {
        blast_radius: 'Medium',
        affected_files: 23,
        affected_tickets: 8,
        risk_score: 65,
        top_developers: ['alice@company.com', 'bob@company.com'],
        estimated_effort: '2-3 days',
        recommendations: [
          'Review with security team',
          'Add comprehensive tests',
          'Update documentation'
        ]
      }
    },
    prediction: {
      title: '🔮 Predictive Analytics',
      description: 'ML-powered predictions for tickets, hotspots, and bottlenecks',
      input: 'PROJ-456: Refactor user service',
      action: 'Generate Predictions',
      mockResult: {
        completion_date: '2024-01-15',
        confidence: 0.78,
        risk_level: 'Medium',
        hotspots: [
          { file: 'user/service.py', risk: 'High', changes: 23 },
          { file: 'auth/middleware.py', risk: 'Medium', changes: 12 }
        ],
        bottlenecks: [
          { developer: 'alice@company.com', severity: 'High', workload: 15 }
        ]
      }
    }
  }

  const runExample = async () => {
    setIsRunning(true)
    setResult(null)
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    setResult(examples[activeExample as keyof typeof examples].mockResult)
    setIsRunning(false)
  }

  const currentExample = examples[activeExample as keyof typeof examples]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">
          Interactive Examples
        </h2>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Try our AI-powered features live. See how we extract insights, detect gaps, 
          analyze impact, and predict outcomes.
        </p>
      </div>

      {/* Example Selector */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.entries(examples).map(([key, example]) => (
          <button
            key={key}
            onClick={() => handleExampleChange(key)}
            className={`p-4 rounded-lg border-2 text-left transition-all ${
              activeExample === key
                ? 'border-indigo-500 bg-indigo-50'
                : 'border-gray-200 hover:border-gray-300 bg-white'
            }`}
          >
            <div className="font-semibold text-gray-900 mb-2">{example.title}</div>
            <div className="text-sm text-gray-600">{example.description}</div>
          </button>
        ))}
      </div>

      {/* Interactive Demo */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">{currentExample.title}</h3>
          <p className="text-sm text-gray-600 mt-1">{currentExample.description}</p>
        </div>

        <div className="p-6">
          {/* Input Section */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Input
            </label>
            <div className="flex gap-3">
              <input
                type="text"
                value={currentExample.input}
                readOnly
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-700"
              />
              <button
                onClick={runExample}
                disabled={isRunning}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {isRunning ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Processing...
                  </div>
                ) : (
                  currentExample.action
                )}
              </button>
            </div>
          </div>

          {/* Results Section */}
          {isRunning && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                <span className="text-blue-800">
                  {activeExample === 'decision' && 'Analyzing ticket content and extracting decisions...'}
                  {activeExample === 'gap' && 'Scanning repository for gaps and inconsistencies...'}
                  {activeExample === 'impact' && 'Calculating blast radius and affected components...'}
                  {activeExample === 'prediction' && 'Running ML models for predictions...'}
                </span>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-900">Results:</h4>
              
              {activeExample === 'decision' && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="space-y-3">
                    <div>
                      <span className="font-medium text-green-900">Decision:</span>
                      <span className="ml-2 text-green-800">{result.decision}</span>
                    </div>
                    <div>
                      <span className="font-medium text-green-900">Reasoning:</span>
                      <span className="ml-2 text-green-800">{result.reasoning}</span>
                    </div>
                    <div>
                      <span className="font-medium text-green-900">Confidence:</span>
                      <span className="ml-2 text-green-800">{(result.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div>
                      <span className="font-medium text-green-900">Sources:</span>
                      <span className="ml-2 text-green-800">{result.sources.join(', ')}</span>
                    </div>
                  </div>
                </div>
              )}

              {activeExample === 'gap' && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-red-600">{result.orphaned_tickets}</div>
                    <div className="text-sm text-red-800">Orphaned Tickets</div>
                  </div>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-yellow-600">{result.undocumented_features}</div>
                    <div className="text-sm text-yellow-800">Undocumented</div>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-blue-600">{result.missing_decisions}</div>
                    <div className="text-sm text-blue-800">Missing Decisions</div>
                  </div>
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-purple-600">{result.stale_work}</div>
                    <div className="text-sm text-purple-800">Stale Work</div>
                  </div>
                </div>
              )}

              {activeExample === 'impact' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-center">
                      <div className="text-lg font-bold text-yellow-600">{result.blast_radius}</div>
                      <div className="text-sm text-yellow-800">Blast Radius</div>
                    </div>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
                      <div className="text-lg font-bold text-blue-600">{result.affected_files}</div>
                      <div className="text-sm text-blue-800">Affected Files</div>
                    </div>
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
                      <div className="text-lg font-bold text-red-600">{result.risk_score}/100</div>
                      <div className="text-sm text-red-800">Risk Score</div>
                    </div>
                  </div>
                  <div>
                    <span className="font-medium text-gray-900">Recommendations:</span>
                    <ul className="mt-2 space-y-1">
                      {result.recommendations.map((rec: string, i: number) => (
                        <li key={i} className="text-sm text-gray-700">• {rec}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {activeExample === 'prediction' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
                      <div className="text-lg font-bold text-green-600">{result.completion_date}</div>
                      <div className="text-sm text-green-800">Predicted Completion</div>
                    </div>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
                      <div className="text-lg font-bold text-blue-600">{(result.confidence * 100).toFixed(0)}%</div>
                      <div className="text-sm text-blue-800">Confidence</div>
                    </div>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-center">
                      <div className="text-lg font-bold text-yellow-600">{result.risk_level}</div>
                      <div className="text-sm text-yellow-800">Risk Level</div>
                    </div>
                  </div>
                  <div>
                    <span className="font-medium text-gray-900">Code Hotspots:</span>
                    <div className="mt-2 space-y-2">
                      {result.hotspots.map((hotspot: any, i: number) => (
                        <div key={i} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <span className="font-mono text-sm">{hotspot.file}</span>
                          <span className={`px-2 py-1 rounded text-xs ${
                            hotspot.risk === 'High' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {hotspot.risk} Risk
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}