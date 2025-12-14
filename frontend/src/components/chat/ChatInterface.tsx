'use client'

import { useEffect, useRef, useState } from 'react'
import { useChatStore } from '@/stores/chat'
import { chatApi } from '@/lib/api/chat'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import type { ChatMessage as ChatMessageType } from '@/types'

export default function ChatInterface() {
  const {
    messages,
    sessionId,
    isLoading,
    model,
    maxResults,
    searchType,
    filterConfluence,
    filterJira,
    filterGit,
    filterCode,
    addMessage,
    setSessionId,
    setLoading,
  } = useChatStore()

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [streamingEnabled, setStreamingEnabled] = useState(false)
  const [streamingState, setStreamingState] = useState<{
    isStreaming: boolean
    content: string
    metadata: any
    sources: any[]
    progress: {
      processingTime: number
      chunksReceived: number
      sourcesFound: number
      estimatedDuration: number
      progressPercentage: number
    }
    error: string | null
    retryCount: number
  }>({
    isStreaming: false,
    content: '',
    metadata: null,
    sources: [],
    progress: {
      processingTime: 0,
      chunksReceived: 0,
      sourcesFound: 0,
      estimatedDuration: 0,
      progressPercentage: 0
    },
    error: null,
    retryCount: 0
  })

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const extractSourceMetadata = (answer: string) => {
    return {
      confluence_count: (answer.match(/\[DOC-\d+\]/g) || []).length,
      jira_count: (answer.match(/\[TICKET-\d+\]/g) || []).length,
      git_count: (answer.match(/\[COMMIT-\d+\]/g) || []).length,
      code_count: (answer.match(/\[CODE-\d+\]/g) || []).length,
    }
  }

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage: ChatMessageType = {
      role: 'user',
      content,
    }
    addMessage(userMessage)

    setLoading(true)

    try {
      if (streamingEnabled) {
        // Reset streaming state
        const startTime = Date.now()
        const estimatedDuration = chatApi.estimateStreamingDuration({
          question: content,
          session_id: sessionId,
          model,
          max_results: maxResults,
          search_type: searchType,
          stream: true
        })

        setStreamingState({
          isStreaming: true,
          content: '',
          metadata: null,
          sources: [],
          progress: {
            processingTime: 0,
            chunksReceived: 0,
            sourcesFound: 0,
            estimatedDuration,
            progressPercentage: 0
          },
          error: null,
          retryCount: 0
        })

        let fullContent = ''
        let sources: any[] = []
        let metadata: any = null
        let chunksReceived = 0

        await chatApi.createStreamingRequest(
          {
            question: content,
            session_id: sessionId,
            model,
            max_results: maxResults,
            search_type: searchType,
            stream: true
          },
          // onMetadata
          (searchMetadata) => {
            metadata = searchMetadata
            const processingTime = (Date.now() - startTime) / 1000
            const progressPercentage = Math.min(95, (processingTime / estimatedDuration) * 100)
            
            setStreamingState(prev => ({
              ...prev,
              metadata: searchMetadata,
              progress: {
                ...prev.progress,
                processingTime,
                sourcesFound: searchMetadata.total_results || 0,
                progressPercentage
              }
            }))
            console.log('Search metadata:', searchMetadata)
          },
          // onSources
          (searchSources) => {
            sources = searchSources
            const processingTime = (Date.now() - startTime) / 1000
            const progressPercentage = Math.min(95, (processingTime / estimatedDuration) * 100)
            
            setStreamingState(prev => ({
              ...prev,
              sources: searchSources,
              progress: {
                ...prev.progress,
                processingTime,
                progressPercentage
              }
            }))
            console.log('Search sources:', searchSources)
          },
          // onMessage (content chunks)
          (chunk) => {
            fullContent += chunk
            chunksReceived++
            const processingTime = (Date.now() - startTime) / 1000
            const progressPercentage = Math.min(95, (processingTime / estimatedDuration) * 100)
            
            setStreamingState(prev => ({
              ...prev,
              content: fullContent,
              progress: {
                ...prev.progress,
                processingTime,
                chunksReceived,
                progressPercentage
              }
            }))
          },
          // onComplete
          (completionMetadata) => {
            console.log('Streaming complete:', completionMetadata)
            
            // Extract source metadata
            const sourceMetadata = extractSourceMetadata(fullContent)

            // Add final message with sources
            const assistantMessage: ChatMessageType = {
              role: 'assistant',
              content: fullContent,
              sources: sources,
              source_metadata: sourceMetadata,
            }
            addMessage(assistantMessage)
            
            // Reset streaming state
            setStreamingState({
              isStreaming: false,
              content: '',
              metadata: null,
              sources: [],
              progress: {
                processingTime: (Date.now() - startTime) / 1000,
                chunksReceived,
                sourcesFound: sources.length,
                estimatedDuration: 0,
                progressPercentage: 100
              },
              error: null,
              retryCount: 0
            })
          },
          // onError
          (error) => {
            console.error('Streaming error:', error)
            
            setStreamingState(prev => ({
              ...prev,
              isStreaming: false,
              error: error.message || 'Failed to get streaming response',
              progress: {
                ...prev.progress,
                processingTime: (Date.now() - startTime) / 1000,
                progressPercentage: 0
              }
            }))
          },
          // Enhanced options with retry handling
          {
            maxRetries: 3,
            retryDelay: 2000,
            timeout: 120000,
            onRetry: (retryCount, error) => {
              console.log(`Retry attempt ${retryCount}:`, error.message)
              setStreamingState(prev => ({
                ...prev,
                retryCount,
                error: `Retrying... (${retryCount}/3): ${error.message}`
              }))
            }
          }
        )
      } else {
        // Use regular API
        const response = await chatApi.ask({
          question: content,
          session_id: sessionId,
          model,
          max_results: maxResults,
          search_type: searchType,
          include_confluence: filterConfluence,
          include_jira: filterJira,
          include_git: filterGit,
          include_code: filterCode,
        })

        // Extract source metadata
        const sourceMetadata = extractSourceMetadata(response.answer)

        // Add assistant message
        const assistantMessage: ChatMessageType = {
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
          source_metadata: sourceMetadata,
        }
        addMessage(assistantMessage)

        // Update session ID if provided
        if (response.session_id) {
          setSessionId(response.session_id)
        }
      }
    } catch (error: any) {
      console.error('Error sending message:', error)

      // Add error message
      const errorMessage: ChatMessageType = {
        role: 'assistant',
        content: `❌ Error: ${error.response?.data?.detail || error.message || 'Failed to get response'}`,
      }
      addMessage(errorMessage)
      
      // Reset streaming state on error
      setStreamingState({
        isStreaming: false,
        content: '',
        metadata: null,
        sources: [],
        progress: {
          processingTime: 0,
          chunksReceived: 0,
          sourcesFound: 0,
          estimatedDuration: 0,
          progressPercentage: 0
        },
        error: error.response?.data?.detail || error.message || 'Failed to get response',
        retryCount: 0
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">🤖 AI Assistant</h2>
            <p className="text-sm text-gray-600">
              Ask general questions or sync documentation for specific answers
            </p>
          </div>
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <span className="text-sm text-gray-600">Streaming</span>
              <input
                type="checkbox"
                checked={streamingEnabled}
                onChange={(e) => setStreamingEnabled(e.target.checked)}
                className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
              />
            </label>
            {streamingEnabled && (
              <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded">
                ⚡ Real-time
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto bg-gray-50 px-6 py-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <div className="text-6xl mb-4">💬</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Start a Conversation
              </h3>
              <p className="text-gray-600">
                Ask questions about your documentation, code, tickets, and more.
              </p>
              <div className="mt-6 text-left bg-blue-50 rounded-lg p-4">
                <p className="text-sm font-semibold text-gray-900 mb-2">
                  💡 Example questions:
                </p>
                <ul className="text-sm text-gray-700 space-y-1">
                  <li>• What is this project about?</li>
                  <li>• Show me recent commits</li>
                  <li>• What are the open tickets?</li>
                  <li>• Explain the authentication flow</li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <ChatMessage key={index} message={message} />
            ))}
            {/* Enhanced Streaming Progress Indicator */}
            {streamingState.isStreaming && (
              <div className="flex justify-start mb-4">
                <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 max-w-3xl w-full">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span className="text-sm font-medium text-blue-800">Processing your request...</span>
                    </div>
                    <span className="text-xs text-blue-600">
                      {streamingState.progress.progressPercentage.toFixed(0)}%
                    </span>
                  </div>
                  
                  {/* Progress Bar */}
                  <div className="w-full bg-blue-200 rounded-full h-2 mb-3">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
                      style={{ width: `${streamingState.progress.progressPercentage}%` }}
                    ></div>
                  </div>
                  
                  {streamingState.metadata && (
                    <div className="text-xs text-blue-600 grid grid-cols-2 gap-2">
                      <div>⏱️ Time: {streamingState.progress.processingTime.toFixed(1)}s</div>
                      <div>📊 Sources: {streamingState.progress.sourcesFound}</div>
                      <div>📝 Chunks: {streamingState.progress.chunksReceived}</div>
                      <div>🎯 ETA: {Math.max(0, streamingState.progress.estimatedDuration - streamingState.progress.processingTime).toFixed(1)}s</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Enhanced Streaming Sources Display */}
            {streamingState.sources.length > 0 && streamingState.isStreaming && (
              <div className="flex justify-start mb-4">
                <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-3 max-w-3xl">
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm font-medium text-green-800">
                      📚 Found {streamingState.sources.length} relevant sources
                    </div>
                    <div className="text-xs text-green-600">
                      {streamingState.sources.filter(s => s.score > 0.8).length} high relevance
                    </div>
                  </div>
                  <div className="space-y-2">
                    {streamingState.sources.slice(0, 4).map((source, index) => (
                      <div key={index} className="flex items-center justify-between text-xs">
                        <div className="text-green-700">
                          <span className="font-medium capitalize">{source.type.replace('_', ' ')}:</span> 
                          <span className="ml-1">{source.title.length > 40 ? source.title.substring(0, 40) + '...' : source.title}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <div className={`w-2 h-2 rounded-full ${
                            source.score > 0.8 ? 'bg-green-500' : 
                            source.score > 0.6 ? 'bg-yellow-500' : 'bg-gray-400'
                          }`}></div>
                          <span className="text-green-600">{(source.score * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    ))}
                    {streamingState.sources.length > 4 && (
                      <div className="text-xs text-green-600 text-center pt-1 border-t border-green-200">
                        + {streamingState.sources.length - 4} more sources
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Enhanced Streaming Content */}
            {streamingState.content && (
              <div className="flex justify-start mb-4">
                <div className="bg-white rounded-lg px-4 py-3 shadow-md max-w-3xl">
                  <div className="prose prose-sm">
                    {streamingState.content}
                    <span className="inline-block w-2 h-4 bg-indigo-600 animate-pulse ml-1"></span>
                  </div>
                  
                  {/* Enhanced Streaming Stats */}
                  {streamingState.progress.chunksReceived > 0 && (
                    <div className="mt-3 pt-2 border-t border-gray-100">
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <div className="flex items-center space-x-3">
                          <span>📊 {streamingState.progress.chunksReceived} chunks</span>
                          <span>⏱️ {streamingState.progress.processingTime.toFixed(1)}s</span>
                          <span>🔍 {streamingState.progress.sourcesFound} sources</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span>{(streamingState.content.length / streamingState.progress.processingTime).toFixed(0)} chars/s</span>
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Streaming Error Display with Retry */}
            {streamingState.error && (
              <div className="flex justify-start mb-4">
                <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 max-w-3xl">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="text-red-600">❌</div>
                    <span className="text-sm font-medium text-red-800">Streaming Error</span>
                  </div>
                  <p className="text-sm text-red-700 mb-3">{streamingState.error}</p>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleSendMessage(messages[messages.length - 2]?.content || '')}
                      className="text-xs bg-red-100 hover:bg-red-200 text-red-700 px-2 py-1 rounded transition-colors"
                    >
                      🔄 Retry
                    </button>
                    <button
                      onClick={() => {
                        setStreamingEnabled(false)
                        handleSendMessage(messages[messages.length - 2]?.content || '')
                      }}
                      className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded transition-colors"
                    >
                      📝 Try without streaming
                    </button>
                  </div>
                  {streamingState.retryCount > 0 && (
                    <div className="text-xs text-red-600 mt-2">
                      Retry attempt: {streamingState.retryCount}
                    </div>
                  )}
                </div>
              </div>
            )}

            {isLoading && !streamingState.content && (
              <div className="flex justify-start mb-4">
                <div className="bg-gray-100 rounded-lg px-4 py-3 shadow-md">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                    <span className="text-sm text-gray-600">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Chat Input */}
      <ChatInput onSend={handleSendMessage} disabled={isLoading} />
    </div>
  )
}
