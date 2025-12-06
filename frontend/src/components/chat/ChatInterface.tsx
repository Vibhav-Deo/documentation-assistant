'use client'

import { useEffect, useRef } from 'react'
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

      // Update session ID
      if (response.session_id) {
        setSessionId(response.session_id)
      }
    } catch (error: any) {
      console.error('Error sending message:', error)

      // Add error message
      const errorMessage: ChatMessageType = {
        role: 'assistant',
        content: `❌ Error: ${error.response?.data?.detail || error.message || 'Failed to get response'}`,
      }
      addMessage(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h2 className="text-xl font-bold text-gray-900">🤖 AI Assistant</h2>
        <p className="text-sm text-gray-600">
          Ask general questions or sync documentation for specific answers
        </p>
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
            {isLoading && (
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
