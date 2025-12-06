import type { ChatMessage } from '@/types'
import { formatDateTime } from '@/lib/utils'

interface ChatMessageProps {
  message: ChatMessage
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-3xl ${isUser ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-900'} rounded-lg px-4 py-3 shadow-md`}>
        <div className="prose prose-sm max-w-none">
          <div className={`whitespace-pre-wrap ${isUser ? 'text-white' : 'text-gray-900'}`}>
            {message.content}
          </div>
        </div>

        {/* Source Badges */}
        {!isUser && message.source_metadata && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.source_metadata.confluence_count > 0 && (
              <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
                📄 Confluence: {message.source_metadata.confluence_count}
              </span>
            )}
            {message.source_metadata.jira_count > 0 && (
              <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-green-100 text-green-800">
                🎫 Jira: {message.source_metadata.jira_count}
              </span>
            )}
            {message.source_metadata.git_count > 0 && (
              <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-purple-100 text-purple-800">
                💻 Git: {message.source_metadata.git_count}
              </span>
            )}
            {message.source_metadata.code_count > 0 && (
              <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-orange-100 text-orange-800">
                📝 Code: {message.source_metadata.code_count}
              </span>
            )}
          </div>
        )}

        {/* Detailed Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <details className="mt-3">
            <summary className="cursor-pointer text-xs text-gray-600 hover:text-gray-800">
              📚 View {message.sources.length} sources
            </summary>
            <div className="mt-2 space-y-1">
              {message.sources.map((source, idx) => (
                <div key={idx} className="text-xs text-gray-700 pl-2">
                  • {source}
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </div>
  )
}
