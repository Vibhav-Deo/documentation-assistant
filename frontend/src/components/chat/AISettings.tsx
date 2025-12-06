import { useChatStore } from '@/stores/chat'

const MODEL_OPTIONS = ['mistral', 'llama2', 'codellama', 'neural-chat']
const SEARCH_TYPES = ['semantic', 'hybrid', 'keyword'] as const

export default function AISettings() {
  const { model, maxResults, searchType, setModel, setMaxResults, setSearchType } =
    useChatStore()

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-4">
      <h3 className="font-semibold text-gray-900 mb-4">🤖 AI Settings</h3>

      <div className="space-y-4">
        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Model
          </label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            {MODEL_OPTIONS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        {/* Max Results */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Max Results: {maxResults}
          </label>
          <input
            type="range"
            min="1"
            max="10"
            value={maxResults}
            onChange={(e) => setMaxResults(Number(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>1</span>
            <span>10</span>
          </div>
        </div>

        {/* Search Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Search Type
          </label>
          <div className="space-y-2">
            {SEARCH_TYPES.map((type) => (
              <label key={type} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  value={type}
                  checked={searchType === type}
                  onChange={(e) => setSearchType(e.target.value as typeof type)}
                  className="w-4 h-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-700 capitalize">{type}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
