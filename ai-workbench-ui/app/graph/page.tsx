'use client'

export default function GraphPage() {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Knowledge Graph</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Explore table lineage and data relationships
        </p>
      </div>

      <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
          <div className="text-center">
            <div className="text-6xl mb-4">🕸️</div>
            <h3 className="text-xl font-semibold mb-2">Lineage Graph</h3>
            <p>Interactive knowledge graph visualization coming soon</p>
            <p className="text-sm mt-2">Neo4j integration with D3.js/Cytoscape</p>
          </div>
        </div>
      </div>
    </div>
  )
}
