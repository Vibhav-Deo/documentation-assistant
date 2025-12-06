'use client'

import { useState } from 'react'
import { syncApi } from '@/lib/api/sync'

export default function ConfluenceSync() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    confluence_base_url: '',
    confluence_username: '',
    confluence_api_token: '',
    space_key_or_url: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await syncApi.syncConfluence(formData)
      setSuccess(`✅ Successfully synced ${result.pages} pages (${result.chunks} chunks)`)
      // Clear form
      setFormData({
        confluence_base_url: '',
        confluence_username: '',
        confluence_api_token: '',
        space_key_or_url: '',
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to sync Confluence documentation')
    } finally {
      setIsLoading(false)
    }
  }

  const canSync = Object.values(formData).every((value) => value.trim() !== '')

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Confluence Documentation Sync</h2>
        <p className="mt-1 text-sm text-gray-600">
          Sync your Confluence documentation to provide context for AI responses
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
          <label htmlFor="confluence_base_url" className="block text-sm font-medium text-gray-700">
            Confluence Base URL
          </label>
          <input
            type="url"
            id="confluence_base_url"
            value={formData.confluence_base_url}
            onChange={(e) => setFormData({ ...formData, confluence_base_url: e.target.value })}
            placeholder="https://your-domain.atlassian.net/wiki"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
            required
          />
        </div>

        <div>
          <label htmlFor="confluence_username" className="block text-sm font-medium text-gray-700">
            Email / Username
          </label>
          <input
            type="email"
            id="confluence_username"
            value={formData.confluence_username}
            onChange={(e) => setFormData({ ...formData, confluence_username: e.target.value })}
            placeholder="your-email@company.com"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
            required
          />
        </div>

        <div>
          <label htmlFor="confluence_api_token" className="block text-sm font-medium text-gray-700">
            API Token
          </label>
          <input
            type="password"
            id="confluence_api_token"
            value={formData.confluence_api_token}
            onChange={(e) => setFormData({ ...formData, confluence_api_token: e.target.value })}
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
          <label htmlFor="space_key_or_url" className="block text-sm font-medium text-gray-700">
            Space Key or URL
          </label>
          <input
            type="text"
            id="space_key_or_url"
            value={formData.space_key_or_url}
            onChange={(e) => setFormData({ ...formData, space_key_or_url: e.target.value })}
            placeholder="TEAM or https://your-domain.atlassian.net/wiki/spaces/TEAM"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter either the space key (e.g., "TEAM") or the full space URL
          </p>
        </div>

        <div className="pt-4">
          <button
            type="submit"
            disabled={!canSync || isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '🔄 Syncing...' : '🔄 Sync Confluence Documentation'}
          </button>
        </div>
      </form>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
        <h3 className="text-sm font-medium text-blue-900">💡 How it works</h3>
        <ul className="mt-2 text-sm text-blue-700 space-y-1">
          <li>• Your Confluence pages will be fetched and indexed</li>
          <li>• The AI will use this documentation to provide accurate answers</li>
          <li>• Credentials are only used for syncing and are not stored</li>
          <li>• You can re-sync anytime to update the documentation</li>
        </ul>
      </div>
    </div>
  )
}
