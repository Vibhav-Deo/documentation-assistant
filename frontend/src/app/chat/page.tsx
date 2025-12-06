'use client'

import ProtectedRoute from '@/components/auth/ProtectedRoute'
import Sidebar from '@/components/chat/Sidebar'
import ChatInterface from '@/components/chat/ChatInterface'

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          <ChatInterface />
        </div>
      </div>
    </ProtectedRoute>
  )
}
