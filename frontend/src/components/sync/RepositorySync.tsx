'use client'

import { useState, useEffect } from 'react'
import { syncApi } from '@/lib/api/sync'

export default function RepositorySync() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showRepos, setShowRepos] = useState(false)
  const [repositories, setRepositories] = useState<any[]>([])

  const [formData, setFormData] = useState<{
    provider: 'github' | 'gitlab' | 'bitbucket'
    repo_url: string
    access_token: string
    branch: string
  }>({
    provider: 'github',
    repo_url: '',
    access_token: '',
    branch: 'main',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const result = await syncApi.syncRepository(formData)
      setSuccess(
        `✅ Successfully synced ${result.repo_name}\n` +
          `📄 ${result.files_synced} files • 💾 ${result.commits_synced} commits • 🔀 ${result.prs_synced} PRs`
      )
      // Clear token
      setFormData({
        ...formData,
        access_token: '',
      })
      // Refresh repos list
      loadRepositories()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to sync repository')
    } finally {
      setIsLoading(false)
    }
  }

  const loadRepositories = async () => {
    try {
      const result = await syncApi.getRepositories()
      setRepositories(result.repositories)
    } catch (err) {
      console.error('Failed to load repositories:', err)
    }
  }

  useEffect(() => {
    if (showRepos) {
      loadRepositories()
    }
  }, [showRepos])

  const canSync = formData.provider && formData.repo_url && formData.access_token

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Code Repository Sync</h2>
        <p className="mt-1 text-sm text-gray-600">
          Sync code repositories to provide codebase context for AI responses
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
            <p className="text-sm text-green-800 whitespace-pre-line">{success}</p>
          </div>
        )}

        <div>
          <label htmlFor="provider" className="block text-sm font-medium text-gray-700">
            Provider
          </label>
          <select
            id="provider"
            value={formData.provider}
            onChange={(e) => setFormData({ ...formData, provider: e.target.value as 'github' | 'gitlab' | 'bitbucket' })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
            required
          >
            <option value="github">GitHub</option>
            <option value="gitlab">GitLab</option>
            <option value="bitbucket">Bitbucket</option>
          </select>
        </div>

        <div>
          <label htmlFor="repo_url" className="block text-sm font-medium text-gray-700">
            Repository URL
          </label>
          <input
            type="url"
            id="repo_url"
            value={formData.repo_url}
            onChange={(e) => setFormData({ ...formData, repo_url: e.target.value })}
            placeholder="https://github.com/owner/repo"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter the full repository URL (e.g., https://github.com/owner/repo)
          </p>
        </div>

        <div>
          <label htmlFor="access_token" className="block text-sm font-medium text-gray-700">
            Personal Access Token
          </label>
          <input
            type="password"
            id="access_token"
            value={formData.access_token}
            onChange={(e) => setFormData({ ...formData, access_token: e.target.value })}
            placeholder="••••••••••••••••"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Generate a token from{' '}
            {formData.provider === 'github' && (
              <a
                href="https://github.com/settings/tokens"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:text-indigo-500"
              >
                GitHub Settings
              </a>
            )}
            {formData.provider === 'gitlab' && (
              <a
                href="https://gitlab.com/-/profile/personal_access_tokens"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:text-indigo-500"
              >
                GitLab Settings
              </a>
            )}
            {formData.provider === 'bitbucket' && (
              <a
                href="https://bitbucket.org/account/settings/app-passwords/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:text-indigo-500"
              >
                Bitbucket Settings
              </a>
            )}
          </p>
        </div>

        <div>
          <label htmlFor="branch" className="block text-sm font-medium text-gray-700">
            Branch (Optional)
          </label>
          <input
            type="text"
            id="branch"
            value={formData.branch}
            onChange={(e) => setFormData({ ...formData, branch: e.target.value })}
            placeholder="main"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
          />
          <p className="mt-1 text-xs text-gray-500">Defaults to "main" if not specified</p>
        </div>

        <div className="pt-4">
          <button
            type="submit"
            disabled={!canSync || isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? '🔄 Syncing... (this may take a few minutes)' : '🔄 Sync Repository'}
          </button>
        </div>
      </form>

      <div className="mt-6">
        <button
          onClick={() => setShowRepos(!showRepos)}
          className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
        >
          {showRepos ? '▼ Hide Synced Repositories' : '▶ View Synced Repositories'}
        </button>

        {showRepos && (
          <div className="mt-4 bg-gray-50 rounded-md p-4">
            {repositories.length === 0 ? (
              <p className="text-sm text-gray-500">No repositories synced yet</p>
            ) : (
              <div className="space-y-3">
                {repositories.map((repo) => (
                  <div key={repo.id} className="bg-white p-3 rounded-md border border-gray-200">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-medium text-gray-900">{repo.repo_name}</h4>
                          <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">
                            {repo.provider}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-gray-500">{repo.repo_url}</p>
                        {repo.last_synced && (
                          <p className="mt-1 text-xs text-gray-500">
                            Last synced: {new Date(repo.last_synced).toLocaleString()}
                          </p>
                        )}
                        <div className="mt-2 flex gap-3 text-xs text-gray-600">
                          <span>📄 {repo.file_count || 0} files</span>
                        </div>
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
          <li>• Code files, commits, and pull requests will be indexed</li>
          <li>• The AI can answer questions about your codebase structure and history</li>
          <li>• Supports Python, JavaScript, TypeScript, Java, Go, and more</li>
          <li>• Credentials are only used for syncing and are not stored</li>
          <li>• Re-sync to get the latest code changes</li>
        </ul>
      </div>
    </div>
  )
}
