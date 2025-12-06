'use client'

import { useState, useEffect } from 'react'
import { syncApi } from '@/lib/api/sync'

export default function JiraSync() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showTickets, setShowTickets] = useState(false)
  const [tickets, setTickets] = useState<any[]>([])

  const [formData, setFormData] = useState({
    server: '',
    email: '',
    api_token: '',
    project_key: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await syncApi.syncJira(formData)
      setSuccess(
        `✅ Successfully synced ${result.tickets_synced} tickets from project ${result.project_key}`
      )
      // Clear sensitive data
      setFormData({
        server: formData.server,
        email: formData.email,
        api_token: '',
        project_key: formData.project_key,
      })
      // Refresh tickets list
      loadTickets()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to sync Jira tickets')
    } finally {
      setIsLoading(false)
    }
  }

  const loadTickets = async () => {
    try {
      const result = await syncApi.getJiraTickets(10)
      setTickets(result.tickets)
    } catch (err) {
      console.error('Failed to load tickets:', err)
    }
  }

  useEffect(() => {
    if (showTickets) {
      loadTickets()
    }
  }, [showTickets])

  const canSync = Object.values(formData).every((value) => value.trim() !== '')

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Jira Project Sync</h2>
        <p className="mt-1 text-sm text-gray-600">
          Sync Jira tickets to provide project context for AI responses
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="rounded-md bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {success && (
          <div className="rounded-md bg-green-50 p-4">
            <p className="text-sm text-green-800">{success}</p>
          </div>
        )}

        <div>
          <label htmlFor="server" className="block text-sm font-medium text-gray-700">
            Jira Server URL
          </label>
          <input
            type="url"
            id="server"
            value={formData.server}
            onChange={(e) => setFormData({ ...formData, server: e.target.value })}
            placeholder="https://your-domain.atlassian.net"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
            required
          />
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Email
          </label>
          <input
            type="email"
            id="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="your-email@company.com"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
            required
          />
        </div>

        <div>
          <label htmlFor="api_token" className="block text-sm font-medium text-gray-700">
            API Token
          </label>
          <input
            type="password"
            id="api_token"
            value={formData.api_token}
            onChange={(e) => setFormData({ ...formData, api_token: e.target.value })}
            placeholder="••••••••••••••••"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Generate an API token from your{' '}
            <a
              href="https://id.atlassian.com/manage-profile/security/api-tokens"
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 hover:text-indigo-500"
            >
              Atlassian Account Settings
            </a>
          </p>
        </div>

        <div>
          <label htmlFor="project_key" className="block text-sm font-medium text-gray-700">
            Project Key
          </label>
          <input
            type="text"
            id="project_key"
            value={formData.project_key}
            onChange={(e) => setFormData({ ...formData, project_key: e.target.value.toUpperCase() })}
            placeholder="PROJ"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter the project key (e.g., "PROJ" for tickets like PROJ-123)
          </p>
        </div>

        <div className="pt-4">
          <button
            type="submit"
            disabled={!canSync || isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '🔄 Syncing...' : '🔄 Sync Jira Project'}
          </button>
        </div>
      </form>

      <div className="mt-6">
        <button
          onClick={() => setShowTickets(!showTickets)}
          className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
        >
          {showTickets ? '▼ Hide Synced Tickets' : '▶ View Synced Tickets'}
        </button>

        {showTickets && (
          <div className="mt-4 bg-gray-50 rounded-md p-4">
            {tickets.length === 0 ? (
              <p className="text-sm text-gray-500">No tickets synced yet</p>
            ) : (
              <div className="space-y-3">
                {tickets.map((ticket) => (
                  <div
                    key={ticket.id}
                    className="bg-white p-3 rounded-md border border-gray-200"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">
                            {ticket.key}
                          </span>
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            {ticket.ticket_type}
                          </span>
                          <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                            {ticket.status}
                          </span>
                        </div>
                        <h4 className="mt-2 text-sm font-medium text-gray-900">{ticket.summary}</h4>
                        {ticket.assignee && (
                          <p className="mt-1 text-xs text-gray-500">Assignee: {ticket.assignee}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
        <h3 className="text-sm font-medium text-blue-900">💡 How it works</h3>
        <ul className="mt-2 text-sm text-blue-700 space-y-1">
          <li>• All tickets from the specified project will be synced</li>
          <li>• The AI can answer questions about tickets, status, and assignments</li>
          <li>• Credentials are only used for syncing and are not stored</li>
          <li>• Re-sync to get the latest ticket updates</li>
        </ul>
      </div>
    </div>
  )
}
