import { useChatStore } from '@/stores/chat'

export default function SourceFilters() {
  const {
    filterConfluence,
    filterJira,
    filterGit,
    filterCode,
    setSourceFilter,
  } = useChatStore()

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-4">
      <details>
        <summary className="cursor-pointer font-semibold text-gray-900 mb-3">
          🎯 Filter Sources
        </summary>
        <p className="text-sm text-gray-600 mb-3">
          Select which sources to include in answers
        </p>
        <div className="grid grid-cols-2 gap-3">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filterConfluence}
              onChange={(e) => setSourceFilter('confluence', e.target.checked)}
              className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-700">📄 Confluence</span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filterJira}
              onChange={(e) => setSourceFilter('jira', e.target.checked)}
              className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-700">🎫 Jira</span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filterGit}
              onChange={(e) => setSourceFilter('git', e.target.checked)}
              className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-700">💻 Git</span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filterCode}
              onChange={(e) => setSourceFilter('code', e.target.checked)}
              className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-700">📝 Code</span>
          </label>
        </div>
      </details>
    </div>
  )
}
